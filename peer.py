from socket import *
import time
hostname=gethostname()
host = gethostbyname(hostname)
s=socket(AF_INET,SOCK_STREAM)
s.connect((gethostname(),15600))
s.send(bytes("JOIN LAM 123455",'utf-8'))
time.sleep(5)



