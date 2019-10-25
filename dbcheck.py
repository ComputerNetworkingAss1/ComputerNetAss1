import db

db=db.DB()

# for user in db.db.accounts.find():
#     print(user["username"]+" : " +user["password"])

# newvalue_of_friends = {"$set": {"friends": []}}
# db.db.accounts.update({"username": "VIETNAM"}, newvalue_of_friends)
# db.db.accounts.update({"username": "AJS"}, newvalue_of_friends)
# for i in range(10):
#     db.make_friend(str(i),"10")
for i in range(15):
   print(str(i)+" friend is "+str(db.get_all_friend(str(i))))

for i in range(15):
   print(str(i)+" request friend is "+str(db.get_request_friend(str(i))))