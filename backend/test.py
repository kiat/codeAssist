import unittest
import requests

env_file = "http://localhost:5000"


class APITestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Create test data that will be used across multiple tests."""
        cls.instructor_id = cls.create_instructor()
        cls.student_id = cls.create_student()
        cls.course_id = cls.create_course(cls.instructor_id)
        cls.assignment_id_A1 = cls.create_assignment(cls.course_id, "A1")
        cls.A1_zip_path = "assignment-examples/A1/A1.zip"
        cls.A1_py_path = "assignment-examples/A1/calculator.py"
        cls.assignment_id_A2 = cls.create_assignment(cls.course_id, "A2")
        cls.A2_zip_path = "assignment-examples/A2/A2.zip"
        cls.A2_py_path = "assignment-examples/A2/spiral.py"

    @classmethod
    def create_instructor(cls):
        """Create an instructor and return the ID."""
        url = "http://localhost:5000/create_user"
        data = {
            "name": "Instructor Name",
            "email": "instructor@email.com",
            "password": "password",
            "eid": "unique-instructor-id",
            "role": "instructor"
        }
        response = requests.post(url, json=data)
        return response.json().get("id")

    @classmethod
    def create_student(cls):
        """Create a student and return the ID."""
        url = "http://localhost:5000/create_user"
        data = {
            "name": "Ricky Woodruff",
            "email": "ricky@student.com",
            "password": "password",
            "eid": "unique-student-id",
            "role": "student"
        }
        response = requests.post(url, json=data)
        return response.json().get("id")

    @classmethod
    def create_course(cls, instructor_id):
        """Create a course and return the ID."""
        url = "http://localhost:5000/create_course"
        data = {
            "name": "Introduction to Curl Testing",
            "instructor_id": instructor_id,
            "semester": "Fall",
            "year": 2024,
            "entryCode": "1000",
        }
        response = requests.post(url, json=data)
        return response.json().get("id")

    @classmethod
    def create_assignment(cls, course_id, assignment_name):
        """Create an assignment and return the ID."""
        url = f"http://localhost:5000/create_assignment"
        data = {"name": assignment_name, "course_id": course_id}
        response = requests.post(url, json=data)
        return response.json().get("id")

    # Actual tests to be run:
    def test_upload_autograder_A1(self):
        """Upload autograder for Assignment A1."""
        url = "http://localhost:5000/upload_assignment_autograder"
        with open(self.A1_zip_path, "rb") as f:
            files = {"file": f}
            data = {"assignment_id": self.assignment_id_A1}
            response = requests.post(url, files=files, data=data)
            self.assertEqual(response.status_code, 200)

    def test_upload_submission_A1(self):
        """Upload a student's submission for Assignment A1."""
        url = "http://localhost:5000/upload_submission"
        with open(self.A1_py_path, "rb") as f:
            files = {"file": f}
            data = {
                "assignment_id": self.assignment_id_A1,
                "student_id": self.student_id,
            }
            response = requests.post(url, files=files, data=data)
            self.assertEqual(response.status_code, 200)

    def test_upload_autograder_A2(self):
        """Upload autograder for Assignment A2."""
        url = "http://localhost:5000/upload_assignment_autograder"
        with open(self.A2_zip_path, "rb") as f:
            files = {"file": f}
            data = {"assignment_id": self.assignment_id_A2}
            response = requests.post(url, files=files, data=data)
            self.assertEqual(response.status_code, 200)

    def test_upload_submission_A2(self):
        """Upload a student's submission for Assignment A2."""
        url = "http://localhost:5000/upload_submission"
        with open(self.A2_py_path, "rb") as f:
            files = {"file": f}
            data = {
                "assignment_id": self.assignment_id_A2,
                "student_id": self.student_id,
            }
            response = requests.post(url, files=files, data=data)
            self.assertEqual(response.status_code, 200)

    @classmethod
    def tearDownClass(cls):
        """Clean up test data in order after running the test suite"""
        cls.delete_assignment(cls.assignment_id_A1)
        cls.A1_zip_path = ""
        cls.A1_py_path = ""
        cls.delete_assignment(cls.assignment_id_A2)
        cls.A2_zip_path = ""
        cls.A2_py_path = ""
        cls.delete_student()
        cls.delete_course()
        cls.delete_instructor()
 
    @classmethod
    def delete_instructor(cls):
        url = f"{env_file}/delete_user?id={cls.instructor_id}"
        response = requests.delete(url)

    @classmethod
    def delete_student(cls):
        url = f"{env_file}/delete_user?id={cls.student_id}"
        response = requests.delete(url)

    @classmethod
    def delete_course(cls):
        url = f"{env_file}/delete_course?course_id={cls.course_id}"
        response = requests.delete(url)

    @classmethod
    def delete_assignment(cls, assignment_id):
        url = f"{env_file}/delete_assignment?assignment_id={assignment_id}"
        response = requests.delete(url)


if __name__ == "__main__":
    unittest.main()
