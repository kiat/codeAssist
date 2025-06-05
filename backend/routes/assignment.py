import uuid
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from api import db
from api.models import Assignment, AssignmentExtension, Submission, RegradeRequest, Course
from api.schemas import AssignmentSchema, CourseSchema, AssignmentExtensionSchema
from util.errors import NotFoundError, BadRequestError, InternalProcessingError

assignment = Blueprint('assignment', __name__)

@assignment.route('/update_assignment', methods=["PUT"])
@cross_origin()
def update_assignment():
    '''
    /update_assignment updates the assignment in the database
    Requires from the frontend a JSON containing:
    @param assignment_id    the id of the assignment
    @param name             the name of the assignment
    @param course_id        the id of the course
    '''
    data = request.json
    required_fields = ["assignment_id", "name", "course_id"]

    if not all(field in data for field in required_fields):
        raise BadRequestError("Missing required fields")

    assignment_id = data["assignment_id"]
    assignment_name = data["name"]
    course_id = data["course_id"]

    # Check for name conflict in the same course
    existing_assignment = db.session.query(Assignment).filter(
        Assignment.course_id == course_id,
        Assignment.name == assignment_name,
        Assignment.id != assignment_id
    ).first()

    if existing_assignment:
        raise BadRequestError("An assignment with this name already exists")

    del data["assignment_id"]

    updated_assignment_info = {getattr(Assignment, name): val for name, val in data.items()}

    try:
        updated_rows = db.session.query(Assignment).filter_by(id=assignment_id).update(updated_assignment_info)
        if not updated_rows:
            raise NotFoundError("Assignment not found")
        db.session.commit()
        return jsonify({"message": "Assignment updated successfully"}), 200
    except Exception:
        db.session.rollback()
        raise InternalProcessingError("Failed to update assignment")
    
@assignment.route('/get_assignment', methods=["GET"])
@cross_origin()
def get_assignment():
    '''
    /get_assignment gets the assignment from the database
    Requires from the frontend a JSON containing:
    @param assignment_id    the id of the assignment
    '''
    assignment_id = request.args.get("assignment_id")
    assignment_obj = db.session.query(Assignment).filter_by(id=assignment_id).first()

    if not assignment_id:
        raise BadRequestError("Missing assignment_id")
    
    if not assignment_obj:
        raise NotFoundError("Assignment not found")

    result = AssignmentSchema().dump(assignment_obj, many=False)
    return jsonify(result), 200


@assignment.route('/create_assignment', methods=["POST"])
@cross_origin()
def create_assignment():
    '''
    /create_assignment creates an assignment and generates an assignment
    id in the database
    Requires from the frontend a JSON containing:
    @param name         the name of the assignment
    @param course_id    id of the course
    '''
    assignment_data = request.json

    assignment_name = assignment_data.get("name")
    course_id = assignment_data.get("course_id")

    if not assignment_name or not course_id:
        raise BadRequestError("Missing assignment name or course ID")

    try:
    # Check if assignment already exists for the course
        existing_assignment = db.session.query(Assignment).filter_by(course_id=course_id, name=assignment_name).one_or_none()
        if existing_assignment:
            raise BadRequestError("An assignment with this name already exists")

        assignment_id = str(uuid.uuid4())
        assignment_data["id"] = assignment_id
        # not creating a container yet
        assignment_data["container_id"] = None
        valid_assignment_data = {k: v for k, v in assignment_data.items() if v is not None or isinstance(v, bool)}

        db.session.add(Assignment(**valid_assignment_data))
        db.session.commit()
        
        # Fetch created assignment to return response
        created_assignment = db.session.query(Assignment).filter_by(id=assignment_id).first()
        if not created_assignment:
            raise InternalProcessingError("Assignment creation failed")  # Handle edge case

        result = AssignmentSchema().dump(created_assignment)
        return jsonify(result), 200
    except (BadRequestError, NotFoundError) as e:
        raise e
    except Exception as e:
        db.session.rollback()
        raise InternalProcessingError("Failed to create assignment")

