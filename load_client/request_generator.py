import threading

from load_client.servers_management import ServerManager, Server
from load_client.auto_scaler import ThresholdAS, BellmanAS, DumbAS
from load_client.global_vars import max_server_queue_len
import random
from time import sleep
from typing import TYPE_CHECKING


from load_client.load_balancers import RandomLB, JsqLB, BellmanLB
from load_client.pie_file_data_parser import PieDataParser
from load_client.reward_calculator import CostCalculator

"""
This is the main class to holds a data structure for courses
Since we run this only once, everything is declared in the class level. We do not need
to instantiate an object (but we can).
Create the dictionary, and parse the file from which we take the course number index.
For each course number, add an element to the dictionary. The key for the element is
the course number, and the value is Course TypedDict object. We only fill the num
attribute in this new object, and other values are added in separate function, each
value in its special function.
"""

class RequestGenerator:
    def generate_request(self, sim_mgr: 'SimExecManager'):
        server_obj:Server = sim_mgr.lb_obj.pick_server ()
        # We are good with the queue, send the request
        sim_mgr.as_obj.trigger_scale_out()


        if (server_obj is None) or (server_obj.current_running_tasks >= max_server_queue_len):

            # The queue in the server side is full. Reject the request
            sim_mgr.inc_num_of_rejections()
            sim_mgr.inc_num_of_completed_tasks()
            print("============== REJECT!!!!!!!!!! " + str (sim_mgr.get_num_of_completed_tasks()))
            return

        if server_obj.start_req(sim_mgr.simulation_params.avg_load_level):
            print ("started  task ", sim_mgr.get_tasks_global_index())
            sim_mgr.inc_tasks_global_index()



