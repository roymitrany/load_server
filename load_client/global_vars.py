




# Full list of server IP addresses and ports (we trust the programmer that they have the same length
#full_srv_ip_addr_list = ["35.170.37.1", "35.174.93.186", "52.87.31.244", "34.232.193.79", "127.0.0.1"]
full_srv_ip_addr_list = ["127.0.0.1", "127.0.0.1", "127.0.0.1", "127.0.0.1", "127.0.0.1"]
full_srv_port_list = [5000, 5001, 5002, 5003, 5004]



#The server's timeout (in seconds)
server_timeout = 200

# Maximal queue length
#max_server_queue_len =  int(server_timeout*average_rate/num_of_servers)
max_server_queue_len = 5

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
reward_reject = -3000
