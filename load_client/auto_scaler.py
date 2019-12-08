'''
Auto scaler classes.
We will define an abstract class, and then some types of auto scaler, such as high and low threshold.
Mark's LB algorithm will be added right here.
'''
from abc import ABC, abstractmethod
from typing import List

from load_client.global_vars import max_server_queue_len
from load_client.pie_file_data_parser import get_index_for_queue_list, PieDataParser, get_queue_state_index


class BasicAS(ABC):

    def __init__(self, mgr):
        self.srv_manager = mgr


    @abstractmethod
    def trigger_scale_in(self):
        pass

    @abstractmethod
    def trigger_scale_out(self):
        pass



class ThresholdAS(BasicAS):
    high_threshold = 0.8
    low_threshold = 0.4

    def trigger_scale_in(self):
        self.trigger_scale_in_out() #TODO: Separate scale in from scale out

    def trigger_scale_out(self):
        self.trigger_scale_in_out() #TODO: Separate scale in from scale out

    def trigger_scale_in_out(self):
        overall_possible_tasks = len(self.srv_manager.available_srv_list) * max_server_queue_len
        overall_current_tasks = 0
        # Count the current number of tasks
        for server in self.srv_manager.active_srv_list:
            overall_current_tasks += server.current_running_tasks

        if overall_current_tasks>self.high_threshold*overall_possible_tasks:
            # If number of active servers is bigger than the number of available servers, probably we already started
            # a new server, so do not start another one
            if len (self.srv_manager.active_srv_list) > len (self.srv_manager.available_srv_list):
                return
            self.srv_manager.scale_out()

        if overall_current_tasks<self.low_threshold*overall_possible_tasks:
            self.srv_manager.scale_in()


class BellmanAS(BasicAS):

    def __init__(self, mgr, pie_data_parser):
        super ().__init__ (mgr)
        self.data_parser:PieDataParser = pie_data_parser

    def trigger_scale_in(self):

        print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
        # get index out of servers queue
        index = get_queue_state_index (self.srv_manager)
        op = self.data_parser.scale_in_policy_list[index]
        for i in range(len(self.srv_manager.full_srv_list)):
            print ("in: i is ", i)
            print ("in: index is ", index)
            print ("in: ", op)
            if (int(op[i])==1) and (self.srv_manager.full_srv_list[i].current_running_tasks ==0):
            #if int (op[i]) == 1:
                self.srv_manager.scale_in(i)

    def trigger_scale_out(self):

        index = get_queue_state_index (self.srv_manager)
        op = self.data_parser.scale_out_policy_list[index]
        print ("out: index is ", index)
        print ("out: ",op)
        if op>0:
            self.srv_manager.scale_out()


