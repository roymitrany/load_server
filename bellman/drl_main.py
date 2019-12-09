from bellman.solve_ql import QBellman
import torch
import numpy as np
import bellman.my_dqn as my_dqn





gamma = 0.02
numQ = 5
mxQ = 5
act_arr = (numQ+1)*2 #+1 for rejection
act_srv = 2
in_actions = (act_arr, act_srv)
arr_rate = 15
srv_rate = 7
dpl_rate = 3
build_cost = 5
reward = 100
reject = 100
destroy_cost = 0
hold_cost = 1
delay_pen = [0, 0, 0, 1, 1.1, 1.3, 1.4, 1.5]



myQL = QBellman(gamma, numQ, mxQ, None, in_actions)
myQL.set_Rates( arr_rate, srv_rate, dpl_rate, gamma)
myQL.set_Costs(reward, reject, destroy_cost, hold_cost, build_cost)
myQL.set_delayP(delay_pen)

print(myQL)

myQL.make_IndexMappingTable()

numit = 15000

err_func = torch.nn.L1Loss()
for it in range(numit):
    myQL.run_BE()
    if it%1000 == 0:
        print(".", end='')
    #print(myQL.States.mean())
print()


# myQL.make_plot()
myQL.print_pol()
myQL.save_pol("pie_file")
exit(0)

if (a==0):
    s = np.zeros([myQL.NumQueues], dtype='i4')
    [rw,n_t, a_p]=myQL.run_Step(s)
    N=10000
    Ar = myQL.run_Long_Sim( N)
    print(Ar)
#####################################################
######### Starting Initalizing the Aggregation #####
#####################################################
learning_cycles=1
steps_percycle=5000
learning_rate=0.9
myQL.init_Agg_MDP()
s=np.zeros([myQL.NumQueues],dtype='i4')
# myQL.Make_step_agg(s,0)
myQL.Learn_nCycles(learning_cycles,steps_percycle,learning_rate)
#myQL.Learn_withPol_agg(10000)
Avg_Agg_rw=myQL.run_Long_Sim_agg(10000)
#myQL.make_plot_agg()
#myQL.make_plot()
a=2

#####################################################
######### Starting Initalizing the Deep Network #####
#####################################################

TRi = my_dqn.tripleDQN()
n_per_layerArr = np.zeros(2, dtype=int)
n_per_layerArr[0] = (numQ+1)*(mxQ+2)
n_per_layerArr[1] = numQ*mxQ
n_inputsArr = numQ
total_lrsArr = 3
n_outputsArr = (numQ + 1) * 2

n_per_layerSrv = np.zeros(2, dtype=int)
n_per_layerSrv[0] = numQ*(mxQ+2)
n_per_layerSrv[1] = numQ*mxQ
n_inputsSrv = numQ
total_lrsSrv = 3
n_outputsSrv = (numQ) * 2

n_per_layerDpl = np.zeros(2, dtype=int)
n_per_layerDpl[0] = numQ*(mxQ+2)
n_per_layerDpl[1] = numQ*mxQ
n_inputsDpl = numQ
total_lrsDpl = 3
n_outputsDpl = 1
lr=0.1

TRi.ArrNet = my_dqn.ArrDQN(n_per_layerArr, total_lrsArr, n_inputsArr, n_outputsArr,lr)
TRi.SrvNet = my_dqn.SrvDQN(n_per_layerSrv, total_lrsSrv, total_lrsSrv, n_outputsSrv,lr)
TRi.DplNet = my_dqn.DplDQN(n_per_layerDpl,total_lrsDpl, n_inputsDpl, n_outputsDpl,lr)

TRi.QB = QBellman(gamma, numQ, mxQ, None, in_actions)
TRi.QB.set_Rates( arr_rate, srv_rate, dpl_rate, gamma)
TRi.QB.set_Costs(reward, reject, destroy_cost, hold_cost, build_cost)
TRi.QB.set_delayP(delay_pen)

TRi.QB.set_Qval()

TRi.TripleStep((0,0,0,0), 10)

a=2





