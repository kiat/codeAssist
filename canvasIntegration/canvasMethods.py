from canvasapi import Canvas
import psycopg2
import uuid
import requests

# Configuration for Canvas API and base URL
HOST = "canvas.instructure.com"
base_url = 'https://{}/api/v1/courses'.format(HOST)


access_token = "7~LtosN8jbYTcfAqkdIxQitgO0lXQJ0s4d7xzqqmXFb00aVPfXgRTeM0oHdWvq3og4"
header = {'Authorization': 'Bearer ' + access_token}


# Create a canvas object using the API
canvas = Canvas("https://canvas.instructure.com", access_token)

def get_user(user_id):
    """
    Get user information from the Canvas API given a user_id.

    Args:
        user_id: The user's ID.

    Returns:
        student: A canvasapi user object.
    """
    student = canvas.get_user(user_id)
    return student

def get_courses_from_user(user):
    """
    Get a list of courses for a given user.

    Args:
        user: A canvasapi user object.

    Returns:
        courses: A list of canvasapi course objects.
    """
    courses = list(user.get_courses())
    course_list = []
    for course in courses:
        course_list.append(course.id)
    return courses

def get_course(course_id_list):
    """
    Get a list of course objects for a list of course IDs.

    Args:
        course_id_list: A list of course IDs.

    Returns:
        courses_list: A list of canvasapi course objects.
    """
    courses_list = []
    for course_id in course_id_list:
        course = canvas.get_course(course_id)
        courses_list.append(course)
    return courses_list



def get_students(course):
    """
    Get a list of students enrolled in a given course.

    Args:
        course: A canvasapi course object.

    Returns:
        students: A list of dictionaries containing student information.
    """
    student_list = list(course.get_enrollments())
    students = []
    for student in student_list:
        sis_user_id = student.user_id
        user = student.user
        print("USERSS")
        print(user)
        if student.type == "StudentEnrollment":
            try:
                email = student.user["login_id"]
            except KeyError:
                email = "N/A"
            student_dict = {"name": student.user["name"], "email": email, "sis_user_id": sis_user_id}
            students.append(student_dict)
    return students

def get_instructors(course):
    """
    Get a list of instructors for a given course.

    Args:
        course: A canvasapi course object.

    Returns:
        instructors: A list of dictionaries containing instructor information.
    """
    student_list = list(course.get_enrollments())
    instructors = []
    print("teacher", student_list)
    for student in student_list:
        sis_user_id = student.user_id
        if student.type == "TeacherEnrollment":
            try:
                email = student.login_id
            except AttributeError:
                email = "N/A"
            student_dict = {"name": student.user["name"], "email": email, "sis_user_id": sis_user_id}
            instructors.append(student_dict)
    return instructors

def get_assignments(course):
    """
    Get a list of assignments for a given course.

    Args:
        course: A canvasapi course object.

    Returns:
        assignment_list: A list of dictionaries containing assignment information.
    """
    ...
    assignments = list(course.get_assignments())
    print(assignments)
    assignment_list = []
    for assignment in assignments:
        assignment_info = {}
        assignment_info["name"] = assignment.name
        assignment_info["due date"] = assignment.due_at
        assignment_info['points'] = assignment.points_possible
        assignment_info['allowed attempts'] = assignment.allowed_attempts
        assignment_info['sis_course_id'] = course.id
        assignment_info['sis_assignment_id'] = assignment.id
        assignment_list.append(assignment_info)
    return assignment_list

def get_data_from_canvas():
    """
    Get data from Canvas API, including user, courses, students, instructors, and assignments.

    Returns:
        dict1: A dictionary containing lists of students, courses, and assignments.
    """
    user = get_user(37784013)
    courses_id = get_courses_from_user(user)
    courses = get_course(courses_id)
    courses.pop()
    dict1 = {}
    dict1["students"] = []
    dict1["courses"] = []
    dict1["assignments"] = []
    for course in courses:
        print("Course Name: " + str(course.name))
        students = get_students(course)
        #print("Students: " + str(students))
        for student in students:
            dict1["students"].append(student)
        instructor = get_instructors(course)[0]
        course_tuple = [course.name, instructor, course.id]
        dict1["courses"].append(course_tuple)
        #print("Instructor: " + str(instructor))
        assignments = get_assignments(course)
        for assignment in assignments:
            dict1["assignments"].append(assignment)
        print("Assignments: " + str(get_assignments(course)))
    return dict1



def check_if_instructor_in_database(cursor, instructor_id):
    """
     Check if an instructor with a given sis_user_id exists in the database.

     Args:
         cursor: A psycopg2 cursor object.
         instructor_id: The instructor's sis_user_id.

     Returns:
         The instructor's UUID if found, otherwise False.
     """
    postgres_select_query = """ SELECT id from instructors where sis_user_id = %s"""
    cursor.execute(postgres_select_query, [instructor_id])
    record = cursor.fetchall()
    if record:
        return record[0][0] #return instructor_uuid
    return False


def check_if_course_in_database(cursor, course_id):
    """
    Check if a course with a given sis_course_id exists in the database.

    Args:
        cursor: A psycopg2 cursor object.
        course_id: The course's sis_course_id.

    Returns:
        The course's UUID if found, otherwise False.
    """
    postgres_select_query = """ SELECT id from courses where sis_course_id = %s"""
    cursor.execute(postgres_select_query, [course_id])
    record = cursor.fetchall()
    if record:
        return record[0][0]  #return course_uuid
    return False

