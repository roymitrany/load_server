import subprocess
import threading
from time import sleep, time
import re
from typing import List

from load_client.global_vars import full_srv_ip_addr_list, full_srv_port_list, server_startup_time, task_limit
from load_client.global_vars import get_num_of_completed_tasks, inc_num_of_completed_tasks

SERVER_STATE_DOWN = 0
SERVER_STATE_INIT = 1
SERVER_STATE_DRAIN = 2
SERVER_STATE_AVAILABLE = 3


def activate_server(srv_mgr, srv_obj):
    '''
    A separate thread that waits for the server to be available and then updates the available servers list
    :param srv_mgr: servers manager singleton object
    :param srv_obj: the current server object to activate
    :return:
    '''
    sleep(server_startup_time)
    srv_mgr.available_srv_list.append(srv_obj)
    srv_obj.running_state = SERVER_STATE_AVAILABLE

def deactivate_server(srv_mgr, srv_obj):
    '''
    A separate thread that waits for the server to drain and then updates the active servers list
    Maybe later we will actually stop the server in AWS
    :param srv_mgr: servers manager singleton object
    :param srv_obj: the current server object to deactivate
    :return:
    '''
    while True:
        sleep(1)
        if srv_obj.current_running_tasks ==0: # No more running tasks, we can take the server out of active list
            break
    srv_mgr.active_srv_list.remove(srv_obj)
    srv_obj.current_running_tasks=SERVER_STATE_DOWN

