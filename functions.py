import requests, json
from math import acos, sin, cos, radians
import numpy as np
import threading
import time
import geopy.distance


def fixBoundingBox(direction, lat, lon, radius):
    bboxFixedCoords = {"minLat": 0, "maxLat": 0, "minLon": 0, "maxLon": 0}
    if (direction == 'North'):
        bboxFixedCoords["minLon"] = lon
        bboxFixedCoords["maxLon"] = geopy.distance.distance(miles=radius).destination(geopy.Point(lat,lon), bearing=0).longitude
        bboxFixedCoords["minLat"] = geopy.distance.distance(miles=radius).destination(geopy.Point(lat,lon), bearing=270).latitude
        bboxFixedCoords["maxLat"] = geopy.distance.distance(miles=radius).destination(geopy.Point(lat,lon), bearing=90).latitude
    elif (direction == 'East'):
        bboxFixedCoords["minLon"] = geopy.distance.distance(miles=radius).destination(geopy.Point(lat,lon), bearing=180).longitude
        bboxFixedCoords["maxLon"] = geopy.distance.distance(miles=radius).destination(geopy.Point(lat,lon), bearing=0).longitude
        bboxFixedCoords["minLat"] = lat
        bboxFixedCoords["maxLat"] = geopy.distance.distance(miles=radius).destination(geopy.Point(lat,lon), bearing=90).latitude
    elif (direction == 'South'):
        bboxFixedCoords["minLon"] = geopy.distance.distance(miles=radius).destination(geopy.Point(lat,lon), bearing=180).longitude
        bboxFixedCoords["maxLon"] = lon
        bboxFixedCoords["minLat"] = geopy.distance.distance(miles=radius).destination(geopy.Point(lat,lon), bearing=270).latitude
        bboxFixedCoords["maxLat"] = geopy.distance.distance(miles=radius).destination(geopy.Point(lat,lon), bearing=90).latitude
    elif (direction == 'West'):
        bboxFixedCoords["minLon"] = geopy.distance.distance(miles=radius).destination(geopy.Point(lat,lon), bearing=180).longitude
        bboxFixedCoords["maxLon"] = geopy.distance.distance(miles=radius).destination(geopy.Point(lat,lon), bearing=0).longitude
        bboxFixedCoords["minLat"] = geopy.distance.distance(miles=radius).destination(geopy.Point(lat,lon), bearing=270).latitude
        bboxFixedCoords["maxLat"] = lat
    elif (direction == 'North-East'):
        topRight = geopy.distance.distance(miles=radius).destination(geopy.Point(lat,lon), bearing=45)
        bboxFixedCoords["minLon"] = lon
        bboxFixedCoords["maxLon"] = topRight.longitude
        bboxFixedCoords["minLat"] = lat
        bboxFixedCoords["maxLat"] = topRight.latitude
    elif (direction == 'South-East'):
        bottomRight = geopy.distance.distance(miles=radius).destination(geopy.Point(lat,lon), bearing=135)
        bboxFixedCoords["minLon"] = bottomRight.longitude
        bboxFixedCoords["maxLon"] = lon
        bboxFixedCoords["minLat"] = lat
        bboxFixedCoords["maxLat"] = bottomRight.latitude
    elif (direction == 'South-West'):
        bottomLeft = geopy.distance.distance(miles=radius).destination(geopy.Point(lat,lon), bearing=225)
        bboxFixedCoords["minLon"] = bottomLeft.longitude
        bboxFixedCoords["maxLon"] = lon
        bboxFixedCoords["minLat"] = bottomLeft.latitude
        bboxFixedCoords["maxLat"] = lat
    elif (direction == 'North-West'):
        bottomLeft = geopy.distance.distance(miles=radius).destination(geopy.Point(lat,lon), bearing=315)
        bboxFixedCoords["minLon"] = lon
        bboxFixedCoords["maxLon"] = bottomLeft.longitude
        bboxFixedCoords["minLat"] = bottomLeft.latitude
        bboxFixedCoords["maxLat"] = lat

    return bboxFixedCoords

