from canvasapi import Canvas
import psycopg2
import uuid
import requests

HOST = "canvas.instructure.com"
base_url = 'https://{}/api/v1/courses'.format(HOST)


access_token = "7~LtosN8jbYTcfAqkdIxQitgO0lXQJ0s4d7xzqqmXFb00aVPfXgRTeM0oHdWvq3og4"
header = {'Authorization': 'Bearer ' + access_token}


#get course from canvas website
canvas = Canvas("https://canvas.instructure.com", access_token)

#Tasks:
#Implement external tool in canvas assignments DONE
#get students in CodeAssist database DONE
#get courses in CodeAssist database DONE
#FIgure out how to add external app in add app menu (View configuration -> add app) DONE
#Enrollment only allowed through LTI when automatic roster sync is enabled DONE
#Make new folder on github and put on github DONE
#Get grade from codeassist assignments to canvas DONE
#create script to sync roster DONE

def get_user(user_id):
    student = canvas.get_user(user_id)
    return student

def get_courses_from_user(user):
    courses = list(user.get_courses())
    course_list = []
    for course in courses:
        course_list.append(course.id)
    return courses

def get_course(course_id_list):
    courses_list = []
    for course_id in course_id_list:
        course = canvas.get_course(course_id)
        courses_list.append(course)
    return courses_list



def get_students(course):
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
    postgres_select_query = """ SELECT id from instructors where sis_user_id = %s"""
    cursor.execute(postgres_select_query, [instructor_id])
    record = cursor.fetchall()
    if record:
        return record[0][0] #return instructor_uuid
    return False


def check_if_course_in_database(cursor, course_id):
    postgres_select_query = """ SELECT id from courses where sis_course_id = %s"""
    cursor.execute(postgres_select_query, [course_id])
    record = cursor.fetchall()
    if record:
        return record[0][0]  #return course_uuid
    return False

def check_if_assignment_in_database(cursor, assignment_id):
    postgres_select_query = """ SELECT id from assignments where sis_assignment_id = %s"""
    cursor.execute(postgres_select_query, [assignment_id])
    record = cursor.fetchall()
    if record:
        return record[0][0] #return assignment_uuid
    return False

def check_if_student_in_database(cursor, student_id):
    postgres_select_query = """ SELECT id from students where sis_user_id = %s"""
    cursor.execute(postgres_select_query, [student_id])
    record = cursor.fetchall()
    if record:
        return record[0][0] #return student_uuid
    return False

def put_instructor_in_database(cursor, instructor_name, email_address, sis_id):
    postgres_insert_query = """ INSERT INTO instructors (id, password, name, email_address, sis_user_id) VALUES (%s,%s,%s,%s,%s)"""
    instructor_id = str(uuid.uuid4())
    record_to_insert = (instructor_id, "N/A", instructor_name, email_address, sis_id)
    print("Added new instructor: " + instructor_name)
    cursor.execute(postgres_insert_query, record_to_insert)
    return instructor_id

def put_course_in_database(cursor, course_name, instructor_id, sis_course_id, sis_instructor_id):
    postgres_insert_query = """ INSERT INTO courses (id, name, instructor_id, sis_course_id, sis_instructor_id) VALUES (%s,%s,%s,%s,%s)"""
    record_to_insert = (str(uuid.uuid4()), course_name, instructor_id, sis_course_id, sis_instructor_id)
    print("Added new course: " + course_name)
    cursor.execute(postgres_insert_query, record_to_insert)
    return sis_course_id

def put_student_in_database(cursor, student_name, email_address, sis_id):
    postgres_insert_query = """ INSERT INTO students (id, password, name, email_address, sis_user_id) VALUES (%s,%s,%s,%s,%s)"""
    student_id = str(uuid.uuid4())
    record_to_insert = (student_id, "N/A", student_name, email_address, sis_id)
    cursor.execute(postgres_insert_query, record_to_insert)
    return student_id

def put_assignment_in_database(cursor, assignment_name, course_id, autograder_points, due_date, sis_assignment_id, sis_course_id):
    postgres_insert_query = """ INSERT INTO assignments (id, name, course_id, autograder_points, due_date, sis_assignment_id, sis_course_id) VALUES (%s,%s,%s,%s,%s,%s,%s)"""
    assignment_id = str(uuid.uuid4())
    record_to_insert = (assignment_id, assignment_name, course_id, autograder_points, due_date, sis_assignment_id, sis_course_id)
    cursor.execute(postgres_insert_query, record_to_insert)
    return assignment_id

def put_submission_in_database(cursor, sis_assignment_id, sis_student_id):
    postgres_insert_query = """ INSERT INTO submissions (id, student_id, assignment_id, sis_assignment_id, sis_user_id) VALUES (%s,%s,%s,%s,%s)"""
    student_uuid = check_if_student_in_database(cursor, sis_student_id)
    assignment_uuid = check_if_assignment_in_database(cursor, sis_assignment_id)
    submission_id = str(uuid.uuid4())
    record_to_insert = (submission_id, student_uuid, assignment_uuid, sis_assignment_id, sis_student_id)
    cursor.execute(postgres_insert_query, record_to_insert)
    return submission_id

def get_grades_from_databases(cursor):
    cursor.execute('''SELECT * from submissions''')
    result = cursor.fetchall()
    for assignment in result:
        grade = assignment[5]
        sis_assignment_id = assignment[9]
        sis_student_id = assignment[10]
        sis_course_id = assignment[11]
        url = '{}/{}/assignments/{}'.format(base_url, sis_course_id, sis_assignment_id)
        comments = "No comments"
        assign_grade_for_assignment(url, header, sis_student_id, grade, comments, False)


def connect_to_database():
    try:
        connection = psycopg2.connect(user="postgres",
                                      password="Asiangoat343623",
                                      host="127.0.0.1",
                                      port="5432",
                                      database="CodeAssist_Database")
        cursor = connection.cursor()
        #write_to_database(cursor, connection)
        #put_submission_in_database(cursor, 36290578, 37784186)
        get_grades_from_databases(cursor)
        connection.commit()


    except (Exception, psycopg2.Error) as error:
        print(error)
        print("NOTHING ADDED TO DATABASE BECAUSE OF ERROR")

    finally:
        # closing database connection.
        if connection:
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")





#connect_to_database()

