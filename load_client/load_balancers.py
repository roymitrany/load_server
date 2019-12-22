'''
Load balancer classes.
We will define an abstract class, and then some types of LB such as random, round robin, optimal etc.
Mark's LB algorithm will be added right here.
'''
from abc import ABC, abstractmethod
import random
from typing import Optional

from load_client.pie_file_data_parser import PieDataParser, get_queue_state_index
from load_client.servers_management import ServerManager, Server, SERVER_STATE_AVAILABLE


class BasicLB(ABC):
    def __init__(self, mgr):
        print ("init basic class!!")
        self.srv_manager:ServerManager = mgr

    @abstractmethod
    def pick_server(self)->Server:
        pass


class RandomLB(BasicLB):
    def pick_server(self)->Server:
        server_index = random.randint(0, len(self.srv_manager.available_srv_list) - 1)
        return self.srv_manager.available_srv_list[server_index]

class RoundRobinLB(BasicLB):
    curr_srv:int=0
    def pick_server(self)->Server:
        self.curr_srv += 1
        if self.curr_srv>=len(self.srv_manager.available_srv_list):
            self.curr_srv=0
        return self.srv_manager.available_srv_list[self.curr_srv]

class JsqLB(BasicLB):
    '''
    Find the shortest queue from all available servers, and return it
    '''
    def pick_server(self)->Optional[Server]:
        min_length:int = 9999
        curr_srv: Optional[Server] = None
        for server in self.srv_manager.available_srv_list:
            num = server.current_running_tasks
            print ("Queue length for server %s is %d" %(server.srv_port, num))
            if num<min_length:
                # Set the current server as the favorite pick
                min_length = num
                curr_srv = server
                print ("Picking server %d with %d tasks" % (server.srv_port, num))
        if curr_srv:
            return curr_srv
        else:
            return None

class BellmanLB(BasicLB):
    def __init__(self, mgr):
        super ().__init__ (mgr)
        self.data_parser:PieDataParser = PieDataParser("pie.txt")

    def print_available_servers(self)->str:
        ret_str = ''
        for server in self.srv_manager.full_srv_list:
            if server.running_state == SERVER_STATE_AVAILABLE:
                ret_str+='1'
            else:
                ret_str+='0'
        return ret_str

    def print_current_running_tasks(self)->str:
        ret_str = ''
        for server in self.srv_manager.full_srv_list:
            ret_str+=str(server.current_running_tasks)
        return ret_str

    def pick_server(self)->Optional[Server]:
        queue_state_index = get_queue_state_index (self.srv_manager)
        srv_index = self.data_parser.load_balance_policy_list[queue_state_index]

        print ("Bellman LB: index is ", queue_state_index, " picked server is: ", srv_index, " current available servers: ",
               self.print_available_servers (), " current running tasks: ", self.print_current_running_tasks ())

        # If we need to reject, let's do it now
        if srv_index == -1:
            print ("index is ", queue_state_index, " REJECTING BY POLICY")
            return None
        server:Server =  self.srv_manager.full_srv_list[srv_index]

        # Check if the server is available
        if server.running_state!= SERVER_STATE_AVAILABLE:
            print("picked server: ", str(srv_index), ". Srever running state: ", str(server.running_state))
            print ("index is ",  queue_state_index, " REJECTING BY SERVER STATE")
            return None

        return server

def create_lb_obj(lb_type, mgr)->BasicLB: #TODO Throw exception for type mismatch
    if lb_type == "random":
        return RandomLB(mgr)
    if lb_type == "round_robin":
        return RoundRobinLB(mgr)
    if lb_type == "jsq":
        return JsqLB(mgr)
    if lb_type == "bellman":
        return BellmanLB(mgr)
