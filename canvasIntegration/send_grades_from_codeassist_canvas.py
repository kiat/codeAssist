import requests
from canvasapi import Canvas
import psycopg2
import uuid
import os

"""
This script synchronizes grades between the CodeAssist database and Canvas. It connects to the local
PostgreSQL database and retrieves grades from the CodeAssist database, then sends the grades to Canvas
using the Canvas API.
"""

# Configuration for Canvas API and base URL
HOST=os.getenv("HOST")
access_token = os.getenv("ACCESS_TOKEN")


base_url = 'https://{}/api/v1/courses'.format(HOST)


header = {'Authorization': 'Bearer ' + access_token}

def post_grade_to_canvas(base_url, header, user_id, grade, comment, verbose=False):
    """
    Post a grade and optional comment to Canvas API for a specific user.

    Args:
        base_url (str): The base URL for the Canvas API.
        header (dict): The header containing the access token.
        user_id (int): The user ID of the student.
        grade (float): The grade to be posted.
        comment (str): An optional comment to be posted along with the grade.
        verbose (bool, optional): If True, print additional debug information. Defaults to False.
    """

    url = '{}/submissions/{}'.format(base_url, user_id)
    if verbose:
        print('url: ' + url)

    payload = {'submission[posted_grade]': grade}
    if comment:
        payload.update({'comment[text_comment]': comment})

    r = requests.put(url, headers=header, data=payload)
    print(url, header, payload)

    if verbose:
        print('result of put assign_grade_for_assignment:', r.text)
    if r.status_code == requests.codes.ok:
        page_response = r.json()
        return True

def send_grades_from_codeassist_to_canvas(cursor):
    """
        Retrieve grades from CodeAssist database and send them to Canvas.

        Args:
            cursor (psycopg2.extensions.cursor): The database cursor.
    """
    cursor.execute('''SELECT * from submissions''')
    result = cursor.fetchall()
    for assignment in result:
        grade = assignment[5]
        sis_assignment_id = assignment[9]
        sis_student_id = assignment[10]
        sis_course_id = assignment[11]
        url = '{}/{}/assignments/{}'.format(base_url, sis_course_id, sis_assignment_id)
        comments = "No comments"
        post_grade_to_canvas(url, header, sis_student_id, grade, comments, False)


def connect_to_database():
    """
     Connect to the CodeAssist database, retrieve grades and send them to Canvas, then close the connection.
    """
    try:
        connection = psycopg2.connect(user="postgres",
                                      password="Asiangoat343623",
                                      host="127.0.0.1",
                                      port="5432",
                                      database="CodeAssist_Database")
        cursor = connection.cursor()
        send_grades_from_codeassist_to_canvas(cursor)
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
