import torch
import numpy as np
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

import matplotlib.pyplot as plt


class myLabels():
    def __init__(self, numlabels, numsamples, numdistributions, means, vars):
        self.nLabels = numlabels
        self.nDims = numdistributions
        if not torch.is_tensor(means):
            print('Expected a tensor for mins!\n')
        if not torch.is_tensor(vars):
            print('Expected a tensor for maxs!\n')
        self.lmeans = means
        self.lvars = vars
        self.nSamples = numsamples

        self.allInputs = torch.Tensor(numlabels, numsamples).zero_()
        self.allLabels = torch.Tensor(numsamples, 1).zero_()
        self.allDetailedLabels = torch.Tensor(numsamples, self.nDims).zero_()
        # self.allnoisedLabels = torch.Tensor(numlabels, 1).zero_()
        # self.noisedInputs = torch.Tensor(numlabels, numdistributions).zero_()
        # self.TheWeights = torch.tensor([2.6, 1.5, 1.2])

        # self.noise = noise_factor

    @property
    def make_labels(self):  # makes nLabels between minsVals and maxsVals of dimension nDims
        for i in range(0, self.nSamples):
            tmp_label = torch.randint(0, self.nDims, [1, 1])
            self.allLabels[i] = tmp_label
            self.allDetailedLabels[i, tmp_label] = 1
            tmp_var = self.lvars[tmp_label]
            tmp_mean = self.lmeans[tmp_label]
            tmp_sample = (torch.randn([1, self.nLabels])*tmp_var) + tmp_mean

            self.allInputs[:, i] = tmp_sample
            # self.noisedInputs[:, i] = self.allInputs[:, i] + self.noise * torch.randn([1, self.nLabels])
            # self.allLabels[:, 0] = self.allLabels[:, 0] + self.allInputs[:, i] * self.TheWeights[i]
        # self.allnoisedLabels[:, 0] = 0.01 * torch.randn([1, self.nLabels]) + self.allLabels[:, 0]
        return self.allInputs

    def __repr__(self):
        return '\n#Samples is: ' + self.nLabels.__str__() + '\n#Dimensions is: ' + self.nDims.__str__() + \
               '\nmeans are: ' + self.lmeans.__str__() + '\nvars are: ' + self.lvars.__str__()


class myRegInput():
    def __init__(self, numlabels):
        self.nSamples = numlabels
        self.Samples = torch.randn([numlabels, 1], out=None, dtype=torch.float32)
        # self.S=

    def __repr__(self):
        return '\nSamples are:\n ' + self.Samples.__str__()


class myGdetect(nn.Module):
    def __init__(self, n_measurments, nGdistributions):
        super(myGdetect, self).__init__()
        # self.conv1 = nn.Conv2d(in_channels=1, out_channels=6, kernel_size=5)
        # self.conv2 = nn.Conv2d(in_channels=6, out_channels=12, kernel_size=5)

        # self.fc1 = nn.Linear(in_features=12 * 4 * 4, out_features=120)
        self.fc1 = nn.Linear(in_features=n_measurments, out_features=(nGdistributions*nGdistributions), bias=False)
        self.fc2 = nn.Linear(in_features=(nGdistributions*nGdistributions), out_features=nGdistributions, bias=False)
        # self.myInp = myRegInput(ns)
        # self.out = nn.Linear(in_features=60, out_features=10)

    def forward(self, inp):
        l1 = self.fc1(inp)
        l1out = F.sigmoid(l1)
        # l1out = F.relu(l1)
        l2 = self.fc2(l1out)
        l22 = F.relu(l2)
        #l22 = F.sigmoid(l2)
        myp = F.softmax(l2, 0)
        return myp

    def __repr__(self):
        return 'This is my Regression contents: \n' + \
               super(myGdetect, self).__repr__() + \
               'weights1: \n' + self.fc1.weight.__str__() + \
               'weights1: \n' + self.fc2.weight.__str__()
        # super(nn.Linear, self).__repr__()

#  numlabels, numsamples, numdistributions, means, vars):

def adjust_learning_rate(optimizer, mlr):
    """Sets the learning rate to the initial LR decayed by 10 every 30 epochs"""
    lr = mlr * 0.9995 #(0.1 ** (epoch // 30))
    for param_group in optimizer.param_groups:
        param_group['lr'] = lr
    return lr

#t_means = torch.tensor([0, 2, -1, -2], dtype=torch.float32)
#t_vars = torch.tensor([0.004, 0.003, 0.0025, 0.01], dtype=torch.float32)*100

t_means = torch.Tensor([0, 2, -1, -2])
t_vars = torch.Tensor([0.004, 0.003, 0.0025, 0.01])*100

torch.set_grad_enabled(True)

num_dim = 4
nno = 0.06
num_msrments = 50
num_samples = 7500
inp = myLabels(num_msrments, num_samples, t_means.shape.numel(), t_means, t_vars)
ls = inp.make_labels
myr = myGdetect(num_msrments, num_dim)
nit = num_samples
loss_func = torch.nn.MSELoss(size_average=True)
mylr = 0.4125
my_optimizer = optim.SGD(myr.parameters(), lr=mylr)
my_optimizer.zero_grad()
loss_track = np.empty(nit)*0
for i in range(0, nit):
    # y_pred = model(x)

    # loss = criterion(y_pred, y)
    # optimizer.zero_grad()
    # loss.backward()
    # optimizer.step()

    # ls = inp.make_labels
    # myr.zero_grad()
    my_pred = myr(inp.allInputs[:, i])
    my_loss = loss_func(my_pred, inp.allDetailedLabels[i, :])
    my_optimizer.zero_grad()
    my_loss.backward()

    my_optimizer.step()
    print(my_loss.item())
    loss_track[i] = my_loss.item()
    mylr = adjust_learning_rate(my_optimizer, mylr)
    # print('Sum: ')
    # print(sum(sum(abs(inp.noisedLabels - inp.allLabels))))
#plt.plot(loss_track[-990:-1])
plt.plot(loss_track)
print('loss mean was ')
print(loss_track.mean())
print(loss_track[-10:-1].mean())

print('learning rate was ')
print(mylr)

plt.show()
# print('Original_Weights: \n')
# print(inp.TheWeights)