@assignment.route('/duplicate_assignment', methods=["POST", "GET"])
@cross_origin()
def duplicate_assignment():
    '''
    /duplicate_assignment duplicates an existing assignment with a new name
    Requires from the frontend a JSON containing:
    @param oldAssignmentId         id of the old assignment
    @param newAssignmentTitle      name of the new assignment
    @param currentCourseId         id of the current course
    '''

    data = request.json
    required_fields = ["oldAssignmentId", "newAssignmentTitle", "currentCourseId"]

    if not all(field in data for field in required_fields):
        raise BadRequestError("Missing required fields")
    
    old_assignment_id = data["oldAssignmentId"]
    new_name = data["newAssignmentTitle"]
    current_course_id = data["currentCourseId"]

    try:
        old_assignment = db.session.query(Assignment).filter_by(id=old_assignment_id).one_or_none()
        if old_assignment is None:
            raise NotFoundError("Old assignment not found")

        course_assignment = db.session.query(Assignment).filter_by(
            course_id=current_course_id,
            name=new_name
        ).one_or_none()

        if course_assignment is not None:
            raise BadRequestError("An assignment with this name already exists in this course")

        new_assignment_id = str(uuid.uuid4())
        old_assignment_data = AssignmentSchema().dump(old_assignment)
        old_assignment_data['id'] = new_assignment_id
        old_assignment_data['name'] = new_name
        old_assignment_data['course_id'] = current_course_id

        new_assignment = Assignment(**old_assignment_data)
        db.session.add(new_assignment)
        db.session.commit()

        new_assignment_data = AssignmentSchema().dump(new_assignment)
        return jsonify(new_assignment_data), 201
    
    except (BadRequestError, NotFoundError) as e:
        raise e
    except Exception as e:
        db.session.rollback()
        raise InternalProcessingError("Failed to duplicate assignment")

@assignment.route('/delete_assignment', methods=["DELETE"])
@cross_origin()
def delete_assignment():
    assignment_id = request.args.get("assignment_id")
    if not assignment_id:
        raise BadRequestError("Missing assignment ID")
    
    #delete regrade requests, submissions, and assignment
    try:
        db.session.query(RegradeRequest).filter(
            RegradeRequest.submission_id.in_(
                db.session.query(Submission.id).filter(
                    Submission.assignment_id == assignment_id
                )
            )
        ).delete(synchronize_session=False)

        db.session.query(Submission).filter(
            Submission.assignment_id == assignment_id
        ).delete(synchronize_session=False)

        deleted = db.session.query(Assignment).filter(
            Assignment.id == assignment_id
        ).delete(synchronize_session=False)

        db.session.commit()

        if deleted:
            return jsonify("Assignment deleted successfully"), 200
        else:
            raise NotFoundError("Assignment not found")

    except Exception:
        db.session.rollback()
        raise InternalProcessingError("Failed to delete assignment")

@assignment.route('/delete_submissions', methods=["DELETE"])
@cross_origin()
def delete_submissions():
    assignment_id = request.args.get("assignment_id")
    if not assignment_id:
        raise BadRequestError("Missing assignment ID")

    # Fetch all submissions for this assignment
    related_submissions = db.session.query(Submission).filter_by(assignment_id=assignment_id).all()
    if not related_submissions:
        raise NotFoundError("No submissions found for this assignment")

    try:
        for submission in related_submissions:
            # Delete all regrade requests for this submission
            db.session.query(RegradeRequest).filter_by(submission_id=submission.id).delete(synchronize_session=False)
            # Delete the submission itself
            db.session.delete(submission)
        db.session.commit()
        return jsonify("Submissions deleted successfully"), 200
    except Exception:
        db.session.rollback()
        raise InternalProcessingError("Failed to delete submissions")


