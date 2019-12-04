from typing import Dict, List

class CostCalculator:
    def __init__(self):
        self.completion_times  = Dict[int, int]
        self.timeouts = 0
        self.rejections = 0
        self.server_startups = 0
        self.server_shutdowns = 0
        self.curr_num_of_servers = List[int]

    def calculate_cost(self):
        val = self.timeouts*1000 + self.server_startups*1000 + self.server_shutdowns*1000 + self.rejections *2000
        return val # TODO: loop on lists and add values
        # TODO: All multipliers should be imported from global vars