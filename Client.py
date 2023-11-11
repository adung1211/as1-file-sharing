import socket
import os
import threading
import tqdm
import json


class Client:
    def __init__(self, server_address):
        self.server_address = server_address
        self.lock = threading.Lock()
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(self.server_address)

        self.p2p_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.p2p_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.p2p_socket.bind((self.client_socket.getsockname()[0], self.client_socket.getsockname()[1]))
        self.p2p_socket.listen(5)

    def fetch(self, filename):
        data = self.client_socket.recv(1024)
        source = json.loads(data.decode())
        
        if (len(source) == 0):
            print("None hostname published that file you requested")
            return
        print("List of hostname address that published the file:")
        for source_i in source:
            print(source_i)
        print("Choose the address and port of the hostname you want to fetch form")
        
        while True:
            try:
                source_addr = input(">Address: ")
                source_port = input(">Port: ")
                source_port = int(source_port)
                down_soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                down_soc.connect((source_addr, source_port))
                self.p2p_receive(filename, down_soc)
                return
            except ConnectionRefusedError:
                print("Connection fail, please try another hostname")
                continue
    
    def publish(self, fname):
        data = self.client_socket.recv(1024)
        if data == b"OK":
            print("Publish success file {}".format(fname)) 

    def send_command(self):
        print("To start, type 'publish fname' or 'fetch fname' or 'quit'")
        while True:
            command = input("> ")

            type, *arg = command.split()
            if type == 'fetch':
                self.client_socket.send(command.encode('utf-8'))
                self.fetch(arg[0])
            elif type == 'publish':
                self.client_socket.send(command.encode('utf-8'))
                self.publish(arg[0])
            elif type == 'quit':
                os._exit(0)

    def p2p_receive(self, filename, down_soc):
        msg = "Request " + str(filename)
        down_soc.send(str(msg).encode()) 
        
        #file_down = down_soc.recv(1024).decode()
        file_down = "received_" + filename
        print("Downloading {}...".format(filename))
        file_size = down_soc.recv(1024).decode()
        #print("{} bytes".format(file_size))

        file = open(file_down, "wb")
        file_bytes = b""
        done = False
        progress =tqdm.tqdm(unit="B", unit_scale=True, unit_divisor=1000, total=int(file_size))

        while not done:
            data = down_soc.recv(128 * 1024)
            if file_bytes[-5:] == b"<END>":
                done = True
            else:
                file_bytes += data
            progress.update(128 * 1024)
        
        file.write(file_bytes)
        file.close()
        print("\nDownload {} completed".format(filename))

    def p2p_transfer(self, send_socket, filename):
        file = open(filename, "rb")
        file_size = os.path.getsize(filename)

        #send_socket.send(str("received_" + filename).encode())
        send_socket.send(str(file_size).encode())

        data = file.read()
        send_socket.sendall(data)
        send_socket.send(b"<END>")
        file.close()
        send_socket.close() #!!!!!!!!!!!!!!!!!!!

    def p2p_handle(self, send_socket, send_addr):
        #print("P2P connected to {}".format(send_addr))
        data = send_socket.recv(1024).decode('utf-8')
        type, *args = data.split()
        if type == 'Request':
            self.p2p_transfer(send_socket, args[0])
        if type == 'PING':
            return

    def p2p_connection(self):
        while True:
            send_socket, send_addr = self.p2p_socket.accept()
            #print("Connected p2p to {}".format(send_addr))
            threading.Thread(target=self.p2p_handle, args=(send_socket, send_addr)).start()

    def start(self):
        print("Connected to File-sharing server")
        while (True):
            hostname = input(">Input your hostname: ")
            self.client_socket.send(hostname.encode())
            data = self.client_socket.recv(1024)
            if data == b"REG":
                print("Sign in Successfully")
            elif data == b"LOG":
                print("Login in Successfully")
            elif data == b"FAIL":
                print("Hostname is already running, please retry !")
                continue
            break
            
        
        threading.Thread(target=self.p2p_connection, args=()).start()
        #self.p2p_connection()
        self.send_command()

if __name__ == "__main__":
    client = Client(("127.0.0.1", 8080))
    client.start()
    
