import requests
import sys
import json
import psycopg2

def main(backend_url, db_url):
    # Create an Instructor
    instructor_info = {"name": "Jane Doe", "password": "password123", "email": "jane@example.com", "eid": "jd123"}
    requests.post(f"{backend_url}/create_instructor", json=instructor_info)

    # Create a Student
    student_info = {"name": "John Smith", "password": "password123", "email": "john@example.com", "eid": "js321"}
    requests.post(f"{backend_url}/create_student", json=student_info)

    # Connect to Database
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("SELECT id FROM instructors WHERE email_address = 'jane@example.com'")
    instructor_id = cur.fetchone()[0]
    cur.execute("SELECT id FROM students WHERE email_address = 'john@example.com'")
    student_id = cur.fetchone()[0]

    # Create a Course
    course_info = {"name": "TEST101", "instructor_id": instructor_id, "semester": "Fall", "year": 2023, "entryCode": "011503"}
    course_response = requests.post(f"{backend_url}/create_course", json=course_info)
    course_id = course_response.json().get("id")

    # Enroll Student in Course
    enrollment_info = {"student_id": student_id, "course_id": course_id}
    requests.post(f"{backend_url}/create_enrollment", json=enrollment_info)

    # Create an Assignment
    assignment_info = {"name": "Test Assignment", "course_id": course_id, "due_date": "2023-12-11"}
    assignment_response = requests.post(f"{backend_url}/create_assignment", json=assignment_info)

    # # Upload Submission 
    # submission_info = {"student_id": student_id, "assignment_id": assignment_id}

    # # Upload Assignment Autograder

    # # Fetch Submission Results

    cur.close()
    conn.close()

if __name__ == "__main__":
    backend_url = sys.argv[1]
    db_url = sys.argv[2]
    main(backend_url, db_url)