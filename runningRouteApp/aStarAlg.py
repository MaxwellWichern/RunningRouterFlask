import random

def searchRunner(list, startNode, goalNode, length, n, TOL, heuristicNum, heuristicLength, heuristicMutation):
    percentage = 90
    #for i in range(n):
        #print(i)
    while True:
        possiblePath, curLength = aStarSearch(list, startNode, goalNode, percentage, heuristicNum, heuristicLength, heuristicMutation)
        if float(curLength) > float(length)-TOL and float(curLength) < float(length)+TOL:
            return possiblePath, curLength
        percentage -= 5
    
    return None

            

def aStarSearch(list, startNode, goalNode, mutateChance, heuristicNum, heuristicLength, heuristicMutation):
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
                connectedNodes[i-1] = element
                if not hasBeenVisited:
                    print("not visited")
                    valueOfConnectedNodes[i-1] = heuristic(list, curNode, goalNode, heuristicNum, heuristicLength, heuristicMutation)
                    valueOfConnectedNodes[i-1] += element[1]
                else:
                    print("visited")
                    valueOfConnectedNodes[i-1] = 1000
        print("outside of heuristic issue")
        print(pathLength)
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
    print(path)
    print(pathLength)
    return path, pathLength

def heuristic(list, startNode, goalNode, numberOfPaths, nodeToGo, mutateChance, amountToBreak):
    print("Entered Heuristic: {}".format(mutateChance))
    if startNode == goalNode:
        return 0
    pathLengths = []
    count = 1
    for i in range(numberOfPaths):
        print(i)
        curLength = 0
        curNode = startNode
        curNodeIndex = -1
        visited = []
        for j in range(nodeToGo):
            print(j)
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
                curNode = list[curNode][index][0]
            if curNode == goalNode:
                break
        if curNode == goalNode:
            pathLengths.append(curLength)

    while(pathLengths.count < 1):
        for i in range(numberOfPaths):
            print(i)
            curLength = 0
            curNode = startNode
            curNodeIndex = -1
            visited = []
            for j in range(nodeToGo):
                print(j)
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
                    curNode = list[curNode][index][0]
                if curNode == goalNode:
                    break
            if curNode == goalNode:
                pathLengths.append(curLength)
        if count >= amountToBreak:
            break
        count += 1
        
    minVal = 10000
    print(len(pathLengths))
    if len(pathLengths) > 0:
        minVal = pathLengths[0]
        for el in pathLengths:
            print(el)
            if el < minVal:
                minVal = el
    print("return 10000")
    return minVal