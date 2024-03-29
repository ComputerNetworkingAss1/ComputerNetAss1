import json
import socket
from abc import abstractmethod


class Peer(object):
    """ Implements the core functionality that might be used by a peer in a P2P networks. """

    def __init__(self, serverhost='localhost', serverport=13999, listen_num=100):
        self.serverhost, self.serverport = serverhost, int(serverport)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(('', int(serverport)))
        self.socket.listen(listen_num)
        self.peerlist = {}
        self.handlers = {}

    def add_handler(self, message_type, func):
        self.handlers[message_type] = func

    @abstractmethod
    def classifier(self, msg):
        pass

    def recv(self):
        while True:
            conn, addr = self.socket.accept()
            buf = conn.recv(2048)
            msg = json.loads(buf.decode('utf-8'))
            self.classifier(msg)

    @abstractmethod
    def run(self):
        pass

    @staticmethod
    def socket_send(address, msgtype, msgdata):
        """ Send JSON serialized data over a new TCP connection. """
        msg = {'msgtype': msgtype, 'msgdata': msgdata}
        msg = json.dumps(msg).encode('utf-8')
        # import pdb; pdb.set_trace()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            #print(address)
            s.connect(address)
        except ConnectionRefusedError:
            print('ConnectionRefusedError')
            raise
        else:
            s.send(msg)
        finally:
            s.close()



class Symbol(object):
    @abstractmethod
    def send(self):
        pass

    @abstractmethod
    def recv(self):
        pass