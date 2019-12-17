import threading
import time
import os
from pathlib import Path
from typing import List
from abc import ABC, abstractmethod
import matplotlib.pyplot as plt
import matplotlib

from load_client.reward_calculator import CostCalculator

matplotlib.use('Agg')
plt.rc('font', size=16)

from load_client.global_vars import  data_collection_interval
from load_client.servers_management import ServerManager


class DataCollector(ABC):

    def __init__(self, sim_mgr, res_path):
        self.sim_mgr = sim_mgr
        self.srv_mgr: ServerManager = sim_mgr.srv_mgr
        self.res_path:str = res_path
        self.x_list: List[int] = []
        self.y_list: List[List[int]] = []
        self.counter = 1
        self.f = None


        # Create an empty list of each server
        for i in range(len(self.srv_mgr.full_srv_list)):
            self.y_list.append([]*0)

    @abstractmethod
    def save_ongoing_data(self):
        pass

    @abstractmethod
    def save_summary_data(self):
        pass

    @abstractmethod
    def print_data(self):
        pass

    @abstractmethod
    def plot_data(self):
        pass

    def simulation_finished(self):
        self.f.close()
        self.print_data()
        self.plot_data()

class ResponseDurationData(DataCollector):
    def __init__(self, sim_mgr, res_path):
        super ().__init__ (sim_mgr, res_path)
        filename = os.path.join(self.res_path, "response_duration.txt")
        self.f = open (filename, "a")


        # Create an empty list of each server
        for i in range(len(self.srv_mgr.full_srv_list)):
            self.y_list.append([]*0)

    def save_ongoing_data(self):
        """
        The response duration is event driven metric, and is collected by the server.
        Therefore we have to call this method only once, when the simulation is completed, and take the data from
        the server objects
        :return:
        """
        # We have to find out which of the servers collected the most events. This will determine
        # the dimension of the x_list and y_lists (all have to be with same length
        max_len = 0
        for  server in self.srv_mgr.full_srv_list:
            # Update the duration list max_len
            max_len = max(max_len, len(server.response_duration_list))

        # build y lists and x list for plot
        for i in range (0, len (self.srv_mgr.full_srv_list)):
            server = self.srv_mgr.full_srv_list[i]

            # Simply copy the duration list as a new y list, and pad with 0's until you reach max_length
            self.y_list[i] = server.response_duration_list + [0]*(max_len-len(server.response_duration_list))

        self.x_list = range(1, max_len+1) # Build the x axis according to max_len

        # Create the CSV file
        for count in range(max_len):
            line = str(count) # start a line string for the csv record
            for i in range (0, len (self.srv_mgr.full_srv_list)):

                # rely on y list created earlier
                line = line + "," + str(self.y_list[i][count]) # append a value to the csv line
            self.f.write(line + "\n") # write the csv line to the file

    def save_summary_data(self):
        return

    def print_data(self):
        #print ("X axis: " + str(self.x_list))
        #for i in range(0,len(self.srv_manager.full_srv_list)):
        #    print ("Y axis for     ", str(self.srv_manager.full_srv_list[i].srv_port), ": ", str (self.y_list[i]))
        return


    def plot_data(self):
        fig, ax = plt.subplots (figsize=(30,15))

        ax.set (xlabel='Response Count', ylabel='Response Time',
                title='Server Response time')
        ax.grid ()

        for i in range(len(self.srv_mgr.full_srv_list)):
            srv_queue_arr = self.y_list[i]
            srv_port = self.srv_mgr.full_srv_list[i].srv_port
            ax.plot (self.x_list, srv_queue_arr, label=str(srv_port))
        plt.legend (loc='upper left')
        fig.savefig(os.path.join(self.res_path, "srv_resp_time.png"))

