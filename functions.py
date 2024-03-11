import requests, json
from math import acos, sin, cos, radians
import numpy as np
#import threading
import time
import geopy.distance
from multiprocessing import Lock, Process
from multiprocessing.pool import ThreadPool
import threading

#This function fixes the bounding box around the start location to help limit the number of nodes as well as add a neat utility to the user
#Parameters include
# direction: (North, South, East, West, North-East, North-West, South-East, South-West)
# lat: latitude positioning in Decimal Degrees
# lon: longitude positioning in Decimal Degrees
# distMile: The distance in miles
def fixBoundingBox(direction, lat, lon, distMile):

    bboxFixedCoords = {"minLat": 0, "minLon": 0, "maxLat": 0, "maxLon": 0}
    if (direction == 'North'):
        bboxFixedCoords["minLon"] = lon
        bboxFixedCoords["maxLon"] = geopy.distance.distance(miles=distMile).destination(geopy.Point(lat,lon), bearing=90).longitude
        bboxFixedCoords["minLat"] = geopy.distance.distance(miles=distMile).destination(geopy.Point(lat,lon), bearing=180).latitude
        bboxFixedCoords["maxLat"] = geopy.distance.distance(miles=distMile).destination(geopy.Point(lat,lon), bearing=0).latitude
    elif (direction == 'East'):
        bboxFixedCoords["minLon"] = geopy.distance.distance(miles=distMile).destination(geopy.Point(lat,lon), bearing=270).longitude
        bboxFixedCoords["maxLon"] = geopy.distance.distance(miles=distMile).destination(geopy.Point(lat,lon), bearing=90).longitude
        bboxFixedCoords["minLat"] = lat
        bboxFixedCoords["maxLat"] = geopy.distance.distance(miles=distMile).destination(geopy.Point(lat,lon), bearing=0).latitude
    elif (direction == 'South'):
        bboxFixedCoords["minLon"] = geopy.distance.distance(miles=distMile).destination(geopy.Point(lat,lon), bearing=270).longitude
        bboxFixedCoords["maxLon"] = lon
        bboxFixedCoords["minLat"] = geopy.distance.distance(miles=distMile).destination(geopy.Point(lat,lon), bearing=180).latitude
        bboxFixedCoords["maxLat"] = geopy.distance.distance(miles=distMile).destination(geopy.Point(lat,lon), bearing=0).latitude
    elif (direction == 'West'):
        bboxFixedCoords["minLon"] = geopy.distance.distance(miles=distMile).destination(geopy.Point(lat,lon), bearing=270).longitude
        bboxFixedCoords["maxLon"] = geopy.distance.distance(miles=distMile).destination(geopy.Point(lat,lon), bearing=90).longitude
        bboxFixedCoords["minLat"] = geopy.distance.distance(miles=distMile).destination(geopy.Point(lat,lon), bearing=180).latitude
        bboxFixedCoords["maxLat"] = lat
    elif (direction == 'North-East'):
        topRight = geopy.distance.distance(miles=distMile).destination(geopy.Point(lat,lon), bearing=45)
        bboxFixedCoords["minLon"] = lon
        bboxFixedCoords["maxLon"] = topRight.longitude
        bboxFixedCoords["minLat"] = lat
        bboxFixedCoords["maxLat"] = topRight.latitude
    elif (direction == 'South-East'):
        bottomRight = geopy.distance.distance(miles=distMile).destination(geopy.Point(lat,lon), bearing=135)
        bboxFixedCoords["minLon"] = bottomRight.longitude
        bboxFixedCoords["maxLon"] = lon
        bboxFixedCoords["minLat"] = lat
        bboxFixedCoords["maxLat"] = bottomRight.latitude
    elif (direction == 'South-West'):
        bottomLeft = geopy.distance.distance(miles=distMile).destination(geopy.Point(lat,lon), bearing=225)
        bboxFixedCoords["minLon"] = bottomLeft.longitude
        bboxFixedCoords["maxLon"] = lon
        bboxFixedCoords["minLat"] = bottomLeft.latitude
        bboxFixedCoords["maxLat"] = lat
    elif (direction == 'North-West'):
        bottomLeft = geopy.distance.distance(miles=distMile).destination(geopy.Point(lat,lon), bearing=315)
        bboxFixedCoords["minLon"] = lon
        bboxFixedCoords["maxLon"] = bottomLeft.longitude
        bboxFixedCoords["minLat"] = bottomLeft.latitude
        bboxFixedCoords["maxLat"] = lat
    else:
        bboxFixedCoords["minLon"] = geopy.distance.distance(miles=distMile).destination(geopy.Point(lat,lon), bearing=270).longitude
        bboxFixedCoords["maxLon"] = geopy.distance.distance(miles=distMile).destination(geopy.Point(lat,lon), bearing=90).longitude
        bboxFixedCoords["minLat"] = geopy.distance.distance(miles=distMile).destination(geopy.Point(lat,lon), bearing=180).latitude
        bboxFixedCoords["maxLat"] = geopy.distance.distance(miles=distMile).destination(geopy.Point(lat,lon), bearing=0).latitude
    bboxFixedCoords["minLon"] = int(bboxFixedCoords["minLon"] * 10000000)/10000000
    bboxFixedCoords["maxLon"] = int(bboxFixedCoords["maxLon"] * 10000000)/10000000
    bboxFixedCoords["minLat"] = int(bboxFixedCoords["minLat"] * 10000000)/10000000
    bboxFixedCoords["maxLat"] = int(bboxFixedCoords["maxLat"] * 10000000)/10000000
    return bboxFixedCoords

