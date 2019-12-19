'''
Auto scaler classes.
We will define an abstract class, and then some types of auto scaler, such as high and low threshold.
Mark's LB algorithm will be added right here.
'''
from abc import ABC, abstractmethod
from time import time

from load_client.global_vars import max_server_queue_len, as_high_threshold, as_low_threshold
from load_client.pie_file_data_parser import  PieDataParser, get_queue_state_index
from load_client.servers_management import SERVER_STATE_AVAILABLE


class BasicAS(ABC):

    def __init__(self, mgr):
        self.srv_manager = mgr


    @abstractmethod
    def trigger_scale_in(self):
        pass

    @abstractmethod
    def trigger_scale_out(self):
        pass

class DumbAS(BasicAS):

    def trigger_scale_in(self):
        return

    def trigger_scale_out(self):
        return



class ThresholdAS(BasicAS):
    last_scale_change = time ()

    def trigger_scale_in(self):
        self.trigger_scale_in_out()

    def trigger_scale_out(self):
        self.trigger_scale_in_out()

    def trigger_scale_in_out(self):
        # check if we should do some scaling work. The code is pretty much the same for both sides, so we better
        # implement it once and pay the price of one unnecessary if
        overall_possible_tasks = len(self.srv_manager.available_srv_list) * max_server_queue_len
        overall_current_tasks = 0
        # Count the current number of tasks
        for server in self.srv_manager.active_srv_list:
            overall_current_tasks += server.current_running_tasks

        # If number of active servers is smaller than the number of available servers, probably we already stopped
        # a server, so do not stop another one
        if len(self.srv_manager.active_srv_list)!=len(self.srv_manager.available_srv_list):
            print ("Num of active servers: ", len(self.srv_manager.active_srv_list), "Num of available servers: ", len(self.srv_manager.available_srv_list))
            return

        # If to little time passed since last change, do nothing
        if time() - self.srv_manager.cool_down_period < self.last_scale_change:
            print ("Too soon to remove another server")
            return


        # Do not delete the last server
        #if len (self.available_srv_list) < 2:
        #    return

        if overall_current_tasks>as_high_threshold*overall_possible_tasks:
            # If number of active servers is bigger than the number of available servers, probably we already started
            # a new server, so do not start another one
            self.srv_manager.scale_out()
            self.last_scale_change = time ()

        if overall_current_tasks<as_low_threshold*overall_possible_tasks:
            self.srv_manager.scale_in()
            self.last_scale_change = time ()

class BellmanAS(BasicAS):

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

    def trigger_scale_in(self):

        # get index out of servers queue
        index = get_queue_state_index (self.srv_manager)
        op = self.data_parser.scale_in_policy_list[index]
        print ("Bellman scale in: index is ", index, " op is: ", op, " current available servers: ", \
               self.print_available_servers (), " current running tasks: ", self.print_current_running_tasks())
        for i in range(len(self.srv_manager.full_srv_list)):
            if (int(op[i])==1) and (self.srv_manager.full_srv_list[i].current_running_tasks ==0):
                self.srv_manager.scale_in(i)

    def trigger_scale_out(self):

        index = get_queue_state_index (self.srv_manager)
        op = self.data_parser.scale_out_policy_list[index]
        print ("Bellman scale out: index is ", index, " out: ",op)
        print ("out: ",op)
        if op>0:
            self.srv_manager.scale_out()

def create_as_obj(as_type, mgr)->BasicAS: #TODO Throw exception for type mismatch
    if as_type == "dumb":
        return DumbAS(mgr)
    if as_type == "threshold":
        return ThresholdAS(mgr)
    if as_type == "bellman":
        return BellmanAS(mgr)
