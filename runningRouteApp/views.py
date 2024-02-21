from flask import Flask
from flask import request, jsonify
import requests
from main import app
import json
from collections import OrderedDict
from functions import overpassQuery, optimizeOverpassResult, optimizeForAdjList

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
        out body;
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
    data = request.form
    #2 get data from overpass using #1
    result = overpassQuery(data['mileage'], data['lat'], data['lon'], data['address'], data['direction'], data['roadList'])
    #  use coords to calculate distances between nodes using getDistance()
    orderedResult = OrderedDict(result)
    #coordNodes, adjacencyMatrixWeighted = optimizeOverpassResult(result)
    #adjList, coordArray = optimizeForAdjList(orderedResult)
    #print(coordArray)
    #3 find one route for now, but I would like maybe 4-5 per user request (send to algorithm in this step)
    #4 return routes

    #print(adjacencyMatrix.shape, file=open('output.txt', 'a'))
    #print(list(adjacencyMatrixWeighted), file=open('output.txt', 'a'))
    
    return orderedResult