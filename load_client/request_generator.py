import threading

from load_client.data_collector import DataCollector, collect_data
from load_client.global_vars import initial_num_of_servers, task_limit, average_rate, max_server_queue_len, \
    avg_load_level, set_simulation_finished
from load_client.global_vars import get_num_of_completed_tasks, inc_num_of_completed_tasks
from load_client.global_vars import get_tasks_global_index, inc_tasks_global_index
import random
from time import sleep


from load_client.load_balancers import RandomLB, JsqLB
from load_client.servers_management import ServerManager, Server
from load_client.value_function import ValueFunc

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
lb_obj = JsqLB (srv_mgr)
#lb_obj = RandomLB (srv_mgr)
data_collector = DataCollector(srv_mgr)

value_func_obj:ValueFunc = ValueFunc()


def generate_request():
    global lb_obj, value_func_obj
    server_obj:Server = lb_obj.pick_server ()
    #server_obj:Server = srv_mgr.get_server_obj(server_id)
    if server_obj.current_running_tasks>=max_server_queue_len:

        # The queue in the server side is full. Reject the request
        value_func_obj.rejections += 1
        inc_num_of_completed_tasks()
        print("============== REJECT!!!!!!!!!! " + str (get_num_of_completed_tasks()))
        return

    # We are good with the queue, send the request
    server_obj.start_req(avg_load_level)

    print ("started  task ", get_tasks_global_index())
    inc_tasks_global_index()


data_collection_thread = threading.Thread (target=collect_data, args=(data_collector,))
data_collection_thread.start ()

# Loop for generating requests
for i in range (task_limit):
    time_to_sleep = random.expovariate(average_rate) #TODO: take the timing from an external time generator
    sleep(time_to_sleep)
    print("------------after sleeping " + str(time_to_sleep))
    generate_request ()


# wait until all responses arrive back
for server in srv_mgr.full_srv_list:
    server.response_thread.join()

set_simulation_finished()
# Stop data collection
data_collection_thread.join()

# print totals
print ("==================total started tasks: " + str(get_tasks_global_index()))
print ("==================Number of rejects: " + str(value_func_obj.rejections))
print ("==========  requests per server ===========")
for server in srv_mgr.full_srv_list:
    print ("server %s sent %d requests" % (server.srv_port, server.total_request_counter))

for server in srv_mgr.full_srv_list:
    print ("server %s max pending requests: %d" % (server.srv_port, server.max_running_tasks))

for server in srv_mgr.full_srv_list:
    print ("server %s duration: " % server.srv_port, end=" ")
    for num in server.process_duration_list:
        print(num, end=" ")
    print("")

