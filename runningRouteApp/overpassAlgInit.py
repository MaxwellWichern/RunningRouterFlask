import os
import requests, json
import geopy.distance
from multiprocessing import Lock, Process
import multiprocessing
from threading import Semaphore
from math import sqrt
from .db import updateAdjListTTL
import random
from time import sleep, time
from itertools import pairwise
import networkx as nx
import matplotlib.pyplot as plt
import traceback
import ast


#This function fixes the bounding box around the start location to help limit the number of nodes as well as add a neat utility to the user
#Parameters include
# direction: (North, South, East, West, North-East, North-West, South-East, South-West)
# lat: latitude positioning in Decimal Degrees
# lon: longitude positioning in Decimal Degrees
# distMile: The distance in miles
def fixBoundingBox(direction, lat, lon, distMile):

    bboxFixedCoords = {"minLat": 0, "minLon": 0, "maxLat": 0, "maxLon": 0}
    bboxFixedCoords["minLon"] = geopy.distance.distance(miles=distMile).destination(geopy.Point(lat,lon), bearing=270).longitude
    bboxFixedCoords["maxLon"] = geopy.distance.distance(miles=distMile).destination(geopy.Point(lat,lon), bearing=90).longitude
    bboxFixedCoords["minLat"] = geopy.distance.distance(miles=distMile).destination(geopy.Point(lat,lon), bearing=180).latitude
    bboxFixedCoords["maxLat"] = geopy.distance.distance(miles=distMile).destination(geopy.Point(lat,lon), bearing=0).latitude
    if (direction == 'N'):
        bboxFixedCoords["minLon"] = lon
    elif (direction == 'E'):
        bboxFixedCoords["minLat"] = lat
    elif (direction == 'S'):
        bboxFixedCoords["maxLon"] = lon
    elif (direction == 'W'):
        bboxFixedCoords["maxLat"] = lat
    elif (direction == 'NE'):
        topRight = geopy.distance.distance(miles=sqrt(2*distMile*distMile)).destination(geopy.Point(lat,lon), bearing=45)
        bboxFixedCoords["minLon"] = lon
        bboxFixedCoords["maxLon"] = topRight.longitude
        bboxFixedCoords["minLat"] = lat
        bboxFixedCoords["maxLat"] = topRight.latitude
    elif (direction == 'SE'):
        bottomRight = geopy.distance.distance(miles=sqrt(2*distMile*distMile)).destination(geopy.Point(lat,lon), bearing=135)
        bboxFixedCoords["minLon"] = bottomRight.longitude
        bboxFixedCoords["maxLon"] = lon
        bboxFixedCoords["minLat"] = lat
        bboxFixedCoords["maxLat"] = bottomRight.latitude
    elif (direction == 'SW'):
        bottomLeft = geopy.distance.distance(miles=sqrt(2*distMile*distMile)).destination(geopy.Point(lat,lon), bearing=225)
        bboxFixedCoords["minLon"] = bottomLeft.longitude
        bboxFixedCoords["maxLon"] = lon
        bboxFixedCoords["minLat"] = bottomLeft.latitude
        bboxFixedCoords["maxLat"] = lat
    elif (direction == 'NW'):
        topLeft = geopy.distance.distance(miles=sqrt(2*distMile*distMile)).destination(geopy.Point(lat,lon), bearing=315)        
        bboxFixedCoords["minLon"] = lon
        bboxFixedCoords["maxLon"] = topLeft.longitude
        bboxFixedCoords["minLat"] = topLeft.latitude
        bboxFixedCoords["maxLat"] = lat
    else:
        #throw an error
        print("")
    
    #fix the coordinates to have 7 decimals, arbitrarily chosen
    bboxFixedCoords["minLon"] = int(bboxFixedCoords["minLon"] * 10000)/10000
    bboxFixedCoords["maxLon"] = int(bboxFixedCoords["maxLon"] * 10000)/10000
    bboxFixedCoords["minLat"] = int(bboxFixedCoords["minLat"] * 10000)/10000
    bboxFixedCoords["maxLat"] = int(bboxFixedCoords["maxLat"] * 10000)/10000
    return bboxFixedCoords

