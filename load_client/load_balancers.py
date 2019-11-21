'''
Load balancer classes.
We will define an abstract class, and then some types of LB such as random, round robin, optimal etc.
Mark's LB algorithm will be added right here.
'''
from abc import ABC, abstractmethod
import random

from load_client.servers_management import ServerManager


class BasicLB(ABC):
    def __init__(self, initial_num_of_servers):
        assert isinstance (initial_num_of_servers, int)
        self.num_of_servers = initial_num_of_servers
        print ("init basic class!!")

    @abstractmethod
    def pick_server(self, srv_mgr:ServerManager):
        pass


class RandomLB(BasicLB):
    def pick_server(self, srv_mgr:ServerManager):
        return random.randint(0, len(srv_mgr.available_servers_list)-1)

class RoundRobinLB(BasicLB):
    curr_srv:int=0
    def pick_server(self, srv_mgr:ServerManager):
        self.curr_srv += 1
        if self.curr_srv>=self.num_of_servers:
            self.curr_srv=0
        return self.curr_srv
