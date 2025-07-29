import uuid
import requests
import random
import string
from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin
from api import db
from api.models import User, Course, AdminEmail
from api.schemas import UserSchema, CourseSchema
from util.errors import BadRequestError, NotFoundError, InternalProcessingError, ConflictError
from util.encryption_utils import hash_password, verify_password


user = Blueprint('user', __name__)

@user.route('/create_user', methods=["POST"])
@cross_origin()
def create_user():
    '''
    /create_user creates a user and generates a sis_user_id in the database
    Requires from the frontend a JSON containing:
    @param name         name of the user
    @param password     password for the user
    @param email        email of the user
    @param eid          eid of the user
    @param role         role of the user

    Roles have 3 categories:
    Admin
    Instructor
    Student
    '''

    name = request.json.get('name')
    password = request.json.get('password')
    email_address = request.json.get('email_address')
    sis_user_id = request.json.get('eid')
    role = request.json.get('role')
    if not name or name == "" or not password or password == "" or not email_address or email_address == "" or not sis_user_id or sis_user_id == "" or not role or role == "":
        raise BadRequestError("Missing required fields")
    
    if not isinstance(role, str):
        role = str(role)

    role = role.lower()

    valid_roles = ["admin", "instructor", "student"]
    if role not in valid_roles:
        raise BadRequestError("Invalid role. Must be one of: admin, instructor, student")

    eid_check = db.session.query(User).filter_by(sis_user_id=sis_user_id).first()
    if eid_check:
        raise ConflictError("EID already in use")
    email_check = db.session.query(User).filter_by(email_address=email_address).first()
    if email_check:
        raise ConflictError("Email already in use")

    user_id = str(uuid.uuid4())

    hashed_password = hash_password(password)

    user = User(
        id=user_id,
        name=name,
        email_address=email_address,
        password=hashed_password,
        sis_user_id=sis_user_id,
        role=role
    )
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise InternalProcessingError("Error creating user")
    
    res = UserSchema().dump(user)

    return jsonify(res), 201

@user.route('/user_login', methods=["POST"])
@cross_origin()
def user_login():
    email = request.json.get('email')
    password = request.json.get('password')

    if not email or not password:
        raise BadRequestError("Missing email or password")

    # Fetch user by email only
    db_user = db.session.query(User).filter_by(email_address=email).first()
    if not db_user:
        raise NotFoundError("Email and password combination not found")


    # handle the case where the user is a dict (e.g., from a mock or test)
    # or an ORM object
    # If db_user is a dictionary, extract the password from it
    # If db_user is an ORM object, extract the password attribute
    if isinstance(db_user, dict):
        stored_hash = db_user.get('password')
    else:
        stored_hash = getattr(db_user, 'password')

    # Verify the provided password against the stored (hashed) password
    if not verify_password(password, stored_hash):
        raise NotFoundError("Email and password combination not found")

    # Serialize and return
    result = UserSchema().dump(db_user)
    return jsonify(result), 200

@user.route('/create_google_user', methods=["GET", "POST"])
@cross_origin()
def create_google_user():
    '''
    /create_user creates a student and generates a sis_user_id in the database
    Requires from the frontend a JSON containing:
    @param credential   Google ID Token to authenticate a valid login
    @param name         name of the user
    @param email        email of the user
    @param eid          eid of the user
    @param role         automatically set as admin
    Roles have 3 categories:
    0 = Instructor
    2 = Student
    '''
    id_token = request.json['credential']

    url = f'https://oauth2.googleapis.com/tokeninfo?id_token={id_token}'
    response = requests.get(url)
    data = response.json()

    # or data['aud'] != google_client_id_link - maybe should be added as a precaution
    if 'error' in data:
        return "Invalid google token", 400

    # TODO Create new database tables to unify all users
    if request.method != "POST":
        return "all good"

    # generate random, encrypted password to be used within the database
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for _ in range(12))

    user_id = str(uuid.uuid4())
    name = request.json['name']
    email_address = data['email']
    sis_user_id = request.json['eid']
    role = request.json['role']

    user_data = {
        "id": user_id,
        "name": name,
        "email_address": email_address,
        "password": password,
        "sis_user_id": sis_user_id,
        "role": role
    }

    db.session.add(User(**user_data))
    db.session.commit()

    res = db.session.query(User).filter_by(id=user_id)
    res = UserSchema().dump(res, many=True)[0]

    return jsonify(res)

@user.route('/google_login', methods=["POST", "GET"])
@cross_origin()
def google_login():
    '''
    /google_login logs in a user that exists in the database
    Requires from the frontend a JSON containing:
    @param email          email of the student
    '''
    id_token = request.json['credential']

    url = f'https://oauth2.googleapis.com/tokeninfo?id_token={id_token}'
    response = requests.get(url)
    data = response.json()

    if 'error' in data:
        return "Invalid google token", 400

    email = data['email']

    # Check if email is in admin_emails table
    is_admin = db.session.query(AdminEmail).filter_by(email=email).first() is not None

    user = db.session.query(User).filter_by(email_address=email).first()

    if not user:
        if not is_admin:
            return email, 202
        # Create new admin user
        user = User(
            id=str(uuid.uuid4()),
            name="admin",
            email_address=email,
            password='',
            sis_user_id=email,  # Use email as a unique sis_user_id
            role='admin',
            coding_insights='No history.'
        )
        db.session.add(user)
        db.session.commit()
        user_data = UserSchema().dump(user)
        return jsonify(user_data)

    # Existing user logic (update role if needed)
    if is_admin and user.role != "admin":
        user.role = "admin"
        db.session.commit()

    user_data = UserSchema().dump(user)
    return jsonify(user_data)

