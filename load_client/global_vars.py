# Full list of server IP addresses and ports (we trust the programmer that they have the same length
#full_srv_ip_addr_list = ["35.170.37.1", "35.174.93.186", "52.87.31.244", "34.232.193.79", "54.224.65.178"]
#full_srv_ip_addr_list = ["10.0.31.59", "10.0.31.232", "10.0.31.225", "10.0.31.21", "10.0.31.254"]
full_srv_ip_addr_list = ["127.0.0.1", "127.0.0.1", "127.0.0.1", "127.0.0.1", "127.0.0.1"]
full_srv_port_list = [5000, 5001, 5002, 5003, 5004]
#full_srv_port_list = [5006, 5007, 5008, 5009, 5010]

#The server's timeout (in seconds)
server_timeout = 45

# Maximal queue length
#max_server_queue_len =  int(server_timeout*average_rate/num_of_servers)
max_server_queue_len = 5

# Interval in seconds between statistics data collection
data_collection_interval = 1

as_high_threshold = 0.7
as_low_threshold = 0.3

############################# Results filenames ###############################
response_duration_filename = "response_duration.txt"
exec_summary_filename = "exec_summary.txt"
queues_filename = "queues.txt"
num_of_servers_filename = "num_of_servers.txt"
calculated_cost_filename = "calculated_cost.txt"

############################# Reward Parameters ###############################
# Penalties get negative values. Reward get positive values. This way we can treat everything as a reward
# and let the global definition take the decision what is a reward and what is a penalty
reward_scale_in = 0
reward_scale_out = -25
reward_use_per_second = -10
reward_response = 120
reward_delay_per_ms = -0.01
reward_reject = -20
