from flask import request, jsonify
import requests
import json
from collections import OrderedDict
import runningRouteApp.overpassAlgInit as rt
from runningRouteApp.aStarAlg import searchRunner
from geopy import distance
from geopy.geocoders import Nominatim
from flask import Blueprint
from flask_cors import CORS
import runningRouteApp.db as rdb
import networkx as nx
import geopy as gp


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

#test query figuring out how to set up the adjacency list retrieved from mongo
@runnerBP.route("/mongoTesting", methods=['POST'])
def getLists():
    data = request.form
    list = getAdjList(data["email"])
    list["list"] = json.loads(list["list"])
    return list


#test query with networkx
@runnerBP.route("/netXOverpass", methods=['POST'])
def getGraph():
    data = request.form
    print("Overpass Query")
    result, lat, lon = rt.overpassQuery(data["mileage"], data["lat"], data["lon"], data["direction"])

    # Create an empty NetworkX graph
    G = nx.Graph()
    coords = dict()
    # Extract nodes and edges from the response
    for element in reversed(result['elements']):
        if element['type'] == 'way':
            nodes = element['nodes']
            for i in range(len(nodes) - 1):
                if nodes[i] not in coords:
                    coords[result['elements'][i]['id']] = (result["elements"][i])
                distanceToNode = int(gp.distance.distance((result['elements'][i]['lat'], result['elements'][i]['lat']), (result['elements'][i+1]['lat'], result['elements'][i+1]['lat'])).miles * 100000) / 100000
                
                G.add_edge(nodes[i], nodes[i+1], weight=distanceToNode)
        else: break
    return result

#current main query, begins by getting data from overpass, it turns it into an orderedDict, and then 
#turns the data into an adjacency list to be used for the algorithm
@runnerBP.route("/overpassGather", methods=['POST'])
def bundlePythonResults():
    #1 get data sent by this request, mileage/lat/lon/direction/ "user info"
    data = request.form
    newNeeded = False
    exisitingList = {}
    startid=0
    lat = data["lat"]
    lon = data["lon"]
    #2 check if we need to create a new adjacency list
    #2.1 if the request is not provided with an email, the user is not logged in, skip this because we need to save data with an email
    if data["email"]:
        #2.2 get the saved adjacency_list. If it doesn't exist, we can skip and go to 3 to create it
        existingList = rdb.getAdjList(data["email"])
        if existingList:
            newNeeded, lat, lon, tempList = rt.validateExistingList(data, existingList)
            if tempList: 
                adjList = tempList
                print("list reset")
        else: 
            print("new needed: no list yet")
            newNeeded = True
        
    #3.1 if we need a new list get data from overpass using #1
    if newNeeded:
        try:
            result, lat, lon, startid = rt.overpassQuery(data['mileage'], lat, lon, data['direction'])
        except Exception as e:
            print("Could not create query")
            return e
        listSize = 0
        for node in result["elements"]:
            if node["type"] == "node": listSize+=1
        try:
            orderedResult = OrderedDict(result)
        except Exception as e:
            print(e.__traceback__)
            print("Error ", e)
            print("Element was not a dict, cannot continue the algorithm")
            return result
        
        #3.2 create the adjacency list and corresponding coordinate array which has latitude and longitude
        adjList, coordArray = rt.createAdjListThreadless(orderedResult)
        #3.3 add the new adjacency list to mongo, replacing the old list and add the TTL date for the element
        try:
            if not data["email"]:
                print("Mongo Query: Add")
                rdb.addAdjList(data["email"], adjList, [lat, lon], float(data["mileage"])/2.0, coordArray, listSize, startid)
            else:
                print("Mongo Query: update full")
                rdb.updateAdjListFull(data["email"], adjList, [lat, lon], float(data["mileage"])/2.0, coordArray, listSize, startid)
        except Exception as e:
            print("Error adding Element, check the form data")
            print(e)

    if (existingList):
        coordArray = existingList["coordArray"]
        listSize = existingList["numNodes"]
        startid = existingList["startid"]
    #4 find one route for now, but I would like maybe 4-5 per user request (send to algorithm in this step)    
    #this next line finds the id of the first adjacent node
    endid = adjList[str(startid)][1][0]
    #def searchRunner(list, startNode, goalNode, length, n, TOL, heuristicNum, heuristicLength, heuristicMutation):


    #TODOnew process implemented here, break the length into at least 4 sections, once it is 4 miles, go mile by mile as each section
    path, length = searchRunner(adjList, str(endid), str(startid), data["mileage"], 20, 0.5, 5, int(listSize * 0.25), 90)



    #5 return routes
    coordListPath = []
    print("",file=open('output.txt', 'w'))
    for nodeId in path:
        coordListPath.append([coordArray[adjList[nodeId][0]]["lat"],coordArray[adjList[nodeId][0]]["lon"]])
        print('{},{},red,square,"Pune"'.format(coordArray[adjList[nodeId][0]]["lat"],coordArray[adjList[nodeId][0]]["lon"]), file=open('output.txt', 'a'))
    return jsonify({"Path": coordListPath, "Length": length})

