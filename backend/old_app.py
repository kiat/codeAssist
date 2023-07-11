from flask import Flask, flash, request, jsonify, redirect
from sqlalchemy import update, or_
from flask_cors import CORS, cross_origin
from werkzeug.utils import secure_filename
import docker_client
from functools import reduce
import json
import sys
import uuid
from api import app, db
from api.models import *
from api.schemas import *

'''
app.py is (currently) the gateway for ALL backend endpoints
This was created using Flask. 
Documentation for Flask can be found here: https://flask.palletsprojects.com/en/2.3.x/quickstart/
'''

 
if __name__ == '__main__':
    app.run()
