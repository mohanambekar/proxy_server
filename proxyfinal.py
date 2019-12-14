#!/usr/bin/pytho
import os,sys,thread,socket,hashlib,time,threading
import os.path
from os import path
from urlparse import urlparse

QUEUE = 100     #pending connections      
SIZE = 5000  #max no of bytes that can be received
oldTime = 100


locks = {}
#created empty dictionary for locks
#we will create lock for each file and store it in dictionary with keyname as filename

#denying access to some website
blockedlist = []
string = "YTpi"

fileCount = {}

def main():
    flag = 0
    shost = ''                     #localhost
    sport = 8080    #first argument
    cache_dir = os.getcwd()
    cache_dir = os.path.join(cache_dir, "cache")
    if not (os.path.exists(cache_dir)):
        os.mkdir("cache")

    #deleting files which older then some time
    fileCountpath = os.getcwd()
    fileCountpath = os.path.join(fileCountpath, "FileCount.txt")
    if os.path.exists(fileCountpath):
        fileCount = loadFileCount()
        print fileCount
        deleteOldFiles()
        print fileCount
    
    
    try:
        #creating a socket for client to proxy and vice-versa
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((shost,sport))
        sock.listen(QUEUE)

    except socket.error, (value, message):
        
        if sock:
           sock.close()
        #print "Could not open socket:", message
        sys.exit(1)
    
    #accepting the connection and creating new thread
    while 1:
        flag += 1
        conn, cadd = sock.accept()
        #if flag == 1:
        #   conn.send("HTTP/1.0 407 Proxy Authentication Required\r\n")
        #   conn.send("Proxy-Authenticate: Basic\r\n")
        #   m = conn.recv(SIZE)
        #   print m
        thread.start_new_thread(function, (conn, cadd, flag))
    
    sock.close()

def function(conn, cadd, flag): 
        '''req1 = conn.recv(SIZE)
        if flag == 1:
            conn.send("HTTP/1.0 407 Proxy Authentication Required\r\n")
            conn.send("Proxy-Authenticate: Basic\r\n")'''
        req = conn.recv(SIZE)
        print req
        req_list = req.split('\r\n\r\n')
        length1 = len(req_list)
        #auth = req_list[length1 - 1].split(" ")[2]

        if True:
            if len(req_list) < 2:
                conn.close()
                return
            temp1 = open("tmp", "w") 
            temp1.write(req)
            temp1.close()
            line = req.split('\r\n')[0]
            #method such as GET,POST
            method = line.split(" ")[0]
            url = line.split(" ")[1]
            filename = line.split()[1].partition("/")[2]
            #print filename
            pos = filename.find("/")
    

            http_pos = url.find("://")         # find pos of ://

            if (http_pos==-1):
                temp = url
            else:
                temp = url[(http_pos+3):]       # get the rest of url

            port_pos = temp.find(":")          # find the port pos (if any)

            # find end of web server
            webserver_pos = temp.find("/")
            if webserver_pos == -1:
                webserver_pos = len(temp)

            webserver = ""
            port = -1

            if (port_pos==-1 or webserver_pos < port_pos):
                port = 80
                webserver = temp[:webserver_pos]
            #print webserver
            else:
                port = int((temp[(port_pos+1):])[:webserver_pos-port_pos-1])
                webserver = temp[:port_pos]

            isblocked = False
            #check if webserver is in the blockedlist
            if webserver in blockedlist:
                isblocked = True

            if isblocked:
                conn.send("HTTP/1.1 200 OK\r\n")
                conn.send("Content-Lenght: 11\r\n")
                conn.send("\r\n")
                conn.send("access denied!!!\r\n")
                conn.send("\r\n\r\n")
                return 

            if method == "GET":
                get_req(conn,webserver,req,filename,port)

            elif method == "POST":
                pos_req(conn,webserver,req)         

#function for GET method

