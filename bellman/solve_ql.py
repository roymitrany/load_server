import torch
import numpy as np

from matplotlib import pyplot as plt



class QBellman:
    def __init__(self, gamma, nq, mxq, in_states=None, in_actions=None):
        # in_states, in_actions - tuples of numpy.array type
        # self.StateActions = torch.tensor()
        if in_states == None:
            statesperQ= mxq + 3
            self.num_states_tuple = (nq) * (statesperQ,)
        else:
            self.num_states_tuple = in_states

        self.in_actions = in_actions
        self.arr_actions = in_actions[0]
        self.srv_actions = in_actions[1]

        self.gamma = gamma
        self.NumQueues = nq
        self.MaxQsize = mxq
        # constant for random action
        self.numEvents = self.NumQueues * 2 + 1
        self.doArr = self.NumQueues * 2
        self.doSrv = self.NumQueues

        self.num_states = (self.MaxQsize+3)**self.NumQueues

        # self.NextStateMapping = np.zeros((self.num_actions, self.num_states,  self.num_states), dtype=np.int32)

        self.TransitionsP_Arr = np.zeros([self.arr_actions, self.num_states])
        self.TransitionsP_Srv = np.zeros([self.NumQueues, self.srv_actions, self.num_states])
        self.TP_Srv_effRates_T = torch.Tensor(self.NumQueues, self.num_states)

        self.TransitionsP_Dpl = np.zeros([self.NumQueues, self.num_states])
        self.TP_Dpl_effRates_T = torch.Tensor(self.NumQueues, self.num_states)

        self.delta_T = torch.Tensor(self.num_states)
        self.CostState_T = torch.Tensor(self.num_states)
        self.TransitionsP_Arr[:, :] = 0
        self.TransitionsP_Srv[:, :, :] = 0
        self.TransitionsP_Dpl[:, :] = 0

        self.TP_Srv_effRates_T[:, :] = 0
        self.TP_Dpl_effRates_T[:, :] = 0

        self.States = torch.Tensor(self.num_states)
        self.States[:] = -100
        self.Rewards_T = torch.Tensor(self.arr_actions, self.num_states)

        self.Pol = np.zeros([self.num_states, self.NumQueues + 2])

        self.Q_dpl = None
        self.Q_arr = None
        self.Q_srv = None

        self.ARR = 1
        self.SRV = 2

        self.IDLE = 0   # -2
        self.DEPLOYING = 1   # -1
        self.FULL = self.MaxQsize+2
        self.EMPTY = 2   # 0
        # for MaxQsize =3: ix0 = -2, ix1 =-1, ix2= 0 (empty), ix3 =1, ix4 =2, ix5 =3 (FULL)
        self.err_func = torch.nn.L1Loss(size_average=True)
        self.LastErr = 100000

        self.arr_rate = None
        self.srv_rate = None
        self.deploy_rate = None
        self.gamma = None
        self.all_rates = np.zeros([self.NumQueues * 2 + 1])

        self.init_Agg_MDP()

    #################--End Init--##################################
    ###################################################


    def init_Agg_MDP(self):
        self.mx_Idle_agg = self.MaxQsize
        self.mx_Full_agg = self.MaxQsize
        self.mx_Dpl_agg = self.MaxQsize
        self.mx_Low_agg = self.MaxQsize
        self.mx_Hi_agg = self.MaxQsize
        self.mx_Emp_agg = self.MaxQsize
        self.th_Low_agg = self.EMPTY+1
        self.th_Hi_agg = self.FULL-1
        self.ixI = 0  # idle

        self.ixD = 1
        self.ixL = 2
        self.ixH = 3

        self.ixE = 4
        self.ixF = 4

        self.agg_tuple_sz = 4

        self.agg_num_tuple = (self.agg_tuple_sz) * ((self.NumQueues+1),)
        self.num_st_agg = (self.NumQueues + 1) ** self.agg_tuple_sz

        self.num_arr_actions_agg = 8
        self.polH_YD = 0
        self.polH_ND = 1
        self.polL_YD = 2
        self.polL_ND = 3
        self.polM_YD = 4
        self.polM_ND = 5
        self.polR_YD = 6
        self.polR_ND = 7
        self.num_srv_actions_agg = 2

        self.TArr_ix_act_ix_agg = torch.zeros(self.num_st_agg, self.num_arr_actions_agg, self.num_st_agg,dtype=torch.float32)
        self.TArr_count_agg= np.zeros([self.num_st_agg, self.num_arr_actions_agg, self.num_st_agg],'f4')
        self.TSrv_ix_act_ix_agg = torch.zeros(self.num_st_agg, self.num_srv_actions_agg, self.num_st_agg,dtype=torch.float32)
        self.TSrv_count_agg = np.zeros([self.num_st_agg, self.num_srv_actions_agg, self.num_st_agg], 'f4')
        self.TDpl_ix_ix_agg = torch.zeros(self.num_st_agg,  self.num_st_agg,dtype=torch.float32)
        self.TDpl_count_agg = np.zeros([self.num_st_agg, self.num_st_agg], 'f4')

        self.Vagg = torch.ones(1,self.num_st_agg,dtype=torch.float32)
        self.delta_agg = torch.zeros(1,self.num_st_agg,dtype=torch.float32)
        self.miu_agg = torch.zeros(1,self.num_st_agg,dtype=torch.float32)
        self.zeta_agg = torch.zeros(1,self.num_st_agg,dtype=torch.float32)
        self.miu_agg_cnt = torch.zeros(1,self.num_st_agg,dtype=torch.float32)
        self.zeta_agg_cnt = torch.zeros(1,self.num_st_agg,dtype=torch.float32)
        self.RWarr_Agg = torch.zeros(self.num_arr_actions_agg,self.num_st_agg,dtype=torch.float32)
        self.RWarr_Agg_cnt = torch.zeros(self.num_arr_actions_agg,self.num_st_agg ,dtype=torch.float32)
        self.RWsrv_Agg = torch.zeros(self.num_srv_actions_agg,self.num_st_agg,dtype=torch.float32)
        self.RWsrv_Agg_cnt = torch.zeros(self.num_srv_actions_agg, self.num_st_agg,dtype=torch.float32)

        self.RW_hold_Agg = torch.zeros(1,self.num_st_agg,dtype=torch.float32)
        self.RW_hold_Agg_cnt = torch.zeros(1,self.num_st_agg,dtype=torch.float32)

        self.PolA_agg = np.zeros([1,self.num_st_agg],'i4')
        self.PolS_agg = np.zeros([1, self.num_st_agg],'i4')

    def _Zero_Agg_Arrays(self):
        self.TArr_ix_act_ix_agg = torch.zeros(self.num_st_agg, self.num_arr_actions_agg, self.num_st_agg,dtype=torch.float32)
        self.TArr_count_agg = np.zeros([self.num_st_agg, self.num_arr_actions_agg, self.num_st_agg], dtype='f4')
        self.TSrv_ix_act_ix_agg = torch.zeros(self.num_st_agg, self.num_srv_actions_agg, self.num_st_agg,dtype=torch.float32)
        self.TSrv_count_agg = np.zeros([self.num_st_agg, self.num_srv_actions_agg, self.num_st_agg], dtype='f4')
        self.TDpl_ix_ix_agg = torch.zeros(self.num_st_agg, self.num_st_agg,dtype=torch.float32)
        self.TDpl_count_agg = np.zeros([self.num_st_agg, self.num_st_agg],dtype='f4')

        self.delta_agg = torch.zeros(1, self.num_st_agg,dtype=torch.float32)
        self.miu_agg = torch.zeros(1, self.num_st_agg,dtype=torch.float32)
        self.zeta_agg = torch.zeros(1, self.num_st_agg,dtype=torch.float32)
        self.miu_agg_cnt = torch.zeros(1, self.num_st_agg,dtype=torch.float32)
        self.zeta_agg_cnt = torch.zeros(1, self.num_st_agg,dtype=torch.float32)
        self.RWarr_Agg = torch.zeros(self.num_arr_actions_agg, self.num_st_agg)
        self.RWarr_Agg_cnt = torch.zeros(self.num_arr_actions_agg, self.num_st_agg,dtype=torch.float32)
        self.RWsrv_Agg = torch.zeros(self.num_srv_actions_agg, self.num_st_agg,dtype=torch.float32)
        self.RWsrv_Agg_cnt = torch.zeros(self.num_srv_actions_agg, self.num_st_agg,dtype=torch.float32)

        self.RW_hold_Agg = torch.zeros(1, self.num_st_agg,dtype=torch.float32)
        self.RW_hold_Agg_cnt = torch.zeros(1, self.num_st_agg,dtype=torch.float32)



    def transate_det2agg(self, in_ag_tuple):
        tmp_d = np.array(in_ag_tuple)
        agg = np.zeros(self.agg_tuple_sz, dtype=int)

        agg[self.ixI] = np.sum(tmp_d == self.IDLE)
        agg[self.ixD] = np.sum(tmp_d == self.DEPLOYING)
        # agg[self.ixE] = np.sum(tmp_d == self.IDLE)
        agg[self.ixL] = np.sum((tmp_d >= self.EMPTY)&(tmp_d < self.th_Low_agg))
        agg[self.ixH] = np.sum((tmp_d < self.FULL)&(tmp_d >= self.th_Hi_agg))

        return agg
    
    def _find_Hq(self, in_st_arr):
        whereto = np.where((in_st_arr < self.FULL) & (in_st_arr >= self.th_Hi_agg))
        whereto_a = np.array(whereto)
        if (whereto_a.size > 0):
            return whereto_a[0,0]
        else:
            return None

    def _find_Lq(self, in_st_arr):
        whereto = np.where((in_st_arr >= self.EMPTY) & (in_st_arr < self.th_Low_agg))
        whereto_a = np.array(whereto)
        if (whereto_a.size > 0):
            return whereto_a[0,0]
        else:
            return None

    def _find_Mq(self, in_st_arr):
        whereto = np.where((in_st_arr < self.th_Hi_agg) & (in_st_arr >= self.th_Low_agg))
        whereto_a = np.array(whereto)
        if (whereto_a.size > 0):
            return whereto_a[0,0]
        else:
            return None

    def _find_numEmpty(self, in_st_arr):
        whereto = np.where(in_st_arr == self.EMPTY)
        whereto_a = np.array(whereto)
        if (whereto_a.size > 0):
            return sum(sum(whereto_a))
        else:
            return 0

    def SchedHorR_agg(self, in_st_tuple, d_new):
        # sched_type = Low, Empty or reject if no place
        # in_ag_arr = np.array(in_ag_tuple)
        # d_new - deploy or not a new queue
        in_st_arr = np.array(in_st_tuple)

        whereto = self._find_Hq(in_st_arr)
        if (whereto != None):
            in_st_arr[whereto] += 1
            rw = self.c_rw
        else:
            rw = -self.c_rj
        # in_ag_arr = self.transate_det2agg(in_st_arr)
        if d_new==1:
            new_q = self._have_IdleQ(in_st_arr)
            if (new_q!=None):
                in_st_arr[new_q]=self.DEPLOYING
                rw -= self.c_build


        return in_st_arr,rw

    def SchedLorR_agg(self, in_st_tuple, d_new):
        # sched_type = Low, Empty or reject if no place
        # in_ag_arr = np.array(in_ag_tuple)
        in_st_arr = np.array(in_st_tuple)

        whereto = self._find_Lq(in_st_arr)
        if (whereto != None):
            in_st_arr[whereto] += 1
            rw = self.c_rw
        else:
            rw = -self.c_rj
        # in_ag_arr = self.transate_det2agg(in_st_arr)
        if d_new==1:
            new_q = self._have_IdleQ(in_st_arr)
            if (new_q!=None):
                in_st_arr[new_q]=self.DEPLOYING
                rw -= self.c_build

        return in_st_arr,rw

    def SchedMorR_agg(self, in_st_tuple, d_new):
        # sched_type = Low, Empty or reject if no place
        # in_ag_arr = np.array(in_ag_tuple)
        in_st_arr = np.array(in_st_tuple)

        whereto = self._find_Mq(in_st_arr)
        if (whereto != None):
            in_st_arr[whereto] += 1
            rw = self.c_rw
        else:
            rw = -self.c_rj
        # in_ag_arr = self.transate_det2agg(in_st_arr)
        if d_new == 1:
            new_q = self._have_IdleQ(in_st_arr)
            if (new_q != None):
                in_st_arr[new_q] = self.DEPLOYING
                rw -= self.c_build

        return in_st_arr, rw

    def SchedR_agg(self, in_st_tuple, d_new):
        # sched_type = Low, Empty or reject if no place
        # in_ag_arr = np.array(in_ag_tuple)
        in_st_arr = np.array(in_st_tuple)


        rw = -self.c_rj

        # in_ag_arr = self.transate_det2agg(in_st_arr)
        if d_new==1:
            new_q = self._have_IdleQ(in_st_arr)
            if (new_q!=None):
                in_st_arr[new_q]=self.DEPLOYING
                rw -= self.c_build

        return in_st_arr,rw

    def Dpl_agg(self, in_st_tuple):
        pdf = np.zeros([self.NumQueues])
        nxt_st_arr = np.array((in_st_tuple))
        n=0
        for i in range(self.NumQueues):
            if in_st_tuple[i]==self.DEPLOYING:
                pdf[i]=1
                n += 1
        if n==0:
            here_bug=1
        dpl_q = np.random.choice(np.arange(0, self.NumQueues), p=pdf / n)
        nxt_st_arr[dpl_q] =self.EMPTY


        return [nxt_st_arr,0]

    def Srv_agg(self,in_st_tuple, d_pol):
        pdf=np.zeros([self.NumQueues])
        nxt_st_arr=np.array((in_st_tuple))
        n=0
        rw = 0
        for i in range(self.NumQueues):
            if in_st_tuple[i]>self.EMPTY:
                pdf[i]=1
                n+=1
        if n==0:
            here_bug=1
        served_q=np.random.choice(np.arange(0, self.NumQueues) , p=pdf / n)
        nxt_st_arr[served_q] -= 1
        if nxt_st_arr[served_q] == self.EMPTY:
            if d_pol==1:
                nxt_st_arr[served_q] =self.IDLE
        return [nxt_st_arr, rw]

    def Learn_nCycles(self, ncycles,nsteps,lr):

        egreedy = 0
        for nc in range(ncycles):
            self.Learn_withPol_agg(nsteps, egreedy)

            if (egreedy>0.5):
                n_g=(1-egreedy)*lr
                egreedy = 1- n_g
            else:
                egreedy+=0.1
            self.run_BE_agg(10000)
            self.make_plot_agg()
            self._Zero_Agg_Arrays()
        here=56

    def Learn_withPol_agg(self, nsteps, egreedy):

        curr_st_tuple = np.zeros(self.NumQueues,dtype=int)
        explore = 1
        for i in range(nsteps):
            [nxt_st,rw] = self.Make_step_agg(curr_st_tuple,egreedy,explore)
            curr_st_tuple=nxt_st

        t_sums=self.TArr_count_agg.sum(0)
        for s in range(self.num_st_agg):
            for ar in range(self.num_arr_actions_agg):
                if t_sums[ar,s]>0:
                    self.TArr_ix_act_ix_agg[:, ar, s] = torch.tensor(self.TArr_count_agg[:, ar, s] / t_sums[ar,s])
                else:
                    self.TArr_ix_act_ix_agg[:, ar, s]=0

        t_sums = self.TSrv_count_agg.sum(0)
        for s in range(self.num_st_agg):
            for ar in range(2):
                if t_sums[ar,s] > 0:
                    self.TSrv_ix_act_ix_agg[:, ar, s] = torch.tensor(self.TSrv_count_agg[:, ar, s] / t_sums[ar,s])
                else:
                    self.TSrv_ix_act_ix_agg[:, ar, s] = 0

        t_sums = self.TDpl_count_agg.sum(0)
        for s in range(self.num_st_agg):
            if t_sums[s] > 0:
                self.TDpl_ix_ix_agg[:,s] = torch.tensor(self.TDpl_count_agg[s,:]/t_sums[s])
            else:
                self.TDpl_ix_ix_agg[:, s] = 0

        self.RWsrv_Agg = self.RWsrv_Agg/self.RWsrv_Agg_cnt
        self.RWarr_Agg = self.RWarr_Agg/self.RWarr_Agg_cnt
        self.RW_hold_Agg = self.RW_hold_Agg/self.RW_hold_Agg_cnt

        self.RW_hold_Agg[torch.isinf(self.RW_hold_Agg)] = 0
        self.RW_hold_Agg[torch.isnan(self.RW_hold_Agg)] = 0
        self.RWsrv_Agg[torch.isinf(self.RWsrv_Agg)] = 0
        self.RWarr_Agg[torch.isinf(self.RWarr_Agg)] = 0
        self.RWsrv_Agg[torch.isnan(self.RWsrv_Agg)] = 0
        self.RWarr_Agg[torch.isnan(self.RWarr_Agg)] = 0

        self.zeta_agg = self.zeta_agg/self.zeta_agg_cnt
        self.miu_agg = self.miu_agg/self.miu_agg_cnt
        self.zeta_agg[torch.isinf(self.zeta_agg)] = 0
        self.miu_agg[torch.isinf(self.miu_agg)] = 0
        self.zeta_agg[torch.isnan(self.zeta_agg)] = 0
        self.miu_agg[torch.isnan(self.miu_agg)] = 0
        self.delta_agg = 1/(self.zeta_agg+self.miu_agg+self.arr_rate+self.gamma)
        self.delta_agg[torch.isinf(self.delta_agg)] = 0
        self.delta_agg[torch.isnan(self.delta_agg)] = 0



    def _make_pdf_agg(self,in_st_tuple):
        # REMINDERS:
        # self.miu_agg = torch.Tensor(self.num_st_agg)
        # self.zeta_agg = torch.Tensor(self.num_st_agg)
        # self.RWarr_Agg = torch.Tensor(self.num_st_agg, self.num_arr_actions_agg)
        # self.RWsrv_Agg = torch.Tensor(self.num_st_agg, self.num_srv_actions_agg)
        # self.RW_hold_Agg = torch.Tensor(self.num_st_agg)
        p = np.zeros([3])
        for i in range(self.NumQueues):
            if in_st_tuple[i]>self.EMPTY:
                p[1]+=self.srv_rate
            elif (in_st_tuple[i]==self.DEPLOYING):
                p[2]+=self.deploy_rate
        in_st_ix=self.give_ix(in_st_tuple,self.num_states_tuple)
        in_st_agg=self.transate_det2agg(in_st_tuple)
        inst_agg_ix = np.ravel_multi_index(in_st_agg,self.agg_num_tuple)
        p[0] = self.arr_rate
        pdf = p / p.sum()
        return pdf

    def _update_ArrStats_agg(self,sched_to,rw,nxt_st_arr,in_state_ix_agg,in_st_tuple):

        nxt_st_agg = self.transate_det2agg(nxt_st_arr)
        nxst_st_agg_ix = np.ravel_multi_index(nxt_st_agg, self.agg_num_tuple)
        self.TArr_count_agg[nxst_st_agg_ix, sched_to, in_state_ix_agg] += 1
        self.RWarr_Agg[sched_to, in_state_ix_agg] += rw
        self.RWarr_Agg_cnt[sched_to, in_state_ix_agg] += 1
        #self.RW_hold_Agg[0, in_state_ix_agg] += self._calc_Costs(in_st_tuple)
        #self.RW_hold_Agg_cnt[0, in_state_ix_agg] += 1

    def Make_step_agg(self, in_st_tuple, egreedy,explore_flag):

        in_st_tuple_agg = self.transate_det2agg(in_st_tuple)
        in_state_ix_agg = np.ravel_multi_index(in_st_tuple_agg, self.agg_num_tuple)
        pdf = self._make_pdf_agg(in_st_tuple)

        rnd_act = np.random.choice(np.arange(0, 3), p=pdf)
        act_pol = np.zeros(2, dtype=int)
        egreedy_choice = np.random.choice(np.arange(0, 2), p=[1-egreedy,egreedy])

        if (explore_flag==1):
            [nxt_st_arr, rw] = self.SchedHorR_agg(in_st_tuple, 1)
            self._update_ArrStats_agg(0,rw,nxt_st_arr,in_state_ix_agg,in_st_tuple)

            [nxt_st_arr, rw] = self.SchedHorR_agg(in_st_tuple, 0)
            self._update_ArrStats_agg(1,rw,nxt_st_arr,in_state_ix_agg,in_st_tuple)

            [nxt_st_arr, rw] = self.SchedLorR_agg(in_st_tuple, 1)
            self._update_ArrStats_agg(2,rw,nxt_st_arr,in_state_ix_agg,in_st_tuple)

            [nxt_st_arr, rw] = self.SchedLorR_agg(in_st_tuple, 0)
            self._update_ArrStats_agg(3,rw,nxt_st_arr,in_state_ix_agg,in_st_tuple)

            [nxt_st_arr, rw] = self.SchedMorR_agg(in_st_tuple, 1)
            self._update_ArrStats_agg(4,rw,nxt_st_arr,in_state_ix_agg,in_st_tuple)

            [nxt_st_arr, rw] = self.SchedMorR_agg(in_st_tuple, 0)
            self._update_ArrStats_agg(5,rw,nxt_st_arr,in_state_ix_agg,in_st_tuple)

            [nxt_st_arr, rw] = self.SchedR_agg(in_st_tuple, 1)
            self._update_ArrStats_agg(6,rw,nxt_st_arr,in_state_ix_agg,in_st_tuple)

            [nxt_st_arr, rw] = self.SchedR_agg(in_st_tuple, 0)
            self._update_ArrStats_agg(7,rw,nxt_st_arr,in_state_ix_agg,in_st_tuple)

            if pdf[1]>0:
                for se in range(self.num_srv_actions_agg):
                    [nxt_st_arr, rw] = self.Srv_agg(in_st_tuple, se)
                    nxt_st_agg = self.transate_det2agg(nxt_st_arr)
                    nxt_st_agg_ix = np.ravel_multi_index(nxt_st_agg, self.agg_num_tuple)
                    self.TSrv_count_agg[in_state_ix_agg, se, nxt_st_agg_ix] += 1
                    self.RWsrv_Agg[se, in_state_ix_agg] += rw
                    self.RWsrv_Agg_cnt[se, in_state_ix_agg] += 1

            if pdf[2]>0:
                [nxt_st_arr, rw] = self.Dpl_agg(in_st_tuple)
                nxt_st_agg = self.transate_det2agg(nxt_st_arr)
                nxt_st_agg_ix = np.ravel_multi_index(nxt_st_agg, self.agg_num_tuple)
                self.TDpl_count_agg[nxt_st_agg_ix, in_state_ix_agg] += 1
                # self.RWarr_Agg[in_state_ix_agg, sched_to] += rw

                # self.delta_agg[in_state_ix_agg]=self._calc_delta(in_st_tuple)
        # end of [ if (explore_flag==1): ]

        if (rnd_act == 0):
            if egreedy_choice == 0:
                rand_pol = np.random.choice(np.arange(0, self.num_arr_actions_agg), \
                                            p=np.ones(self.num_arr_actions_agg) / self.num_arr_actions_agg)
                sched_to = rand_pol
            else:
                sched_to = self.PolA_agg[in_state_ix_agg]
            # self.polH_YD = 0 self.polH_ND = 1 self.polL_YD = 2 self.polM_ND = 3
            # self.polM_YD = 4 self.polL_ND = 5 self.polR_YD = 6 self.polR_YD = 7
            if  (sched_to==self.polH_YD):
                [nxt_st_arr,rw] = self.SchedHorR_agg(in_st_tuple,1)
            elif (sched_to==self.polH_ND):
                [nxt_st_arr,rw] = self.SchedHorR_agg(in_st_tuple, 0)
            elif (sched_to==self.polL_YD):
                [nxt_st_arr,rw] = self.SchedLorR_agg(in_st_tuple, 1)
            elif (sched_to==self.polL_ND):
                [nxt_st_arr,rw] = self.SchedLorR_agg(in_st_tuple, 0)
            elif (sched_to==self.polM_YD):
                [nxt_st_arr,rw] = self.SchedMorR_agg(in_st_tuple, 1)
            elif (sched_to==self.polM_ND):
                [nxt_st_arr,rw] = self.SchedMorR_agg(in_st_tuple, 0)
            elif (sched_to==self.polR_YD):
                [nxt_st_arr,rw] = self.SchedR_agg(in_st_tuple, 1)
            elif (sched_to==self.polR_ND):
                [nxt_st_arr,rw] = self.SchedR_agg(in_st_tuple, 0)

            if (explore_flag == 2):
                nxt_st_agg = self.transate_det2agg(nxt_st_arr)
                nxst_st_agg_ix = np.ravel_multi_index(nxt_st_agg, self.agg_num_tuple)
                self.TArr_count_agg[nxst_st_agg_ix,sched_to,in_state_ix_agg] += 1
                # z=self.TArr_count_agg.sum(2);
                if (rw>0):
                    here=3
                self.RWarr_Agg[sched_to,in_state_ix_agg]+=rw
                self.RWarr_Agg_cnt[sched_to,in_state_ix_agg] += 1

            #self.RW_hold_Agg[0,in_state_ix_agg]+=self._calc_Costs(in_st_tuple)
            #self.RW_hold_Agg_cnt[0, in_state_ix_agg] += 1