@assignment.route('/create_extension', methods=["POST", "GET"])
@cross_origin()
def create_extension():
    data = request.json
    required_fields = ["assignment_id", "student_id"]

    if not all(field in data for field in required_fields):
        raise BadRequestError("Missing required fields")
    
    assignment_id = data["assignment_id"]
    student_id = data["student_id"]
    # Check if there are any extensions for this assignment and student
    related_extension = db.session.query(AssignmentExtension).filter_by(assignment_id=assignment_id, student_id=student_id).first()
    if related_extension:
        db.session.delete(related_extension)
        db.session.commit()

    extension_id = str(uuid.uuid4())
    release_date_extension = data['release_date_extension']
    due_date_extension = data['due_date_extension']
    late_due_date_extension = data['late_due_date_extension']

    extension_data = {
        "id": extension_id,
        "assignment_id": assignment_id,
        "student_id": student_id,
        "release_date_extension": release_date_extension,
        "due_date_extension": due_date_extension,
        "late_due_date_extension": late_due_date_extension
    }
    try:
        db.session.add(AssignmentExtension(**extension_data))
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise InternalProcessingError("Failed to create extension")
    newExtension = db.session.query(AssignmentExtension).filter_by(id=extension_id).first()
    newExtension = AssignmentExtensionSchema().dump(newExtension, many=False)
    return jsonify(newExtension)

@assignment.route('/get_extension', methods=["GET"])
@cross_origin()
def get_extension():
    assignment_id = request.args.get("assignment_id")
    student_id = request.args.get("student_id")
    
    if not assignment_id or not student_id:
        raise BadRequestError("Missing assignment_id or student_id")

    try:
        extension = db.session.query(AssignmentExtension).filter_by(
            assignment_id=assignment_id, 
            student_id=student_id
        ).first()

        if extension is None:
            # Return a safe default instead of a 404 error
            extension_data = {
                "id": None,
                "assignment_id": assignment_id,
                "student_id": student_id,
                "release_date_extension": None,
                "due_date_extension": None,
                "late_due_date_extension": None
            }
        else:
            extension_data = AssignmentExtensionSchema().dump(extension)

        return jsonify(extension_data), 200

    except Exception:
        raise InternalProcessingError("Failed to fetch extension")

@assignment.route('/get_assignment_extensions', methods=["GET"])
@cross_origin()
def get_assignment_extensions():
    assignment_id = request.args.get("assignment_id")
    
    if not assignment_id:
        raise BadRequestError("Missing assignment_id")

    try:
        extensions = db.session.query(AssignmentExtension).filter_by(
            assignment_id=assignment_id
        ).all()

        extensions_data = AssignmentExtensionSchema().dump(extensions, many=True)
        return jsonify(extensions_data), 200

    except (BadRequestError, NotFoundError) as e:
        raise e
    except Exception:
        raise InternalProcessingError("Failed to fetch assignment extensions")
    
@assignment.route('/delete_extension', methods=["DELETE"])
@cross_origin()
def delete_extension():
    extension_id = request.args.get("extension_id")
    if not extension_id:
        raise BadRequestError("Missing extension_id")
    
    try:
        extension = db.session.query(AssignmentExtension).filter_by(id=extension_id).first()
        if not extension:
            raise NotFoundError("Extension not found")

        db.session.delete(extension)
        db.session.commit()

        return jsonify({"message": "Extension deleted successfully"}), 200
    except (BadRequestError, NotFoundError) as e:
        raise e
    except Exception:
        db.session.rollback()
        raise InternalProcessingError("Failed to delete extension")

@assignment.route('/courses', methods=["GET"])
@cross_origin()
def get_courses():
    instructor_id = request.args.get("instructor_id")
    if instructor_id:
        courses = db.session.query(Course).filter_by(instructor_id=instructor_id).all()
    else:
        courses = db.session.query(Course).all()
    
    courses_data = CourseSchema().dump(courses, many=True)
    return jsonify(courses_data)