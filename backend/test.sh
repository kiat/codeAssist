curl -X POST -F "name=Instructor Name" -F "email=instructor@email.com" -F "password=password" localhost:5000/create_instructor
curl -X POST localhost:5000/create_course -d '{"name":"CS371L Mobile Computing", "instructor_id":"963634fd-a109-457c-955b-2337681be624"}' -H Content-Type:\ application/json
curl -X POST localhost:5000/create_assignment -d '{"name":"A1", "course_id":"e575f3bc-bda6-4b14-a1aa-b93717425c59"}' -H Content-Type:\ application/json
curl -X POST localhost:5000/update_assignment -d '{"assignment_id":"dabe443b-b8b1-403a-92b6-003cfd0f4eb2", "published":"true"}' -H Content-Type:\ application/json
curl localhost:5000/get_assignment?assignment_id=dabe443b-b8b1-403a-92b6-003cfd0f4eb2
curl -X POST localhost:5000/update_assignment -d '{"assignment_id":"dabe443b-b8b1-403a-92b6-003cfd0f4eb2", "due_date":"12/17/2022", "published":false}' -H Content-Type:\ application/json
curl -X POST -F "name=Ricky Woodruff" -F "email=ricky@student.com" -F "password=password" localhost:5000/create_student
curl -X POST localhost:5000/create_enrollment_bulk -d '{"course_id":"e575f3bc-bda6-4b14-a1aa-b93717425c59", "student_ids":["177e9a44-8135-4b23-a99b-ad94e9694948", "e5d5d204-f44f-4397-86a0-93ab49a5f817", "70750539-1bce-400d-a5ee-2a580a96c0bd"]}' -H Content-Type:\ application/json


curl -X POST -F "file=@/Users/rickywoodruff/Desktop/Spiral.py" -F "assignment=A1" -F "student_id=f72dfb2d-4a93-4712-9400-3942b86c5561" -F "assignment_id=dabe443b-b8b1-403a-92b6-003cfd0f4eb2" localhost:5000/upload_submission


studentid = f72dfb2d-4a93-4712-9400-3942b86c5561
courseid = 37840b94-2ccb-4464-9e22-25f707839dfa
assignmentid = dabe443b-b8b1-403a-92b6-003cfd0f4eb2