############################---SERVICE AGG
        elif (rnd_act == 1):
            if egreedy_choice == 0:
                rand_pol = np.random.choice(np.arange(0, 2), \
                                            p=np.ones(2) / 2.0)
                isdestroy = rand_pol
            else:
                isdestroy = self.PolS_agg[in_state_ix_agg]

            [nxt_st_arr,rw] = self.Srv_agg(in_st_tuple, isdestroy)

            nxt_st_agg = self.transate_det2agg(nxt_st_arr)


            if (explore_flag == 2):
                #nxt_st_agg = self.transate_det2agg(nxt_st_arr)
                nxt_st_agg_ix = np.ravel_multi_index(nxt_st_agg, self.agg_num_tuple)
                self.TSrv_count_agg[in_state_ix_agg, isdestroy, nxt_st_agg_ix] += 1
                self.RWsrv_Agg[isdestroy,in_state_ix_agg] += rw
                self.RWsrv_Agg_cnt[isdestroy, in_state_ix_agg ] += 1



        else: #deployment
            [nxt_st_arr, rw] = self.Dpl_agg(in_st_tuple)
            if explore_flag==2:
                nxt_st_agg = self.transate_det2agg(nxt_st_arr)
                nxt_st_agg_ix = np.ravel_multi_index(nxt_st_agg, self.agg_num_tuple)
                self.TDpl_count_agg[nxt_st_agg_ix, in_state_ix_agg] += 1
            # self.RWarr_Agg[in_state_ix_agg, sched_to] += rw


            #self.zeta_agg[0,in_state_ix_agg]+=torch.tensor(self.deploy_rate*in_st_tuple_agg[self.ixD])
            #self.zeta_agg_cnt[0,in_state_ix_agg] +=1

        if (explore_flag>0):
            self.RW_hold_Agg[0, in_state_ix_agg] += self._calc_Costs(in_st_tuple)
            self.RW_hold_Agg_cnt[0, in_state_ix_agg] += 1

            self.update_Rates_agg(in_st_tuple_agg,in_state_ix_agg,in_st_tuple_agg)
        return [nxt_st_arr, rw]

    def update_Rates_agg(self,in_st_tuple,in_state_ix_agg,in_st_tuple_agg):
        self.zeta_agg[0, in_state_ix_agg] += torch.tensor(self.deploy_rate * in_st_tuple_agg[self.ixD])
        self.zeta_agg_cnt[0, in_state_ix_agg] += 1
        es = self._find_numEmpty(in_st_tuple)
        ids = in_st_tuple_agg[self.ixI]
        dps = in_st_tuple_agg[self.ixD]
        acs = self.NumQueues - es - ids - dps
        self.miu_agg[0, in_state_ix_agg] += torch.tensor(self.srv_rate * acs)
        self.miu_agg_cnt[0, in_state_ix_agg] += 1

    def run_BE_agg(self, nit):
        err_now=torch.zeros(nit)
        Vagg_arr=torch.zeros(self.num_arr_actions_agg,self.num_st_agg)
        Vagg_srv = torch.zeros(self.num_srv_actions_agg,self.num_st_agg )
        Vgg_srv_All = torch.zeros(1,self.num_st_agg)
        for n in range(nit):
            for i in range(self.num_arr_actions_agg):
                Vagg_arr[i,:] = torch.matmul(self.Vagg,self.TArr_ix_act_ix_agg[:,i,:])+self.RWarr_Agg[i,:]
            VaggMa = Vagg_arr.max(dim=0, keepdim=False)

            self.PolA_agg=VaggMa.indices
            Vagg_arr_All = VaggMa.values*self.arr_rate



            Vgg_srv_All[:] = 0
            for i in range(self.num_srv_actions_agg):
                Vagg_srv[i,:] = torch.matmul(self.Vagg,self.TSrv_ix_act_ix_agg[:,i,:])+self.RWsrv_Agg[i,:]
            Vagg_srvMa = Vagg_srv.max(dim=0, keepdim=False)
            Vgg_srv_All = Vagg_srvMa.values
            self.PolS_agg = Vagg_srvMa.indices
            Vgg_srv_All *= self.miu_agg.squeeze()


            # Vagg_dpl = torch.Tensor(self.num_st_agg)
            # for i in range(self.NumQueues):
            Vagg_dpl = torch.matmul(self.Vagg,self.TDpl_ix_ix_agg)
            V_agg_dpl_t=torch.matmul(self.Vagg,self.TDpl_ix_ix_agg)
            Vagg_dpl *= self.zeta_agg.squeeze()
            V_agg_dpl_t2 = V_agg_dpl_t*self.zeta_agg.squeeze()

            total_V = self.delta_agg.squeeze() * (Vagg_dpl + Vgg_srv_All + Vagg_arr_All - self.RW_hold_Agg)

            err_now[n]=torch.sum(torch.abs(self.Vagg - total_V))
            self.Vagg = total_V
        here=1





    @staticmethod
    def give_ix(arr_or_tuple, st_sp_tuple):
        # use this func to make sure you got index and not array or tuple of subscripts
        cl = arr_or_tuple.__class__
        if cl==tuple:
            in_state_ix = np.ravel_multi_index(arr_or_tuple, st_sp_tuple)
            return in_state_ix
        if (cl==np.ndarray) & (arr_or_tuple.size>1):
            in_state_ix = np.ravel_multi_index(arr_or_tuple, st_sp_tuple)
            return in_state_ix
        return arr_or_tuple


    def set_Qval(self): # Q-value data
        self.Q_dpl = torch.Tensor(self.num_states)
        self.Q_arr = torch.Tensor(self.arr_actions, self.num_states)
        self.Q_srv = torch.Tensor(self.NumQueues, self.srv_actions, self.num_states)

    def make_plot(self):
        plt.plot(range(self.num_states), self.States.numpy(), label='V')
        plt.title('Value function')
        plt.xlabel('states')
        plt.ylabel('V')
        plt.legend()
        plt.grid()
        plt.show()

    def make_plot_agg(self):
        plt.plot(range(self.num_st_agg), self.Vagg[0,:].numpy(), label='Vagg')
        plt.title('Value function')
        plt.xlabel('states')
        plt.ylabel('Vagg')
        plt.legend()
        plt.grid()
        plt.show()

    def set_Rates(self, a, s, d, gam=None):
        self.arr_rate = a
        self.srv_rate = s
        self.deploy_rate = d
        if gam != None:
            self.gamma = gam


    def set_Costs(self, c_rw, c_rj, c_destroy, c_haveq, c_build):
        # self.c_build  = c_build
        self.c_rw = c_rw
        self.c_rj = c_rj
        self.c_destroy = c_destroy
        self.c_build = c_build
        self.c_haveq=c_haveq

    def set_delayP(self, eta):
        self.eta = eta


    def __repr__(self):
        str1 = 'Number of Queues: ' + str(self.NumQueues) + '\n'
        str2 = 'Max tasks in each Q: ' + str(self.MaxQsize) + '\n'
        str3 = 'Tot Num of states: ' + str(self.num_states) + '\n'
        str4 = 'Costs are: ' + '\n' + 'Reject Cost: ' + str(self.c_rj)+ '\n' + 'Reward: ' + str(self.c_rw) + '\n'
        str5 = 'Build cost: ' + str(self.c_build)+ '\n' + 'Having a Q cost p/t: ' + str(self.c_haveq)+ '\n'
        str6 = 'Times are: ' + '\n' + 'Deploy: ' + str(self.deploy_rate)+ '\n' + 'Serve: ' + str(self.srv_rate)+ '\n'
        str7 = 'Arrivals: ' + str(self.arr_rate) + '\n' + 'Discount: ' + str(self.gamma)
        return str1+str2+str3+str4+str5+str6+str7

    #def checkArr_toQ(self):
    def print_pol(self):
        for i in range(self.num_states):
            current_st_subs = np.unravel_index(i, self.num_states_tuple)
            ar=np.array(current_st_subs)
            ar=ar-2
            print(ar.__str__()+ ' =>  ' + self.Pol[i,:].__str__())


    def save_pol(self, filename):
        f = open (filename, "w")

        for i in range (self.num_states):
            current_st_subs = np.unravel_index (i, self.num_states_tuple)
            ar = np.array (current_st_subs)
            ar = ar - 2
            f.write (ar.__str__ () + ' =>  ' + self.Pol[i, :].__str__ ()+ '\n')
            if i % 1000 == 0:
                print ("@", end='')

        print()
        f.close()

    #####################################1#####################
