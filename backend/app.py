from flask_cors import CORS
from api import app
from routes import register_routes
from util.errors import register_error_handlers

CORS(app)
# @app.route('/', methods=["GET", "POST"])
# @cross_origin()
# def hello_world():
#     '''
#     This is the default response with no methods and extensions - '/'
#     If you host the backend locally at localhost:5001 it should display "Hello World"
#     '''
#     return 'Hello World'

register_routes(app)

register_error_handlers(app)

if __name__ == "__main__":
    app.run()
