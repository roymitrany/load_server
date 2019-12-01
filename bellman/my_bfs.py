# Code in file tensor/two_layer_net_numpy.py
import numpy as np

# N is batch size; D_in is input dimension;
# H is hidden dimension; D_out is output dimension.
class myNode():
    def __init__(self, mid):
        self.mid = mid
        self.nbors = []
        self.num_nbors = 0

    def add_n(self, mid):
        if isinstance(mid, myNode):
            self.nbors.append(mid)
        else:
            self.nbors.append(myNode(mid))
        self.num_nbors += 1

    def __repr__(self):
        str = self.mid.__str__() + ': Neighbors are: '
        if self.nbors:
            for item in self.nbors:
                str = str+(item.mid.__str__())
            str = str + 'total is ' + self.num_nbors.__str__()
            return str
        else:
            return(self.mid.__str__() + ': No neighbors\n')

class myGraph():
    def __init__(self):
        self.verts = []
        self.ids = np.array([])

    def check_presence(self, isid):
        return np.any(self.ids == isid)

    def add_v(self, mid):
        if isinstance(mid, myNode):
            if not self.check_presence(mid.mid):
                self.verts.append(mid)
                self.ids = np.resize(self.ids, [self.ids.size+1])
                self.ids[-1] = mid.mid
            else:
                print("This id already present in graph")

        else:
            if not self.check_presence(mid):
                self.verts.append(myNode(mid))
                self.ids = np.resize(self.ids, [self.ids.size + 1])
                self.ids[-1] = mid
            else:
                print("This id already present in graph")

    def find_ix(self, mid):
        if isinstance(mid, myNode):
            l_id = mid.mid
        else:
            l_id = mid
        j = 0
        for item in self.verts:
            if item.mid == l_id:
                return j
            j += 1
        return -1


    def add_e(self, id1, id2):
        ix1 = self.find_ix(id1)
        ix2 = self.find_ix(id2)
        if (ix1 > -1) & (ix2 > -1):
            self.verts[ix1].add_n(id2)
            self.verts[ix2].add_n(id1)
        else:
            print("node(s) do not exist")

    def print_myg(self):
        for item in self.verts:
            print(item)

mg1 = myGraph()

mg1.add_v(12)
mg1.add_v(14)
mnd = myNode(52)
mg1.add_v(mnd)
mg1.add_e(12, 14)
mg1.add_e(52, 14)
# print(mnd)
mg1.print_myg()