##########################################################

    ##########################################################
    ##########################################################




    def run_BE(self):

        # all_V = []
        arr_res = torch.Tensor(self.arr_actions, self.num_states)
        for i in range(self.arr_actions):
            arr_res[i, :] = self.States[self.TransitionsP_Arr[i, :]] + self.Rewards_T[i, :]


        arr_V_all = arr_res.max(dim=0, keepdim=False)
        arr_V=arr_V_all.values
        self.Pol[:,-1] = arr_V_all.indices
        arr_V = arr_V * self.arr_rate

        all_V = arr_V
        srv_res = torch.Tensor(self.srv_actions, self.num_states)
        for i in range(self.NumQueues):
            for a in range(self.srv_actions):
                srv_res[a, :] = (self.States[self.TransitionsP_Srv[i, a, :]])
            srv_V_all = srv_res.max(dim=0, keepdim=False)
            self.Pol[:,i] = srv_V_all.indices
            srv_V = srv_V_all.values
            srv_V = srv_V * self.TP_Srv_effRates_T[i, :]
            all_V += srv_V

        dpl_res = torch.Tensor(self.NumQueues, self.num_states)
        for i in range(self.NumQueues):
            dpl_res[i, :] = self.States[self.TransitionsP_Dpl[i, :]] * self.TP_Dpl_effRates_T[i, :]
        dpl_V = sum(dpl_res)


        total_V = self.delta_T * (dpl_V + all_V - self.CostState_T)
        self.LastErr = self.err_func(total_V, self.States.data)
        self.States = total_V



        






        # self.States = (self.arr_rate*arr_V + self.srv_rate*srv_V + self.deploy_rate*dpl_V + self.CostState_T)*self.delta_T