def process_responses(server, srv_mgr):
    '''
    The function runs on a separate thread, a thread for each server
    :param srv_mgr: The server manager
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
                        print (output.strip ())
                        duration_match = re.search(r'duration\": \"([\d]+)', output)
                        duration = int(duration_match.group(1))
                        server.response_duration_list.append(duration)
                        inc_num_of_completed_tasks()
                        server.process_list.remove(process)
                        server.current_running_tasks -= 1
                        srv_mgr.scale_in_event.set() # Notify the world that scale in should be triggered. Should be caught by AS
                    if output.find ("current_tasks") > -1: # For statistics only. We will not increment counters here
                        tasks_queue_match = re.search(r'current_tasks\": \"([\d]+)', output)
                        tasks_queue = int(tasks_queue_match.group(1))
                        server.response_tasks_queue_list.append(tasks_queue)



        if get_num_of_completed_tasks() >=task_limit:
            print ("Overall tasks completed: " + str (get_num_of_completed_tasks()))
            break
        #print ("Server " + str(server.srv_index) + ": Overall tasks completed: " + str (get_num_of_completed_tasks()))
        sleep(1)

class Server:
    response_duration_list: List[int]

    def __init__(self, index:int, ip_addr:str, port:int):
        self.srv_index = index
        self.srv_ip = ip_addr
        self.srv_port = port
        self.process_list: List[subprocess.Popen] = []
        self.response_thread:threading.Thread = threading.Thread()
        self.running_state:int = SERVER_STATE_DOWN

        # All the statistics below refer to the particular server
        self.current_running_tasks = 0 # The number of requests that their response has not arrived yet (measured by client)
        self.response_duration_list: List[int] = [] # The time measured by server to complete the task, including time waiting in queue
        self.response_tasks_queue_list: List[int] = [] # The number of tasks that the server documented (including current task)
        self.request_tasks_queue_list: List[int] = [] # The number of tasks that the client documented when a response arrived (exluding current task)




    def activate(self):
        self.running_state = SERVER_STATE_INIT
        #Maybe later will actually start a server in AWS

    def deactivate(self):
        self.running_state = SERVER_STATE_DRAIN
        # In any case we will not stop the server here, because it has to drain first
        pass

    def start_req(self, load):
        process: subprocess.Popen = subprocess.Popen (["python", "http_client.py", self.srv_ip, str (self.srv_port), str (load)],
                                                      stdout=subprocess.PIPE,
                                                      stderr=subprocess.PIPE)
        self.current_running_tasks += 1
        self.process_list.append (process)
        self.request_tasks_queue_list.append (self.current_running_tasks)


class ServerManager:
    cool_down_period = 5.0
    total_scale_out_counter = 0
    total_scale_in_counter = 0

    def __init__(self, num_of_servers:int):
        self.full_srv_list: List[Server] = [] #TODO: Change list to map, with key = ip_port
        self.active_srv_list: List[Server] = [] # Servers that are active, including non available and draining
        self.available_srv_list: List[Server] = [] # Available servers only. LB should look at this list
        self.last_scale_change = time()
        self.scale_in_event = threading.Event ()
        self.scale_out_event = threading.Event ()


        for i in range(len(full_srv_ip_addr_list)):

            # Create a server object
            srv:Server = Server(i, full_srv_ip_addr_list[i], full_srv_port_list[i])
            self.full_srv_list.append(srv)

         # Turn on required number of servers
        for i in range(num_of_servers):
            self.activate_server(i)

        for server in self.full_srv_list:
            # first start the thread that receives the responses
            server.response_thread = threading.Thread (target=process_responses, args=(server,self,))
            server.response_thread.start ()

        print("waiting for initial servers to start") # TODO: export to a method that will actually wait for the servers
        sleep(server_startup_time)


    def get_server_obj(self, srv_index):
        return self.full_srv_list[srv_index]

    def activate_server(self, srv_index):
        curr_server:Server = self.get_server_obj(srv_index)
        self.active_srv_list.append (curr_server)
        curr_server.activate()
        x = threading.Thread (target=activate_server, args=(self, curr_server))
        x.start ()

    def deactivate_server(self, srv_index):
        curr_server:Server = self.get_server_obj(srv_index)
        self.available_srv_list.remove(curr_server)
        curr_server.deactivate()
        x = threading.Thread (target=deactivate_server, args=(self, curr_server))
        x.start ()

    def find_inactive_server (self) -> int: #TODO: return server object instead of server index
        """

        :return: The index in full server list of a server that is down
        If all servers are active, return -1
        """
        inactive_server = -1
        count = 0
        for server in self.full_srv_list:
            if server.running_state == SERVER_STATE_DOWN:
                inactive_server =  count
                return inactive_server
            count += 1
        return inactive_server

    def scale_out(self):

        """# If to little time passed since last change, do nothing
        if time() - self.cool_down_period < self.last_scale_change:
            return
        self.last_scale_change = time()"""
        # Look for an available server and activate it. Available server is in full list but not in active list.
        # We can pick the first one we find, it doesn't matter
        server_index = self.find_inactive_server ()
        if server_index < 0:  # No available servers, nothing to do
            return

        # Activate the available server
        print ("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++ SCALE OUTTTTTTTTTTTTTT")
        self.total_scale_out_counter += 1 # increment the counter only when we are sure that a new server will start
        self.activate_server (server_index) # TODO: change from index to server object

    def scale_in(self, server_index=-1):

        # If number of active servers is smaller than the number of available servers, probably we already stopped
        # a server, so do not stop another one
        if len(self.active_srv_list)<len(self.available_srv_list):
            return

        # If to little time passed since last change, do nothing
        if time() - self.cool_down_period < self.last_scale_change:
            return
        self.last_scale_change = time()

        # Do not delete the last server
        #if len (self.available_srv_list) < 2:
        #    return

        if server_index < 0:
            # Server index not specified. Remove the one with fewest tasks
            shortest_queue = 9999
            for server in self.active_srv_list:
                if server.current_running_tasks < shortest_queue:
                    server_index = server.srv_index

        # Deactivate the specific server (if not yet deactivated)
        if self.full_srv_list[server_index].running_state == SERVER_STATE_AVAILABLE:
            self.deactivate_server (server_index)
            # increment the counter only when we are sure that we are terminating the server
            print ("--------------------------------------------------------- SCALE INNNNNNNNNNNNNNNN")
            self.total_scale_in_counter += 1




