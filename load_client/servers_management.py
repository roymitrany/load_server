import subprocess
import threading
from time import sleep
from abc import ABC, abstractmethod
import random
from typing import List

full_servers_list = ["127.0.0.1", "127.0.0.1", "127.0.0.1", "127.0.0.1", "127.0.0.1"]
full_srv_port_list = [5000, 5001, 5002, 5003, 5004]
server_startup_time = 5

def activate_server(srv_mgr, srv_obj):
    '''
    A separate thread that waits for the server to be available and then updates the available servers list
    :param srv_mgr: servers manager singleton object
    :param srv_obj: the current server object to activate
    :return:
    '''
    sleep(server_startup_time)
    srv_mgr.available_servers_list.append(srv_obj)

class Server:
    def __init__(self, ip_addr:str, port:int):
        self.srv_ip = ip_addr
        self.srv_port = port
        self.process_list: List[subprocess.Popen] = []
        self.total_request_counter = 0
        self.current_running_tasks = 0
        self.max_running_tasks = 0
        self.process_duration_list: List[int] = []

    def activate(self):
        pass #Maybe later will actually start a server in AWS
    def deactivate(self):
        pass

    def start_req(self, load):
        process: subprocess.Popen = subprocess.Popen (["python", "http_client.py", self.srv_ip, str (self.srv_port), str (load)],
                                                      stdout=subprocess.PIPE,
                                                      stderr=subprocess.PIPE)
        self.current_running_tasks += 1
        self.max_running_tasks = max(self.current_running_tasks, self.max_running_tasks)
        self.total_request_counter += 1
        self.process_list.append (process)


class ServerManager:
    def __init__(self, num_of_servers:int):
        self.full_srv_list: List[Server] = [] #TODO: Change list to map, with key = ip_port
        self.active_srv_list: List[Server] = []
        self.desired_servers_list: List[Server] = []
        self.available_servers_list: List[Server] = []

        for i in range(len(full_servers_list)):

            # Create a server object
            srv:Server = Server(full_servers_list[i], full_srv_port_list[i])
            self.full_srv_list.append(srv)

         # Turn on required number of servers
        for i in range(num_of_servers):
            self.activate_server(i)

        print("waiting for initial servers to start") # TODO: export to a method that will actually wait for the servers
        sleep(5)


    def get_server_obj(self, srv_index):
        return self.full_srv_list[srv_index]

    def activate_server(self, srv_index):
        curr_server:Server = self.get_server_obj(srv_index)
        self.active_srv_list.append(curr_server)
        x = threading.Thread (target=activate_server, args=(self, curr_server))
        x.start ()

    def deactivate_server(self, srv_index):
        curr_server:Server = self.get_server_obj(srv_index)
        self.active_srv_list.remove(curr_server)
        curr_server.deactivate()
