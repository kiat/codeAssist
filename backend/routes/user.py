import uuid
from flask import Blueprint, request, jsonify, current_app, url_for
from flask_cors import cross_origin
from api import db
from api.models import User
from api.schemas import UserSchema
from util.errors import BadRequestError, NotFoundError, InternalProcessingError, ConflictError
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message
from flask import current_app
from api import mail  # Import mail from the main app


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

    user = User(
        id=user_id,
        name=name,
        email_address=email_address,
        sis_user_id=sis_user_id,
        role=role
    )
    user.set_password(password) # Store hashed password

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise InternalProcessingError("Error creating user")
    
    res = UserSchema().dump(user)

    return jsonify(res), 201

@user.route('/user_login', methods = ["POST"])
@cross_origin()
def user_login():
    email = request.json.get('email')
    password = request.json.get('password')

    if not email or email == "" or not password or password == "":
        raise BadRequestError("Missing email or password")

    res = db.session.query(User).filter_by(email_address=email).first()

    # check hashed password
    if not res or not res.check_password(password):
        raise NotFoundError("Email and password combination not found")
    
    if not res:
        raise NotFoundError("Email and password combination not found")
    
    res = UserSchema().dump(res)

    return jsonify(res), 200



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

# Reset password helpers
PASSWORD_RESET_SALT = "password-reset-salt"
def generate_reset_token(email):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps(email, salt=PASSWORD_RESET_SALT)

def verify_reset_token(token, expiration=3600):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt=PASSWORD_RESET_SALT, max_age=expiration)
    except:
        return None
    return email

@user.route('/reset_password', methods=['POST'])
@cross_origin()
def reset_request():
    '''
    /reset_password allows users to request a password reset by email.
    '''
    email = request.json.get('email')
    if not email or email == "":
        raise BadRequestError("Missing email")

    user = User.query.filter_by(email_address=email).first()
    if not user:
        raise NotFoundError("Email not found")

    # Generate Token
    token = generate_reset_token(user.email_address)
    reset_url = url_for('user.reset_token', token=token, _external=True)

    # Send Email
    try:
        msg = Message(
            subject='Password Reset Request',
            recipients=[email],
            body=f'''To reset your password, visit the following link:
{reset_url}

If you did not request this, ignore this email.
'''
        )
        mail.send(msg)
    except Exception as e:
        raise InternalProcessingError("Failed to send email")

    return jsonify({"message": "An email has been sent with reset instructions"}), 200


@user.route('/reset_password/<token>', methods=['POST'])
@cross_origin()
def reset_token(token):
    '''
    /reset_password/<token> allows users to reset their password.
    '''
    email = verify_reset_token(token)
    if email is None:
        raise BadRequestError("Invalid or expired token")

    new_password = request.json.get('password')
    if not new_password or new_password == "":
        raise BadRequestError("Password required")

    # Find User
    user = User.query.filter_by(email_address=email).first()
    if not user:
        raise NotFoundError("User not found")

    user.set_password(new_password)  # Hash password before storing
    db.session.commit()

    return jsonify({"message": "Password updated successfully"}), 200