##########################################################
##########################################################

    def _calc_Costs(self, in_state):
        n_active = self._count_ActiveQ(in_state)
        hcost = 0
        for q_in in range(self.NumQueues):
            in_this_q = in_state[q_in]
            hcost += (in_this_q-2) * self.eta[in_this_q]
        allcost = n_active * self.c_haveq + hcost
        return allcost

    def make_IndexMappingTable(self):

        for current_st_index in range(self.num_states):

            if current_st_index % 1000 == 0:
                print ("+", end='')
            current_st_subs = np.unravel_index(current_st_index, self.num_states_tuple)
            in_state_tuple = np.array(current_st_subs)
            # n_actives = self.__count_ActiveQ(in_state_tuple)
            self.delta_T[current_st_index] = self._calc_delta(current_st_subs)
            self.CostState_T[current_st_index] = torch.Tensor([self._calc_Costs(current_st_subs)])

            for q_in in range(self.NumQueues):
                self._transition_Rule1(current_st_subs, q_in, current_st_index)  #arrival, action to Q number q_in
                self._transition_Rule2(current_st_subs, q_in, current_st_index)
                self._transition_Rule3(current_st_subs, q_in, current_st_index)
                a = 1
            self._transition_Rule1r(current_st_subs, current_st_index) #rejection

    def _calc_delta(self, in_state_tuple):

        delta = self.arr_rate + self.gamma
        for i in range(self.NumQueues):
            if in_state_tuple[i] == self.DEPLOYING:
                delta += self.deploy_rate
            if in_state_tuple[i] > self.EMPTY:
                delta += self.srv_rate
        return delta ** (-1)

    def _make_pdf(self, in_state_tuple):
        p = np.zeros([self.NumQueues*2+1])
        for i in range(self.NumQueues):
            if in_state_tuple[i] == self.DEPLOYING:
                p[self.NumQueues+i] = self.deploy_rate
            elif in_state_tuple[i] > self.EMPTY:
                    p[i] = self.srv_rate

        p[-1] = self.arr_rate
        pdf =p/p.sum()
        return pdf

    def run_Long_Sim(self, num_its):
        init_state=np.zeros(self.NumQueues,dtype=int)
        TOT_RW = 0
        self.States_Stats=np.zeros([self.NumQueues,num_its])
        current_state=init_state
        for i in range(num_its):
            rw, next_state, a_p = self.run_Step(current_state)
            TOT_RW += rw
            self.States_Stats[:, i] = next_state
            current_state = next_state
        Avg_RW = TOT_RW/num_its
        return Avg_RW

    def run_Long_Sim_agg(self, num_its):
        init_state=np.zeros(self.NumQueues,dtype=int)
        TOT_RW = 0
        self.States_Stats=np.zeros([self.NumQueues,num_its])
        current_state=init_state
        for i in range(num_its):
            next_state, rw = self.Make_step_agg(current_state, 1)
            TOT_RW += rw
            self.States_Stats[:, i] = next_state
            current_state = next_state
        Avg_RW = TOT_RW/num_its
        return Avg_RW

    def run_Step(self, in_st_tuple):
        in_state_ix = np.ravel_multi_index(in_st_tuple, self.num_states_tuple)
        pdf = self._make_pdf(in_st_tuple)
        rnd_act = np.random.choice(np.arange(0, self.numEvents), p = pdf)
        act_pol = np.zeros(2,dtype=int)
        if (rnd_act == self.doArr):
            sched_to = self.Pol[in_state_ix, -1]
            [rw, nxt_st] = self._ActRule_arr(in_st_tuple, sched_to)
            act_pol[0] = rnd_act
            act_pol[1] = sched_to
        elif (rnd_act < self.doSrv):
            [rw, nxt_st] = self._ActRule_srv(in_st_tuple, rnd_act)
            term_yn = self.Pol[in_state_ix,rnd_act]
            act_pol[0] = rnd_act
            act_pol[1] = term_yn
        else:
            nxt_st = self._ActRule_dpl(in_st_tuple, rnd_act - self.NumQueues)
            rw = 0
            act_pol[0] = rnd_act
            act_pol[1] = rnd_act

        return [rw, nxt_st, act_pol]

    def _ActRule_arr(self, in_state_tuple, sched_to):
        in_state_ix = np.ravel_multi_index(in_state_tuple, self.num_states_tuple)
        to_deploy=None
        sched_to = sched_to.__int__()
        if sched_to > (self.NumQueues):
            to_deploy = self._have_IdleQ(in_state_tuple)
            sched_to_q = sched_to - (self.NumQueues+1)
        else:
            sched_to_q = sched_to
        nextQ_arr = np.array(in_state_tuple)

        if sched_to_q < (self.NumQueues):
            q_dest = in_state_tuple[sched_to_q.__int__()]
            if (q_dest > self.DEPLOYING) & (q_dest < self.FULL):
                nextQ_arr[sched_to_q.__int__()] += 1
                rw = self.c_rw
            else:
                rw = -self.c_rj
        else:
            rw = -self.c_rj
        if to_deploy != None:
            nextQ_arr[to_deploy] = self.DEPLOYING
            rw -= self.c_build


        nextQ_arr_ix = self.TransitionsP_Arr[sched_to, in_state_ix]
        nextQ_ix_test = np.unravel_index(nextQ_arr_ix.__int__(), self.num_states_tuple)
        testOK=nextQ_arr==nextQ_ix_test
        if testOK.sum()<3:
            hasbug=1
        return rw,nextQ_arr


    def _ActRule_srv(self, in_st_tuple, q_served):
        q_served = q_served.__int__()
        rw = 0
        in_state_ix = np.ravel_multi_index(in_st_tuple, self.num_states_tuple)
        nextQ_arr = np.array(in_st_tuple)
        nextQ_arr[q_served] -= 1
        d_pol = self.Pol[in_state_ix, q_served]
        if (nextQ_arr[q_served]==self.EMPTY) & (d_pol==1): # the policy is to terminate
            nextQ_arr[q_served] = self.IDLE
            rw -= self.c_destroy
        #srv_res[a, :] = (self.States[self.TransitionsP_Srv[i, a, in_state_ix]])
        return rw,nextQ_arr

    def _ActRule_dpl(self, in_st_tuple, q_deployed):
        q_deployed = q_deployed.__int__()
        in_state_ix = np.ravel_multi_index(in_st_tuple, self.num_states_tuple)
        nextQ_arr = np.array(in_st_tuple)
        if nextQ_arr[q_deployed] != self.DEPLOYING:
            bug_deploy=1
        nextQ_arr[q_deployed] = self.EMPTY
        return nextQ_arr

    def get_Rates_NStates(self, in_state_tuple):
        # srv_rates, dpl_rates = get_Rates_NStates(in_state_tuple)
        srv_rates=torch.Tensor(self.NumQueues)
        for i in range(self.NumQueues):
            q = in_state_tuple[i]
            if (q>self.DEPLOYING)&(q<self.FULL):
                srv_rates[i]=self.srv_rate
            else:
                srv_rates[i] = 0

        dpl_rates = torch.Tensor(self.NumQueues)
        for i in range(self.NumQueues):
            q = in_state_tuple[i]
            if (q==self.DEPLOYING):
                dpl_rates[i]=self.deploy_rate
            else:
                dpl_rates[i] = 0
        return srv_rates, dpl_rates

    def calc_Qvalue(self, r_prev, Q_arr_in, Q_srv_in, Q_dpl_in, in_state_tuple,srv_rates, dpl_rates):



        in_state_ix = np.ravel_multi_index(in_state_tuple, self.num_states_tuple)
        # Reminder : self.Q_arr = torch.Tensor(self.arr_actions, self.num_states)
        # arr_res = torch.Tensor(self.arr_actions, 1)

        # arr_res[:] = self.Q_arr[:, in_state_ix]  # + self.Rewards_T[i, in_state_ix]

        # arr_V = arr_res * self.arr_rate

        Q_all_set = Q_arr_in.max(dim=0, keepdim=False)

        Q_all = Q_all_set.values * self.arr_rate



        # Reminder : self.Q_srv = torch.Tensor(self.NumQueues, self.srv_actions, self.num_states)

        srv_res = torch.Tensor(self.srv_actions)
        i = 0
        for a in np.arange(0,(self.NumQueues)*2,2):
            #for a in range(self.srv_actions):
            srv_res = Q_srv_in[a:a+2]
            srv_Q_all_set = srv_res.max(dim=0, keepdim=False)
            # self.Pol[:,i] = srv_V_all.indices
            srv_Q = srv_Q_all_set.values
            srv_Q = srv_Q * srv_rates[i]
            i += 1
            Q_all += srv_Q
        # states_Q[ind_arr_states:ind_srv_states - 1] = srv_res * self.delta_T[in_state_ix]

        dpl_res = torch.Tensor(self.NumQueues)
        for i in range(self.NumQueues):
            dpl_res[i] = Q_dpl_in[i] * dpl_rates[i]
        dpl_Q = sum(dpl_res)

        Q_all += dpl_Q

        Q_all *= self.delta_T[in_state_ix]

        return Q_all*self.gamma + r_prev


    def _transition_Rule3(self, in_state_tuple, n, in_state_ix):

        new_state_tuple = np.array(in_state_tuple)  # preliminary value of new state is equal to the prev. state

        if (in_state_tuple[n] == self.DEPLOYING):
            new_state_tuple[n] = self.EMPTY
            new_state_ix = np.ravel_multi_index(new_state_tuple, self.num_states_tuple)
            self.TransitionsP_Dpl[n, in_state_ix] = torch.Tensor([new_state_ix])
            self.TP_Dpl_effRates_T[n, in_state_ix] = self.deploy_rate
        else:
            self.TransitionsP_Dpl[n, in_state_ix] = torch.Tensor([in_state_ix])
            self.TP_Dpl_effRates_T[n, in_state_ix] = 0


    def _count_ActiveQ(self, in_state_tuple):
        tmp = np.array(in_state_tuple)
        n = 0
        for i in range(self.NumQueues):
            if tmp[i] > self.DEPLOYING:
                n += 1
        return n


    def _have_IdleQ(self, in_state_tuple):
        tmp = np.array(in_state_tuple)
        idles = np.where(tmp == self.IDLE)
        if idles[0].size > 0:
            id = idles[0]
            return id[0]
        else:
            return None

    def _transition_Rule2(self, in_state_tuple, n, in_state_ix):
        # reminder: self.TransitionsP_Srv = np.zeros([self.NumQueues, self.srv_actions, self.num_states])
        new_state_tuple = np.array(in_state_tuple)  # preliminary value of new state is equal to the prev. state

        if (in_state_tuple[n] > self.EMPTY) :   # Q number n not empty, service is possible
            self.TP_Srv_effRates_T[n, in_state_ix] = self.srv_rate
            new_state_tuple[n] -= 1
            new_state_ix = np.ravel_multi_index(new_state_tuple, self.num_states_tuple)
            self.TransitionsP_Srv[n, 0, in_state_ix] = torch.Tensor([new_state_ix])
            if new_state_tuple[n] == self.EMPTY:  # termination is possible
                new_state_tuple[n] = self.IDLE
                new_state_ix = np.ravel_multi_index(new_state_tuple, self.num_states_tuple)
                self.TransitionsP_Srv[n, 1, in_state_ix] = torch.Tensor([new_state_ix])
            else:   # termination is impossible
                self.TransitionsP_Srv[n, 1, in_state_ix] = torch.Tensor([new_state_ix])
        else:
            self.TP_Srv_effRates_T[n, in_state_ix] = 0
            new_state_ix = np.ravel_multi_index(new_state_tuple, self.num_states_tuple)
            self.TransitionsP_Srv[n, 0, in_state_ix] = torch.Tensor([new_state_ix])
            self.TransitionsP_Srv[n, 1, in_state_ix] = torch.Tensor([new_state_ix])

    def _transition_Rule1(self, in_state_tuple, n, in_state_ix):


        new_state_tuple = np.array(in_state_tuple)
        n_deploy = n + (self.NumQueues+1)  # action of allocating to n and deployment
        to_deploy = self._have_IdleQ(in_state_tuple)
        if to_deploy != None:
            if new_state_tuple[to_deploy] != self.IDLE:
                bug = 1
        if (in_state_tuple[n] < self.FULL) & (in_state_tuple[n] > self.DEPLOYING):

            new_state_tuple[n] += 1
            new_state_ix = np.ravel_multi_index(new_state_tuple, self.num_states_tuple)
            if new_state_ix > (self.num_states - 1):
                buggy = 1
            self.TransitionsP_Arr[n, in_state_ix] = torch.Tensor([new_state_ix])


            if to_deploy != None:  # yes deploy
                new_state_tuple[to_deploy] = self.DEPLOYING

                new_state_ix = np.ravel_multi_index(new_state_tuple, self.num_states_tuple)
                if new_state_ix > (self.num_states-1):  # just debugging
                    buggy = 1
                self.TransitionsP_Arr[n_deploy, in_state_ix] = torch.Tensor([new_state_ix])

                self.Rewards_T[n_deploy, in_state_ix] = self.c_rw - self.c_build
                self.Rewards_T[n, in_state_ix] = self.c_rw
            else:   # no deploy, stay in the same state
                self.TransitionsP_Arr[n_deploy, in_state_ix] = torch.Tensor([new_state_ix])
                self.Rewards_T[n, in_state_ix] = self.c_rw
                self.Rewards_T[n_deploy, in_state_ix] = self.c_rw - self.c_build


        else:  # no available Q
            new_state_ix = np.ravel_multi_index(new_state_tuple, self.num_states_tuple)
            self.TransitionsP_Arr[n, in_state_ix] = torch.Tensor([new_state_ix])
            if to_deploy != None:  # yes deploy
                new_state_tuple[to_deploy] = self.DEPLOYING

                new_state_ix = np.ravel_multi_index(new_state_tuple, self.num_states_tuple)
                self.TransitionsP_Arr[n_deploy, in_state_ix] = torch.Tensor([new_state_ix])
                self.Rewards_T[n_deploy, in_state_ix] = - self.c_rj - self.c_build
                self.Rewards_T[n, in_state_ix] = - self.c_rj
            else:  # no deploy
                self.TransitionsP_Arr[n_deploy, in_state_ix] = torch.Tensor([new_state_ix])
                self.Rewards_T[n, in_state_ix] = - self.c_rj
                self.Rewards_T[n_deploy, in_state_ix] = - self.c_rj

    def _transition_Rule1r(self, in_state_tuple, in_state_ix):

        n = self.NumQueues
        new_state_tuple = np.array(in_state_tuple)
        n_deploy = n + (self.NumQueues+1)  # action of rejecting and deployment
        to_deploy = self._have_IdleQ(in_state_tuple)
        if to_deploy != None:
            if new_state_tuple[to_deploy] != self.IDLE:
                bug = 1

         # Only rejection is considered
        new_state_ix = np.ravel_multi_index(new_state_tuple, self.num_states_tuple)
        self.TransitionsP_Arr[n, in_state_ix] = torch.Tensor([new_state_ix])
        if to_deploy != None:  # yes deploy
            new_state_tuple[to_deploy] = self.DEPLOYING

            new_state_ix = np.ravel_multi_index(new_state_tuple, self.num_states_tuple)
            self.TransitionsP_Arr[n_deploy, in_state_ix] = torch.Tensor([new_state_ix])
            self.Rewards_T[n_deploy, in_state_ix] = - self.c_rj - self.c_build
            self.Rewards_T[n, in_state_ix] = - self.c_rj
        else:  # no deploy
            self.TransitionsP_Arr[n_deploy, in_state_ix] = torch.Tensor([new_state_ix])
            self.Rewards_T[n, in_state_ix] = - self.c_rj
            self.Rewards_T[n_deploy, in_state_ix] = - self.c_rj

                # self.TransitionsP_Arr[n, in_state_ix] = new_state_ix


