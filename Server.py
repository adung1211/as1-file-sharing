import socket
import threading
import json

class Server:
    def __init__(self):
        self.clients = {}
        self.host_addr = {}
        self.lock = threading.Lock()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('127.0.0.1', 8080))
        self.server_socket.listen(5)
    
    def fetch(self, client_socket, fname):
        source = []
        for hostname in self.clients:
            if fname in self.clients[hostname]:
                source.append("Hostname: " + hostname + ", Address: " + str(self.host_addr[hostname][0]) + ", Port: " + str(self.host_addr[hostname][1]))
        client_socket.sendall(json.dumps(source).encode())
        #client_socket.send(b"<END>")
    
    def publish(self,client_socket, hostname, fname):
        self.clients[hostname].append(fname)
        print("Success publish " + fname + " from {}".format(hostname))
        client_socket.send(b"OK")
        
    def handle_client(self, client_socket, client_addr):
        hostname = self.login(client_socket, client_addr)
        try:
            while True:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                type, *args = data.split()
                if type == 'publish':
                    with self.lock:
                        self.publish(client_socket, hostname, args[0])
                elif type == 'fetch':
                    with self.lock:
                        self.fetch(client_socket, args[0])
                elif type == 'quit':
                    break
        except ConnectionResetError:
                print("Disconnected to {}".format(hostname))
    
    def discover(self, hostname):
        for hostname_i in self.clients:
            if hostname_i == hostname:
                # Print the list of published files.
                print("Files published by {}:".format(hostname))
                for fname in self.clients[hostname_i]:
                    print(fname)
                print("Success discover")
                return
        #Can not find that hostname
        print("Error: Not existed that hostname")
    
    def ping(self, hostname):
        if hostname in self.clients:
            client_addr = self.host_addr[hostname]
            self.temp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #self.temp_socket.settimeout(3)
            try:
                self.temp_socket.connect(client_addr)
                self.temp_socket.send(b"PING")
            except ConnectionRefusedError:
                    print("{} is not active".format(hostname))
                    self.temp_socket.close()
                    return False
            else:
                print("{} is active".format(hostname))
                self.temp_socket.close()
                return True
        else:
            print(hostname + " not exist !")
            self.temp_socket.close()
        return False
    
    def start_shell(self):
        while True:
            command = input()
            type, *arg = command.split()
            if type == 'discover':
                self.discover(arg[0])
            elif type == 'ping':
                self.ping(arg[0])

    def login(self, client_socket, client_addr):
        while True:
            hostname = client_socket.recv(1024).decode()
            if not hostname in self.clients:
                self.clients[hostname] = []
                self.host_addr[hostname] = client_addr
                client_socket.send(b"REG")
            else:
                if  self.ping(hostname) == True:
                    client_socket.send(b"FAIL")
                    continue
                else:
                    self.host_addr[hostname] = client_addr
                    client_socket.send(b"LOG")
            return hostname
    
    def start(self):
        print("Server listening for incoming connections...")
        threading.Thread(target=self.start_shell, args=()).start()
        while True:
            client_socket, client_addr = self.server_socket.accept()    
            print("Connected to {}".format(client_addr))
            threading.Thread(target=self.handle_client, args=(client_socket, client_addr)).start()

if __name__ == "__main__":
    server = Server()
    server.start()
