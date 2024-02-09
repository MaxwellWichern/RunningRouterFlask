import flask
from flask_cors import CORS

app = flask.Flask(__name__)
CORS(app)

if __name__ == "__main__":
    app.run(debug = True)