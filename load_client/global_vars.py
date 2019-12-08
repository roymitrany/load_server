
# Global number of the tasks that were completed (not sure if we will ever use it)
tasks_completed = 0

def get_num_of_completed_tasks():
    global tasks_completed
    return tasks_completed

def inc_num_of_completed_tasks():
    global tasks_completed
    tasks_completed +=1

# Global index for the request (not sure if we will ever use it)
tasks_global_index = 0

def get_tasks_global_index():
    global tasks_global_index
    return tasks_global_index

def inc_tasks_global_index():
    global tasks_global_index
    tasks_global_index +=1

# Global indicator that simulation is finished (in order to stop data collection
simulation_finished = False

def is_simulation_finished():
    global simulation_finished
    return simulation_finished

def set_simulation_finished():
    global simulation_finished
    simulation_finished = True


# The number of servers to start with. The maximal number of servers is implicitely defined by the full list of servers
initial_num_of_servers = 3

######### From here on, immutable variables that we don't need to wrap with functions
# The average load that we should set for each task
avg_load_level = 10

# Full list of server IP addresses and ports (we trust the programmer that they have the same length
full_srv_ip_addr_list = ["35.170.37.1", "35.174.93.186", "52.87.31.244", "34.232.193.79", "127.0.0.1"]
full_srv_port_list = [5000, 5001, 5002, 5003, 5004]

# Amount of time to wait between the time that the server is initiated, until it is available.
server_startup_time = 1

# Average requests per second
average_rate = 2.0

#The server's timeout (in seconds)
server_timeout = 60

# Maximal queue length
#max_server_queue_len =  int(server_timeout*average_rate/num_of_servers)
max_server_queue_len = 5

# the number of tasks to be completed before we stop the test
task_limit = 500

# Interval in seconds between statistics data collection
data_collection_interval = 1

############################# Reward Parameters ###############################
# Penalties get negative values. Reward get positive values. This way we can treat everything as a reward
# and let the global definition take the decision what is a reward and what is a penalty
reward_scale_in = -1000
reward_scale_out = -1000
reward_use_per_second = -1
reward_response = 1000
reward_delay_per_ms = -0.1
reward_reject = 3000
