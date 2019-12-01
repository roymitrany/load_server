import time
import os
from pathlib import Path
from typing import List
from abc import ABC, abstractmethod
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
plt.rc('font', size=16)

from load_client.global_vars import is_simulation_finished, data_collection_interval
from load_client.servers_management import ServerManager, Server

class DataCollector(ABC):

    def __init__(self, mgr, res_path):
        self.srv_manager: ServerManager = mgr
        self.res_path:str = res_path
        self.x_list: List[int] = []
        self.y_list: List[List[int]] = []
        self.counter = 1
        self.f = None


        # Create an empty list of each server
        for i in range(len(self.srv_manager.full_srv_list)):
            self.y_list.append([]*0)

    @abstractmethod
    def collect_data(self):
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
    def __init__(self, mgr, res_path):
        super ().__init__ (mgr, res_path)
        filename = os.path.join(self.res_path, "response_duration.txt")
        self.f = open (filename, "a")


        # Create an empty list of each server
        for i in range(len(self.srv_manager.full_srv_list)):
            self.y_list.append([]*0)

    def collect_data(self):
        """
        The response duration is event driven metric, and is collected by the server.
        Therefore we have to call this method only once, when the simulation is completed, and take the data from
        the server objects
        :param counter:
        :return:
        """
        # We have to find out which of the servers collected the most events. This will determine
        # the dimension of the x_list and y_lists (all have to be with same length
        max_len = 0
        for  server in self.srv_manager.full_srv_list:
            # Update the duration list max_len
            max_len = max(max_len, len(server.response_duration_list))

        # build y lists and x list for plot
        for i in range (0, len (self.srv_manager.full_srv_list)):
            server = self.srv_manager.full_srv_list[i]

            # Simply copy the duration list as a new y list, and pad with 0's until you reach max_length
            self.y_list[i] = server.response_duration_list + [0]*(max_len-len(server.response_duration_list))

        self.x_list = range(1, max_len+1) # Build the x axis according to max_len

        # Create the CSV file
        for count in range(max_len):
            line = str(count) # start a line string for the csv record
            for i in range (0, len (self.srv_manager.full_srv_list)):

                # rely on y list created earlier
                line = line + "," + str(self.y_list[i][count]) # append a value to the csv line
            self.f.write(line + "\n") # write the csv line to the file

    def print_data(self):
        print ("X axis: " + str(self.x_list))
        for i in range(0,len(self.srv_manager.full_srv_list)):
            print ("Y axis for     ", str(self.srv_manager.full_srv_list[i].srv_port), ": ", str (self.y_list[i]))


    def plot_data(self):
        fig, ax = plt.subplots (figsize=(30,15))

        ax.set (xlabel='Response Count', ylabel='Response Time',
                title='Server Response time')
        ax.grid ()

        for i in range(len(self.srv_manager.full_srv_list)):
            srv_queue_arr = self.y_list[i]
            srv_port = self.srv_manager.full_srv_list[i].srv_port
            ax.plot (self.x_list, srv_queue_arr, label=str(srv_port))
        plt.legend (loc='upper left')
        fig.savefig(os.path.join(self.res_path, "srv_resp_time.png"))


class QueueLenData(DataCollector):
    def __init__(self, mgr, res_path):
        super ().__init__ (mgr, res_path)
        filename = os.path.join(self.res_path, "queues.txt")
        self.f = open (filename, "a")


        # Create an empty list of each server
        for i in range(len(self.srv_manager.full_srv_list)):
            self.y_list.append([]*0)

    def collect_data(self):
        """
        The queue len data is event metric driven, and therefore called periodically from the "collect_data": thread
        :return:
        """
        self.counter += 1
        self.x_list.append(self.counter*data_collection_interval) # add the x axis (currently counter) element
        line = str(self.counter) # start a line string for the csv record
        for i in range (0, len (self.srv_manager.full_srv_list)):
            server = self.srv_manager.full_srv_list[i]
            line = line + "," + str(server.current_running_tasks) # append a value to the csv line
            self.y_list[i].append(server.current_running_tasks) # append the queue length calue to the server's array
        self.f.write(line + "\n") # write the csv line to the file

    def print_data(self):
        print ("X axis: " + str(self.x_list))
        for i in range(0,len(self.srv_manager.full_srv_list)):
            print ("Y axis for     ", str(self.srv_manager.full_srv_list[i].srv_port), ": ", str (self.y_list[i]))

            # For debug, print also the queue length measured in client side
            print ("server version ", str (self.srv_manager.full_srv_list[i].srv_port), ": ",
                   str (self.srv_manager.full_srv_list[i].response_tasks_queue_list))
            print ("client version ", str (self.srv_manager.full_srv_list[i].srv_port), ": ",
                   str (self.srv_manager.full_srv_list[i].request_tasks_queue_list))

    def plot_data(self):
        fig, ax = plt.subplots (figsize=(30,15))

        ax.set (xlabel='Time(seconds)', ylabel='Queue Length',
                title='Server Queue Length by Time')
        ax.grid ()

        for i in range(len(self.srv_manager.full_srv_list)):
            srv_queue_arr = self.y_list[i]
            srv_port = self.srv_manager.full_srv_list[i].srv_port
            ax.plot (self.x_list, srv_queue_arr, label=str(srv_port))
        plt.legend (loc='upper right')
        fig.savefig(os.path.join(self.res_path, "srv_queue.png"))


class DataCollectionManager:
    def __init__(self, mgr):
        ts = time.time()
        self.srv_manager: ServerManager = mgr

        # Create folder for all the results
        self.res_path = os.path.join(os.getcwd(), "results", str(ts))
        os.makedirs(self.res_path)

        # Create a class of queue length data
        self.queue_len_data = QueueLenData(mgr, self.res_path)
        self.response_duration_data = ResponseDurationData(mgr, self.res_path)

    def collect_data(self):
        self.queue_len_data.collect_data()

    def simulation_finished(self):
        self.response_duration_data.collect_data()
        self.queue_len_data.simulation_finished()
        self.response_duration_data.simulation_finished()



def collect_data(data_collector):
    while True:
        time.sleep (data_collection_interval)
        data_collector.collect_data()
        if is_simulation_finished():
            data_collector.simulation_finished()
            break

