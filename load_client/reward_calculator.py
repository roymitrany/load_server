import threading
from time import sleep
from typing import Dict, List

from load_client.global_vars import reward_scale_out, reward_scale_in, reward_reject, reward_response, \
    reward_delay_per_ms, get_num_of_completed_tasks, task_limit, reward_use_per_second
from load_client.servers_management import ServerManager

def count_num_of_active_server(mgr:ServerManager, num_of_servers_list):
    '''
    A separate thread counts the number of active servers each second and adds it to the list
    :param num_of_servers_list:
    :param mgr: servers manager singleton object
    :return:
    '''
    while True:
        count = len(mgr.active_srv_list)
        lst = num_of_servers_list
        lst.append(count)
        if get_num_of_completed_tasks() >=task_limit:
            print ("reward calculator server counter is exiting")
            break
        sleep(1)

class CostCalculator:

    def __init__(self, mgr:ServerManager):
        self.num_of_servers_list:List[int] = []*0
        self.num_of_servers_list.append(0)
        self.rejections = 0
        self.srv_mgr = mgr
        x = threading.Thread (target=count_num_of_active_server, args=(mgr,self.num_of_servers_list, ))
        x.start ()

    def calculate_cost(self):
        scale_out_cost = self.srv_mgr.total_scale_out_counter*reward_scale_out
        scale_in_cost = self.srv_mgr.total_scale_in_counter*reward_scale_in
        rejection_cost = self.rejections *reward_reject

        # From each server, take number of responses and delay of each response (server side)
        response_counter = 0
        total_delay = 0
        for server in self.srv_mgr.full_srv_list:
            response_counter += len(server.response_duration_list)
            for num in server.response_duration_list:
                total_delay += num

        response_cost = response_counter*reward_response
        delay_cost = total_delay*reward_delay_per_ms

        # Count the total cost of holding n servers each second
        servers_counter = sum(self.num_of_servers_list)
        server_execution_cost = servers_counter*reward_use_per_second

        print ("^^^^^^^^^^^^^^^^^^^^^^^^Reward  calculation^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        print ("scale out cost: " , scale_out_cost)
        print ("scale in cost: " , scale_in_cost)
        print ("rejection cost: " , rejection_cost)
        print ("delay cost: " , delay_cost)
        print ("server execution cost: " , server_execution_cost)

        print ("Service earnings: " , response_cost)

        val = scale_out_cost + scale_in_cost + rejection_cost + response_cost + delay_cost + server_execution_cost
        print ("Total Reward: " , val)
        print ("reward per response", str(val/(task_limit-self.rejections)))
        print ("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        return val