# when the user queries to generate a route, the start point might not correspond with a node on a highway tag,
# so this finds the nearest coordinate that will be within the area
#lat: latitude
#lon: longitude
#mileage: distance goal, but in this case it is used as the vicinity to check around
def findCheckStart(lat, lon, mileage, list = None):
    meters = 100
    min = mileage
    while meters/2 < min and min == mileage:
        query = '''
            [out:json];
            (
                way(around: {0}, {1}, {2})["highway"="residential"];
                way(around: {0}, {1}, {2})["highway"="secondary"];
                way(around: {0}, {1}, {2})["highway"="tertiary"];
                way(around: {0}, {1}, {2})["highway"="unclassified"];
                way(around: {0}, {1}, {2})["highway"="primary"];
            );
            (._;>;);
            out body;
        '''.format(meters, float(lat), float(lon))

        overPass_url = "https://overpass-api.de/api/interpreter"
        query_params = {"data": query}
        failed = True
        count = 0
        while failed and count < 5:
            try:
                response = requests.post(overPass_url, data=query_params)
                result = response.json()
                failed = False
            except requests.exceptions.ConnectionError as re: 
                print("Error: ", re)
            sleep(1)

        #finds the distance of the nodes that were found if any, the closest one is set as the start and returns
        minNode = None
        if list:
            for node in result['elements']:
                if node["type"] == "node":
                    if str(node["id"]) in list:
                        tempD = geopy.distance.distance((lat, lon), (node['lat'], node['lon']))
                        if tempD < min: 
                            min = tempD
                            minNode = node
        else:
            for node in result['elements']:
                if node["type"] == "node":
                    tempD = geopy.distance.distance((lat, lon), (node['lat'], node['lon']))
                    if tempD < min: 
                        min = tempD
                        minNode = node
        meters *= 2

    if minNode is None: return False, False, False
    return minNode["lat"], minNode["lon"] , minNode["id"]
        

#This is the first method called to begin the route gen, specifically finding all the nodes and ways located in the area selected
#mileage: the mileage goal for the route
#lat: latitude
#lon: longitude
#direction: direction is of the form North, East, South, West, North-East, North-West, South-East, South-West
#-----------This is used to limit the bounding box in the query to help prevent excess data
def overpassQuery(mileage, lat, lon, direction, roadOption):
    #find the start location
    radius = 1609.344 * float(mileage)/2.0
    try:
        print("Find correct start")
        lat, lon, startid = findCheckStart(lat, lon, radius)
    except Exception as e:
        print("Error: ", e)
        print("Start point not within 2 mile area, recommended to find a new start")
        return None
    #fix the bounding box
    print("Fix bounding box")
    coordsForBBox = fixBoundingBox(None, float(lat), float(lon), float(mileage)/2)
    bboxString = '[bbox: {}, {}, {}, {}]'.format(coordsForBBox["minLat"],coordsForBBox["minLon"], coordsForBBox["maxLat"], coordsForBBox["maxLon"])
    ways = ''
    if "Streets" in roadOption or roadOption == '[]':
        ways += '''way(around: {0}, {1}, {2})["highway"="residential"];
            way(around: {0}, {1}, {2})["highway"="secondary"];
            way(around: {0}, {1}, {2})["highway"="tertiary"];
            way(around: {0}, {1}, {2})["highway"="unclassified"];
            way(around:{0}, {1}, {2})["highway" = "service"];
            '''.format(radius, float(lat), float(lon))
    if "Highways" in roadOption:
        ways += 'way(around: {0}, {1}, {2})["highway"="primary"];'.format(radius, float(lat), float(lon))

    if "Walkways" in roadOption:
        ways += '''way(around: {0}, {1}, {2})["highway" = "footway"];
          	way(around: {0}, {1}, {2})["highway" = "cycleway"];
            way(around: {0}, {1}, {2})["surface" = "dirt"];
            way(around: {0}, {1}, {2})["surface" = "unpaved"];
            '''.format(radius, float(lat), float(lon))
        
    query = '''
        [out:json]{1};
        (
            {0}
        );
        (._;>;);
        out body;
    '''.format(ways, bboxString)
    overPass_url = "https://overpass-api.de/api/interpreter"
    query_params = {"data": query}
    #This is the actual query using the data above
    failed = True
    count = 0
    while failed and count < 5:
        try:
            response = requests.post(overPass_url, data=query_params)
            result = response.json()
            failed = False
        except requests.exceptions.ConnectionError as re: 
            print("Error: ", re)
        sleep(1)
    #print(json.dumps(result, indent=2))
    return result, lat, lon, startid