def check_if_assignment_in_database(cursor, assignment_id):
    """
    Check if an assignment with a given sis_assignment_id exists in the database.

    Args:
        cursor: A psycopg2 cursor object.
        assignment_id: The assignment's sis_assignment_id.

    Returns:
        The assignment's UUID if found, otherwise False.
    """
    postgres_select_query = """ SELECT id from assignments where sis_assignment_id = %s"""
    cursor.execute(postgres_select_query, [assignment_id])
    record = cursor.fetchall()
    if record:
        return record[0][0] #return assignment_uuid
    return False

def check_if_student_in_database(cursor, student_id):
    """
    Check if a student with a given sis_user_id exists in the database.

    Args:
        cursor: A psycopg2 cursor object.
        student_id: The student's sis_user_id.

    Returns:
        The student's UUID if found, otherwise False.
    """
    postgres_select_query = """ SELECT id from students where sis_user_id = %s"""
    cursor.execute(postgres_select_query, [student_id])
    record = cursor.fetchall()
    if record:
        return record[0][0] #return student_uuid
    return False

def put_instructor_in_database(cursor, instructor_name, email_address, sis_id):
    """
    Insert a new instructor into the database.

    Args:
        cursor: A psycopg2 cursor object.
        instructor_name: The instructor's name.
        email_address: The instructor's email address.
        sis_id: The instructor's sis_user_id.

    Returns:
        instructor_id: The new instructor's UUID.
    """
    postgres_insert_query = """ INSERT INTO instructors (id, password, name, email_address, sis_user_id) VALUES (%s,%s,%s,%s,%s)"""
    instructor_id = str(uuid.uuid4())
    record_to_insert = (instructor_id, "N/A", instructor_name, email_address, sis_id)
    print("Added new instructor: " + instructor_name)
    cursor.execute(postgres_insert_query, record_to_insert)
    return instructor_id

def put_course_in_database(cursor, course_name, instructor_id, sis_course_id, sis_instructor_id):
    """
    Insert a new course into the database.

    Args:
        cursor: A psycopg2 cursor object.
        course_name: The course's name.
        instructor_id: The instructor's UUID.
        sis_course_id: The course's sis_course_id.
        sis_instructor_id: The instructor's sis_user_id.

    Returns:
        sis_course_id: The new course's sis_course_id.
    """
    postgres_insert_query = """ INSERT INTO courses (id, name, instructor_id, sis_course_id, sis_instructor_id) VALUES (%s,%s,%s,%s,%s)"""
    record_to_insert = (str(uuid.uuid4()), course_name, instructor_id, sis_course_id, sis_instructor_id)
    print("Added new course: " + course_name)
    cursor.execute(postgres_insert_query, record_to_insert)
    return sis_course_id

def put_student_in_database(cursor, student_name, email_address, sis_id):
    """
    Insert a new student into the database.

    Args:
        cursor: A psycopg2 cursor object.
        student_name: The student's name.
        email_address: The student's email address.
        sis_id: The student's sis_user_id.

    Returns:
        student_id: The new student's UUID.
    """
    postgres_insert_query = """ INSERT INTO students (id, password, name, email_address, sis_user_id) VALUES (%s,%s,%s,%s,%s)"""
    student_id = str(uuid.uuid4())
    record_to_insert = (student_id, "N/A", student_name, email_address, sis_id)
    cursor.execute(postgres_insert_query, record_to_insert)
    return student_id

def put_assignment_in_database(cursor, assignment_name, course_id, autograder_points, due_date, sis_assignment_id, sis_course_id):
    """
    Insert a new assignment into the database.

    Args:
        cursor: A psycopg2 cursor object.
        assignment_name: The assignment's name.
        course_id: The course's UUID.
        autograder_points: The points possible for the assignment.
        due_date: The assignment's due date.
        sis_assignment_id: The assignment's sis_assignment_id.
        sis_course_id: The course's sis_course_id.

    Returns:
        assignment_id: The new assignment's UUID.
    """
    postgres_insert_query = """ INSERT INTO assignments (id, name, course_id, autograder_points, due_date, sis_assignment_id, sis_course_id) VALUES (%s,%s,%s,%s,%s,%s,%s)"""
    assignment_id = str(uuid.uuid4())
    record_to_insert = (assignment_id, assignment_name, course_id, autograder_points, due_date, sis_assignment_id, sis_course_id)
    cursor.execute(postgres_insert_query, record_to_insert)
    return assignment_id

def put_submission_in_database(cursor, sis_assignment_id, sis_student_id):
    """
    Insert a new submission into the database.

    Args:
        cursor: A psycopg2 cursor object.
        sis_assignment_id: The assignment's sis_assignment_id.
        sis_student_id: The student's sis_user_id.

    Returns:
        submission_id: The new submission's UUID.
    """
    postgres_insert_query = """ INSERT INTO submissions (id, student_id, assignment_id, sis_assignment_id, sis_user_id) VALUES (%s,%s,%s,%s,%s)"""
    student_uuid = check_if_student_in_database(cursor, sis_student_id)
    assignment_uuid = check_if_assignment_in_database(cursor, sis_assignment_id)
    submission_id = str(uuid.uuid4())
    record_to_insert = (submission_id, student_uuid, assignment_uuid, sis_assignment_id, sis_student_id)
    cursor.execute(postgres_insert_query, record_to_insert)
    return submission_id
