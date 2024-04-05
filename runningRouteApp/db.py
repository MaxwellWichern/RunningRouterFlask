
from json import dumps
from flask import current_app, g
from werkzeug.local import LocalProxy
from flask_pymongo import PyMongo

from datetime import datetime, timezone

def get_db():
    """
    Configuration method to return db instance
    """
    db = getattr(g, "_database", None)

    if db is None:
        mongo = PyMongo(current_app).cx['main']
        db = g._database = mongo.db
       
    return db


# Use LocalProxy to read the global db instance with just `db`
db = LocalProxy(lambda: get_db())


#Retrieves the adjacency list from mongodb using the field:
#- 'email'; retrieved via login and being sent in process with the request
def getAdjList(email):
    list = db.adjacencyLists.find_one({'email': email})
    return list

#add a new adjacency list
def addAdjList(email, list, center, radius, coordArray, numNodes, startid, wayList):
    currList = getAdjList(email)
    if currList:
        print("Duplicate Email")
        return False
    newList = {"email": email,"list": dumps(list), 
               "createdAt": datetime.now(timezone.utc), 
               "center": center, 
               "radius": radius, 
               "coordArray": coordArray, 
               "numNodes": numNodes,
               "startid": startid,
               "wayList": wayList}
    success = False
    try:
        db.adjacencyLists.insert_one(newList)
        success = True
    except Exception as e:
        print("Error on the insert: ", e)
    return success

#update an adjacency list if the user email already has an existing list
def updateAdjListFull(email, list, center, radius, coordArray, numNodes, startid, wayList):
    
    try:
        response = db.adjacencyLists.update_one(
            {"email": email},
            {"$set": {"list": dumps(list), 
                      "createdAt": datetime.now(timezone.utc), 
                      "center": center, 
                      "radius": radius, 
                      "coordArray": coordArray, 
                      "numNodes": numNodes,
                      "startid": startid,
                      "wayList": wayList}},
            upsert = True
        )
        return response
    except Exception as e:
        print("Error: ", e)
        return None
    
def updateAdjListTTL(email):
    
    try:
        response = db.adjacencyLists.update_one(
            {"email": email},
            {"$set": {"createdAt": datetime.now(timezone.utc)}}
        )
        return response
    except Exception as e:
        print("Error: ", e)
        return None

#delete an adjacency list (I dont think I will see this because I will overwrite or rely on TTL)
def deleteAdjList(email):
    try:
        response = db.adjacencyLists.delete_one({"email": email})
    except Exception as e:
        print("Error Deleting List from Mongo: ", e)
        return None

    return response