#given the cumbersome data to process, I am going to limit ways to their endpoints and insert the midpoints when constructing the path
#I will still have to loop through like before, including checking if a node is in the list already in order to add it, but the issue to overcome
#is tracking the way id and how to associate it between each node. Perhaps I can have an extra element in each adjacency telling me which way it is connected by
# I will have to be careful not to do it backwards however, so when inserting I have to check that
#AdjacencyList Format at an id: [[nodeIdConnected, distance, wayIdConnectedBy],[...],[...]]
def endpointList(orderedDict):
    adjList = dict()
    coordArray = dict()
    dictToList = orderedDict["elements"]
    print("", file=open('logging.txt', 'w'))
    #go through every way
    for element in reversed(dictToList):
        if element["type"] == "node": break
        #cycle through each pair of nodes in the way
        for index, (curNode, nextNode) in enumerate(pairwise(element["nodes"])):
            #go through each node in the list to find its associated 
            #add the first element to the adjacency list and coordArray
            curNode = str(curNode)
            nextNode= str(nextNode)
            if index == 0 and curNode not in coordArray:
                if curNode not in adjList:
                    adjList[curNode] = []
                for el in dictToList:
                    if el["type"] == "way":
                        break
                    if str(el["id"]) == curNode:
                        coordArray[curNode] = el
                        break
            #all nodes will be added to the coordArray
            if nextNode not in coordArray:
                if nextNode not in adjList:
                    adjList[nextNode] = []
                for el in dictToList:
                    if el["type"] == "way":
                        break
                    if str(el["id"]) == nextNode:
                        coordArray[nextNode] = el
                        break
            
            #find the distance between each node, the total distance is stored for each endpoint adjacency
            lat1 = coordArray[str(curNode)]['lat']
            lon1 = coordArray[str(curNode)]['lon']
            lat2 = coordArray[str(nextNode)]['lat']
            lon2 = coordArray[str(nextNode)]['lon']
            distanceToNode = int(geopy.distance.distance((lat1, lon1), (lat2, lon2)).miles * 100000) / 100000
            
            adjList[curNode].append([nextNode, distanceToNode, element["id"]])
            adjList[nextNode].append([curNode, distanceToNode, element["id"]])


    return adjList, coordArray

#this function takes in a list pulled from mongodb and the data provided by the user, it will check a few conditions
#1) if the distance between the starting lat and lon and that provided by the user is greater than the mileage, a new list is needed
#2) if the radius of data saved is less than that of the requested data/2, a new one is needed
#3) otherwise it will be  allow the existing list setting lat lon and adjlist permanently in this use of the algorithm
def validateExistingList(data, existingList):
    #2.3 if it exists, we have our start node from the data element and we will have saved the start node with the list in mongodb to simplify this step
        #----We can find the distance between these two points, if the distance is greater than the mileage, we definitely need one
        lat = existingList["center"][0]
        lon = existingList["center"][1]
        adjList = dict()
        newNeeded = False
        distanceToNode = int(geopy.distance.distance((lat, lon), (data['lat'], data['lon'])).miles * 100000) / 100000
        if (data["direction"] != existingList["direction"]):
            print("New needed: change in direction")
            newNeeded = True
        elif distanceToNode > float(data["mileage"])/2: 
            print("new needed: distance > radius")
            lat=data['lat']
            lon=data['lon']
            newNeeded = True
        
        #2.4 another concern is the same start node but different distance. if the distance is larger, we need a new list, otherwise it is okay and we can reuse it
        elif float(data["mileage"])/2 > float(existingList["radius"]): 
            print("new needed: radius > existing radius")
            lat=data['lat']
            lon=data['lon']
            newNeeded = True
        #2.5 update the TTL/date for the list
        else:
            #print("", file=open("db.txt", 'w'))
            #print(f"{existingList["list"]}\n\n", file=open("db.txt", 'a'))
            adjList = json.loads(existingList["list"])
            #print(f"{adjList}\n\n", file=open("db.txt", 'a'))
            #print(f"{adjList}\n\n", file=open("db.txt", 'a'))

            print("Mongo Query: update TTL")
            updateAdjListTTL(data["email"])    
        return newNeeded, lat, lon, adjList

def rectCheckPoints(mileage, direction, lat, lon, id, list):
    checkpoints = []
    checkpoints.append([lat,lon,id])
    lastLat = lat
    lastLon = lon
    #start assuming north
    startDegree = 270
    if direction == 'E' or direction == 'NE':
        startDegree+=90
    elif direction == 'SE' or direction == 'S':
        startDegree+=180
    elif direction == 'SW' or direction == 'W':
        startDegree += 270
    else:
        startDegree = (startDegree + 90*random.randint(0,4))%360

    h = mileage/4
    bearingInterval = 90
    
    #TODO: randomise rectanglism and therefore the h
    rectanglish = random.uniform(-mileage/5, mileage/5)
    dist = h
    for x in range(4):
        if (x == 0 and len(direction) == 1):
            dist = h/2
        else:
            if x%2 == 1:
                dist = h + rectanglish
            else:
                dist = h - rectanglish
        
        coords = geopy.distance.distance(dist).destination(geopy.Point(lastLat,lastLon), bearing=(startDegree)%360)
 
        try:
            latitude, longitude, newid = findCheckStart(coords.latitude, coords.longitude, 400, list)
            if latitude != False:
                checkpoints.append([latitude, longitude, newid])
                startDegree+=(bearingInterval)
                lastLat = latitude
                lastLon = longitude
            else: 
                print("No checkpoint near this location")
        except Exception as e:
            print("Error: ", e)
            print(traceback.print_exc())

        if len(direction) == 2 and x==3:
            break
    checkpoints.append([lat,lon,id])
    return checkpoints

