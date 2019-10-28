from socket import *
import threading
import select
import logging
import db


class ClientThread(threading.Thread):
    def __init__(self,ip,port,tcpClientSocket):
        threading.Thread.__init__(self)
        #ip of connected peer
        self.ip=ip
        #port of conected peer
        self.port=port
        #socket of conected peer
        self.tcpClientSocket=tcpClientSocket
        #username of conected peer
        self.username=None
        #status (is,not onine)
        self.isOnline=True
        #ServerThread to handle something else,
        #continue reading for more information
        self.ServerThread=None
        print("New thread started for " + ip + ":" + str(port))

    def run(self):
        #locks for thread which will be used for thread synchronization,break the lock
        #when curent peer(which send request to server) succesfully login or logout
        self.lock=threading.Lock()
        print("Connection from : "+self.ip +" : "+str(self.port))
        print("IP Connected: "+ self.ip)

        #handle request from another peer to the server thread
        while True:
            try:
                #waits for incoming message from  peers to registry
                #message form: list with 3 element, first is request type,
                #second is user name, thirst is password
                message=self.tcpClientSocket.recv(1024).decode().split( )

                logging.info("Received from " + self.ip+ " : " + str(self.port) +" -> " +" ".join(message))
                if len(message)==0:
                    break
                #Register Message
                if message[0] =='JOIN':
                    #If the username is exist
                    if db.is_account_exists(message[1]):
                        response="account already exist"
                        print("From-> "+self.ip+ " : "+str(self.port)+" "+response)
                        logging.info("Send to "+ self.ip +" : "+ str(self.port)+ " -> "+response)
                        self.tcpClientSocket.send(response.encode())
                    else:
                        #If not, create an account
                        db.register(message[1],message[2])
                        response='successfully register'
                        logging.info("Send to "+ self.ip +" : "+ str(self.port)+ " -> "+response)
                        self.tcpClientSocket.send(response.encode())
                #Login Message
                elif message[0] =='LOGIN':
                    #Handle login using non-exist account
                    if not db.is_account_exists(message[1]):
                        response="account not exist"
                        logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                        self.tcpClientSocket.send(response.encode())
                    #If account exist, but already online
                    elif db.is_account_online(message[1]):
                        response='account is online'
                        logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                        self.tcpClientSocket.send(response.encode())
                    #account exist and not online, handle password
                    else:
                        truePass=db.get_password(message[1])
                        #password correct
                        if truePass==message[2]:
                            self.username=message[1]
                            self.lock.acquire()
                            try:
                                tcpThreads[self.username]=self
                            finally:
                                self.lock.release()

                            db.user_login(message[1],self.ip,str(message[3]))
                            #login succes, so create server thread for this peer,
                            # also set timer for this thread
                            response='succesfully login'
                            logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                            self.tcpClientSocket.send(response.encode())
                            self.ServerThread=ServerThread(self.username,self.tcpClientSocket)
                            self.ServerThread.start()
                            self.ServerThread.timer.start()
                        else:
                            response="incorect password"
                            logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                            self.tcpClientSocket.send(response.encode())

                #param :type. username of logout account
                elif message[0]=='LOGOUT':
                    #user is online =>removes from online_peers list

                    if len(message) >1 and message[1] is not None and db.is_account_online(message[1]):
                        db.user_logout(message[1])
                        self.lock.acquire()
                        try:
                            if message[1] in tcpThreads:
                                del tcpThreads[message[1]]
                        finally:
                            self.lock.release()
                        print(self.ip + ":" + str(self.port) + " is logged out")
                        logging.info("Send to " + self.ip + ":" + str(self.port) + " ->  is logout")
                        self.tcpClientSocket.close()
                        self.ServerThread.timer.cancel()
                        break

                    else:
                        self.tcpClientSocket.close()
                        break

               #find online friend
                elif message[0]=='CHECKONL':
                    if db.is_account_exists(message[1]) and db.is_account_online(message[1]):
                        ListOnlineFriends=db.get_online_friends(message[1])
                        if len(ListOnlineFriends)==0:
                            response='No firend of you are online now'
                        else:
                            response = "list of online friends are "
                            for i in ListOnlineFriends:
                                response+=i+" "
                        logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                        self.tcpClientSocket.send(response.encode())


                #param: type,username(peer want to add),username(of peer being added)
                elif message[0]=='ADDFRIEND':
                    if len(message)>1 and message[1] and message[2] and db.is_account_exists(message[2]) and db.is_account_online(message[1]):
                        response=db.insert_friend_request(message[2],message[1])
                        if response=='AlreadyFriend':
                            response='You and '+ message[1]+ " are already friend"
                        elif response=='AlreadyAskFriendRequest':
                            response='You have sent a request for ' +message[2]
                        else:
                            response = "your request is successfully sending to " + message[2]
                            logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                        self.tcpClientSocket.send(response.encode())
                    else :
                        response = 'user does not exist'
                        logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                        self.tcpClientSocket.send(response.encode())
                # param: type,username (peer THAT ACCEPT),username(peer being ACCEPTED)
                elif message[0]=='ACCEPTFRIEND':
                    if len(message) > 1 and message[1] and message[2] and db.is_account_exists(message[2]) and db.is_account_online(message[1]):
                        if db.accept_friend_request(message[1],message[2])=='NotInRequest':
                            response=message[2]+ "not in your request list"

                        else:
                            db.make_friend(message[1],message[2])
                            response = "accept successfull you and " + message[2] +" are friend"
                        logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                        self.tcpClientSocket.send(response.encode())
                    else:
                        response = 'user does not exist'
                        logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                        self.tcpClientSocket.send(response.encode())

                elif message[0]=='VIEWREQUESTFRIEND':
                    if len(message)>1 and db.is_account_online(message[1]):
                        ListReFriend= db.get_request_friend(message[1])
                        if len(ListReFriend)==0:
                            response="You have no request"
                        else:
                            response = "list of request friends are "
                            for i in ListReFriend:
                                response += i + " "
                        logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                        self.tcpClientSocket.send(response.encode())
                    else :
                        response='NotLoginYet'
                        self.tcpClientSocket.send(response.encode())



                elif message[0] == "SEARCH":
                    # checks if an account with the username exists
                    if db.is_account_exists(message[1]):
                        # checks if the account is online
                        # and sends the related response to peer
                        if db.is_account_online(message[1]):
                            peer_info = db.get_peer_ip_port(message[1])
                            response = "search-success " + peer_info[0] + ":" + peer_info[1]
                            logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                            self.tcpClientSocket.send(response.encode())
                        else:
                            response = "search-user-not-online"
                            logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                            self.tcpClientSocket.send(response.encode())
                    # enters if username does not exist
                    else:
                        response = "search-user-not-found"
                        logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                        self.tcpClientSocket.send(response.encode())




            except OSError as oErr:
                pass
                # logging.error("OSError: {0}".format(oErr))

    def resetTimeout(self):
        self.ServerThread.resetTimer()

