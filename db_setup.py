from pymongo import MongoClient
from flask import g

def get_db():
    if 'db' not in g:
        g.db = MongoClient("mongodb://mongodb:27017/")["samsung"]
    return g.db