@user.route('/get_user_by_email', methods = ["GET"])
@cross_origin()
def get_user():
    email = request.args.get("email")
    if not email or email == "":
        raise BadRequestError("Missing email argument")

    res = db.session.query(User).with_entities(User.id, User.name, User.email_address, User.role).filter_by(email_address=email).first()
    if not res:
        raise NotFoundError("User not found")
    
    user = {
        "id": res.id,
        "name": res.name,
        "email_address": res.email_address,
        "role": res.role
    }
    return jsonify(user), 200

    #It shows an error for this method but the user_login works



@user.route('/get_user_by_id', methods=["GET"])
@cross_origin()
def get_user_by_id():
    '''
    /get_instructor_by_id gets the student from the database
    Requires from the frontend a JSON containing:
    @param id    the instructor id
    '''

    insid = request.args.get("id")
    if not insid: 
        raise BadRequestError("Missing user id")

    try:
        insid = str(uuid.UUID(insid))
    except (ValueError, TypeError):
        raise BadRequestError("Invalid user id")



    instructor_obj = db.session.query(User).filter_by(id=insid).first() 
    if not instructor_obj: 
        raise NotFoundError("User does not exist")
    
    instructor = UserSchema().dump(instructor_obj)


    return jsonify(instructor)

@user.route('/delete_user', methods=["DELETE"])
@cross_origin()
def delete_user():
    assert current_app

    user_id = request.args.get("id") 
    if not user_id: 
        raise BadRequestError("Missing User id")

    try: 
        user_id = str(uuid.UUID(user_id))
    except(ValueError, TypeError):
        raise BadRequestError("Invalid user id") 

    
    user = db.session.query(User).filter_by(id=user_id).first()
    if not user:
        raise NotFoundError("User Not Found")
    # user = UserSchema().dump(user)
    try:
        db.session.delete(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise InternalProcessingError("Error deleting user")
    return "Success", 200

@user.route('/update_account', methods=["PUT", "POST"])
@cross_origin()
def update_account():
    '''
    /update_account updates the name and/or password of a user.
    Requires from the frontend a JSON containing:
    @param id        the user id (required)
    @param name      the name for the user (optional)
    @param password  the password for the user (optional)
    '''
    # Extract required and optional data from the request
    user_id = request.json.get('id')
    if not user_id:
        raise BadRequestError("Missing user id")
    
    try: 
        user_id = str(uuid.UUID(user_id))
    except(ValueError, TypeError):
        raise BadRequestError("Invalid  user id") 
    

    
    new_name = request.json.get('name')
    new_password = request.json.get('password')


    # Find the user in the database
    user = db.session.query(User).filter_by(id=user_id).first()

    if not user:
        raise NotFoundError("User Not Found")

    # Update the fields if provided
    if new_name:
        user.name = new_name
    if new_password:
        user.password = hash_password(new_password)

    # Commit changes to the database
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise InternalProcessingError("Error updating account")

    # Return a success response
    return jsonify({"message": "Account updated successfully"}), 200

@user.route('/get_all_courses', methods=["GET"])
@cross_origin()
def get_all_courses():
    """Get all courses in the system."""
    courses = db.session.query(Course).all()
    return jsonify(CourseSchema().dump(courses, many=True)), 200

@user.route('/get_all_instructors', methods=["GET"])
@cross_origin()
def get_all_instructors():
    """Get all instructors in the system."""
    instructors = db.session.query(User).filter_by(role="instructor").all()
    return jsonify(UserSchema().dump(instructors, many=True)), 200

@user.route('/get_all_students', methods=["GET"])
@cross_origin()
def get_all_students():
    """Get all students in the system."""
    students = db.session.query(User).filter_by(role="student").all()
    return jsonify(UserSchema().dump(students, many=True)), 200

@user.route('/admin_update_account', methods=["PUT", "POST"])
@cross_origin()
def admin_update_account():
    '''
    /admin_update_account allows admins to update user account details.
    Requires from the frontend a JSON containing:
    @param id              the user id (required)
    @param name            the name for the user (optional)
    @param email_address   the email for the user (optional)
    @param sis_user_id     the EID for the user (optional)
    '''
    user_id = request.json.get('id')
    new_name = request.json.get('name')
    new_email = request.json.get('email_address')
    new_sis_user_id = request.json.get('sis_user_id')

    if not user_id:
        raise BadRequestError("Missing user id")

    user = db.session.query(User).filter_by(id=user_id).first()
    if not user:
        raise NotFoundError("User not found")

    if new_email and new_email != user.email_address:
        existing_user = db.session.query(User).filter_by(email_address=new_email).first()
        if existing_user:
            raise ConflictError("Email already in use")

    if new_sis_user_id and new_sis_user_id != user.sis_user_id:
        existing_user = db.session.query(User).filter_by(sis_user_id=new_sis_user_id).first()
        if existing_user:
            raise ConflictError("EID already in use")

    if new_name:
        user.name = new_name
    if new_email:
        user.email_address = new_email
    if new_sis_user_id:
        user.sis_user_id = new_sis_user_id

    db.session.commit()

    return jsonify({"message": "Account updated successfully"}), 200

# New route to retrieve an instructor's id using their EID
@user.route('/get_instructor_by_eid', methods=["GET"])
@cross_origin()
def get_instructor_by_eid():
    eid = request.args.get("eid")
    if not eid:
        raise BadRequestError("Missing EID")

    user = db.session.query(User).filter_by(sis_user_id=eid, role="instructor").first()
    if not user:
        raise NotFoundError("Instructor with this EID not found")

    return jsonify(UserSchema().dump(user)), 200
