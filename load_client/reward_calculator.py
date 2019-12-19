from load_client.global_vars import reward_scale_out, reward_scale_in, reward_reject, reward_response, \
    reward_delay_per_ms,  reward_use_per_second

class CostCalculator:

    def __init__(self, data_collector:'DataCollectionManager', sim_mgr):
        self.data_collector = data_collector
        self.sim_mgr = sim_mgr
        self.srv_mgr = sim_mgr.srv_mgr
        self.scale_out_cost = self. scale_in_cost = self.rejection_cost = self.delay_cost  = 0
        self.response_cost = self.server_execution_cost = self.total_reward = 0


    def calculate_cost(self):
        self.scale_out_cost = self.srv_mgr.total_scale_out_counter*reward_scale_out
        self.scale_in_cost = self.srv_mgr.total_scale_in_counter*reward_scale_in
        self.rejection_cost = self.sim_mgr.get_num_of_rejections() *reward_reject

        # From each server, take number of responses and delay of each response (server side)
        response_counter = 0
        total_delay = 0
        for server in self.srv_mgr.full_srv_list:
            response_counter += len(server.response_duration_list)
            total_delay += sum(server.response_duration_list)

        self.response_cost = response_counter*reward_response
        self.delay_cost = total_delay*reward_delay_per_ms

        # Count the total cost of holding n servers each second
        servers_counter = sum(self.num_of_servers_list)
        self.server_execution_cost = servers_counter*reward_use_per_second

        # Sum the total cost or reward
        self.total_reward = self.scale_out_cost + self.scale_in_cost + self.rejection_cost\
                            + self.response_cost + self.delay_cost + self.server_execution_cost

    def save_calculated_cost(self, filename):
        f = open (filename, "a")
        # Write the cost summary to the file
        cost_str =  "Total cost: \n"
        cost_str +=  "scale_out_cost: " + str(self.scale_out_cost) + "\n"
        cost_str += "scale_in_cost: " + str(self.scale_in_cost) + "\n"
        cost_str += "rejection_cost: " + str(self.rejection_cost) + "\n"
        cost_str += "delay_cost: " + str(self.delay_cost) + "\n"
        cost_str += "server_execution_cost: " + str(self.server_execution_cost) + "\n"
        cost_str += "response_cost: " + str(self.response_cost) + "\n"
        cost_str += "total_reward: " + str(self.total_reward) + "\n"
        f.write(cost_str + "\n")
        f.close()
