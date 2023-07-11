from flask_cors import cross_origin
from api import app
from routes.assignment import assignment
from routes.course import course
from routes.submission import submission
from routes.user import user

@app.route('/', methods=["GET", "POST"])
@cross_origin()
def hello_world():
    '''
    This is the default response with no methods and extensions - '/'
    If you host the backend locally at localhost:5000 it should display "Hello World"
    '''
    return 'Hello World'

app.register_blueprint(assignment)
app.register_blueprint(course)
app.register_blueprint(submission)
app.register_blueprint(user)

app.run()