#Server thread for clients(each thread serve just
#one client)
class ServerThread(threading.Thread):
    def __init__(self, username, clientSocket):
        threading.Thread.__init__(self)
        #username of conected peer
        self.username=username
        self.timer=threading.Timer(5,self.waitHelloMessage)
        #ClientSocket of coneted peer
        self.tcpClientSoccket=clientSocket
    #when user is online, HELLO hidden message is send to server
    #every second (to indicate user is still online or not)
    #if after 5s  server thread not receive any message, then client is indcated that they disconect

    def waitHelloMessage(self):
        if self.username is not None:
            db.user_logout(self.username)
            if self.username in tcpThreads:
                del tcpThreads[self.username]

            self.tcpClientSoccket.close()
            self.timer.cancel()
            logging.info("Removed " + self.username + " from online peers")
            print("Removed " + self.username + " from online peers")

    # resets timer for serverThread
    def resetTimer(self):
        self.timer.cancel()
        self.timer = threading.Timer(5, self.waitHelloMessage)
        self.timer.start()



print("Registry started...")
port=15600
checkOnlServerport=15500
db=db.DB()
for online_user in db.db.online_peers.find():
    db.user_logout(online_user["username"])
tcpThreads = {}
hostname=gethostname()
host = gethostbyname(hostname)
#host= gethostbyname( '0.0.0.0' )
print("Host ip: "+str(host)+ " port "+str(port))
logging.basicConfig(filename="registry.log", level=logging.INFO)
Mainserver=socket(AF_INET,SOCK_STREAM)
checkOnlServer=socket(AF_INET,SOCK_DGRAM)
Mainserver.bind(('',port))
checkOnlServer.bind(('',checkOnlServerport))
Mainserver.listen(5)

sock_list=[Mainserver,checkOnlServer]
while sock_list:
    print("Listening for incoming connections...")
    read_sock,_,__=select.select(sock_list,[],sock_list)
    for notifed_socket in read_sock:
        if notifed_socket==Mainserver:
            client_socket,addr=Mainserver.accept()
            HandleThread = ClientThread(addr[0], addr[1], client_socket)
            HandleThread.start()
        elif notifed_socket==checkOnlServer:
            message, clientAddress = notifed_socket.recvfrom(1024)
            message = message.decode().split()
            if message[0] == "HELLO":
                if message[1] in tcpThreads:
                    tcpThreads[message[1]].resetTimeout()
                    print("Hello is received from " + message[1])
                    #logging.info("Received from " + clientAddress[0] + ":" + str(clientAddress[1]) + " -> " + " ".join(message))


Mainserver.close()















