# -*- coding: utf-8 -*-

import warnings
import os
#from jax import numpy as np
#from jax import jit
from noisyopt import minimizeSPSA
from training.trainers.training_utils import make_callback_fn, read_parameters, store_parameters
from training.functions.pennylane_functions import make_pennylane_cost_fn, make_pennylane_pred_fn, make_pennylane_pred_fn_for_gradient_descent
from training.cost_accuracy import CostAccuracy
from training.utils import *
#from discopy.tensor import Tensor
from sklearn.base import BaseEstimator

warnings.filterwarnings('ignore')
this_folder = os.path.abspath(os.getcwd())
#os.environ['TOKENIZERS_PARALLELISM'] = 'True'
#os.environ["JAX_PLATFORMS"] = "cpu"

# This avoids TracerArrayConversionError from jax
#Tensor.np = np


class PennylaneTrainer(BaseEstimator):

    def __init__(self, 
                identifier,
                circuits,
                workload_type, 
                classification,
                classical_optimizer,
                measurement,
                a, 
                c, 
                epochs = 500,
                plot_results = True):
        self.identifier = identifier
        self.workload = workload_type
        self.classification = classification
        self.plot_results = plot_results
        self.a = a
        self.c = c
        self.epochs = epochs
        self.result = None
        self.loss_function = multi_class_loss
        self.accuracy = multi_class_acc
        self.circuits = circuits
        self.training_circuits = self.circuits.get_qml_training_circuits()
        self.parameters = []
        self.executions = 0
        self.classical_optimizer = classical_optimizer
        self.measurement = measurement

        if classification == 1:
            self.loss_function = bin_class_loss
            self.accuracy = bin_class_acc

        if not os.path.exists("training//results//" + str(self.identifier)):
            os.makedirs("training//results//" + str(self.identifier))

        hyperparameters_file = "training//results//" + str(self.identifier) + "//" + "hyperparameters.json"

        hyperparameters = {
                "id": str(self.identifier),
                "a": a,
                "c": c,
                "epochs": self.epochs,
                "classification": 2**self.classification,
                "workload": self.workload,
                "optimization_medthod": self.classical_optimizer
            }
        
        with open(hyperparameters_file, "w") as f:
                json.dump(hyperparameters, f, indent=4)


    def fit_with_pennylane_noisyopt(self, X, y, **kwargs):
        costs_accuracies = CostAccuracy()
        self.executions += 1
        self.training_circuits = X
        training_data_labels = y

        print("Number of training circuits: ", len(self.training_circuits))
        validation_circuits = kwargs.get("validation_circuits", None)
        print("Number of validation circuits: ", len(validation_circuits))
        validation_labels = kwargs.get("validation_labels", None)
        qml_params = kwargs.get("qml_params", None)

        current_validation_circuits = select_pennylane_circuits(self.training_circuits, validation_circuits, len(self.training_circuits))
        current_validation_labels = []
        for circuit in current_validation_circuits:
            current_validation_labels.append(validation_labels[validation_circuits.index(circuit)])

        parameters, init_params_spsa = read_parameters(self.identifier, self.training_circuits, qml_params)
        train_pred_fn = None
        dev_pred_fn =  None
        
        if self.measurement == "sample":
            train_pred_fn = make_pennylane_pred_fn(self.training_circuits, parameters, self.classification)
            dev_pred_fn = make_pennylane_pred_fn(current_validation_circuits, parameters, self.classification)
        elif self.measurement == "state":
            train_pred_fn = make_pennylane_pred_fn_for_gradient_descent(self.training_circuits)
            dev_pred_fn = make_pennylane_pred_fn_for_gradient_descent(current_validation_circuits)
        
        train_cost_fn = make_pennylane_cost_fn(train_pred_fn, training_data_labels, self.loss_function, self.accuracy, costs_accuracies, "train")
        dev_cost_fn = make_pennylane_cost_fn(dev_pred_fn, current_validation_labels, self.loss_function, self.accuracy, costs_accuracies, "dev")
            
        callback_fn = make_callback_fn(dev_cost_fn, costs_accuracies, str(self.identifier))
        
        self.result = minimizeSPSA(train_cost_fn,
                                   x0 = init_params_spsa,
                                   a = self.a,
                                   c = self.c,
                                   niter = self.epochs,
                                   callback = callback_fn,
                                   paired=False)
        
        old_params = dict(zip(parameters, self.result.x))
        store_parameters(self.identifier, old_params)

        return self.result


    def fit(self, X, y, **kwargs):
        """
        
        This method is called by the scikit-learn BayesSearchCV class
        which is used to optimize hyperparameters a and c in SPSA algorithm.

        Parameters
        X       array-like of shape (n_samples, n_features)
        y       array-like of shape (n_samples,)
        kwargs  optional data-dependent parameters

        """

        self.fit_with_pennylane_noisyopt(X, y, X_valid = kwargs["X_valid"], save_parameters = True)
        return self


    def score(self, X, y):
        circuits = [item for sublist in X for item in sublist]
        accepted_circuits = []
        score = 0
        accepted_circuits, y_new = select_pennylane_circuits(self.training_circuits, circuits, len(self.training_circuits), y)
        predict_fun_for_score = make_pennylane_pred_fn(accepted_circuits, self.parameters, self.classification)
        predictions = predict_fun_for_score(self.result.x)
        score = self.accuracy(predictions, y_new)
        print("Number of circuits: ", len(circuits), "Number of accepted circuits: ", len(accepted_circuits), "Score: ", score)
        return score