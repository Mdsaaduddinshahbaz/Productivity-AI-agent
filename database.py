from pymongo import MongoClient
import os
# connect to local MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
print(MONGO_URI)
client = MongoClient(MONGO_URI)

# check available databases
print("Databases:", client.list_database_names())

# create/use a database
db = client["testDB"]

# create/use a collection
users = db["users"]
userid=None
#login/signup handling function
def login_existing_user(user:dict):
    global userid
    username=user["username"]
    password=user["password"]
    print("username=",type(user.get("username")),"passoword=",password)
    existing_user=users.find_one({"username":user.get("username")})
    print("existing_user=",existing_user)
    if(existing_user):
        userid=existing_user["_id"]
        print("global_id is set,",userid)
        existing_username=existing_user["username"]
        existing_password=existing_user["password"]
        if username==existing_username and existing_password==password:
            return 1
        else:
            return -1
    return 404
def create_new_user(user:dict):
    global userid
    check_existing_user=users.find_one({"username":user.get("username")})
    if check_existing_user:
        return 0
    users.insert_one(user)
    new_user=users.find_one({"username":user.get("username")})
    userid=new_user["_id"]
    cnt=1
    return cnt
def read_user_info():
    fetch_username=users.find_one({"_id":userid})
    fetch_username.pop("_id")
    return fetch_username
def update_user_info(extended_user_detailss: dict):
    result = users.find_one_and_update(
        {"_id": userid},          # filter
        {'$set': extended_user_detailss}
    )
    if result:
        return {"success": True, "updated_user": result}
    else:
        return {"success": False, "message": "User not found"}
def delete_user_info(fields: list):
    # fields = ["field1", "field2"]  # example
    print(fields)
    unset_query = {field: 1 for field in fields}
    print("deleting_fields=",unset_query)
    print(userid)
    result = users.find_one_and_update(
        {"_id": userid},
        {"$unset": unset_query}
    )
    # return result.modified_count > 0  # True if something got deleted
    print(result)
    if result:
        print("true")
        return {"success": True}
    else:
        print("false")
        return {"success": False}
def return_saved_fields():
    global userid
    existing_user=users.find_one({"_id":userid})
    existing_user.pop("_id")
    return existing_user

for user in users.find():
    print(user)
