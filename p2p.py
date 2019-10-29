import os
import socket
import sys
import json
import threading
import time
import atexit


def get_download_path():
    if os.name == 'nt':
        import winreg
        sub_key = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders'
        downloads_guid = '{374DE290-123F-4565-9164-39C4925E467B}'
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
            location = winreg.QueryValueEx(key, downloads_guid)[0]
        return location
    else:
        return os.path.join(os.path.expanduser('~'), 'downloads')


from math import ceil
from BasedPeer import Peer
from config import *

class Client(Peer):
    def __init__(self,server_info, peername=None, serverhost='localhost', serverport=40000):
        super(Client, self).__init__(serverhost, serverport)
        self.name = peername if peername is not None else ':'.join((serverhost, serverport))
        self.thread=None
        self.server_info=server_info
        handlers = {
            CHAT_MESSAGE: self.recv_message,
            CHAT_ACCEPT: self.chat_accept,
            CHAT_REFUSE: self.chat_refuse,
            REQUEST: self.request,
            DISCONNECT: self.disconnect,
            FILE_TRANSFER: self.file_transfer,
            FILE_TRANSFER_REQUEST: self.recv_file_transfer_request,
            FILE_TRANSFER_ACCEPT: self.recv_file_transfer_accept,
            FILE_TRANSFER_REFUSE: self.recv_file_transfer_refuse,
        }
        for message_type, func in handlers.items():
            self.add_handler(message_type, func)
        self.static_input_mapping = {
            'exit network': self.send_exit_network,

            'list connected peer': self.list_connected_peer,

            'yes': self.accept_request,
            'no': self.refuse_request,

            'help': self.input_prompt,

            'exit': self.system_exit,
        }
        self.dynamic_input_mapping = {
            'request': self.input_request,
            'chat message': self.input_chat_message,
            'disconnect': self.input_disconnect,
            'sendfile': self.input_sendfile,
        }
        self.agree = None
        self.message_format = '{peername}: {message}'
        self.input_prompt_format = '    {cmd:<35} {prompt}'
        self.file_data = {}

    def file_transfer(self, msgdata):
        peername = msgdata['peername']
        filename = msgdata['filename']
        filenum = int(msgdata['filenum'])
        curnum = int(msgdata['curnum'])
        filedata = msgdata['filedata']

        key = peername + '_' + filename
        if self.file_data.get(key) is None:
            self.file_data[key] = [None] * filenum
        self.file_data[key][curnum] = filedata
        #print(self.file_data.get(key) is None)

        flag = True
        for i in self.file_data[key]:
            if i is None:
                flag = False
                break
        if flag is True:
            print(self.file_data[key])
            file_name=filename.split('\\')[-1]
            file_name_sub_head=file_name.split('.')[0]
            file_name_sub_tail=file_name.split('.')[1]
            download_path = get_download_path()
            path=download_path+'\\'+file_name
            check_path=path
            i=1
            while os.path.exists(check_path):
                repalce=file_name_sub_head+str(i)+'.'+file_name_sub_tail
                check_path=download_path+'\\'+repalce
                i+=1
            path=check_path
            print(path)
            with open(path, 'w', encoding='utf-8') as f:
                for i in self.file_data[key]:
                    f.write(i)

    def recv_file_transfer_request(self, msgdata):
        pass

    def recv_file_transfer_accept(self, msgdata):
        pass

    def recv_file_transfer_refuse(self, msgdata):
        pass

    def disconnect(self, msgdata):
        """ Processing received messages from peer:
            Disconnect from the peer. """
        peername = msgdata['peername']
        if peername in self.peerlist:
            print('Disconnected from {}'.format(peername))
            del self.peerlist[peername]

    def recv_message(self, msgdata):
        """ Processing received chat message from peer."""
        peername = msgdata['peername']
        if peername in self.peerlist:
            print(self.message_format.format(peername=peername, message=msgdata['message']))

    def chat_accept(self, msgdata):
        """ Processing received accept chat request message from peer.
            Add the peer to collection of connected peers. """
        peername = msgdata['peername']
        host = msgdata['host']
        port = msgdata['port']
        print('chat accept: {} --- {}:{}'.format(peername, host, port))
        self.peerlist[peername] = (host, port)

    def chat_refuse(self, msgdata):
        """ Processing received refuse chat request message from peer. """
        print('CHAT REFUSE!')

    def request(self, msgdata):
        """ Processing received chat request message from peer. """
        peername = msgdata['peername']
        host, port = msgdata['host'], msgdata['port']
        print('request: {} --- {}:{}'.format(peername, host, port))
        print('Please enter "yes" or "no":')
        while self.agree is None:
            time.sleep(0.1)
        if self.agree is True:
            self.agree = None
            data = {
                'peername': self.name,
                'host': self.serverhost,
                'port': self.serverport
            }
            print('You accept a request, chat start')
            self.socket_send((host, port), msgtype=CHAT_ACCEPT, msgdata=data)
            self.peerlist[peername] = (host, port)
        elif self.agree is False:
            print('You refuse a request')
            self.agree = None
            self.socket_send((host, port), msgtype=CHAT_REFUSE, msgdata={})



    def searchUser(self, username):
        message = "SEARCH " + username
        s=socket.socket(socket.AF_INET,socket. SOCK_STREAM)
        s.connect((self.server_info[0], self.server_info[1]))
        s.send(message.encode())
        response = s.recv(1024).decode().split()
        if response[0] == "search-success":
            return response[1]
        elif response[0] == "search-user-not-online":
            return 0
        elif response[0] == "search-user-not-found":
            return None

    def GetPeerInFo(self,username):
        searchStatus=self.searchUser(username)
        if searchStatus is None or searchStatus is 0:
            return "NotONline"
        else:
            searchStatus = searchStatus.split(":")
            return (searchStatus[0],int(searchStatus[1]))


    def send_request(self, peername):
        """ Send a chat request to peer. """
        if peername not in self.peerlist:
            # try:
            #     server_info = self.connectable_peer[peername]
            # except KeyError:
            #     print('This peer ({}) is not registered.'.format(peername))
            server_info=self.GetPeerInFo(peername)
            if server_info=='NotONline':
                print("User are not online or not exist")
                return
            else:
                data = {
                    'peername': self.name,
                    'host': self.serverhost,
                    'port': self.serverport
                }
                self.socket_send(server_info, msgtype=REQUEST, msgdata=data)
        else:
            print('You have already connected to {}.'.format(peername))

    def send_chat_message(self, peername, message):
        """ Send a chat message to peer. """
        if self.GetPeerInFo(peername)=='NotONline':
            print('Peer does not exist or online')
            if peername in self.peerlist:
                del self.peerlist[peername]
            return
        try:
            peer_info = self.peerlist[peername]
        except KeyError:
            print('chat message: Peer does not exist or online.')
        else:
            data = {
                'peername': self.name,
                'message': message
            }
            self.socket_send(peer_info, msgtype=CHAT_MESSAGE, msgdata=data)
    def send_file(self, peername, filename):
        if self.GetPeerInFo(peername)=='NotONline':
            print('Peer does not exist or online')
            if peername in self.peerlist:
                del self.peerlist[peername]
            return
        try:
            peer_info = self.peerlist[peername]
        except KeyError:
            print("send file: Peer does not exist or online.")
        else:
            read_per = 128
            tmp_text = []
            with open(filename, 'rt', encoding='utf-8') as f:
                while True:
                    text_data = f.read(read_per)
                    if not text_data:
                        break
                    tmp_text.append(text_data)
            tran_num = len(tmp_text)
            for index, item in enumerate(tmp_text):
                data = {
                    'peername': self.name,
                    'filename': filename,
                    'filenum': tran_num,
                    'curnum': index,
                    'filedata': item
                }
                self.socket_send(peer_info, msgtype=FILE_TRANSFER, msgdata=data)

    def send_disconnect(self, peername):
        """ Send a disconnect request to peer. """
        if self.GetPeerInFo(peername)=='NotONline':
            print('Peer does not exist or online')
            if peername in self.peerlist:
                del self.peerlist[peername]
            return
        try:
            peer_info = self.peerlist[peername]
        except KeyError:
            print('disconnect: Peer does not online anymore or something has happened.')
        else:
            data = {'peername': self.name}
            self.socket_send(peer_info, msgtype=DISCONNECT, msgdata=data)

    def list_connected_peer(self):
        """ Output all connected peers information. """
        HavePeer=False
        for peername, peer_info in self.peerlist.items():
            if self.GetPeerInFo(peername) is not 'NotONline':
                HavePeer=True
                print('peername: ' + peername + '---' + peer_info[0] + ':' + str(peer_info[1]))
        if HavePeer==False:
            print('You dont have any connected peer')

    def classifier(self, msg):
        """ Scheduling methods. """
        type_ = msg['msgtype']
        data_ = msg['msgdata']
        self.handlers[type_](data_)

    def recv(self):
        """ TCP socket that receives information. """
        while True:
            conn, addr = self.socket.accept()
            buf = conn.recv(2048)
            msg = json.loads(buf.decode('utf-8'))
            self.classifier(msg)

    def input_request(self, cmd):
        try:
            peername = cmd.split(' ', maxsplit=2)[-1]
        except IndexError:
            print('chat request: Arguments Error.')
        else:
            self.send_request(peername)

    def input_chat_message(self, cmd):
        try:
            peername, message = cmd.split(' ', maxsplit=3)[-2:]
        except IndexError:
            print('chat message: Arguments Error.')
        else:
            self.send_chat_message(peername, message)

    def input_disconnect(self, cmd):
        try:
            peername = cmd.split(' ', maxsplit=1)[-1]
        except IndexError:
            print('disconnect: Arguments Error.')
        else:
            self.send_disconnect(peername)
            if peername in self.peerlist:
                del self.peerlist[peername]

    def input_sendfile(self, cmd):
        try:
            peername, filename = cmd.split(' ', maxsplit=3)[-2:]
        except IndexError:
            print('Error: sendfile.')
        else:
            self.send_file(peername, filename)

    def accept_request(self):
        self.agree = True

    def refuse_request(self):
        self.agree = False

    def send_exit_network(self):
        """ Send a request to server to quit P2P network. """
        data = {'peername': self.name}
        self.socket_send(self.server_info, msgtype=EXIT_NETWORK, msgdata=data)

    def system_exit(self):
        for peername in self.peerlist:
            try:
                self.send_disconnect(peername)
            except ConnectionRefusedError:
                pass
            except:
                pass
        try:
            self.send_exit_network()
        except ConnectionRefusedError:
            pass
        except:
            pass
        sys.exit()

    def input_prompt(self):
        print('You have recieve a chat request, here is some chatting service:')
        print(self.input_prompt_format.format(cmd='listpeer', prompt='xem cac peer dang ket noi'))
        print(self.input_prompt_format.format(cmd='exit network', prompt='thoat khoi net'))
        print(self.input_prompt_format.format(cmd='request [peername]', prompt='yeu cau tro chuyen'))
        print(self.input_prompt_format.format(cmd='chat message [peername] [message]', prompt='gui tin nhan'))
        print(self.input_prompt_format.format(cmd='disconnect [peername]', prompt='ngat ket noi den peer'))
        print(self.input_prompt_format.format(cmd='exit', prompt='thoat khoi chuong trinh'))

    def run(self):
        atexit.register(self.system_exit)
        self.thread = threading.Thread(target=self.recv)
        self.thread.setDaemon(True)
        self.thread.start()