class SummaryData(DataCollector):
    """
    This class handles all the summary information about the execution. It includes the summary results, performance
    grade as well as the initial data for the batch
    """
    cost_calc_obj: CostCalculator


    def __init__(self, sim_mgr, res_path, cost_calc_obj):
        super ().__init__ (sim_mgr, res_path)
        self.filename = os.path.join (res_path, "exec_summary.txt")
        self.cost_calc_obj = cost_calc_obj
        self.response_counter = 0
        self.total_delay = 0
        self.num_of_servers_list:List[int] = []*0
        self.num_of_servers_list.append(0)


    def save_ongoing_data(self):
        return

    def save_summary_data(self):
        """
        The Summary data is collected only when the simulation is finished
        :return:
        Request rate: 3.6
        LB policy: Bellman
        AS Policy: Bellman
        Initial servers: 5
        load level 10 (1.1 sec per request)

        """
        for server in self.srv_mgr.full_srv_list:
            self.response_counter += len(server.response_duration_list)
            self.total_delay += sum(server.response_duration_list)


        self.f = open (self.filename, "a")
        # Write the test parameters to the file
        param_str = "test_parameters:\n"
        #param_str += "load_balancer_class" + lb_obj.__class__.__name__ + "\n"
        self.f.write (param_str + "\n")

        # Write the result summary
        res_str = "Test Results: \n"
        res_str += "Scale out events: " + str(self.srv_mgr.total_scale_out_counter) +  "\n"
        res_str += "Scale in events: " + str(self.srv_mgr.total_scale_in_counter) +  "\n"
        res_str += "Rejections: " + str(self.sim_mgr.get_num_of_rejections()) +  "\n"
        res_str += "Total server responses: " + str(self.response_counter) +  "\n"
        res_str += "Sum of all server processing time: " + str(self.total_delay) +  "\n"
        self.f.write(res_str + "\n")

        self.f.close()



    def print_data(self):
        # print totals
        print ("==================total started tasks: " + str (self.sim_mgr.get_tasks_global_index ()))
        print ("==================Number of rejects: " + str (self.sim_mgr.get_num_of_rejections()))
        print ("==========  requests per server ===========")
        for server in self.srv_mgr.full_srv_list:
            print ("server %s sent %d requests" % (server.srv_port, len (server.response_duration_list)))

        for server in self.srv_mgr.full_srv_list:
            print ("server %s duration: " % server.srv_port, end=" ")
            for num in server.response_duration_list:
                print (num, end=" ")
            print ("")
            print ("server %s queue length: " % server.srv_port, end=" ")
            for num in server.response_tasks_queue_list:
                print (num, end=" ")
            print ("")

        print ("^^^^^^^^^^^^^^^^^^^^^^^^Reward  calculation^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        print ("scale out cost: " , self.cost_calc_obj.scale_out_cost)
        print ("scale in cost: " , self.cost_calc_obj.scale_in_cost)
        print ("rejection cost: " , self.cost_calc_obj.rejection_cost)
        print ("delay cost: " , self.cost_calc_obj.delay_cost)
        print ("server execution cost: " , self.cost_calc_obj.server_execution_cost)

        print ("Service earnings: " , self.cost_calc_obj.response_cost)

        print ("Total Reward: " , self.cost_calc_obj.total_reward)
        print ("reward per response", str(self.cost_calc_obj.total_reward/(self.sim_mgr.get_num_of_completed_tasks()-self.sim_mgr.get_num_of_rejections())))
        print ("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")

    def plot_data(self):
            pass # Summary does not produce a graph


class QueueLenData(DataCollector):
    """
    This data collector counts the enqueueing queue length for each request that arrived to the server.
    It collects the data for each response event, so it is event driven and not time driven
    """
    def __init__(self, sim_mgr, res_path):
        super ().__init__ (sim_mgr, res_path)
        filename = os.path.join(self.res_path, "queues.txt")
        self.f = open (filename, "a")


        # Create an empty list of each server
        for i in range(len(self.srv_mgr.full_srv_list)):
            self.y_list.append([]*0)

    def save_ongoing_data(self):
        return

    def save_summary_data(self):
        """
        The queue len data is event metric driven, and therefore called periodically from the "collect_data": thread
        :return:
        """
        self.counter += 1
        self.x_list.append(self.counter*data_collection_interval) # add the x axis (currently counter) element
        line = str(self.counter) # start a line string for the csv record
        for i in range (0, len (self.srv_mgr.full_srv_list)):
            server = self.srv_mgr.full_srv_list[i]
            line = line + "," + str(server.current_running_tasks) # append a value to the csv line
            self.y_list[i].append(server.current_running_tasks) # append the queue length calue to the server's array
        self.f.write(line + "\n") # write the csv line to the file

    def print_data(self):
        #print ("X axis: " + str(self.x_list))
        for i in range(0, len(self.srv_mgr.full_srv_list)):
            #print ("Y axis for     ", str(self.srv_mgr.full_srv_list[i].srv_port), ": ", str (self.y_list[i]))

            # For debug, print also the queue length measured in client side
            print ("server version ", str (self.srv_mgr.full_srv_list[i].srv_port), ": ",
                   str (self.srv_mgr.full_srv_list[i].response_tasks_queue_list))
            print ("client version ", str (self.srv_mgr.full_srv_list[i].srv_port), ": ",
                   str (self.srv_mgr.full_srv_list[i].request_tasks_queue_list))

    def plot_data(self):
        fig, ax = plt.subplots (figsize=(30,15))

        ax.set (xlabel='Time(seconds)', ylabel='Queue Length',
                title='Server Queue Length by Time')
        ax.grid ()

        for i in range(len(self.srv_mgr.full_srv_list)):
            srv_queue_arr = self.y_list[i]
            srv_port = self.srv_mgr.full_srv_list[i].srv_port
            ax.plot (self.x_list, srv_queue_arr, label=str(srv_port))
        plt.legend (loc='upper right')
        fig.savefig(os.path.join(self.res_path, "srv_queue.png"))

        # TODO: create another data collector for number of active servers per second
        #self.num_of_servers_list.append(len(self.sim_mgr.srv_mgr.active_srv_list))

class DataCollectionManager:
    def __init__(self, sim_mgr):
        ts = time.time()
        self.cost_calc_obj = CostCalculator(self, sim_mgr)

        # Create folder for all the results
        self.res_path = os.path.join(os.getcwd(), "results", str(ts))
        os.makedirs(self.res_path)

        # Create a class of queue length data
        queue_len_data = QueueLenData(sim_mgr, self.res_path)
        response_duration_data = ResponseDurationData(sim_mgr, self.res_path)
        self.summary_data = SummaryData(sim_mgr, self.res_path, self.cost_calc_obj)

        data_collection_thread = threading.Thread (target=collect_data, args=(self,sim_mgr,))
        data_collection_thread.start ()

        self.data_collection_list:List[DataCollector] = [queue_len_data, response_duration_data, self.summary_data]


    def save_ongoing_data(self):
        for data_collector in self.data_collection_list:
            data_collector.save_ongoing_data()

    def simulation_finished(self):
        self.cost_calc_obj.calculate_cost()

        # Generate Summary data
        for data_collector in self.data_collection_list:
            data_collector.save_summary_data()

        # Save and print
        for data_collector in self.data_collection_list:
            data_collector.simulation_finished()

        self.cost_calc_obj.save_calculated_cost(self.summary_data.filename)



def collect_data(data_collector, sim_mgr):
    while True:
        time.sleep (data_collection_interval)
        data_collector.save_ongoing_data()
        if sim_mgr.is_simulation_finished():
            data_collector.simulation_finished()
            break

