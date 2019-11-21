import subprocess
import threading
from typing import List
import random
from time import sleep
import re

from load_client.load_balancers import RandomLB
from load_client.servers_management import ServerManager, Server

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
# Global index for the request (not sure if we will ever use it)
tasks_index: int = 0

# Global number of the tasks that were completed (not sure if we will ever use it)
tasks_completed: int = 0

task_limit: int = 10
num_of_servers = 3
load = num_of_servers*10
lb_obj = RandomLB (num_of_servers)
average_rate = 1

# Create the server management singleton object
srv_mgr:ServerManager = ServerManager(num_of_servers)

def process_responses():
    global tasks_completed, task_limit, srv_mgr
    print ("in process_response 0")
    while True:
        print ("in process_response 1, tasks completed: " + str(tasks_completed))
        active_servers_list: List[Server] = srv_mgr.active_srv_list
        for server in active_servers_list:
            for process in server.process_list : # TODO: make it flexible, according to tasks_index
                #print (output.strip ())
                return_code = process.poll ()
                if return_code is not None:
                    print ('RETURN CODE', return_code)
                    # Process has finished, read rest of the output
                    for byte_output in process.stdout.readlines ():
                        output = byte_output.decode("utf-8")
                        #print (output.strip ())
                        if output.find("duration") > -1:
                            print (output.strip ()) # TODO: save the duration somewhere
                            duration_match = re.search(r'duration\": \"([\d]+)', output)
                            duration = int(duration_match.group(1))
                            server.process_duration_list.append(duration)
                            tasks_completed += 1
                            server.process_list.remove(process)
                            server.current_running_tasks -= 1
        if tasks_completed >=task_limit:
            print ("Overall tasks completed: " + str (tasks_completed))
            break
        sleep(1)


def generate_request():
    global lb_obj, tasks_index, load
    server_id:int = lb_obj.pick_server (srv_mgr)
    server_obj:Server = srv_mgr.get_server_obj(server_id)
    server_obj.start_req(load)

    print ("started  task ", tasks_index)
    tasks_index += 1


# first start the thread that receives the responses
t = threading.Thread (target=process_responses)
t.start ()

# Loop for generating requests
for i in range (task_limit):
    time_to_sleep = random.expovariate(average_rate) #TODO: take the timing from an external time generator
    sleep(time_to_sleep)
    print("------------after sleeping " + str(time_to_sleep))
    generate_request ()


# wait until all responses arrive back
t.join()

# print totals
print ("==================total started tasks: " + str(tasks_index))
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