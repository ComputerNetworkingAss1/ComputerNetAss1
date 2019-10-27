from pymongo import MongoClient


#The code is quite clear so no
#comment needed
class DB:
    def __init__(self):
        self.client=MongoClient('localhost', 27017)
        self.db=self.client['p2p-chat']


    def is_account_exists(self,username):
        if self.db.accounts.find({'username':username}).count() > 0:
            return True
        else:
            return False

    def register(self,username,password):
        account={
            'username':username,
            'password':password,
            'friends':[],
            'addfrienRequest':[]
        }
        self.db.accounts.insert(account)

    def get_password(self,username):
        return self.db.accounts.find_one({"username":username})["password"]

    def is_account_online(self,username):
        if self.db.online_peers.find({"username":username}).count() >0:
            return True
        else:
            return False

    def user_login(self,username,ip,port):
        online_peer={
            "username":username,
            "ip":ip,
            "port":port,
        }
        self.db.online_peers.insert(online_peer)

    def user_logout(self,username):
        self.db.online_peers.remove({"username":username})

    def get_peer_ip_port(self,username):
        res=self.db.online_peers.find_one({"username":username})
        return (res["ip"],res["port"])

    def insert_friend_request(self,username,addfriendUsername):
        if addfriendUsername in self.db.accounts.find_one({"username":username})["friends"]:
            return "AlreadyFriend"
        if addfriendUsername in self.db.accounts.find_one({"username":username})["addfrienRequest"]:
            return "AlreadyAskFriendRequest"
        else:
            friendRequestOfUserName=self.db.accounts.find_one({"username":username})["addfrienRequest"]
            friendRequestOfUserName.append(addfriendUsername)
            query={"username":username}
            newvalues={"$set":{"addfrienRequest":friendRequestOfUserName}}
            self.db.accounts.update(query,newvalues)
            return "OK"

    def accept_friend_request(self,username,acceptUsername):
        User=self.db.accounts.find_one({"username": username})
        friendRequestOfUserName = User["addfrienRequest"]
        if acceptUsername not in friendRequestOfUserName:
            return "NotInRequest"
        friendRequestOfUserName.remove(acceptUsername)
        query = {"username": username}
        newvalue_of_addfriend_request = {"$set": {"addfrienRequest": friendRequestOfUserName}}
        self.db.accounts.update(query, newvalue_of_addfriend_request)
        return "OK"


    def make_friend(self,username1,username2):
        User1 = self.db.accounts.find_one({"username": username1})
        User2 = self.db.accounts.find_one({"username": username2})
        ListFriendOfUsername1 = User1["friends"]
        ListFriendOfUsername2 = User2["friends"]
        self.accept_friend_request(username1,username2)
        self.accept_friend_request(username2,username1)
        if username1 in ListFriendOfUsername2 :
            return "AlreadyFriend"

        query1 = {"username": username1}
        ListFriendOfUsername1.append(username2)
        newvalue_of_friends1 = {"$set": {"friends": ListFriendOfUsername1}}
        self.db.accounts.update(query1, newvalue_of_friends1)

        query2 = {"username": username2}
        ListFriendOfUsername2.append(username1)
        newvalue_of_friends2 = {"$set": {"friends": ListFriendOfUsername2}}
        self.db.accounts.update(query2, newvalue_of_friends2)
        return "OK"






    def get_online_friends(self,username):
        ListFriend=self.db.accounts.find_one({"username":username})["friends"]
        OnlineFriends=[]
        for online_user in self.db.online_peers.find():
            if online_user["username"] in ListFriend:
                OnlineFriends.append(online_user["username"])
        return OnlineFriends

    def get_all_friend(self,username):
        return self.db.accounts.find_one({"username":username})["friends"]

    def get_request_friend(self,username):
        return self.db.accounts.find_one({"username":username})["addfrienRequest"]