def get_req(conn,webserver,req,filename,port):
    k1 = " "    
    li = ["\r\n"]
    curr_dir = os.getcwd()
    print"In egt request"
    #converting the file name using hashlib to hex
    new_filename = hashlib.sha224(filename).hexdigest()
    path1 = os.path.join(curr_dir,"cache/",new_filename)


    try:
        #check if file exists in cache
        if os.path.exists(path1):
            #the request exists in cache directory
            #first aquire the lock here
            if path1 not in locks:
                #create a lock from that file
                lock = threading.Lock()
                locks[path1] = lock
                lock.acquire()
            else:
                lock = locks[path1]
                print"hello tilak123"
                lock.acquire()

            #increment fileCount dictionary value
            if new_filename in fileCount:
                fileCount[new_filename] = int(fileCount[new_filename]) + 1
            else:
                fileCount[new_filename] = 1
            
            f = open(path1, "r")
            content_list = f.readlines()
            f.close()

            #release the lock here
            if path1 in locks:
                lock = locks[path1]
                lock.release()
            
            content_data = req
            content_list1 = content_data.split('\r\n')
            content_list1.pop()
            content_list1.pop()
            for x in content_list:
                if "Last-Modified" in x:
                    content_list1.append(x)

            length = len(content_list1)
            ii = 0
            while ii < length:
                content_list1[ii] = content_list1[ii] + "\r\n"
                ii = ii + 1

            content_data = ""
            for ele in content_list1:
                content_data = content_data + ele
            
            if "Last-Modified" in content_data:
                content_data = content_data.replace("Last-Modified", "If-Modified-Since")

            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            webserver = socket.gethostbyname(webserver)
            s.connect((webserver, port))
            s.send(content_data)

            while 1:
                data1 = s.recv(SIZE)
                line1 = data1.split('\r\n')[0]
                l = line1.split(' ')
                if len(l) > 1:
                    k1 = l[1]
                   
                #if modification has occurred the new response is sent to the client
                if k1 == "200":
                    conn.send(data1)
                    os.remove(path1)
                    f = open(path1,"wb")
                    f.write(data1)
                    conn.send(data1)

                #if not modified then send from cache
                elif k1 == "304":
                    print "sending form cache"

                    #aquire the lock
                    if path1 not in locks:
                        lock = threading.Lock()
                        locks[path1] = lock
                        lock.acquire()
                    else:
                        lock = locks[path1]
                        lock.acquire()
                    
                    t = open(path1, "rb")
                    m = t.read()
                    t.close()
                    #release the lock
                    if path1 in locks:
                        lock = locks[path1]
                        lock.release()
                    conn.send(m)

                if len(data1) < 0:
                    return                  
                
        #if request made for first time
        else:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            webserver = socket.gethostbyname(webserver)
            s.connect((webserver, port))
            s.send(req)
            print"first time"
            # send request to webserver
            con = True
            while con:
              data = s.recv(SIZE)
              if (len(data) > 0):
                 f = open(path1,"a")
                 f.write(data)
                 #print data
                 #create a key in dictionary
                 if new_filename in fileCount:
                     fileCount[new_filename] = int(fileCount[new_filename]) + 1
                 else:
                     fileCount[new_filename] = 1
                 f.close()
                 conn.send(data)
              else:
                 break
        
        s.close()
        conn.close()

        
    except socket.error, (value, message):
            if s:
                s.close()
            if conn:
                conn.close()
            #print "Runtime Error:", message
            sys.exit(1)
    saveFileCount()

#function for post method

def pos_req(conn,webserver, req):
    try:
        post_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        post_socket.connect((webserver,8000))
        post_socket.send(req)

        while 1:
            reply_msg = post_socket.recv(SIZE)
            if(len(reply_msg)):
                conn.send(reply_msg)
            else:
                break
        post_socket.close()
        conn.close()
        return

    except socket.error, (value, message):
        if(post_socket):
            post_socket.close()
        if(conn):
            conn.close()
        #print "Runtime Error:", message
        sys.exit(1)

#deleting files after some time

def deleteOldFiles():
    print"filecount"
    print fileCount
    curr_dir = os.getcwd()
    cache_path = os.path.join(curr_dir,"cache")

    curr_time = time.time()
    for cache_file in os.listdir(cache_path):
        filename = cache_file
        print filename
        cache_file = os.path.join(cache_path, cache_file)
        if os.stat(cache_file).st_mtime < curr_time - oldTime:
            print "I m here"
            if os.path.isfile(cache_file):
                print int(fileCount[filename])
                if(int(fileCount[filename]) < 5):
                    print "Deleted"
                    os.remove(cache_file)
                    fileCount.pop(filename, None)
                else:
                    fileCount[filename] = 0
    
    saveFileCount()    


def loadFileCount():
    f = open('FileCount.txt', 'r')
    data = f.read()
    print data
    data = data.splitlines()
    print data
    for item in data:
        if ':' in item:
            key, value = item.split(':', 1)
            fileCount[key] = int(value)
    f.close()
    print fileCount
    return fileCount
    
def saveFileCount():
    #saving dictionary in text file
    f = open('FileCount.txt', 'w')
    for key, value in fileCount.items():
        f.write('%s:%s\n' % (key, value))
    f.close()
if __name__ == '__main__':
    main()





