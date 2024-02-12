import flask
from flask_cors import CORS

app = flask.Flask(__name__)
CORS(app)

#import from runningRouteApp the necessary routes
from runningRouteApp import bp as runner_bp
app.register_blueprint(runner_bp)

if __name__ == "__main__":
    app.run(debug = True)