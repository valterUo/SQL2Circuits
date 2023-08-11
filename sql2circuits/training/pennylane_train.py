# -*- coding: utf-8 -*-

import warnings
import os
import numpy
from sympy import default_sort_key
from training.functions.pennylane_functions import *
from training.utils import *
from sklearn.base import BaseEstimator
import pennylane as qml
from pennylane import numpy as np

warnings.filterwarnings('ignore')
this_folder = os.path.abspath(os.getcwd())
os.environ['TOKENIZERS_PARALLELISM'] = 'True'

SEED = 0
rng = numpy.random.default_rng(SEED)
numpy.random.seed(SEED)

class SQL2CircuitsEstimatorPennylane(BaseEstimator):

    def __init__(self, optimizer, params, stepsize = 0.01, epochs = 1000, classification = 2):
        self.stepsize = stepsize
        self.optimizer = optimizer
        self.params = params

        self.optimizers = {
            "GradientDescent": qml.GradientDescentOptimizer(self.stepsize),
            "Adagrad": qml.AdagradOptimizer(),
            "Adam": qml.AdamOptimizer(),
            "QNGO": qml.QNGOptimizer(),
            "Rotosolve": qml.RotosolveOptimizer(),
            "RMSProp": qml.RMSPropOptimizer(),
            "Adaptive": qml.AdaptiveOptimizer(),
            "Momentum": qml.MomentumOptimizer(),
            "NesterovMomentum": qml.NesterovMomentumOptimizer(),
            "QNSPSA": qml.QNSPSAOptimizer(),
            "SPSA": qml.SPSAOptimizer(1000),
            "Rotoselect": qml.RotoselectOptimizer()
        }
        
        self.opt = self.optimizers[optimizer]
        
        self.epochs = epochs
        self.classification = classification
        self.loss_function = multi_class_loss
        self.accuracy = multi_class_acc
        self.parameters = np.array(rng.random(len(params)), requires_grad=True)


    def fit(self, X, y, **kwargs):
        self.training_circuits = [item for sublist in X for item in sublist]
        print("Number of training circuits: ", len(self.training_circuits))
        #syms = set()
        #for circ in self.training_circuits:
        #        for symbols in circ.get_param_symbols():
        #            for sym in symbols:
        #                syms.add(sym)
        #params = sorted(syms, key = default_sort_key)
        #print("Number of parameters: ", len(params))

        pred_fn = make_pennylane_pred_fn_for_gradient_descent(self.training_circuits)
        cost_function = make_pennylane_cost_fn(pred_fn, 
                                               y, 
                                               self.loss_function)
        #self.parameters = np.array(rng.random(len(params)), requires_grad=True)
        

        for i in range(self.epochs):
            if i % 10 == 0:
                print(f"Step {i}, Cost: {cost_function(self.parameters)}")
                print("Accuracy: ", self.accuracy(pred_fn(self.parameters), y))
                
            self.parameters = self.opt.step(cost_function, self.parameters)
        return self


    def score(self, X, y):
        circuits = [item for sublist in X for item in sublist]
        accepted_circuits, y_new = select_pennylane_circuits(self.training_circuits, circuits, len(self.training_circuits), y)
        predict_fun_for_score = make_pennylane_pred_fn(accepted_circuits, self.parameters, self.classification)
        predictions = predict_fun_for_score(self.result.x)
        score = self.accuracy(predictions, y_new)
        print("Number of circuits: ", len(circuits), "Number of accepted circuits: ", len(accepted_circuits), "Score: ", score)
        return score