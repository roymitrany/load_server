import subprocess
import threading
from time import sleep, time
import re
from typing import List
from typing import TYPE_CHECKING

from load_client.global_vars import full_srv_ip_addr_list, full_srv_port_list

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
    sleep(srv_mgr.sim_mgr.simulation_params.server_startup_time)
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
    srv_obj.running_state=SERVER_STATE_DOWN


def process_responses(server, sim_mgr):
    '''
    The function runs on a separate thread, a thread for each server
    :param sim_mgr: The simulation manager
    :param server: The server whose response we are dealing with
    :return:
    '''
    #srv_mgr = sim_mgr.srv_mgr
    while True:
        for process in server.process_list : # TODO: make it flexible, according to tasks_index
            #print (output.strip ())
            return_code = process.poll ()
            if return_code is not None:
                # Process has finished, read rest of the output
                for byte_output in process.stdout.readlines ():
                    output = byte_output.decode("utf-8")
                    if output.find("duration") > -1:
                        duration_match = re.search(r'duration\": \"([\d]+)', output)
                        duration = int(duration_match.group(1))
                        server.response_duration_list.append(duration)
                        sim_mgr.inc_num_of_completed_tasks()
                        server.process_list.remove(process)
                        sim_mgr.as_obj.trigger_scale_in() # Notify the world that scale in should be triggered. Should be caught by AS
                    if output.find ("queue_size_enqueue") > -1: # For statistics only. We will not increment counters here
                        tasks_queue_match = re.search(r'queue_size_enqueue\": \"([\d]+)', output)
                        tasks_queue = int(tasks_queue_match.group(1))
                        server.response_tasks_queue_list.append(tasks_queue)
                    if output.find ("queue_size_task_end") > -1: # For statistics only. We will not increment counters here
                        tasks_queue_match = re.search(r'queue_size_task_end\": \"([\d]+)', output)
                        current_running_tasks = int(tasks_queue_match.group(1))
                        server.current_running_tasks = current_running_tasks
                    if (output.find ("Timeoutttt") > -1)or(output.find ("Errorrrr") > -1):
                        # timeout occurred, update counters
                        print("INCOMPLETE TASK!!!", output)
                        server.current_running_tasks -= 1
                        server.process_list.remove (process)
                        sim_mgr.inc_num_of_completed_tasks ()
                        sim_mgr.inc_num_of_rejections ()

        if sim_mgr.get_num_of_completed_tasks() >= sim_mgr.simulation_params.num_of_tasks:
            print ("Overall tasks completed: " + str (sim_mgr.get_num_of_completed_tasks()))
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
        if self.running_state == SERVER_STATE_DOWN:
            self.running_state = SERVER_STATE_INIT
        #Maybe later will actually start a server in AWS

    def deactivate(self):
        if self.running_state == SERVER_STATE_AVAILABLE:
            self.running_state = SERVER_STATE_DRAIN
        # In any case we will not stop the server here, because it has to drain first
        pass

    def start_req(self, load)->int:
        try:
            process: subprocess.Popen = subprocess.Popen (["python", "http_client.py", self.srv_ip, str (self.srv_port), str (load)],
                                                      stdout=subprocess.PIPE,
                                                      stderr=subprocess.PIPE)
            self.process_list.append (process)
            self.request_tasks_queue_list.append (self.current_running_tasks)
        except:
            print ("Error: could not start subprocess")
            return 0

        self.current_running_tasks += 1
        return 1

class ServerManager:
    cool_down_period = 5.0
    total_scale_out_counter = 0
    total_scale_in_counter = 0

    def __init__(self, sim_mgr, num_of_servers:int):
        self.sim_mgr = sim_mgr
        self.full_srv_list: List[Server] = [] #TODO: Change list to map, with key = ip_port
        self.active_srv_list: List[Server] = [] # Servers that are active, including non available and draining
        self.available_srv_list: List[Server] = [] # Available servers only. LB should look at this list


        for i in range(len(full_srv_ip_addr_list)):

            # Create a server object
            srv:Server = Server(i, full_srv_ip_addr_list[i], full_srv_port_list[i])
            self.full_srv_list.append(srv)

         # Turn on required number of servers
        for i in range(num_of_servers):
            self.activate_server(i)

        for server in self.full_srv_list:
            # first start the thread that receives the responses
            server.response_thread = threading.Thread (target=process_responses, args=(server,self.sim_mgr,))
            server.response_thread.start ()

        print("waiting for initial servers to start") # TODO: export to a method that will actually wait for the servers
        sleep(sim_mgr.simulation_params.server_startup_time)


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

        # Look for an available server and activate it. Available server is in full list but not in active list.
        # We can pick the first one we find, it doesn't matter
        server_index = self.find_inactive_server ()
        if server_index < 0:  # No available servers, nothing to do
            return

        # Activate the available server
        print ("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++ SCALE OUTTTTTTTTTTTTTT   ", server_index)
        self.total_scale_out_counter += 1 # increment the counter only when we are sure that a new server will start
        self.activate_server (server_index) # TODO: change from index to server object

    def scale_in(self, server_index=-1):


        if server_index < 0:
            # Server index not specified. Remove the one with fewest tasks
            shortest_queue = 9999
            for server in self.available_srv_list:
                if server.current_running_tasks < shortest_queue:
                    server_index = server.srv_index

        # Deactivate the specific server (if not yet deactivated)
        if self.full_srv_list[server_index].running_state == SERVER_STATE_AVAILABLE:
            self.deactivate_server (server_index)
            # increment the counter only when we are sure that we are terminating the server
            print ("--------------------------------------------------------- SCALE INNNNNNNNNNNNNNNN  ", server_index)
            self.total_scale_in_counter += 1




