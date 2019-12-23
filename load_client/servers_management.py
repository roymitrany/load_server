import subprocess
import threading
from time import sleep, time
import re
from typing import List, Optional

import requests as req

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



def send_http_queue_load_request(server:'Server', load_level=1, timeout=10):
    # print ("generating request....")
    get_path = "/load/queue_load/" + str (load_level)
    url = "http://" + server.srv_ip + ":" + str (server.srv_port) + get_path
    try:
        resp = req.get (url, timeout=timeout)
        output = resp.content.decode ("utf-8")
        if output.find("duration") > -1:
            server.notify_response(output)
        else:
            server.notify_error("bad_response")
    except req.ReadTimeout:
        server.notify_error("timeout")
    except:
        server.notify_error("unknown_error")


class Server:
    response_duration_list: List[int]

    def __init__(self, index:int, sim_mgr, ip_addr:str, port:int):
        self.srv_index = index
        self.sim_mgr = sim_mgr
        self.srv_ip = ip_addr
        self.srv_port = port
        self.running_state:int = SERVER_STATE_DOWN

        # All the statistics below refer to the particular server
        self.current_running_tasks = 0 # The number of requests that their response has not arrived yet (measured by client)
        self.response_duration_list: List[int] = [] # The time measured by server to complete the task, including time waiting in queue
        self.response_tasks_queue_list: List[int] = [] # The number of tasks that the server documented (including current task)


    def activate(self):
        if self.running_state == SERVER_STATE_DOWN:
            self.running_state = SERVER_STATE_INIT
        #Maybe later will actually start a server in AWS

    def deactivate(self):
        if self.running_state == SERVER_STATE_AVAILABLE:
            self.running_state = SERVER_STATE_DRAIN
        # In any case we will not stop the server here, because it has to drain first
        pass

    def start_req(self, load_level)->int:
        try:
            request_thread = threading.Thread (target=send_http_queue_load_request, args=(self, load_level,))
            request_thread.start ()
        except:
            print ("Error: could not start subprocess")
            return 0

        self.current_running_tasks += 1
        return 1

    def notify_error(self, param):
        # timeout occurred, update counters
        print ("INCOMPLETE TASK!!!", param)
        self.current_running_tasks -= 1
        self.sim_mgr.inc_num_of_completed_tasks ()
        self.sim_mgr.inc_num_of_rejections ()


    def notify_response(self, output):
        if output.find ("duration") > -1:
            self.sim_mgr.inc_num_of_completed_tasks ()
            self.sim_mgr.as_obj.trigger_scale_in ()  # Notify the world that scale in should be triggered. Should be caught by AS
            duration_match = re.search (r'duration\": \"([\d]+)', output)
            duration = int (duration_match.group (1))
            self.response_duration_list.append (duration)
        if output.find ("queue_size_enqueue") > -1:  # For statistics only. We will not increment counters here
            tasks_queue_match = re.search (r'queue_size_enqueue\": \"([\d]+)', output)
            tasks_queue = int (tasks_queue_match.group (1))
            self.response_tasks_queue_list.append (tasks_queue)
        if output.find ("queue_size_task_end") > -1:  # For statistics only. We will not increment counters here
            tasks_queue_match = re.search (r'queue_size_task_end\": \"([\d]+)', output)
            current_running_tasks = int (tasks_queue_match.group (1))
            self.current_running_tasks = current_running_tasks


class ServerManager:
    cool_down_period = 5.0
    total_scale_out_counter = 0
    total_scale_in_counter = 0

    def __init__(self, sim_mgr, initial_num_of_servers:int):
        self.sim_mgr = sim_mgr
        self.full_srv_list: List[Server] = []
        self.active_srv_list: List[Server] = [] # Servers that are active, including non available and draining
        self.available_srv_list: List[Server] = [] # Available servers only. LB should look at this list


        for i in range(len(full_srv_ip_addr_list)):

            # Create a server object
            srv:Server = Server(i, self.sim_mgr, full_srv_ip_addr_list[i], full_srv_port_list[i])
            self.full_srv_list.append(srv)

         # Turn on required number of servers
        for server in  self.full_srv_list[0:initial_num_of_servers]:
            self.activate_server(server)

        # wait until at least one server is active
        while len(self.available_srv_list)==0:
            print("No active servers yet...")
            sleep(1)

    def get_server_obj(self, srv_index):
        return self.full_srv_list[srv_index]

    def activate_server(self, server):
        if server in self.active_srv_list:
            return # already active, nothing to do

        self.active_srv_list.append (server)
        server.activate()
        x = threading.Thread (target=activate_server, args=(self, server))
        x.start ()

    def deactivate_server(self, server:Server):
        self.available_srv_list.remove(server)
        server.deactivate()
        x = threading.Thread (target=deactivate_server, args=(self, server))
        x.start ()

    def find_inactive_server (self) -> Optional[Server]:
        """

        :return: A server object that is down
        If all servers are active, return -1
        """
        for server in self.full_srv_list:
            if not server in self.active_srv_list:
                return server
        return None

    def scale_out(self):

        # Look for an available server and activate it. Available server is in full list but not in active list.
        # We can pick the first one we find, it doesn't matter
        server:Server = self.find_inactive_server ()
        if server is None:  # No available servers, nothing to do
            return

        # Activate the available server
        print ("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++ SCALE OUTTTTTTTTTTTTTT   ", server.srv_index)
        self.total_scale_out_counter += 1 # increment the counter only when we are sure that a new server will start
        self.activate_server (server)

    def scale_in(self, server_index=-1):


        if server_index < 0:
            # Server index not specified. Remove the one with fewest tasks
            shortest_queue = 9999
            for server in self.available_srv_list:
                if server.current_running_tasks < shortest_queue:
                    server_index = server.srv_index

        # Deactivate the specific server (if not yet deactivated)
        server = self.full_srv_list[server_index]
        if server.running_state == SERVER_STATE_AVAILABLE:
            self.deactivate_server (server)
            # increment the counter only when we are sure that we are terminating the server
            print ("--------------------------------------------------------- SCALE INNNNNNNNNNNNNNNN  ", server_index)
            self.total_scale_in_counter += 1




