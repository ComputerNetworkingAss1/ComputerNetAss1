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
            'password':password
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
            "port":port
        }
        self.db.online_peers.insert(online_peer)

    def user_logout(self,username):
        self.db.online_peers.remove({"username":username})

    def get_peer_ip_port(self,username):
        res=self.db.online_peers.find_one({"username":username})
        return (res["ip"],res["port"])



