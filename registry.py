from socket import *
import threading
import select
import logging
import db


#Thread create to handle only the peer messages sent to registry
#When a peer firsts connected to registry server( registry server is
#a server handle all "the server" thing), a new client thread is created
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

                            db.user_login(message[1],self.ip,self.port)
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
                        self.tcpClientSocket.close()
                        self.ServerThread.timer.cancel()
                        break

                    else:
                        self.tcpClientSocket.close()
                        break

                #check if an arbitary user is online or not
                elif message[0]=='CHECKONL':
                    if db.is_account_exists(message[1]):
                        if db.is_account_online(message[1]):
                            peer_info=db.get_peer_ip_port(message[1])
                            response = "search successfull " + peer_info[0] + ":" + peer_info[1]
                            logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                            self.tcpClientSocket.send(response.encode())

                        else:
                            response='user does not online'
                            logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                            self.tcpClientSocket.send(response.encode())

                    else:
                        response = "search-user-not-found"
                        logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                        self.tcpClientSocket.send(response.encode())

            except OSError as oErr:
                logging.error("OSError: {0}".format(oErr))



#UDPServer thread for clients(each thread serve just
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
            print("Removed " + self.username + " from online peers")

    # resets timer for udp server
    def resetTimer(self):
        self.timer.cancel()
        self.timer = threading.Timer(5, self.waitHelloMessage)
        self.timer.start()








print("Registry started...")
port=15600
db=db.DB()
tcpThreads = {}
hostname=gethostname()
host = gethostbyname(hostname)
print("Host ip: "+str(host)+ " port "+str(port))
logging.basicConfig(filename="registry.log", level=logging.INFO)
s=socket(AF_INET,SOCK_STREAM)
s.bind((hostname,port))
s.listen(5)
clientsocket,addres=s.accept()
ClientHandleThread=ClientThread(addres[0],addres[1],clientsocket)
ClientHandleThread.start()


















