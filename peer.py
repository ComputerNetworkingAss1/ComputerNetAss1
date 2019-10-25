from socket import *
import threading
import time
import select
import logging



class peerMain:

    # peer initializations
    def __init__(self):
        self.registryName = input("Enter IP address of registry: ")
        self.registryPort = 15600
        self.tcpClientSocket = socket(AF_INET, SOCK_STREAM)
        self.tcpClientSocket.connect((self.registryName, self.registryPort))
        self.checkOnlClientSocket = socket(AF_INET, SOCK_DGRAM)
        self.checkOnlPort = 15500
        self.loginCredentials = (None, None)
        self.isOnline = False
        self.timer = None

        choice = "0"
        logging.basicConfig(filename="peer.log", level=logging.INFO)
        while choice != "3":
            choice = input("Choose: \nCreate account: 1\nLogin: 2\nLogout: 3\nFindOnlFriend: 4\nSee Add Friend Request :5\nAdd Friend :6\nAccept Friend :7\n")
            if choice is "1":
                username = input("username: ")
                password = input("password: ")

                self.createAccount(username, password)

            elif choice is "2" and not self.isOnline:
                username = input("username: ")
                password = input("password: ")
                status = self.login(username, password)
                if status is 1:
                    self.isOnline = True
                    self.loginCredentials = (username, password)
                    self.sendHelloMessage()
            elif choice is "3" and self.isOnline:
                self.logout(1)
                self.isOnline = False
                self.loginCredentials = (None, None)
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

    def login(self, username, password):
        message = "LOGIN " + username + " " + password
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



