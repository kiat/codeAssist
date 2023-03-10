from canvasapi import Canvas
import psycopg2
import uuid


#get course from canvas website
canvas = Canvas("https://canvas.instructure.com", "7~LtosN8jbYTcfAqkdIxQitgO0lXQJ0s4d7xzqqmXFb00aVPfXgRTeM0oHdWvq3og4")

#Tasks:
#Implement external tool in canvas assignments DONE
#get students in CodeAssist database DONE
#get courses in CodeAssist database DONE
#FIgure out how to add external app in add app menu (View configuration -> add app) DONE
#Enrollment only allowed through LTI when automatic roster sync is enabled
#Make new folder on github and put on github
#Get grade from codeassist assignments to canvas
#create script to sync roster

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
    students = [student.user["name"] for student in student_list if student.type == "StudentEnrollment"]
    return students

def get_teachers(course):
    student_list = list(course.get_enrollments())
    teachers = [teacher.user["name"] for teacher in student_list if teacher.type == "TeacherEnrollment"]
    return teachers

def get_assignments(course):
    assignments = list(course.get_assignments())
    assignment_list = []
    for assignment in assignments:
        assignment_info = {}
        assignment_info["name"] = assignment.name
        assignment_info["due date"] = assignment.due_at
        assignment_info['points'] = assignment.points_possible
        assignment_info['allowed attempts'] = assignment.allowed_attempts
        assignment_list.append(assignment_info)

    return assignment_list


def get_data_from_canvas():
    user = get_user(37784013)
    courses_id = get_courses_from_user(user)
    courses = get_course(courses_id)
    print(user)
    courses.pop()
    dict1 = {}
    dict1["students"] = []
    dict1["courses"] = []
    for course in courses:
        print("Course Name: " + str(course.name))
        students = get_students(course)
        #print("Students: " + str(students))
        for student in students:
            dict1["students"].append(student)
        teacher = get_teachers(course)[0]
        course_tuple = [course.name, teacher]
        dict1["courses"].append(course_tuple)
        #print("Instructor: " + str(teacher))
        print("Assignments: " + str(get_assignments(course)))
    return dict1



def put_teacher_in_database(cursor, teacher_name):
    postgres_insert_query = """ INSERT INTO instructors (id, password, name, email_address) VALUES (%s,%s,%s,%s)"""
    teacher_id = str(uuid.uuid4())
    record_to_insert = (teacher_id, "N/A", teacher_name, "N/A")
    cursor.execute(postgres_insert_query, record_to_insert)
    return teacher_id

def put_course_in_database(cursor, course_name, teacher_id):
    postgres_insert_query = """ INSERT INTO courses (id, name, instructor_id) VALUES (%s,%s,%s)"""
    course_id = str(uuid.uuid4())
    record_to_insert = (course_id, course_name, teacher_id)
    cursor.execute(postgres_insert_query, record_to_insert)
    return course_id

def put_student_in_database(cursor, student_name):
    postgres_insert_query = """ INSERT INTO students (id, name, password, email_address) VALUES (%s,%s,%s,%s)"""
    student_id = str(uuid.uuid4())
    record_to_insert = (student_id, student_name, "N/A", "N/A")
    cursor.execute(postgres_insert_query, record_to_insert)
    return student_id

def write_to_database(info_dict):
    try:
        connection = psycopg2.connect(user="postgres",
                                      password="Asiangoat343623",
                                      host="127.0.0.1",
                                      port="5432",
                                      database="CodeAssist_Database")
        cursor = connection.cursor()
        courses = info_dict["courses"]

        for course in courses:
            course_name = course[0]
            teacher_name = course[1]
            course_bool = check_if_course_in_database(cursor, course_name)
            if course_bool:
                print("Course already in database")
            else:
                teacher_id = check_if_teacher_in_database(cursor, teacher_name)
                if teacher_id:
                    print("Teacher already in database")
                    course_id = put_course_in_database(cursor, course_name, teacher_id)
                    print("Added new course: " + course_name)
                else:
                    new_teacher_id = put_teacher_in_database(cursor, teacher_name)
                    print("Added new teacher: " + teacher_name)
                    course_id = put_course_in_database(cursor, course_name, new_teacher_id)
                    print("Added new course: " + course_name)

        students = info_dict["students"]
        for student in students:
            student_name = student
            student_bool = check_if_student_in_database(cursor, student_name)
            if student_bool:
                print("Student already in database")
            else:
                print("Added new student: " + student_name)
                put_student_in_database(cursor, student_name)

        connection.commit()


    except (Exception, psycopg2.Error) as error:
        print(error)

    finally:
        # closing database connection.
        if connection:
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")

def check_if_teacher_in_database(cursor, teacher_name):
    postgres_select_query = """ SELECT id from instructors where name = %s"""
    cursor.execute(postgres_select_query, [teacher_name])
    record = cursor.fetchall()
    if record:
        return record[0][0]
    return False


def check_if_course_in_database(cursor, course_name):
    postgres_select_query = """ SELECT id from courses where name = %s"""
    cursor.execute(postgres_select_query, [course_name])
    record = cursor.fetchall()
    if record:
        return record[0][0]
    return False

def check_if_student_in_database(cursor, student_name):
    postgres_select_query = """ SELECT id from students where name = %s"""
    cursor.execute(postgres_select_query, [student_name])
    record = cursor.fetchall()
    if record:
        return record[0][0]
    return False

info_dict = get_data_from_canvas()
print(info_dict)
write_to_database(info_dict)

