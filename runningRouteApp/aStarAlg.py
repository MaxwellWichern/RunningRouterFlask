import random
import math
import geopy
from collections import OrderedDict

def searchRunner(list, startNode, goalNode, length, n, TOL, heuristicNum, heuristicLength, heuristicMutation, coordArray):
    percentage = 100
    #while percentage > 0:
        #print('Starting new loop while greater than 0\n\n',file=open('output.txt', 'a'))
    possiblePath, curLength = aStarSearch(list, startNode, goalNode, percentage, heuristicNum, heuristicLength, heuristicMutation, coordArray)
    #if float(curLength) > float(length)-TOL and float(curLength) < float(length)+TOL:
    return possiblePath, curLength
        #percentage -= 5

    
    #return None

            

def aStarSearch(list, startNode, goalNode, mutateChance, heuristicNum, heuristicLength, heuristicMutation, coordArray):
    curNode = startNode
    path = OrderedDict()
    pathLength = 0
    while curNode != goalNode:
        #print(pathLength)
        length = len(list[str(curNode)])

        valueOfConnectedNodes = [0 for _ in range(length)]
        connectedNodes = [None for _ in range(length)]
        for i, element in enumerate(list[str(curNode)]):
            connectedNodes[i] = element
            if str(element[0]) not in path:
                #valueOfConnectedNodes[i] = heuristic(list, str(curNode), str(goalNode), heuristicNum, heuristicLength, heuristicMutation, 100, coordArray)
                valueOfConnectedNodes[i] = taxiCabHeuristic(list, coordArray, curNode, goalNode)
                #valueOfConnectedNodes[i] = linearDistanceHeuristic(list, coordArray, curNode, goalNode)
                #print(valueOfConnectedNodes[i], file=open('connecteed.txt', 'a'))
                valueOfConnectedNodes[i] += element[1]
            else:
               valueOfConnectedNodes[i] = 10000
        minVal = 1000
        minValNodeIndex = -1
        #print(valueOfConnectedNodes, "\n")
        for i, element in enumerate(valueOfConnectedNodes):
            #print(element)
            if element < minVal:
                minVal = element
                minValNodeIndex = i
        
        path[str(curNode)] = True
        #print('\n\nactualNodeAdded',file=open('output.txt', 'a'))
        print('{},{},red,square,"Pune"'.format(coordArray[str(curNode)]['lat'],coordArray[str(curNode)]['lon']),file=open('output.txt', 'a'))
        chance = random.randint(1, 100)

        #does not mutate
        if chance < mutateChance:
            pathLength += connectedNodes[minValNodeIndex][1]
            curNode = connectedNodes[minValNodeIndex][0]
        else:
            index = random.randint(1, len(list[str(curNode)]))-1
            pathLength += list[str(curNode)][index][1]
            curNode = list[str(curNode)][index][0]

    path.append(curNode)
    print('{},{},red,square,"Pune"'.format(coordArray[str(curNode)]['lat'],coordArray[str(curNode)]['lon']),file=open('output.txt', 'a'))
    return path, pathLength

def taxiCabHeuristic(list, cordArray, curNode, goalNode):
    if str(curNode) == str(goalNode):
        print(True)
        return 0
    
    Z = geopy.Point(cordArray[str(goalNode)]['lat'], cordArray[str(curNode)]['lon'])
    CPoint = geopy.Point(cordArray[str(curNode)]['lat'], cordArray[str(curNode)]['lon'])
    GPoint = geopy.Point(cordArray[str(goalNode)]['lat'], cordArray[str(goalNode)]['lon'])
    A = round(geopy.distance.distance(CPoint,Z).miles, 5)
    B = round(geopy.distance.distance(GPoint,Z).miles, 5)
    return (A+B)

def xTaxiCabHeuristic(curNode, goalNode):
    (x1, y1) = curNode
    (x2, y2) = goalNode

    return (abs(y2 - y1) + abs(x2 - x1))

