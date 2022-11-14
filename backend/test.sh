curl -X POST -F "name=Instructor Name" -F "email=instructor@email.com" -F "password=password" localhost:5000/create_instructor
curl -X POST localhost:5000/create_course -d '{"name":"CS371L Mobile Computing", "instructor_id":"963634fd-a109-457c-955b-2337681be624"}' -H Content-Type:\ application/json
curl -X POST localhost:5000/create_assignment -d '{"name":"A1", "course_id":"e575f3bc-bda6-4b14-a1aa-b93717425c59"}' -H Content-Type:\ application/json
curl -X POST localhost:5000/update_assignment -d '{"assignment_id":"dabe443b-b8b1-403a-92b6-003cfd0f4eb2", "published":"true"}' -H Content-Type:\ application/json
curl localhost:5000/get_assignment?assignment_id=dabe443b-b8b1-403a-92b6-003cfd0f4eb2
curl -X POST localhost:5000/update_assignment -d '{"assignment_id":"dabe443b-b8b1-403a-92b6-003cfd0f4eb2", "due_date":"12/17/2022", "published":false}' -H Content-Type:\ application/json
