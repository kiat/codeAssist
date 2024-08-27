import uuid
import requests
import random
import string
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from api import db
from api.models import User
from api.schemas import UserSchema

user = Blueprint('user', __name__)

# TODO THIS ROUTE IS NOT BEING USED AT THE MOMENT
@user.route('/create_user', methods=["GET","POST"])
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
    if request.method != "POST":
        return "all good"
    user_id = str(uuid.uuid4())
    name = request.json['name']
    password = request.json['password']
    email_address = request.json['email']
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

    res = None

    db.session.add(User(**user_data))
    db.session.commit()
    res = db.session.query(User).filter_by(id=user_id)
    res = UserSchema().dump(res, many=True)[0]

    # if role == 2:
    #     db.session.add(Student(**user_data))
    #     db.session.commit()
    #     res = db.session.query(Student).filter_by(id=user_id)
    #     res = StudentSchema().dump(res, many=True)[0]

    response = jsonify(res)
    return response

@user.route('/user_login', methods = ["GET", "POST"])
@cross_origin()
def user_login():

    email = request.json['email']
    password = request.json['password']

    res = db.session.query(User).filter_by(email_address=email, password=password)
    res = UserSchema().dump(res, many=True)

    if len(res) == 0:
        return "No user found", 404

    return jsonify(res[0])

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
    @param role         role of the user

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

    response = jsonify(res)
    return response

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

    # or data['aud'] != google_client_id_link - maybe should be added as a precaution
    if 'error' in data:
        return "Invalid google token", 400
    
    # Check the database if there is already a valid login in place
    email = data['email']

    res = db.session.query(User).filter_by(email_address=email)
    res = UserSchema().dump(res, many=True)

    if len(res) == 0:
        return email, 202

    return jsonify(res[0])

@user.route('/get_users', methods = ["GET"])
@cross_origin()
def get_users():
    email = request.args.get("email")
    # role = request.args.get("role")

    res = db.session.query(User).filter_by(email_address=email)
    result = UserSchema().dump(res, many=True)
    # print(result)
    
    # TODO THIS IS A MAJOR SECURITY VULNERABILITY, IT SHOWS PASSWORDS!
    if len(result) == 0:
        return "No user found", 404
    return jsonify(result)

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
    user_id = request.args.get("id")
    User.query.filter_by(id=user_id).delete()
    # user = UserSchema().dump(user)
    db.session.commit()
    return "Success", 200