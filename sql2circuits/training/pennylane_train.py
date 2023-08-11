# -*- coding: utf-8 -*-

import warnings
import os
import numpy
from sympy import default_sort_key
from training.cost_accuracy import CostAccuracy
from training.utils import *
from sklearn.base import BaseEstimator
import pennylane as qml
from pennylane import numpy as np
from training.trainers.pennylane_trainer import make_pennylane_pred_fn, make_pennylane_cost_fn, make_pennylane_pred_fn_for_gradient_descent

warnings.filterwarnings('ignore')
this_folder = os.path.abspath(os.getcwd())
os.environ['TOKENIZERS_PARALLELISM'] = 'True'
#os.environ["JAX_PLATFORMS"] = "cpu"

# This avoids TracerArrayConversionError from jax
#Tensor.np = np

SEED = 0
rng = numpy.random.default_rng(SEED)
numpy.random.seed(SEED)

class SQL2CircuitsEstimatorPennylane(BaseEstimator):

    def __init__(self, epochs = 10000, classification = 2):
        
        self.optimizers = {
            "GradientDescent": qml.GradientDescentOptimizer(),
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
        
        self.opt = self.optimizers["GradientDescent"]
        
        self.epochs = epochs
        self.classification = classification
        self.loss_function = multi_class_loss
        self.accuracy = multi_class_acc


    def fit(self, X, y, **kwargs):
        circuits = [item for sublist in X for item in sublist]

        syms = set()
        for circ in circuits:
                for symbols in circ.get_param_symbols():
                    for sym in symbols:
                        syms.add(sym)
        params = sorted(syms, key = default_sort_key)

        pred_fn = make_pennylane_pred_fn_for_gradient_descent(circuits)
        cost_function = make_pennylane_cost_fn(pred_fn, 
                                               y, 
                                               self.loss_function)
        parameters = np.array(rng.random(len(params)), requires_grad=True)
        

        for i in range(self.epochs):
            if i % 10 == 0:
                print(f"Step {i}, Cost: {cost_function(parameters)}")
                print("Accuracy: ", self.accuracy(pred_fn(parameters), y))
                
            parameters = self.opt.step(cost_function, parameters)
        return self


    def score(self, X, y):
        circuits = [item for sublist in X for item in sublist]
        accepted_circuits, y_new = select_pennylane_circuits(self.training_circuits, circuits, len(self.training_circuits), y)
        predict_fun_for_score = make_pennylane_pred_fn(accepted_circuits, self.parameters, self.classification)
        predictions = predict_fun_for_score(self.result.x)
        score = self.accuracy(predictions, y_new)
        print("Number of circuits: ", len(circuits), "Number of accepted circuits: ", len(accepted_circuits), "Score: ", score)
        return score