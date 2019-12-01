import bellman.solve_ql as solve_ql
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim


#################################
########### Arrived-Net ###########
class ArrDQN(nn.Module):
    def __init__(self,n_neurons_per_layers, n_layers, n_inputs, n_outputs, lr):
        super(ArrDQN, self).__init__()
        self.nLayers = n_layers
        self.nInputs = n_inputs
        self.nOutputs = n_outputs
        self.nNperL = n_neurons_per_layers
        self.fcArr1 = nn.Linear(in_features=self.nInputs, out_features=self.nNperL[0], bias=True)
        self.fcArr2 = nn.Linear(in_features=self.nNperL[0], out_features=self.nNperL[1], bias=True)
        self.fcArr3 = nn.Linear(in_features=self.nNperL[1], out_features=self.nOutputs, bias=True)

        self.loss_funcA = torch.nn.MSELoss(size_average=True)
        self.lr_arr = lr
        optimizerA = optim.SGD(self.parameters(), lr=self.lr_arr)
        optimizerA.zero_grad()

    def forward(self, inp):
            lA1 = self.fcArr1(inp)
            l1out = F.sigmoid(lA1)
            # l1out = F.relu(l1)
            l2 = self.fcArr2(l1out)
            l2out = F.sigmoid(l2)

            l3 = self.fcArr3(l2out)
            l33 = F.relu(l3)
            # l22 = F.sigmoid(l2)
            myp = F.sigmoid(l33)
            return myp

    def __repr__(self):
            return 'The Arr DQN structure contents: \n' + \
                   super(ArrDQN, self).__repr__() + \
                   'weights1: \n' + self.fcArr1.weight.__str__() + \
                   'weights2: \n' + self.fcArr2.weight.__str__() + \
                   'weights3: \n' + self.fcArr3.weight.__str__()
            # super(nn.Linear, self).__repr__()

#################################
########### Served-Net###########
class SrvDQN(nn.Module):
    def __init__(self,n_neurons_per_layers, n_layers, n_inputs, n_outputs, lr):
        super(SrvDQN, self).__init__()
        self.nLayers = n_layers
        self.nInputs = n_inputs
        self.nOutputs = n_outputs
        self.nNperL = n_neurons_per_layers
        self.fcSrv1 = nn.Linear(in_features=self.nInputs, out_features=self.nNperL[0], bias=True)
        self.fcSrv2 = nn.Linear(in_features=self.nNperL[0], out_features=self.nNperL[1], bias=True)
        self.fcSrv3 = nn.Linear(in_features=self.nNperL[1], out_features=self.nOutputs, bias=True)

        self.loss_funcS = torch.nn.MSELoss(size_average=True)
        self.lr_srv = lr
        optimizerS = optim.SGD(self.parameters(), lr=self.lr_srv)
        optimizerS.zero_grad()

    def forward(self, inp):
        lS1 = self.fcSrv1(inp)
        l1out = F.sigmoid(lS1)
        # l1out = F.relu(l1)
        l2 = self.fcSrv2(l1out)
        l2out = F.sigmoid(l2)

        l3 = self.fcSrv3(l2out)
        l33 = F.relu(l3)
        # l22 = F.sigmoid(l2)
        srv_dec = F.sigmoid(l33)
        return srv_dec

