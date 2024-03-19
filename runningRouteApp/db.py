import bson

from flask import current_app, g
from werkzeug.local import LocalProxy
from flask_pymongo import PyMongo

from pymongo.errors import DuplicateKeyError, OperationFailure
from bson.objectid import ObjectId
from bson.errors import InvalidId


def get_db():
    """
    Configuration method to return db instance
    """
    db = getattr(g, "_database", None)

    if db is None:

        db = g._database = PyMongo(current_app).db
       
    return db


# Use LocalProxy to read the global db instance with just `db`
db = LocalProxy(get_db)

def getAdjList(email):
    """
    Retrieves the adjacency list from mongodb using the field:
    - 'email'; retrieved via login and being sent in process with the request
    """
    list = db.adjacencyLists.find_one({'email': email})
    return list

def addAdjList():
    print("adding the adjacency list to mongo")

def updateAdjList():
    print("Changing the Adjacency list")

def deleteAdjList():
    print("Deleting the adjList")
