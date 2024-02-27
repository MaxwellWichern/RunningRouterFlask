from flask import Flask
from flask import request, jsonify
import requests
from main import app
import json
from collections import OrderedDict
from functions import overpassQuery, optimizeOverpassResult, optimizeForAdjList
from geopy import distance

@app.route('/')
def home():
    return "Hello world!"

@app.route('/hello/<name>', methods=['GET'])
def user(name):
    return f"Hello {name}!"

@app.route('/startTesting', methods=['POST'])
def testGetCorrectStart():
    data = request.form
    meters = 20
    min = 1000
    while meters/2 < 1000 and min == 1000:
        query = '''
            [out:json];

            //Get all nodes around 80 meters of the coordinates and asign it to the output set .aroundnodes
            node(around:{},{}, {})->.aroundnodes;

            //get the ways using the input set aroundnodes, but bn is backward, then it filters highways of the specific tag. This uses a regular expression denoted by the ~, then ^ is start, $ is end, and the | is for or
            way(bn.aroundnodes)[highway~"^(residential|primary|secondary|tertiary|unclassified)$"]->.allways;

            //this finds the nodes of all ways and puts them into waynodes
            node(w.allways)->.waynodes;

            //union
            (
            //combines both sets of nodes and the ways into one set to be printed
            node.waynodes.aroundnodes; 
            //way.allways.allways; 
            );

            //prints the previous set put into the default set ._
            out body;
        '''.format(meters, float(data['lat']), float(data['lon']))

        overPass_url = "https://overpass-api.de/api/interpreter"
        query_params = {"data": query}
        response = requests.post(overPass_url, data=query_params)
        result = response.json()

        minNode = None
        for node in result['elements']:
            tempD = distance.distance((data['lat'], data['lon']), (node['lat'], node['lon']))
            print('distance: ' + str(tempD))
            if tempD < min: 
                min = tempD
                minNode = node
        meters *= 2
        print(meters)

    return minNode

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
    result = overpassQuery(data['mileage'], data['lat'], data['lon'], data['direction'])
    #  use coords to calculate distances between nodes using getDistance()
    try:
        orderedResult = OrderedDict(result)
    except:
        return result
    #coordNodes, adjacencyMatrixWeighted = optimizeOverpassResult(result)
    adjList, coordArray = optimizeForAdjList(orderedResult)
    #3 find one route for now, but I would like maybe 4-5 per user request (send to algorithm in this step)
    
    #4 return routes

    #print(adjacencyMatrix.shape, file=open('output.txt', 'a'))
    #print(list(adjacencyMatrixWeighted), file=open('output.txt', 'a'))
    
    return adjList