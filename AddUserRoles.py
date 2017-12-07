from pymongo import MongoClient

DB = MongoClient('localhost', 27017)['ce']
DB.users.update_many({}, {"$addToSet": {"roles": "ROLE_USER"}})

