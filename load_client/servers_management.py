import subprocess
import threading
from time import sleep
from abc import ABC, abstractmethod
import re
from typing import List
from load_client.global_vars import  full_servers_list, full_srv_port_list, server_startup_time, task_limit, initial_num_of_servers
from load_client.global_vars import get_num_of_completed_tasks, inc_num_of_completed_tasks
from load_client.global_vars import get_tasks_global_index, inc_tasks_global_index

def activate_server(srv_mgr, srv_obj):
    '''
    A separate thread that waits for the server to be available and then updates the available servers list
    :param srv_mgr: servers manager singleton object
    :param srv_obj: the current server object to activate
    :return:
    '''
    sleep(server_startup_time)
    srv_mgr.available_servers_list.append(srv_obj)

def process_responses(server):
    '''
    The function runs on a separate thread, a thread for each server
    :param server: The server whose response we are dealing with
    :return:
    '''
    while True:
        for process in server.process_list : # TODO: make it flexible, according to tasks_index
            #print (output.strip ())
            return_code = process.poll ()
            if return_code is not None:
                print ('RETURN CODE', return_code)
                # Process has finished, read rest of the output
                for byte_output in process.stdout.readlines ():
                    output = byte_output.decode("utf-8")
                    #print (output.strip ())
                    if output.find("duration") > -1:
                        print (output.strip ()) # TODO: save the duration somewhere
                        duration_match = re.search(r'duration\": \"([\d]+)', output)
                        duration = int(duration_match.group(1))
                        server.response_duration_list.append(duration)
                        inc_num_of_completed_tasks()
                        server.process_list.remove(process)
                        server.current_running_tasks -= 1
                    if output.find ("current_tasks") > -1: # For statistics only. We will not increment counters here
                        tasks_queue_match = re.search(r'current_tasks\": \"([\d]+)', output)
                        tasks_queue = int(tasks_queue_match.group(1))
                        server.response_tasks_queue_list.append(tasks_queue)
                        server.request_tasks_queue_list.append (server.current_running_tasks)


        if get_num_of_completed_tasks() >=task_limit:
            print ("Overall tasks completed: " + str (get_num_of_completed_tasks()))
            break
        sleep(1)

class Server:
    response_duration_list: List[int]

    def __init__(self, ip_addr:str, port:int):
        self.srv_ip = ip_addr
        self.srv_port = port
        self.process_list: List[subprocess.Popen] = []
        self.response_thread:threading.Thread = threading.Thread()

        # All the statistics below refer to the particular server
        self.total_request_counter = 0 # The total number of requests sent by the client to this server
        self.current_running_tasks = 0 # The number of requests that their response has not arrived yet (measured by client)
        self.max_running_tasks = 0 # The largest number of tasks that the server had to deal with (measured by client)
        self.response_duration_list: List[int] = [] # The time measured by server to complete the task, including time waiting in queue
        self.response_tasks_queue_list: List[int] = [] # The number of tasks that the server documented (including current task)
        self.request_tasks_queue_list: List[int] = [] # The number of tasks that the client documented when a response arrived (exluding current task)




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

        for server in self.full_srv_list:
            # first start the thread that receives the responses
            server.response_thread = threading.Thread (target=process_responses, args=(server,))
            server.response_thread.start ()

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
