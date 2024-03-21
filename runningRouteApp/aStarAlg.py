import random

def searchRunner(list, startNode, goalNode, length, n):
    percentage = 95
    for i in range(n):
        possiblePath, curLength = aStarSearch(list, startNode, goalNode, percentage)
        if curLength == length:
            return possiblePath, curLength
        percentage -= 5
    
    return None

            

def aStarSearch(list, startNode, goalNode, mutateChance):
    curNode = startNode
    path = []
    pathLength = 0
    while curNode != goalNode:
        length = len(list[curNode]) - 1
        valueOfConnectedNodes = [0 for _ in range(length)]
        connectedNodes = [None for _ in range(length)]
        hasBeenVisited = False
        for i, element in enumerate(list[curNode]):
            if i != 0:
                hasBeenVisited = False
                for j in path:
                    if element[0] == j:
                        hasBeenVisited = True
                        break
                connectedNodes[i] = element
                if not hasBeenVisited:
                    valueOfConnectedNodes[i] = heuristic(list, curNode, goalNode, 5, 1000, 90)
                    valueOfConnectedNodes[i] += element[1]
                else:
                    valueOfConnectedNodes[i] = 1000
        
        minVal = 1000
        minValNodeIndex = -1
        for i, element in enumerate(valueOfConnectedNodes):
            if element < minVal:
                if not hasBeenVisited:
                    minVal = element
                    minValNodeIndex = i
        
        path.append(curNode)
        chance = random.randint(1, 100)
        #does not mutate
        if chance < mutateChance:
            pathLength += connectedNodes[minValNodeIndex][1]
            curNode = connectedNodes[minValNodeIndex][0]
        else:
            index = random.randint(1, len(list[curNode])-1)
            pathLength += list[curNode][index][1]
            curNode = list[curNode][index][0]
    
    path.append(curNode)
    #path.append(pathLength)
    return path, pathLength

def heuristic(list, startNode, goalNode, numberOfPaths, nodeToGo, mutateChance):
    if startNode == goalNode:
        return 0
    pathLengths = []
    for i in range(numberOfPaths):
        curLength = 0
        curNode = startNode
        curNodeIndex = -1
        visited = []
        for j in range(nodeToGo):
            chance = random.randint(1, 100)
            minDistance = 1000
            minDistanceNode = -1
            for k, element in enumerate(list[curNode]):
                if k != 0:
                    for l in range(len(visited)):
                        if visited[l] != element[0]:
                            if element[1] < minDistance:
                                minDistance = element[1]
                                minDistanceNode = element[0]
            visited.append(curNode)
            #doesn't mutate
            if chance < mutateChance:
                if minDistanceNode != -1:
                    curLength += minDistance
                    curNode = minDistanceNode
            else:
                index = random.randint(1, len(list[curNode])-1)
                curLength += list[curNode][index][1]
                curNode = list[curNode][index][1]
            if curNode == goalNode:
                break
        if curNode == goalNode:
            pathLengths.append(curLength)
        
        if len(pathLengths) > 0:
            minVal = pathLengths[0]
            for el in pathLengths:
                if el < minVal:
                    minVal = el
        
        return minVal