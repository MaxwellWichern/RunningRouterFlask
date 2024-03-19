from flask import Flask
from flask import request, jsonify
import requests
import json
from collections import OrderedDict
from runningRouteApp.overpassAlgInit import overpassQuery, optimizeForAdjListMulti, createAdjListThreadless
from geopy import distance
from time import time
from geopy.geocoders import Nominatim
from flask import Blueprint
from flask_cors import CORS
from db import getAdjList, addAdjList, updateAdjList, deleteAdjList

runnerBP = Blueprint('runner', __name__, template_folder='templates')
CORS(runnerBP)

#tutorial default route
@runnerBP.route('/')
def home():
    return "Hello world!"

#tutorial route to print a name
@runnerBP.route('/hello/<name>', methods=['GET'])
def user(name):
    return f"Hello {name}!"

# Getting coordinates from an address
@runnerBP.route('/getCoordinates', methods=['POST'])
def getCoordinatesFromAddress():
    geolocator = Nominatim(user_agent="RunningApp")
    data = request.form
    address = data['address']
    location = geolocator.geocode(address)
    print((location.latitude, location.longitude))
    return [location.latitude, location.longitude]

#testing getting the start location within a region to check it is valid
@runnerBP.route('/startTesting', methods=['POST'])
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

#test query to get data from overpass
@runnerBP.route("/test", methods=['POST'])
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

#current main query, begins by getting data from overpass, it turns it into an orderedDict, and then 
#turns the data into an adjacency list to be used for the algorithm
@runnerBP.route("/overpassGather", methods=['POST'])
def bundlePythonResults():
    #1 get data sent by this request, mileage/lat/lon/direction/ "user info"
    data = request.form

    #2 check if we need to create a new adjacency list
        #2.1 if the request is not provided with an email, the user is not logged in, skip this because we need to save data with an email
    
        #2.2 get the saved adjacency_list. If it doesn't exist, we can skip and go to 3 to create it
    
        #2.3 if it exists, we have our start node from the data element and we will have saved the start node with the list in mongodb to simplify this step
        #----We can find the distance between these two points, if the distance is greater than the mileage, we definitely need one
    
        #2.4 another concern is the same start node but different distance. if the distance is larger, we need a new list, otherwise it is okay and we can reuse it
    
        #2.5 update the TTL/date for the list
    
    #3.1 if we need a new list get data from overpass using #1
    result = overpassQuery(data['mileage'], data['lat'], data['lon'], data['direction'])
    #  use coords to calculate distances between nodes using getDistance()
    try:
        orderedResult = OrderedDict(result)
    except:
        return result
    
    #3.2 create the adjacency list and corresponding coordinate array which has latitude and longitude
    #numWorkers = mp.cpu_count()
    #tart = time()
    #adjList, coordArray = optimizeForAdjListMulti(orderedResult, 2)
    #finish = time()-start
    #print("Time: ", finish)
    start = time()
    adjList, coordArray = createAdjListThreadless(orderedResult)
    finish = time()-start
    print("Time: ", finish)
    #3.3 add the new adjacency list to mongo, replacing the old list and add the TTL date for the element

    #4 find one route for now, but I would like maybe 4-5 per user request (send to algorithm in this step)
    
    #5 return routes
    return jsonify(adjList)