# when the user queries to generate a route, the start point might not correspond with a node on a highway tag,
# so find the nearest one and start there
def findCheckStart(lat, lon):
    meters = 20
    min = 3200
    while meters/2 < 3200 and min == 3200:
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
                //combines both sets of nodes into one set
                node.waynodes.aroundnodes; 
            );

            //prints the previous set put into the default set ._
            out body;
        '''.format(meters, float(lat), float(lon))

        overPass_url = "https://overpass-api.de/api/interpreter"
        query_params = {"data": query}
        response = requests.post(overPass_url, data=query_params)
        result = response.json()

        minNode = None
        for node in result['elements']:
            tempD = geopy.distance.distance((lat, lon), (node['lat'], node['lon']))
            if tempD < min: 
                min = tempD
                minNode = node
        meters *= 2

    if minNode is None: return False
    return minNode["lat"], minNode["lon"] 
        

#This is the first method called to begin the route gen, specifically finding all the nodes and ways located in the area selected
def overpassQuery(mileage, lat, lon, direction):
    radius = 1609.344 * float(mileage)/2.0
    try:
        lat, lon = findCheckStart(lat, lon)
    except:
        return "Start point not within 2 mile area, recommended to find a new start"
    coordsForBBox = fixBoundingBox(direction, float(lat), float(lon), float(mileage)/2)
    bboxString = '[bbox: {}, {}, {}, {}]'.format(coordsForBBox["minLat"],coordsForBBox["minLon"], coordsForBBox["maxLat"], coordsForBBox["maxLon"])
    query = '''
        [out:json]{3};
        (
            way(around: {0}, {1}, {2})["highway"="residential"];
            way(around: {0}, {1}, {2})["highway"="secondary"];
            way(around: {0}, {1}, {2})["highway"="tertiary"];
            way(around: {0}, {1}, {2})["highway"="unclassified"];
        );
        (._;>;);
        out body;
    '''.format(radius, float(lat), float(lon), bboxString)
    #overPass_url = "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
    overPass_url = "https://overpass-api.de/api/interpreter"
    query_params = {"data": query}
    response = requests.post(overPass_url, data=query_params)
    result = response.json()
    #print(json.dumps(result, indent=2))
    return result


#the matrix builds, but this is very inefficient going directly to a matrix
def optimizeOverpassResult(jsonObject):
    coordArray = list()
    adjacency_Matrix = np.zeros((1,1))

    first = True
    for element in reversed(jsonObject['elements']):
        if (element['type'] == 'way'):
            #print(element)
            if (first):
                print(element)
            previousNode = -1
            #go through every node inside the way
            for node in element["nodes"]:
                # (next two lines) Search for the corresponding node in the elements list from the json
                for el in jsonObject['elements']:
                    if el["type"] != "node": break
                    if el["id"] == node:
                        #check if the id is in coordArray already, 
                        newEl = True
                        idx = 0 #pre initializing idx outside of the loops so they aren't local variables to those blocks
                        for count, newNode in enumerate(coordArray):
                            #print("NewNode") 
                            #print(newNode)
                            if (newNode[0] == node):
                                #if node is not new, idx is equal to the index of the corresponding node in coordArray
                                idx = count
                                #print(count)
                                newEl = False

                        #print("")
                        #if the node is new, add one 1 to N in the NxN matrix and insert to coordArray
                        if newEl:
                            #print("This was a new node")
                            coordArray.append([node, el["lat"], el["lon"]])
                            if (not first):
                                rows, cols = adjacency_Matrix.shape
                                #print(adjacency_Matrix)
                                A = np.zeros((rows+1, cols+1))
                                #print(A)
                                A[:rows, :cols] = adjacency_Matrix
                                #print(A)
                                adjacency_Matrix = A
                            #index of this element is rows+1 in the coordArray
                            idx = len(coordArray)-1
                            
                        #all the time
                        #print("last Node: " + str(previousNode) + ",\n This node: " + str(idx))
                        if (previousNode != -1):
                            coordDist = getDistance(coordArray[previousNode][1], coordArray[previousNode][2], coordArray[idx][1], coordArray[idx][2])
                            adjacency_Matrix[previousNode,idx] = coordDist
                            adjacency_Matrix[idx, previousNode] = coordDist
                        
                        #print(adjacency_Matrix)
                        previousNode = idx
                        first = False
                        break
        else:
            break
        
    #for count, coords in enumerate(coordArray):
     #   if (count < len(coordArray)-1):
      #     coordArray[count].insert(1,getDistance(coords[0], coords[1], coordArray[count+1][0], coordArray[count+1][1]))

    return coordArray, adjacency_Matrix

#Create an adjacency list from the given object/dict received from the overpass query
def optimizeForAdjListMulti(orderedDict, num):
    adjList = dict()
    coordArray = list()
    mutex = Lock()
    pool = ThreadPool()
    dictToList = orderedDict["elements"]
    numWorkers = num
    wayList = []
    nodeList = []
    for element in dictToList:
        if element["type"] == 'node':
            nodeList.append(element)
        else:
            wayList.append(element)
    
    interval_size = int(len(wayList)/numWorkers)
    
    processes = []
    for x in range(num):
        processes.append(Process(target=multiProcessTwo, args=(wayList[x * interval_size: (x+1)* interval_size], nodeList, coordArray, adjList, mutex)))
        
    for process in processes:
        process.start()

    for process in processes:
        process.join()

    #async_workers = [
      #  pool.apply_async(wayMultiProcess, args=(wayList[i * interval_size: (i+1)* interval_size], nodeList, coordArray, adjList, mutex,)) 
     #   for i in range(numWorkers)
    #]
    #pool.close()
    #pool.join()
    return adjList, coordArray

    
#the process each thread will run, taking in the following parameters:
# start and stop id for the threading
# the json object to go through
# the coordArray for which nodes will be inserted
# the adjacency list for which adjacency data; road type, weight, adjacent node, will be added
# mutex, the mutual exclusion object to prevent deadlocks and race conditions
def wayMultiProcess(wayList, nodeList, coordArray, adjList, mutex):
     #go through every way
    for element in wayList:
        roadType = element["tags"]["highway"]
        previousNode = -1
        #go through every node inside the way
        for node in element["nodes"]:
            #search for the actual node corresponding to the id of the 'node' variable above
            for el in nodeList:
                #if the type is not node, it is a way, just skip out. It is an arbitrary spot usually roughly half, where it switches
                #but it is not set in stone at any one time
                if el["type"] != "node": break
                if el["id"] == node:
                    newNode = True
                    #if the node is new, add a new element to the dict and add an adjacency from previous to it and it to previous
                    
                    if node not in adjList:
                        with mutex:
                            coordArray.append(el)
                            #the first element of a dict will be its location in coordArray
                            adjList[node] = [len(coordArray)-1, []]
                    else: newNode = False

                    #Get the distance to become the weight for the edge of the adjacency (option to switch to km?)
                    lat1 = coordArray[adjList[node][0]]['lat']
                    lon1 = coordArray[adjList[node][0]]['lon']
                    lat2 = coordArray[previousNode]['lat']
                    lon2 = coordArray[previousNode]['lon']

                    distanceToNode = int(geopy.distance.distance((lat1, lon1), (lat2, lon2)).miles * 10000) / 10000   
                    #if the node is in the dict/adjList, we won't add it, but we will have to add the previous node as an adjacent and v.v.
                    with mutex:
                        adjList[node][1].append([coordArray[previousNode]["id"], distanceToNode])
                        idOfLast = coordArray[previousNode]["id"]
                        adjList[idOfLast][1].append([el["id"], distanceToNode])
                        
                    
                    #if this was a new node
                    if newNode:
                        previousNode = len(coordArray)-1
                    #otherwise we want it to be the node at the old location
                    else:
                        previousNode = adjList[node][0]
                    break

def optimizeForAdjListThread(jsonObject, num):
    adjList = dict()
    coordArray = list()
    mutex = threading.Lock()
    threads = []

    threadCount = num

    #total count
    count = len([element for element in jsonObject["elements"]])
    startStopIds = []
    firstWayIndex = 0
    firstWayBool = False
    wayCount = 0
    #find start and stop thread ids
    for ssiCounter, element in enumerate(jsonObject["elements"]):
        #find the count of way elements that i want to thread through
        if element["type"] == "way" and not firstWayBool:
            firstWayBool = True
            wayCount = count - ssiCounter
            firstWayIndex = ssiCounter

        #with the total way count found, determine the correct locations of each start and stop for each thread
        if firstWayBool:
            if (ssiCounter == len(jsonObject["elements"])-1):
                if (len(startStopIds) == threadCount):
                    startStopIds.append(element["id"])
                else:
                    startStopIds[len(startStopIds)-1] = element["id"]
                break
            if ((ssiCounter-firstWayIndex) % max(1, wayCount//threadCount) == 0):
                startStopIds.append(element["id"])
    

    #print(startStopIds)
    #multithreading the process of converting to an adjacency list
    for x in range(0, threadCount):
        thread = threading.Thread(target=wayThreadProcess, args=(startStopIds[x], startStopIds[x+1],jsonObject["elements"], coordArray, adjList, mutex))
        threads.append(thread)
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    return adjList, coordArray

    
#the process each thread will run, taking in the following parameters:
# start and stop id for the threading
# the json object to go through
# the coordArray for which nodes will be inserted
# the adjacency list for which adjacency data; road type, weight, adjacent node, will be added
# mutex, the mutual exclusion object to prevent deadlocks and race conditions
def wayThreadProcess(start, end, jsonObject, coordArray, adjList, mutex):
     #go through every way
    localStart = False
    for element in reversed(jsonObject):
        if (element["id"] == end):
            localStart = True
        if localStart:
            roadType = element["tags"]["highway"]
            previousNode = -1
            #go through every node inside the way
            for node in element["nodes"]:
                #search for the actual node corresponding to the id of the 'node' variable above
                for el in jsonObject:
                    #if the type is not node, it is a way, just skip out. It is an arbitrary spot usually roughly half, where it switches
                    #but it is not set in stone at any one time
                    if el["type"] != "node": break
                    if el["id"] == node:
                        newNode = True
                        #if the node is new, add a new element to the dict and add an adjacency from previous to it and it to previous
                        mutex.acquire()
                        if node not in adjList:  
                            #print(node)          
                            coordArray.append(el)
                            #the first element of a dict will be its location in coordArray
                            #if previousNode == -1:
                            adjList[node] = [len(coordArray)-1, []]
                            
                        else: newNode = False

                        #Get the distance to become the weight for the edge of the adjacency (option to switch to km?)
                        lat1 = coordArray[adjList[node][0]]['lat']
                        lon1 = coordArray[adjList[node][0]]['lon']
                        lat2 = coordArray[previousNode]['lat']
                        lon2 = coordArray[previousNode]['lon']
                        #in meters from miles
                        #distanceToNode = int(1609.344 * geopy.distance.distance((lat1, lon1), (lat2, lon2)).miles * 100) / 100
                        #in miles
                        distanceToNode = int(geopy.distance.distance((lat1, lon1), (lat2, lon2)).miles * 10000) / 10000   
                        #if the node is in the dict/adjList, we won't add it, but we will have to add the previous node as an adjacent and v.v.
                        adjList[node][1].append([coordArray[previousNode]["id"], distanceToNode])
                        idOfLast = coordArray[previousNode]["id"]
                        adjList[idOfLast][1].append([el["id"],distanceToNode])
                        
                        #if this was a new node
                        if newNode:
                            previousNode = len(coordArray)-1
                        #otherwise we want it to be the node at the old location
                        else:
                            previousNode = adjList[node][0]
                        mutex.release()
                        break
        if element["id"] == start:
            break

def multiProcessTwo(wayList, nodeList, coordArray, adjList, mutex):
     #go through every way
    for element in wayList:
        roadType = element["tags"]["highway"]
        previousNode = -1
        #go through every node inside the way
        for node in element["nodes"]:
            #search for the actual node corresponding to the id of the 'node' variable above
            for el in nodeList:
                #if the type is not node, it is a way, just skip out. It is an arbitrary spot usually roughly half, where it switches
                #but it is not set in stone at any one time
                if el["type"] != "node": break
                if el["id"] == node:
                    newNode = True
                    #if the node is new, add a new element to the dict and add an adjacency from previous to it and it to previous
                    mutex.acquire()
                    if node not in adjList:  
                        #print(node)          
                        coordArray.append(el)
                        #the first element of a dict will be its location in coordArray
                        #if previousNode == -1:
                        adjList[node] = [len(coordArray)-1, []]
                    
                    else: newNode = False
                    mutex.release()
                    #Get the distance to become the weight for the edge of the adjacency (option to switch to km?)
                    lat1 = coordArray[adjList[node][0]]['lat']
                    lon1 = coordArray[adjList[node][0]]['lon']
                    lat2 = coordArray[previousNode]['lat']
                    lon2 = coordArray[previousNode]['lon']
                    #in meters from miles
                    #distanceToNode = int(1609.344 * geopy.distance.distance((lat1, lon1), (lat2, lon2)).miles * 100) / 100
                    #in miles
                    distanceToNode = int(geopy.distance.distance((lat1, lon1), (lat2, lon2)).miles * 10000) / 10000   
                    #if the node is in the dict/adjList, we won't add it, but we will have to add the previous node as an adjacent and v.v.
                    mutex.acquire()
                    adjList[node][1].append([coordArray[previousNode]["id"], distanceToNode])
                    idOfLast = coordArray[previousNode]["id"]
                    adjList[idOfLast][1].append([el["id"],distanceToNode])
                    mutex.release()
                    
                    #if this was a new node
                    if newNode:
                        previousNode = len(coordArray)-1
                    #otherwise we want it to be the node at the old location
                    else:
                        previousNode = adjList[node][0]
                    break
