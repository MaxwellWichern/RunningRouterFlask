from flask_cors import CORS
from flask.json import JSONEncoder
from bson import json_util, ObjectId
from datetime import datetime
from flask import Flask, render_template

from .runnerAPI import runnerBP as runner_bp

class MongoJsonEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(obj, ObjectId):
            return str(obj)
        return json_util.default(obj, json_util.CANONICAL_JSON_OPTIONS)

def create_app():
    app = Flask(__name__)
    CORS(app)
    #create another blueprint with mongo CRUD
    app.json_encoder = MongoJsonEncoder
    app.register_blueprint(runner_bp)

    return app