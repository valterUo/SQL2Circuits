# -*- coding: utf-8 -*-
import numpy

class CostAccuracy:

    def __init__(self):
        self.train_costs = []
        self.train_accs = []
        self.dev_costs = []
        self.dev_accs = []
        self.test_accs = []
        self.test_costs = []

    def add_cost(self, cost, type):
        if type == "train":
            self.train_costs.append(cost)
        elif type == "dev":
            self.dev_costs.append(cost)
        elif type == "test":
            self.test_costs.append(cost)
    
    def add_accuracy(self, acc, type):
        if type == "train":
            self.train_accs.append(acc)
        elif type == "dev":
            self.dev_accs.append(acc)
        elif type == "test":
            self.test_accs.append(acc)

    def get_train_costs(self):
        return self.train_costs

    def get_train_loss(self):
        if len(self.train_costs) < 2:
            return 100
        return numpy.around(min(float(self.train_costs[-1]), float(self.train_costs[-2])), 4)
    
    def get_train_acc(self):
        if len(self.train_accs) < 2:
            return 0
        return numpy.around(min(float(self.train_accs[-1]), float(self.train_accs[-2])), 4)
    
    def get_train_accs(self):
        return self.train_accs
    
    def get_dev_costs(self):
        return self.dev_costs
    
    def get_dev_acc(self):
        if len(self.dev_accs) == 0:
            return 0
        return numpy.around(float(self.dev_accs[-1]), 4)
    
    def get_dev_accs(self):
        return self.dev_accs
    
    def get_test_costs(self):
        return self.test_costs
    
    def get_test_accs(self):
        return self.test_accs