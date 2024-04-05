import random
import networkx as nx
import matplotlib.pyplot as plt

def searchRunner(list, startNode, goalNode, length, n, TOL, heuristicNum, heuristicLength, heuristicMutation, coordArray):
    percentage = 100
    while percentage > 0:
        possiblePath, curLength = aStarSearch(list, startNode, goalNode, percentage, heuristicNum, heuristicLength, heuristicMutation, coordArray)
        if float(curLength) > float(length)-TOL and float(curLength) < float(length)+TOL:
            return possiblePath, curLength
        percentage -= 5
    
    return None

            

def aStarSearch(list, startNode, goalNode, mutateChance, heuristicNum, heuristicLength, heuristicMutation, coordArray):
    curNode = startNode
    path = []
    pathLength = 0
    while curNode != goalNode:
        #print(pathLength)
        length = len(list[str(curNode)])
        valueOfConnectedNodes = [0 for _ in range(length)]
        connectedNodes = [None for _ in range(length)]
        hasBeenVisited = False
        for i, element in enumerate(list[str(curNode)]):
            #print(list[str(curNode)])
            hasBeenVisited = False
            for j in path:
                if element[0] == j:
                    hasBeenVisited = True
                    break
            connectedNodes[i] = element
            if not hasBeenVisited:
                valueOfConnectedNodes[i] = heuristic(list, str(curNode), str(goalNode), heuristicNum, heuristicLength, heuristicMutation, 1000, coordArray)
                valueOfConnectedNodes[i] += element[1]
            else:
                valueOfConnectedNodes[i] = 10000
        minVal = 1000
        minValNodeIndex = -1
        print(valueOfConnectedNodes, "\n")
        for i, element in enumerate(valueOfConnectedNodes):
            #print(element)
            if element < minVal:
                minVal = element
                minValNodeIndex = i
        
        path.append(curNode)
        print('\n\nactualNodeAdded'.format(coordArray[str(curNode)]['lat'],coordArray[str(curNode)]['lon']),file=open('output.txt', 'a'))
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

def heuristic(list, startNode, goalNode, numberOfPaths, pathLength, mutateChance, amountToBreak, coordArray):
    print("\n\nHeuristic\n\n", file=open('output.txt', 'a'))
    if startNode == goalNode:
        return 0
    pathLengths = []
    count = 1
    for i in range(numberOfPaths):
        curLength = 0
        curNode = startNode
        curNodeIndex = -1
        visited = []
        for j in range(pathLength):
            chance = random.randint(1, 100)
            minDistance = 1000
            minDistanceNode = -1
            for k, element in enumerate(list[str(curNode)]):
                isVisited = False
                for l in range(len(visited)):
                    #print(visited[l], " and ", element[0])
                    if visited[l] == str(element[0]):
                        #print("Equal")
                        isVisited = True
                if not isVisited:
                    if element[1] < minDistance:
                        minDistance = element[1]
                        minDistanceNode = element[0]
            visited.append(str(curNode))
            
            print('{},{},red,square,"Pune"'.format(coordArray[str(curNode)]['lat'],coordArray[str(curNode)]['lon']),file=open('output.txt', 'a'))
            
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
            visited = []
            for j in range(pathLength):
                chance = random.randint(1, 100)
                minDistance = 1000
                minDistanceNode = -1
                for k, element in enumerate(list[str(curNode)]):
                    isVisited = False
                    for l in range(len(visited)):
                        #print(visited[l], " and ", element[0])
                        if visited[l] == str(element[0]):
                            #print("Equal")
                            isVisited = True
                    if not isVisited:
                        if element[1] < minDistance:
                            minDistance = element[1]
                            minDistanceNode = element[0]
                visited.append(str(curNode))
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
