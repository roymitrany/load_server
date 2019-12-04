'''
Auto scaler classes.
We will define an abstract class, and then some types of auto scaler, such as high and low threshold.
Mark's LB algorithm will be added right here.
'''
from abc import ABC, abstractmethod
import random
import time

from load_client.global_vars import max_server_queue_len
from load_client.servers_management import ServerManager, Server

class BasicAS(ABC):
    def __init__(self, mgr):
        self.srv_manager = mgr


    @abstractmethod
    def trigger_scale_in_out(self):
        pass


class ThresholdAS(BasicAS):
    high_threshold = 0.8
    low_threshold = 0.4
    def trigger_scale_in_out(self):
        overall_possible_tasks = len(self.srv_manager.available_srv_list) * max_server_queue_len
        overall_current_tasks = 0
        # Count the current number of tasks
        for server in self.srv_manager.active_srv_list:
            overall_current_tasks += server.current_running_tasks

        if overall_current_tasks>self.high_threshold*overall_possible_tasks:
            self.srv_manager.scale_out()

        if overall_current_tasks<self.low_threshold*overall_possible_tasks:
            self.srv_manager.scale_in()

