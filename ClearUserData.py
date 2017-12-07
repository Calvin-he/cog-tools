from pymongo import MongoClient

DB = MongoClient('localhost', 27017)['ce']
DB.users.delete_many({})
DB.orders.delete_many({})
DB.comments.delete_many({})