import uuid
from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin
from api import db
from api.models import User
from api.schemas import UserSchema
from util.errors import BadRequestError, NotFoundError, InternalProcessingError, ConflictError
from util.encryption_utils import hash_password, verify_password


user = Blueprint('user', __name__)

@user.route('/create_user', methods=["POST"])
@cross_origin()
def create_user():
    '''
    /create_user creates a student and generates a sis_user_id in the database
    Requires from the frontend a JSON containing:
    @param name         name of the user
    @param password     password for the user
    @param email        email of the user
    @param eid          eid of the user
    @param role         role of the user

    Roles have 2 categories:
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
        user.password = new_password

    # Commit changes to the database
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise InternalProcessingError("Error updating account")

    # Return a success response
    return jsonify({"message": "Account updated successfully"}), 200