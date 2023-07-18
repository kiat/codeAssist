import uuid
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from api import db
from api.models import Student, Instructor
from api.schemas import StudentSchema, InstructorSchema

user = Blueprint('user', __name__)

# TODO THIS ROUTE IS NOT BEING USED AT THE MOMENT
@user.route('/create_user', methods=["GET","POST"])
@cross_origin
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
    }

    res = None

    if role == 0:
        db.session.add(Instructor(**user_data))
        db.session.commit()

        res = db.session.query(Instructor).filter_by(id=user_id)
        res = InstructorSchema().dump(res, many=True)[0]

    elif role == 2:
        db.session.add(Student(**user_data))
        db.session.commit()
        res = db.session.query(Student).filter_by(id=user_id)
        res = StudentSchema().dump(res, many=True)[0]


    response = jsonify(res)
    return response

@user.route('/create_student', methods=["GET", "POST"])
@cross_origin()
def create_student():
    '''
    /create_student creates a student and generates a sis_user_id
    in the database
    Requires from the frontend a JSON containing:
    @param name         name of the student
    @param password     password for the student
    @param email        email of the student
    @param eid          eid of the student
    '''
    # TODO: Remove below - /create_student should only be POST
    if request.method != "POST":
        return "all good"
    user_id = str(uuid.uuid4())
    name = request.json['name']
    password = request.json['password']
    email_address = request.json['email']
    sis_user_id = request.json['eid']

    user_data = {
        "id": user_id,
        "name": name,
        "email_address": email_address,
        "password": password,
        "sis_user_id": sis_user_id,
    }

    db.session.add(Student(**user_data))
    db.session.commit()

    res = db.session.query(Student).filter_by(id=user_id)
    res = StudentSchema().dump(res, many=True)[0]
    response = jsonify(res)
    return response

@user.route('/student_login', methods=["POST", "GET"])
@cross_origin()
def student_login():
    '''
    /student_login logs in a student that exists in the database
    Requires from the frontend a JSON containing:
    @param email          email of the student
    @param password     password for the student
    '''
    email = request.json['email']
    password = request.json['password']

    res = db.session.query(Student).filter_by(email_address=email, password=password)
    res = StudentSchema().dump(res, many=True)

    if len(res) == 0:
        return "No user found", 404

    return jsonify(res[0])

@user.route('/create_instructor', methods=["POST", "GET"])
@cross_origin()
def create_instructor():
    '''
    /create_instructor creates an instructor and generates a
    sis_user_id in the database
    Requires from the frontend a JSON containing:
    @param name         name of the instructor
    @param password     password for the instructor
    @param email        email of the instructor
    @param eid          eid of the instructor
    '''
    user_id = str(uuid.uuid4())
    name = request.json['name']
    password = request.json['password']
    email_address = request.json['email']
    sis_user_id = request.json['eid']

    user_data = {
        "id": user_id,
        "name": name,
        "email_address": email_address,
        "password": password,
        "sis_user_id": sis_user_id,
    }

    db.session.add(Instructor(**user_data))
    db.session.commit()

    res = db.session.query(Instructor).filter_by(id=user_id)
    res = InstructorSchema().dump(res, many=True)[0]

    return jsonify(res)

@user.route('/instructor_login', methods=["POST", "GET"])
@cross_origin()
def instructor_login():
    '''
    /instructor_login logs in an instructor that exists in
    the database
    Requires from the frontend a JSON containing:
    @param email          email of the instructor
    @param password     password for the instructor
    '''
    email = request.json['email']
    password = request.json['password']

    res = db.session.query(Instructor).filter_by(email_address=email, password=password)
    res = InstructorSchema().dump(res, many=True)[0]

    # TODO: What if an instructor does not exist in the database?
    # See: /student_login
    return jsonify(res)

@user.route('/update_account', methods = ["POST"])
@cross_origin()
def update_account():
    '''
    /update_account updates account details in the database
    Requires from the frontend a JSON containing:
    @param id       id of user (can be either instructor or student)
    '''
    user_id = request.json["id"]
    data = request.json
    del data["id"]

    student = db.session.query(Student).filter(Student.id == user_id).first()
    instructor = db.session.query(Instructor).filter(Instructor.id == user_id).first()
    if not student:
        instructor_update = db.session.query(Instructor).filter_by(id = user_id).update(data)
        db.session.commit()
    if not instructor:
        student_update = db.session.query(Student).filter_by(id = user_id).update(data)
        db.session.commit()

    return jsonify({"message": "Success"}), 200

@user.route('/get_student', methods=["GET"])
@cross_origin()
def get_student():
    '''
    /get_student gets the student from the database
    Requires from the frontend a JSON containing:
    @param email    the student email
    '''
    email = request.args.get("email")

    student = db.session.query(Student).filter_by(email_address=email)
    student = StudentSchema().dump(student, many=True)[0]

    return jsonify(student)