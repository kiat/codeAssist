from canvasapi import Canvas
import psycopg2
import uuid
import requests
from canvasMethods import *
"""
This script synchronizes course and roster information between Canvas and the CodeAssist database.
It connects to the local PostgreSQL database and retrieves course, instructor, assignment, and student
information from Canvas using the Canvas API. It then checks if the retrieved data already exists in the
database, and if not, adds the new data.
"""

def sync_roster_and_courses(cursor, connection):
    """
        Synchronize the roster and courses information between Canvas and the local database.

        Args:
            cursor (psycopg2.extensions.cursor): The database cursor.
            connection (psycopg2.extensions.connection): The database connection.
    """

    info_dict = get_data_from_canvas()
    courses = info_dict["courses"]
    assignments = info_dict["assignments"]
    for course in courses:
        course_name = course[0]
        instructor_name = course[1]["name"]
        instructor_email = course[1]["email"]
        sis_instructor_id = course[1]["sis_user_id"]
        course_id = course[2]
        course_bool = check_if_course_in_database(cursor, course_id)
        if course_bool:
            print("Course already in database")
        else:
            instructor_id = check_if_instructor_in_database(cursor, sis_instructor_id)
            if instructor_id:
                print("instructor already in database")
                put_course_in_database(cursor, course_name, instructor_id, course_id, sis_instructor_id)
            else:
                new_instructor_id = put_instructor_in_database(cursor, instructor_name, instructor_email,
                                                               sis_instructor_id)
                put_course_in_database(cursor, course_name, new_instructor_id, course_id, sis_instructor_id)
 
    connection.commit()
    for assignment in assignments:
        sis_assignment_id = assignment["sis_assignment_id"]
        due_date = assignment["due date"]
        assignment_name = assignment["name"]
        sis_course_id = assignment["sis_course_id"]
        points = assignment["points"]
        course_uuid = check_if_course_in_database(cursor, sis_course_id)
        assignment_bool = check_if_assignment_in_database(cursor, sis_assignment_id)
        
        if assignment_bool:
            print("Assignment already in database")
        else:
            assignment_id = put_assignment_in_database(cursor, assignment_name, course_uuid, points, "2011-09-20",
                                                       sis_assignment_id, sis_course_id)
            print("Added new assignment: " + assignment_name)


    students = info_dict["students"]
    for student in students:
        student_name = student["name"]
        student_email = student["email"]
        sis_student_id = student["sis_user_id"]
        student_bool = check_if_student_in_database(cursor, sis_student_id)
        if student_bool:
            print("Student already in database")
        else:
            print("Added new student: " + student_name)
            put_student_in_database(cursor, student_name, student_email, sis_student_id)

    connection.commit()


def connect_to_database():
    """
    Connect to the CodeAssist database, synchronize the roster and courses information, and close the connection.
    """
    try:
        connection = psycopg2.connect(user="postgres",
                                      password="Asiangoat343623",
                                      host="127.0.0.1",
                                      port="5432",
                                      database="CodeAssist_Database")
        cursor = connection.cursor()
        sync_roster_and_courses(cursor, connection)
        #put_submission_in_database(cursor, 36290578, 37784186)
        #get_grades_from_databases(cursor)
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

connect_to_database()
