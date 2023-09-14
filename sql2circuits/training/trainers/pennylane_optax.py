# -*- coding: utf-8 -*-

import warnings
import os
import numpy
from training.functions.pennylane_functions import *
from training.utils import *
from sklearn.base import BaseEstimator

try:
    from jax import numpy as np
    import jax
    import optax
except ModuleNotFoundError:
    try:
        from pennylane import numpy as np
    except ModuleNotFoundError:
        import numpy as np



warnings.filterwarnings('ignore')
this_folder = os.path.abspath(os.getcwd())
os.environ['TOKENIZERS_PARALLELISM'] = 'True'

SEED = 0
rng = numpy.random.default_rng(SEED)
numpy.random.seed(SEED)

# This avoids TracerArrayConversionError from jax
#from discopy.tensor import Tensor
#Tensor.np = np

class PennylaneTrainerJAX(BaseEstimator):

    def __init__(self, identifier, optimizer, params, stepsize = 0.01, learning_rate = 0.01, epochs = 200, classification = 2):
        self.identifier = identifier
        self.stepsize = stepsize
        self.optimizer = optimizer
        self.params = params
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.classification = classification
        self.loss_function = multi_class_loss
        self.accuracy = multi_class_acc
        self.parameters = np.array(rng.random(len(params)))

        this_folder = os.path.abspath(os.getcwd())
        # If there exists a file with the parameters, load them
        if os.path.isfile(this_folder + "/training/parameters/" + self.identifier + ".npy"):
            self.parameters = np.load(this_folder + "/training/parameters/" + self.identifier + ".npy")
            print("Parameters loaded from file")
        else:
            print("No parameters file found")



    def train(self, X, y, **kwargs):
        self.training_circuits = [item for sublist in X for item in sublist]
        print("Number of training circuits: ", len(self.training_circuits))

        pred_fn = make_pennylane_pred_fn_for_gradient_descent(self.training_circuits)
        cost_function = make_pennylane_cost_fn(pred_fn, y, self.loss_function)
        #cost_function = jax.checkpoint(cost_function)
        #cost_function = jax.jit(cost_function)

        self.opt = optax.adam(self.learning_rate)
        opt_state = self.opt.init(self.parameters)

        for i in range(self.epochs):
            cost, grad_circuit = jax.value_and_grad(cost_function)(self.parameters)
            #grad_circuit = jax.grad(cost_function)(self.parameters)
            updates, opt_state = self.opt.update(grad_circuit, opt_state)
            self.parameters = optax.apply_updates(self.parameters, updates)
            
            if i % 10 == 0:
                print(f"Step {i}, Cost: {cost}")
                #print(f"Step {i}")
                print("Accuracy: ", self.accuracy(pred_fn(self.parameters), y))
        
        # Save the parameters
        np.save(this_folder + "/training/parameters/" + self.identifier + ".npy", self.parameters)

        return self.parameters


    def fit(self, X, y, **kwargs):
        self.train(X, y, **kwargs)
        return self


    def score(self, X, y):
        circuits = [item for sublist in X for item in sublist]
        accepted_circuits, y_new = select_pennylane_circuits(self.training_circuits, circuits, len(self.training_circuits), y)
        predict_fun_for_score = make_pennylane_pred_fn_for_gradient_descent(accepted_circuits)
        predictions = predict_fun_for_score(self.parameters)
        score = self.accuracy(predictions, y_new)
        print("Number of circuits: ", len(circuits), "Number of accepted circuits: ", len(accepted_circuits), "Score: ", score)
        return score