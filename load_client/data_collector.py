import time
import os
from pathlib import Path
from typing import List

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

from load_client.global_vars import is_simulation_finished, data_collection_interval
from load_client.servers_management import ServerManager, Server

class QueueLenData:
    def __init__(self, mgr, res_path):
        self.srv_manager: ServerManager = mgr
        self.res_path:str = res_path
        self.x_list: List[int] = []
        self.y_list: List[List[int]] = []
        filename = os.path.join(self.res_path, "queues.txt")
        self.f = open (filename, "a")


        # Create an empty list of each server
        for i in range(len(self.srv_manager.full_srv_list)):
            self.y_list.append([]*0)

    def collect_data(self, counter:int):
        self.x_list.append(counter*data_collection_interval) # add the x axis (currently counter) element
        line = str(counter) # start a line string for the csv record
        for i in range (0, len (self.srv_manager.full_srv_list)):
            server = self.srv_manager.full_srv_list[i]
            line = line + "," + str(server.current_running_tasks) # append a value to the csv line
            self.y_list[i].append(server.current_running_tasks) # append the queue length calue to the server's array
        self.f.write(line + "\n") # write the csv line to the file

    def print_data(self):
        print ("X axis: " + str(self.x_list))
        for i in range(0,len(self.srv_manager.full_srv_list)):
            print ("Y axis for ", str(self.srv_manager.full_srv_list[i].srv_port), ": ", str (self.y_list[i]))

    def plot_data(self):
        fig, ax = plt.subplots ()

        ax.set (xlabel='Time(seconds)', ylabel='Queue Length',
                title='Server Queue Length by Time')

        for i in range(len(self.srv_manager.full_srv_list)):
            srv_queue_arr = self.y_list[i]
            srv_port = self.srv_manager.full_srv_list[i].srv_port
            ax.plot (self.x_list, srv_queue_arr, label=str(srv_port))
        plt.legend (loc='upper right')
        fig.savefig(os.path.join(self.res_path, "srv_queue.png"))

    def simulation_finished(self):
        self.f.close()
        self.print_data()
        self.plot_data()


class DataCollector:
    def __init__(self, mgr):
        ts = time.time()
        self.srv_manager: ServerManager = mgr

        # Create folder for all the results
        self.res_path = os.path.join(os.getcwd(), "results", str(ts))
        os.makedirs(self.res_path)

        # Create a class of queue length data
        self.queue_len_data = QueueLenData(mgr, self.res_path)

    def collect_data(self, counter:int):
        self.queue_len_data.collect_data(counter)

    def simulation_finished(self):
        self.queue_len_data.simulation_finished()


def collect_data(data_collector):
    counter = 1
    while True:
        time.sleep (data_collection_interval)
        data_collector.collect_data(counter)
        counter += 1
        if is_simulation_finished():
            data_collector.simulation_finished()
            break

