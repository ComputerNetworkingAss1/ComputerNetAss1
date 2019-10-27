from socket import *
import threading
import select
import logging
from p2p import Client

class peerMain():

    # peer initializations
    def __init__(self):
        super(peerMain,self).__init__()
        self.registryName = input("Enter IP address of registry: ")
        self.registryPort = 15600
        self.tcpClientSocket = socket(AF_INET, SOCK_STREAM)
        self.tcpClientSocket.connect((self.registryName, self.registryPort))
        self.checkOnlClientSocket = socket(AF_INET, SOCK_DGRAM)
        self.checkOnlPort = 15500
        self.loginCredentials = (None, None)
        self.isOnline = False
        self.timer = None
        self.peerServerPort = None
        self.peerServer = None
        self.peerClient = None
        self.peer=None

        choice = "0"
        logging.basicConfig(filename="peer.log", level=logging.INFO)
        print("Choose: \nCreate account: 1\nLogin: 2\nLogout: 3\nFindOnlFriend: 4\nSee Add Friend Request :5\nAdd Friend :6\nAccept Friend :7\n "\
              +"request [peername]\nchat message [peername] [message]\ndisconnect\nsendfile[peername] [filename]\nlist connected peer")
        while choice != "3":
            choice = input().strip()
            if choice is "1":
                username = input("username: ")
                password = input("password: ")

                self.createAccount(username, password)

            elif choice is "2" and not self.isOnline:
                username = input("username: ")
                password = input("password: ")
                peerServerPort = int(input("Enter a port number for peer server: "))
                status = self.login(username, password,peerServerPort)
                if status is 1:
                    self.isOnline = True
                    self.loginCredentials = (username, password)
                    self.peerServerPort = peerServerPort
                    hostname = gethostname()
                    host = gethostbyname(hostname)
                    self.peer = Client((self.registryName, self.registryPort), serverport=self.peerServerPort,peername=self.loginCredentials[0],serverhost=host)

                    self.sendHelloMessage()
                    self.peer.run()
                    # self.peerServer = PeerServer(self.loginCredentials[0], self.peerServerPort)
                    # self.peerServer.start()
            elif choice is "3" and self.isOnline:
                self.logout(1)
                self.isOnline = False
                self.loginCredentials = (None, None)
                self.peerServer.isOnline = False
                self.peerServer.tcpServerSocket.close()
                if self.peerClient is not None:
                    self.peerClient.tcpClientSocket.close()
                print("Logged out successfully")
            elif choice is "3":
                self.logout(2)
            elif choice is "4" and self.isOnline:
                self.findOnline()
            elif choice is "4" and not self.isOnline:
                print("You havent login yet")
            elif choice is "5":
                if self.isOnline:
                    self.SeeAddFriendRequest()
                else:
                    print('you havent login yet')
            elif choice is "6":
                if self.isOnline:
                    FriendToAdd = input("Enter Friend Name You Want To Add :")
                    self.AddFirend(FriendToAdd)
                else:
                    print('you havent login yet')
            elif choice is "7":
                if self.isOnline:
                    FriendToAccept = input("Enter Friend Name You Want To Accept :")
                    self.AcceptFriend(FriendToAccept)
                else:
                    print('you havent login yet')


            elif choice.startswith('request'):
                if self.peer==None:
                    print('You not login yet')
                else :
                    self.peer.dynamic_input_mapping['request'](choice)

            elif choice.startswith('chat message'):
                if self.peer==None:
                    print('You not login yet')
                else :
                    self.peer.dynamic_input_mapping['chat message'](choice)
            elif choice.startswith('disconnect'):
                if self.peer==None:
                    print('You not login yet')
                else :
                    self.peer.dynamic_input_mapping['disconnect'](choice)
            elif choice.startswith('sendfile'):
                if self.peer==None:
                    print('You not login yet')
                else :
                    self.peer.dynamic_input_mapping['sendfile'](choice)
            elif choice in ['yes','no','list connected peer']:
                if self.peer is None:
                    print('You not login yet')
                else:
                    self.peer.static_input_mapping[choice]()

            elif choice == "CANCEL":
                self.timer.cancel()
                break
        if choice != "CANCEL":
            self.tcpClientSocket.close()


    def createAccount(self, username, password):
        message = "JOIN " + username + " " + password
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode()
        logging.info("Received from " + self.registryName + " -> " + response)
        print(response)

    def login(self, username, password,peerServerPort):
        message = "LOGIN " + username + " " + password+" "+ str(peerServerPort)
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode()
        logging.info("Received from " + self.registryName + " -> " + response)
        if response == "succesfully login":
            print("Logged in successfully...")
            return 1
        elif response == "account not exist":
            print("Account does not exist...")
            return 0
        elif response == "account is online":
            print("Account is already online...")
            return 2
        elif response == "incorect password":
            print("Wrong password...")
            return 3

    def logout(self, option):
        if option == 1:
            message = "LOGOUT " + self.loginCredentials[0]
            self.timer.cancel()
        else:
            message = "LOGOUT"
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
        self.tcpClientSocket.send(message.encode())

    # function for searching an online user
    def findOnline(self):
        if self.loginCredentials[0]!=None:
            message = "CHECKONL "+self.loginCredentials[0]
            logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
            self.tcpClientSocket.send(message.encode())
            response = self.tcpClientSocket.recv(1024).decode()
            logging.info("Received from " + self.registryName + " -> " + response)
            print(response)

        else:
            print("You havent login yet")
    def SeeAddFriendRequest(self):
        message="VIEWREQUESTFRIEND "+self.loginCredentials[0]
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode()
        logging.info("Received from " + self.registryName + " -> " + response)
        print(response)
    def AddFirend(self,FriendToAdd):
        message='ADDFRIEND '+ self.loginCredentials[0]+" "+FriendToAdd
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode()
        logging.info("Received from " + self.registryName + " -> " + response)
        print(response)
    def AcceptFriend(self,FriendToAccept):
        message = 'ACCEPTFRIEND ' + self.loginCredentials[0] + " " + FriendToAccept
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode()
        logging.info("Received from " + self.registryName + " -> " + response)
        print(response)




    def sendHelloMessage(self):
        message = "HELLO " + self.loginCredentials[0]
        logging.info("Send to " + self.registryName + ":" + str(self.checkOnlPort) + " -> " + message)
        self.checkOnlClientSocket.sendto(message.encode(), (self.registryName, self.checkOnlPort))
        self.timer = threading.Timer(1, self.sendHelloMessage)
        self.timer.start()




# peer is started
main = peerMain()



