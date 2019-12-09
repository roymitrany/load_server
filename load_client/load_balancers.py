'''
Load balancer classes.
We will define an abstract class, and then some types of LB such as random, round robin, optimal etc.
Mark's LB algorithm will be added right here.
'''
from abc import ABC, abstractmethod
import random

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
    def pick_server(self)->Server:
        min_length:int = 9999
        curr_srv: Server
        for server in self.srv_manager.available_srv_list:
            num = server.current_running_tasks
            print ("Queue length for server %s is %d" %(server.srv_port, num))
            if num<min_length:
                # Set the current server as the favorite pick
                min_length = num
                curr_srv = server
                print ("Picking server %d with %d tasks" % (server.srv_port, num))
        return curr_srv

class BellmanLB(BasicLB):
    def __init__(self, mgr, pie_data_parser):
        super ().__init__ (mgr)
        self.data_parser:PieDataParser = pie_data_parser

    def pick_server(self)->Server:
        queue_state_index = get_queue_state_index (self.srv_manager)
        srv_index = self.data_parser.load_balance_policy_list[queue_state_index]

        # If we need to reject, let's do it now
        if srv_index == -1:
            print ("index is ", queue_state_index, " REJECTING BY POLICY")
            return None
        server:Server =  self.srv_manager.full_srv_list[srv_index]

        # Check if the server is available
        if server.running_state!= SERVER_STATE_AVAILABLE:
            print ("index is ",  queue_state_index, " REJECTING BY SERVER STATE")
            return None

        return server