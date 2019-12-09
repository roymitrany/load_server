import threading

from load_client.auto_scaler import ThresholdAS, BellmanAS, DumbAS
from load_client.data_collector import DataCollectionManager, collect_data
from load_client.global_vars import initial_num_of_servers, task_limit, average_rate, max_server_queue_len, \
    avg_load_level, set_simulation_finished
from load_client.global_vars import get_num_of_completed_tasks, inc_num_of_completed_tasks
from load_client.global_vars import get_tasks_global_index, inc_tasks_global_index
import random
from time import sleep


from load_client.load_balancers import RandomLB, JsqLB, BellmanLB
from load_client.pie_file_data_parser import PieDataParser
from load_client.servers_management import ServerManager, Server
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

# Create the server management singleton object
srv_mgr:ServerManager = ServerManager(initial_num_of_servers)
#pie_parser = PieDataParser("pie_file")
#lb_obj = BellmanLB (srv_mgr, pie_parser)
lb_obj = JsqLB (srv_mgr)
#lb_obj = RandomLB (srv_mgr)
#as_obj = ThresholdAS(srv_mgr)
as_obj = DumbAS()
#as_obj = BellmanAS(srv_mgr, pie_parser)
data_collector = DataCollectionManager(srv_mgr)

cost_calc_obj:CostCalculator = CostCalculator(srv_mgr)

def scale_out_trigger(mgr:ServerManager):
    '''
    A separate thread that waits for a scale out event to arrive from the server manager, upon request launch
    :param mgr: servers manager singleton object
    :return:
    '''
    while True:
        mgr.scale_out_event.wait(timeout=60)
        as_obj.trigger_scale_out()
        mgr.scale_out_event.clear()
        if get_num_of_completed_tasks() >=task_limit: # This will work only if wait event has timeout
            print ("Scale out thread is exiting")
            break

def scale_in_trigger(mgr:ServerManager):
    '''
    A separate thread that waits for a scale in event to arrive from the server manager, upon response arrival
    :param mgr: servers manager singleton object
    :return:
    '''
    while True:
        mgr.scale_in_event.wait(timeout=60)
        as_obj.trigger_scale_in()
        mgr.scale_in_event.clear()
        if get_num_of_completed_tasks() >=task_limit:
            print ("Scale in thread is exiting") # This will work only if wait event has timeout
            break


def generate_request():
    global lb_obj, cost_calc_obj
    server_obj:Server = lb_obj.pick_server ()
    # We are good with the queue, send the request
    srv_mgr.scale_out_event.set ()  # Notify the world that scale in should be triggered. Should be caught by AS

    if (server_obj is None) or (server_obj.current_running_tasks >= max_server_queue_len):

        # The queue in the server side is full. Reject the request
        cost_calc_obj.rejections += 1
        inc_num_of_completed_tasks()
        print("============== REJECT!!!!!!!!!! " + str (get_num_of_completed_tasks()))
        return

    server_obj.start_req(avg_load_level)

    print ("started  task ", get_tasks_global_index())
    inc_tasks_global_index()


data_collection_thread = threading.Thread (target=collect_data, args=(data_collector,))
data_collection_thread.start ()
x = threading.Thread (target=scale_out_trigger, args=(srv_mgr,))
x.start ()
y = threading.Thread (target=scale_in_trigger, args=(srv_mgr,))
y.start ()

# Loop for generating requests
for i in range (task_limit):
    time_to_sleep = random.expovariate(average_rate) #TODO: take the timing from an external time generator
    sleep(time_to_sleep)
    print("------------after sleeping " + str(time_to_sleep) + " Task no. " + str(i))
    generate_request ()

# wait until all responses arrive back
for server in srv_mgr.full_srv_list:
    server.response_thread.join()

set_simulation_finished()
# Stop data collection
data_collection_thread.join()

# print totals
print ("==================total started tasks: " + str(get_tasks_global_index()))
print ("==================Number of rejects: " + str(cost_calc_obj.rejections))
print ("==========  requests per server ===========")
for server in srv_mgr.full_srv_list:
    print ("server %s sent %d requests" % (server.srv_port, len(server.response_duration_list)))

for server in srv_mgr.full_srv_list:
    print ("server %s duration: " % server.srv_port, end=" ")
    for num in server.response_duration_list:
        print(num, end=" ")
    print("")
    print ("server %s queue length: " % server.srv_port, end=" ")
    for num in server.response_tasks_queue_list:
        print(num, end=" ")
    print("")
cost_calc_obj.calculate_cost()
exit(0)