def findCheckPoints(mileage, direction, lat, lon, id, list):
    checkpoints = []
    checkpoints.append([lat,lon,id])
    lastLat = lat
    lastLon = lon
    bearingDegree = 300
    if direction == 'NE': bearingDegree=(bearingDegree+45)%360
    elif direction == 'E': bearingDegree=(bearingDegree+90)%360
    elif direction == 'SE': bearingDegree=(bearingDegree+135)%360
    elif direction == 'S': bearingDegree=(bearingDegree+180)%360
    elif direction == 'SW': bearingDegree=(bearingDegree+225)%360
    elif direction == 'W': bearingDegree=(bearingDegree+270)%360
    elif direction == 'NW': bearingDegree=(bearingDegree+315)%360
    elif direction == 'N': bearingDegree=bearingDegree
    else: bearingDegree=(bearingDegree+(45*random.randint(0,8)))%360
    
    if mileage < 4:
        bearingInterval = 45
        for x in range(0, 4):
            genRand = random.randint(-5,10)
            if x != mileage - 1:
                coords = geopy.distance.distance(miles=mileage/4).destination(geopy.Point(lastLat,lastLon), bearing=(bearingDegree+genRand)%360)
                try:
                    start = time.now()
                    latitude, longitude, newid = findCheckStart(coords.latitude, coords.longitude, 400, list)
                    if latitude != False:
                        checkpoints.append([latitude, longitude, newid])
                        bearingDegree+=(bearingInterval + genRand)
                        lastLat = latitude
                        lastLon = longitude
                    else: 
                        print("No node in viscinity")
                except Exception as e:
                    print("Error: ", e)
                    print("None returned when finding point, may not exist")
            else:
                checkpoints.append([lat,lon,id])
    else:
        #Assume North of not provided: TODO Change this if it is not found and different direction needed
        #from the beginning lat and lon, find a checkpoint a mile or less away a certain degree above the x axis.
        #use this bearing +- 1 or 2 degrees of bearing to allow for some random for the rest of the segments starting at the one just found
        #at the last segment, just connect it to the starting node
        #Below modulus 360
        #North: +0 degrees bearing, North-East: +45 degrees bearing, East: +90, SE: +135, S: +180, SW: +225, W: +270, NW: +315
        bearingInterval = (180)/(mileage-2)
        for x in range(0, mileage):
            #print(x)
            genRand = random.randint(-10,30)
            if x != mileage - 1:
                coords = geopy.distance.distance(miles=0.75).destination(geopy.Point(lastLat,lastLon), bearing=(bearingDegree+genRand)%360)
                try:
                    start = time()
                    latitude, longitude, newid = findCheckStart(coords.latitude, coords.longitude, 1609, list)
                    if latitude != False:
                        end = time() - start
                        checkpoints.append([latitude, longitude, newid])
                        bearingDegree+=(bearingInterval+genRand)
                        lastLat = latitude
                        lastLon = longitude
                    else: 
                        print("No node in viscinity")
                except Exception as e:
                    print("Error: ", e)
                    print("None returned when finding point, may not exist")
            else:
                checkpoints.append([lat, lon, id])
    return checkpoints

def generateDataForOutput(adjList, coordArray):
    G = nx.Graph()
    for node1 in adjList:
        for neighbor in adjList[str(node1)]:    
            orig = coordArray[str(node1)]
            curNeighbor = coordArray[str(neighbor[0])]
            G.add_node(str(node1), pos=(orig['lon'], orig['lat']))
 
            G.add_node(str(curNeighbor['id']), pos=(curNeighbor['lon'], curNeighbor['lat']))
            G.add_edge(str(node1), str(curNeighbor['id']), weight=neighbor[1])
    
    return G
            
def xTaxiCabHeuristic(G, c, g):
    pc = G.nodes[c]['pos']
    pg = G.nodes[g]['pos']
    (x1, y1) = pc
    (x2, y2) = pg

    return abs(y1 - y2) + abs(x1 - x2)

def xLinearDistanceHeuristic(c, g):
    (x1, y1) = c
    (x2, y2) = g

    return sqrt((y1-y2)**2 + (x2-x1)**2)