#################################
########### Deploy-Net###########
class DplDQN(nn.Module):
    def __init__(self,n_neurons_per_layers, n_layers, n_inputs, n_outputs, lr):
        super(DplDQN, self).__init__()
        self.nLayers = n_layers
        self.nInputs = n_inputs
        self.nOutputs = n_outputs
        self.nNperL = n_neurons_per_layers
        self.fcDpl1 = nn.Linear(in_features=self.nInputs, out_features=self.nNperL[0], bias=True)
        self.fcDpl2 = nn.Linear(in_features=self.nNperL[0], out_features=self.nNperL[1], bias=True)
        self.fcDpl3 = nn.Linear(in_features=self.nNperL[1], out_features=self.nOutputs, bias=True)

        self.loss_funcA = torch.nn.MSELoss(size_average=True)
        self.lr_dpl = lr
        optimizerA = optim.SGD(self.parameters(), lr=self.lr_dpl)
        optimizerA.zero_grad()

    def forward(self, inp):
        lS1 = self.fcDpl1(inp)
        l1out = F.sigmoid(lS1)
        # l1out = F.relu(l1)
        l2 = self.fcDpl2(l1out)
        l2out = F.sigmoid(l2)

        l3 = self.fcDpl3(l2out)
        l33 = F.relu(l3)
        # l22 = F.sigmoid(l2)
        srv_dec = F.sigmoid(l33)
        return srv_dec


def _make_pdf(s_ql: solve_ql, in_state):
    return s_ql._make_pdf(in_state)


class tripleDQN():
    def __init__(self):
        super(tripleDQN, self).__init__()


        # self.fc1 = nn.Linear(in_features=12 * 4 * 4, out_features=120)

        # self.myInp = myRegInput(ns)
        # self.out = nn.Linear(in_features=60, out_features=10)
        self.ArrNet = None
        self.SrvNet = None
        self.DplNet = None


        self.QB = None

    def TripleStep(self, init_state, prev_rw, prev_act_pol):

        # REMINDER:
        # self.Q_dpl = torch.Tensor(self.num_states)
        # self.Q_arr = torch.Tensor(self.arr_actions, self.num_states)
        # self.Q_srv = torch.Tensor(self.NumQueues, self.srv_actions, self.num_states)

        init_state_ix = solve_ql.QBellman.give_ix(init_state, self.QB.num_states_tuple)
        [rw, nxt_st,  act_pol] = self.QB.run_Step(init_state)

        Qarr_netOut = self.ArrNet(torch.Tensor(nxt_st))
        Qsrv_netOut = self.SrvNet(torch.Tensor(nxt_st))
        Qdpl_netOut = self.DplNet(torch.Tensor(nxt_st))
        srv_rates, dpl_rates = self.QB.get_Rates_NStates(init_state)
        QVAL_nxt_st = self.QB.calc_Qvalue( prev_rw, Qarr_netOut, Qsrv_netOut, Qdpl_netOut, init_state, srv_rates, dpl_rates)


        if (prev_act_pol[0] == self.QB.doArr):
            self.QB.Q_arr[prev_act_pol[1],init_state_ix] = QVAL_nxt_st
        elif (prev_act_pol[0] < self.QB.doSrv):
            self.QB.Q_srv[prev_act_pol[1],init_state_ix] = QVAL_nxt_st
        else:
            self.QB.Q_dpl[prev_act_pol[1]] = QVAL_nxt_st
            rw = 0
        #my_pred = myr(inp.allInputs[:, i])
        #my_loss = loss_func(my_pred, inp.allDetailedLabels[i, :])
        #my_optimizer.zero_grad()
        #my_loss.backward()

        #my_optimizer.step()
        #print(my_loss.item())
        #loss_track[i] = my_loss.item()
        #mylr = adjust_learning_rate(my_optimizer, mylr)

        return nxt_st,act_pol,rw


    def __repr__(self):
            return 'The general DQN structure contents: Type print of the contents to see them\n' #+ \
                 #  super(firstDQN, self).__repr__() + \
                 #  'weights1: \n' + self.fc1.weight.__str__() + \
                 #  'weights2: \n' + self.fc2.weight.__str__() + \
                 #  'weights3: \n' + self.fc3.weight.__str__()
            # super(nn.Linear, self).__repr__()


def adjust_learning_rate(optimizer, mlr):
        """Sets the learning rate to the initial LR decayed by 10 every 30 epochs"""
        lr = mlr * 0.9995  # (0.1 ** (epoch // 30))
        for param_group in optimizer.param_groups:
            param_group['lr'] = lr
        return lr

