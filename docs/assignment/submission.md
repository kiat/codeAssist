
# Assignment Submission Cycle

## Relevant Endpoints
1. ```/upload_assignment_autograder```: This endpoint allows an instructor to upload an autograder for an assignment.
2. ```/upload_submission```: This endpoint is called when users upload their assignment submission.

## General Flow

#### 1. Instructor uploads an autograder for an assignment

Autograders have associated docker container IDs so that containers do not need to be spun up every time a submission occurs. When an autograder is uploaded, we first check to see if an assignment already has an existing ```container_id```. If it does, we update the existing container by removing previous autograder files and then extracting the new autograder zip into the container.


If the assignment does not have a docker container ID, then we are uploading an autograder for this assignment for the first time. In this case, the ```/upload_assignment_autograder``` endpoint writes a ```Dockerfile``` to create a new docker image. Then, a container is run using this docker image. We update the assignment database entry with this container ID and then stop the container.

See ```./autograder.md``` for more autograder details.

#### 2. Student uploads a submission for grading

Now that we have a container with the assignment autograder, we can use this to grade student submissions. When a student's submission is uploaded through ```/upload_submission```, we first retrieve the associated container ID for this assignment (which is stored in our database). Then, we copy the student's file into the container and run it against our autograder. The autograder will write out the results into ```/autograder/results/results.json``` inside of the container. This ```.json``` file is then decoded for the submission results. Then, we upload this submission data to our database. This includes submission metadata and resultsand we set this submission as the current active submission for this user, for this assignment. The container can cleaned up (removing submission files) and stopped.


This process also includes an autograder timeout feature. The autograder timeout is specified by the instructor when uploading an autograder. When a submission is run, we retrieve ```autograder_timeout``` from the assignment's database entry. When executing the autograder container, we run a ```subprocess``` with ```timeout=autograder_timeout```. Once this timeout is reached, we stop the container and display an error message
to the user.

#### 3. AI feedback generated for student submission

Once the student's submission has been graded, an AI feedback generation task starts. After stopping the Docker container in ```/upload_submission```, we start a background task for asynchronously retrieving this AI feedback. In assignment creation, the instructor specifies the OpenAI model to be used. The student's program code and previous submission weaknesses are provided to the model to generate tailored feedback regarding weakpoints in their code. By providing insights specific to the student, the model pays closer attention to coding tendencies addressed in previous submissions.


Feedback takes a few seconds to be generated. Once it is, the ```ai_feedback``` field for the submission entry in the database is updated. While this is happening, our client will keep polling for the submission data until the feedback is provided.

See ```./ai_feedback.md``` for a more detailed breakdown of this process.