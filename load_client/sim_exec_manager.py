import random
from time import sleep

from load_client.auto_scaler import DumbAS, BasicAS, ThresholdAS
from load_client.data_collector import DataCollectionManager, collect_data
from load_client.load_balancers import JsqLB, BasicLB
from load_client.request_generator import RequestGenerator
from load_client.servers_management import ServerManager


class SimulationParams:
    # Force to specify the params in object construction
    def __init__(self, num_of_tasks=0, avg_load_level=0, initial_num_of_servers=0, average_rate=0.0, server_startup_time=0):
        self.num_of_tasks = num_of_tasks
        self.avg_load_level = avg_load_level
        self.initial_num_of_servers = initial_num_of_servers
        self.average_rate = average_rate
        self.server_startup_time = server_startup_time


class SimExecManager:
    data_collector:DataCollectionManager
    srv_mgr:ServerManager
    lb_obj:BasicLB
    as_obj:BasicAS
    tasks_completed:int
    def __init__(self, sim_params:SimulationParams):
        # the number of tasks to be completed before we stop the test
        self.simulation_params = sim_params
        # Number of the tasks that were completed (not sure if we will ever use it)
        self.tasks_completed = 0

        # Number of rejected tasks (due to full servers)
        self.num_of_rejections = 0

        # Index for the request (not sure if we will ever use it)
        self.tasks_global_index = 0

        # Indicator that simulation is finished (in order to stop data collection
        self.simulation_finished = False

        self.srv_mgr = ServerManager(self, sim_params.initial_num_of_servers)
        self.lb_obj = JsqLB (self.srv_mgr) # TODO find an intelligent way to get the lb and as classes as parameters
        #self.as_obj = DumbAS(self.srv_mgr)
        self.as_obj = ThresholdAS(self.srv_mgr)

        self.data_collector = DataCollectionManager(self)
        self.request_generator = RequestGenerator()


    def get_num_of_completed_tasks(self):
        return self.tasks_completed

    def inc_num_of_completed_tasks(self):
        self.tasks_completed += 1


    def get_num_of_rejections(self):
        return self.num_of_rejections

    def inc_num_of_rejections(self):
        self.num_of_rejections += 1


    def get_tasks_global_index(self):
        return self.tasks_global_index

    def inc_tasks_global_index(self):
        self.tasks_global_index += 1


    def is_simulation_finished(self):
        return self.simulation_finished

    def set_simulation_finished(self):
        self.simulation_finished = True

    def run_simulation(self):
        # Loop for generating requests
        for i in range (self.simulation_params.num_of_tasks):
            time_to_sleep = random.expovariate (
                self.simulation_params.average_rate)  # TODO: take the timing from an external time generator
            sleep (time_to_sleep)
            print ("------------after sleeping " + str (time_to_sleep) + " Task no. " + str (i))
            self.request_generator.generate_request (self)

        # wait until all responses arrive back
        for server in self.srv_mgr.full_srv_list:
            server.response_thread.join ()

        self.set_simulation_finished ()


# Initialize the server manager first, everything depends on it


# Create the server management singleton object
#pie_parser = PieDataParser("pie_file")
#lb_obj = BellmanLB (srv_mgr, pie_parser)
#global_vars.lb_obj = JsqLB (global_vars.srv_mgr)
#lb_obj = RandomLB (srv_mgr)
#as_obj = ThresholdAS(srv_mgr)
#global_vars.as_obj = DumbAS()
#as_obj = BellmanAS(srv_mgr, pie_parser)



sim_params = SimulationParams(num_of_tasks=100, avg_load_level=7, initial_num_of_servers=5, average_rate=3.6, server_startup_time=2)
s=SimExecManager(sim_params)
s.run_simulation()




exit(0)