def linearDistanceHeuristic(list, cordArray, curNode, goalNode):
    if str(curNode) == str(goalNode):
        return 0
    if len(list[str(curNode)]) < 2:
        return 1000
    return round(geopy.distance.distance((cordArray[str(goalNode)]["lat"],  (cordArray[str(goalNode)]["lon"]), (cordArray[str(curNode)]["lat"], cordArray[str(curNode)]["lon"]))).miles, 2)
    #return math.sqrt((cordArray[str(goalNode)]["lat"] - cordArray[str(curNode)]["lat"])**2 + (cordArray[str(goalNode)]["lon"] - cordArray[str(curNode)]["lon"])**2)

def xLinearDistanceHeuristic(curNode, goalNode):
    (x1, y1) = curNode
    (x2, y2) = goalNode

    return (math.sqrt((y1-y2)**2 + (x1-x2)**2))

#def edgeRunnerHeuristic(list, startNode, goalNode, blockLength):
    

#def blockFinder(list, marked, curNode, blockLength):
 #   marked[]



def heuristic(list, startNode, goalNode, numberOfPaths, pathLength, mutateChance, amountToBreak, coordArray):
    #print("\n\nHeuristic\n\n", file=open('output.txt', 'a'))
    if startNode == goalNode:
        return 0
    pathLengths = []
    count = 1
    for i in range(numberOfPaths):
        #print("\n\nNew Path\n\n", file=open('output.txt', 'a'))
        curLength = 0
        curNode = startNode
        curNodeIndex = -1
        visited = dict()
        for j in range(pathLength):
            chance = random.randint(1, 100)
            minDistance = 1000
            minDistanceNode = -1
            for k, element in enumerate(list[str(curNode)]):
                if str(element[0]) not in visited:
                    if element[1] < minDistance:
                        minDistance = element[1]
                        minDistanceNode = element[0]

            visited[str(curNode)] = True
            
            #print('{},{},red,square,"Pune"'.format(coordArray[str(curNode)]['lat'],coordArray[str(curNode)]['lon']),file=open('output.txt', 'a'))
            
            #doesn't mutate
            if chance < mutateChance:
                if minDistanceNode != -1:
                    curLength += minDistance
                    curNode = minDistanceNode
                else:
                    index = random.randint(0, len(list[str(curNode)]))-1
                    curLength += list[str(curNode)][index][1]
                    curNode = list[str(curNode)][index][0]
            else:
                index = random.randint(0, len(list[str(curNode)]))-1
                curLength += list[str(curNode)][index][1]
                curNode = list[str(curNode)][index][0]
            if str(curNode) == str(goalNode):
                break
        if str(curNode) == str(goalNode):
            pathLengths.append(curLength)

    while(len(pathLengths) < 1):
        print('Still not found')
        for i in range(numberOfPaths):
            curLength = 0
            curNode = startNode
            curNodeIndex = -1
            visited = dict()
            for j in range(pathLength):
                chance = random.randint(1, 100)
                minDistance = 1000
                minDistanceNode = -1
                for k, element in enumerate(list[str(curNode)]):
                    if str(element[0]) not in visited:
                        if element[1] < minDistance:
                            minDistance = element[1]
                            minDistanceNode = element[0]
                visited[str(curNode)] = True
                #doesn't mutate
                if chance < mutateChance:
                    if minDistanceNode != -1:
                        curLength += minDistance
                        curNode = minDistanceNode
                else:
                    index = random.randint(1, len(list[str(curNode)]))-1
                    curLength += list[str(curNode)][index][1]
                    curNode = list[str(curNode)][index][0]
                if str(curNode) == str(goalNode):
                    break
            if str(curNode) == str(goalNode):
                pathLengths.append(curLength)
        if count >= amountToBreak:
            break
        count += 1
    print('found')
    minVal = 10000
    if len(pathLengths) > 0:
        minVal = pathLengths[0]
        for el in pathLengths:
            if el < minVal:
                minVal = el
    
    return minVal
