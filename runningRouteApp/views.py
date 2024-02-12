from flask import Flask
from flask import request, jsonify
import requests
from main import app
import json


@app.route('/')
def home():
    return "Hello world!"

@app.route('/hello/<name>', methods=['GET'])
def user(name):
    return f"Hello {name}!"

@app.route("/test", methods=['POST'])
def getNodesAndWays():
    data = request.form
    radius = 1609.344 * float(data["mileage"])/2.0
    if (data["address"] != "NULL"):
        location = True #temp data
        # geocode to get coords, else just use lat and lon

    query = '''
        [out:json];
        nw(around: {}, {}, {})["highway"];
        (._;>;);
        out geom;
    '''.format(radius, float(data["lat"]), float(data["lon"]))
    overPass_url = "https://overpass-api.de/api/interpreter"
    query_params = {"data": query}
    response = requests.post(overPass_url, data=query_params)
    result = response.json()
    print(json.dumps(result, indent=2))
    return result

@app.route("/overpassGather", methods=['POST'])
def bundlePythonResults():
    #1 get data sent by this request, mileage/start/ other criteria
    #2 get data from overpass using #1
    #3 send the data to the graph builder
    #  clean data? should I try and optimize the nodes as only the intersections
    #4 find one route for now, but I would like maybe 4-5 per user request (send to algorithm int this step)
    #5 return routes
    print("Hell0")