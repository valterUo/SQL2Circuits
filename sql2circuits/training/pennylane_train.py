# -*- coding: utf-8 -*-

import warnings
import os
import numpy
from sympy import default_sort_key
import torch
from training.utils import *
from discopy.tensor import Tensor
from sklearn.base import BaseEstimator
import pennylane as qml
from training.trainers.pennylane_trainer import make_pennylane_pred_fn, make_pennylane_cost_fn, make_pennylane_pred_fn_for_gradient_descent

warnings.filterwarnings('ignore')
this_folder = os.path.abspath(os.getcwd())
os.environ['TOKENIZERS_PARALLELISM'] = 'True'
#os.environ["JAX_PLATFORMS"] = "cpu"

# This avoids TracerArrayConversionError from jax
Tensor.np = np

SEED = 0
rng = numpy.random.default_rng(SEED)
numpy.random.seed(SEED)

class SQL2CircuitsEstimatorPennylane(BaseEstimator):

    def __init__(self, epochs = 100, classification = 2):
        #self.opt = qml.GradientDescentOptimizer()
        #self.opt = qml.AdagradOptimizer()
        self.opt = qml.AdamOptimizer()
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
        cost_function = make_pennylane_cost_fn(pred_fn, y, self.loss_function, self.accuracy)
        parameters = torch.tensor(rng.random(len(params)))

        for i in range(self.epochs):
            parameters = self.opt.step(cost_function, parameters)
            if i % 1 == 0:
                #print(f"parameters: {parameters}")
                print(f"Step {i}, Cost: {cost_function(parameters)}")
        return self


    def score(self, X, y):
        circuits = [item for sublist in X for item in sublist]
        accepted_circuits, y_new = select_pennylane_circuits(self.training_circuits, circuits, len(self.training_circuits), y)
        predict_fun_for_score = make_pennylane_pred_fn(accepted_circuits, self.parameters, self.classification)
        predictions = predict_fun_for_score(self.result.x)
        score = self.accuracy(predictions, y_new)
        print("Number of circuits: ", len(circuits), "Number of accepted circuits: ", len(accepted_circuits), "Score: ", score)
        return score