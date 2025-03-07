import uuid
from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin
from api import db
from api.models import User
from api.schemas import UserSchema
from util.errors import BadRequestError, NotFoundError

user = Blueprint('user', __name__)

# TODO THIS ROUTE IS NOT BEING USED AT THE MOMENT
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

    Roles have 3 categories:
    0 = Instructor
    1 = TA
    2 = Student
    '''

    # TODO Create new database tables to unify all users
    user_id = str(uuid.uuid4())
    name = request.json['name']
    password = request.json['password']
    email_address = request.json['email_address']
    sis_user_id = request.json['eid']
    role = request.json['role']

    user = User(
        id=user_id,
        name=name,
        email_address=email_address,
        password=password,
        sis_user_id=sis_user_id,
        role=role
    )

    res = None

    db.session.add(user)
    db.session.commit()
    res = UserSchema().dump(user)

    # if role == 2:
    #     db.session.add(Student(**user_data))
    #     db.session.commit()
    #     res = db.session.query(Student).filter_by(id=user_id)
    #     res = StudentSchema().dump(res, many=True)[0]
    response = jsonify(res)
    return response, 201

@user.route('/user_login', methods = ["POST"])
@cross_origin()
def user_login():
    email = request.json['email']
    password = request.json['password']

    if not email or email == "" or not password or password == "":
        raise BadRequestError("Missing email or password")

    res = db.session.query(User).filter_by(email_address=email, password=password).first()

    if not res:
        raise NotFoundError("Email and password combination not found")
    
    res = UserSchema().dump(res)

    return jsonify(res)



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

    instructor = db.session.query(User).filter_by(id=insid)
    instructor = UserSchema().dump(instructor, many=True)[0]

    return jsonify(instructor)

@user.route('/delete_user', methods=["DELETE"])
@cross_origin()
def delete_user():
    assert current_app
    user_id = request.args.get("id")
    User.query.filter_by(id=user_id).delete()
    # user = UserSchema().dump(user)
    db.session.commit()
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
    new_name = request.json.get('name')
    new_password = request.json.get('password')

    # Find the user in the database
    user = db.session.query(User).filter_by(id=user_id).first()

    # Update the fields if provided
    if new_name:
        user.name = new_name
    if new_password:
        user.password = new_password

    # Commit changes to the database
    db.session.commit()

    # Return a success response
    return jsonify({"message": "Account updated successfully"}), 200