def overpassQuery(mileage, lat, lon, address, direction, roadList):
    radius = 1609.344 * float(mileage)/2.0
    if (address != "NULL"):
        location = True #temp data
        # geocode to get coords, else just use lat and lon
    if direction:
        coordsForBBox = fixBoundingBox(direction, lat, lon, radius)
        bboxString = '[bbox: {}, {}, {}, {}];'.format(coordsForBBox["minLat"],coordsForBBox["minLon"], coordsForBBox["maxLat"], coordsForBBox["maxLon"])
    query = '''
        (
            way(around: {0}, {1}, {2})["highway"="residential"];
            way(around: {0}, {1}, {2})["highway"="secondary"];
            way(around: {0}, {1}, {2})["highway"="tertiary"];
            way(around: {0}, {1}, {2})["highway"="unclassified"];
        );
        (._;>;);
        out body;
    '''.format(radius, float(lat), float(lon))
    #overPass_url = "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
    overPass_url = "https://overpass-api.de/api/interpreter"
    query_params = {"data": query}
    response = requests.post(overPass_url, data=query_params)
    result = response.json()
    #print(json.dumps(result, indent=2))
    return result


#forgoing distance until the matrix can be built
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

def optimizeForAdjList(jsonObject):
    adjList = dict()
    coordArray = list()
    mutex = threading.Lock()
    threads = []

    threadCount = 4

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

        #with the waycount found determine the correct locations
        if firstWayBool:
            if (ssiCounter == len(jsonObject["elements"])-1):
                if (len(startStopIds) == threadCount):
                    startStopIds.append(element["id"])
                else:
                    startStopIds[len(startStopIds)-1] = element["id"]
                break
            if ((ssiCounter-firstWayIndex) % max(1, wayCount//threadCount) == 0):
                startStopIds.append(element["id"])
    

    print(startStopIds)
    #multithreading the process of converting to an adjacency list
    for x in range(0, threadCount):
        thread = threading.Thread(target=wayThreadProcess, args=(startStopIds[x], startStopIds[x+1],jsonObject, coordArray, adjList, mutex))
        threads.append(thread)
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    return adjList, coordArray

#get the distance in kilometers between two coordinates
def getDistance(lat1, lon1, lat2, lon2):
    return acos(sin(radians(lat1))*sin(radians(lat2))+cos(radians(lat1))*cos(radians(lat2))*cos(radians(lon2-lon1)))*6371
    
#the process each thread will address
def wayThreadProcess(start, end, jsonObject, coordArray, adjList, mutex):
     #go through every way
    localStart = False
    for element in reversed(jsonObject["elements"]):
        if (element["id"] == end):
            localStart = True
        if localStart:
            roadType = element["tags"]["highway"]
            previousNode = -1
            #go through every node inside the way
            for node in element["nodes"]:
                #search for the actual node corresponding to the id of the 'node' variable above
                for el in jsonObject["elements"]:
                    #if the type is not node, it is a way, just skip out. It is an arbitrary spot usually roughly half, where it switches
                    #but it is not set in stone at any one time
                    if el["type"] != "node": break
                    if el["id"] == node:
                        newNode = True
                        #if the node is new, add a new element to the dict and add an adjacency from previous to it and it to previous
                        mutex.acquire()
                        if str(node) not in adjList:  
                            #print(node)          
                            coordArray.append(el)
                            #the first element of a dict will be its location in coordArray
                            #if previousNode == -1:
                            adjList[str(node)] = {'coordArrayId': len(coordArray)-1, 'adjacencies': []}
                            
                        else: newNode = False
                        #if the node is in the dict/adjList, we won't add it, but we will have to add the previous node as an adjacent and v.v.
                        adjList[str(node)]['adjacencies'].append({'nodeId': str(coordArray[previousNode]["id"]), 'connectedBy': roadType})
                        idOfLast = coordArray[previousNode]["id"]
                        adjList[str(idOfLast)]['adjacencies'].append({'nodeId': str(el["id"]), 'connectedBy': roadType})
                        
                        #if this was a new node
                        if newNode:
                            previousNode = len(coordArray)-1
                        #otherwise we want it to be the node at the old location
                        else:
                            previousNode = adjList[str(node)]['coordArrayId']
                        mutex.release()
                        break
        #TODO I do not believe the very last way is included unfortunately
        #The thread Ids are [start,stop), but does that really matter?
        #end of thread interval, leave 
        if element["id"] == start:
            break

