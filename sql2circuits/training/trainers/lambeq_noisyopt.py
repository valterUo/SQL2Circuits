# -*- coding: utf-8 -*-

import warnings
import os

try:
    import jax
except ModuleNotFoundError:
    pass

from noisyopt import minimizeSPSA
from training.trainers.training_utils import make_callback_fn, read_parameters, visualize_result
from training.functions.lambeq_functions import make_lambeq_cost_fn, make_lambeq_pred_fn
from training.cost_accuracy import CostAccuracy
from training.utils import *
from sklearn.base import BaseEstimator

warnings.filterwarnings('ignore')
this_folder = os.path.abspath(os.getcwd())

class LambeqTrainer(BaseEstimator):

    def __init__(self, 
                id,
                circuits,
                workload_type, 
                classification,
                classical_optimizer,
                measurement,
                a, 
                c,
                identifier, 
                epochs = 500,
                plot_results = True):
        self.id = id
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
        self.parameters = []
        self.classical_optimizer = classical_optimizer
        self.measurement = measurement
        self.identifier = identifier

        if classification == 1:
            self.loss_function = bin_class_loss
            self.accuracy = bin_class_acc

        self.hyperparameters_file = "training//results//" + str(self.identifier) + "//" + "hyperparameters.json"

        hyperparameters = {
                "id": self.id,
                "a": a,
                "c": c,
                "epochs": self.epochs,
                "classification": 2**self.classification,
                "workload": self.workload,
                "optimization_medthod": self.classical_optimizer
            }
        
        store_and_log(0, hyperparameters, self.hyperparameters_file)
    

    def fit_with_lambeq_noisyopt(self, X, y, **kwargs):
        self.training_circuits = X
        training_data_labels = y

        print("Number of training circuits: ", len(self.training_circuits))
        validation_circuits = kwargs.get("validation_circuits", None)
        print("Number of validation circuits: ", len(validation_circuits))
        validation_labels = kwargs.get("validation_labels", None)

        current_validation_circuits = select_circuits(self.training_circuits, validation_circuits, len(self.training_circuits))
        current_validation_labels = []
        for circuit in current_validation_circuits:
            current_validation_labels.append(validation_labels[validation_circuits.index(circuit)])

        parameters, init_params_spsa = read_parameters(self.id, self.training_circuits)
        
        if self.measurement == "sample":
            raise Exception("Lambeq supports currently only state measurement.")

        train_pred_fn = make_lambeq_pred_fn(self.training_circuits, parameters, self.classification)
        val_pred_fn = make_lambeq_pred_fn(current_validation_circuits, parameters, self.classification)
        #test_pred_fn = self.make_pred_fn(test_circuits, self.parameters, self.classification)

        costs_accuracies = CostAccuracy()

        train_cost_fn = make_lambeq_cost_fn(train_pred_fn, training_data_labels, self.loss_function, self.accuracy, costs_accuracies, "train")
        dev_cost_fn = make_lambeq_cost_fn(val_pred_fn, current_validation_labels, self.loss_function, self.accuracy, costs_accuracies, "dev")

        callback_fn = make_callback_fn(dev_cost_fn, costs_accuracies, self.identifier)
        
        self.result = minimizeSPSA(train_cost_fn,
                                    x0 = init_params_spsa,
                                    a = self.a,
                                    c = self.c,
                                    niter = self.epochs,
                                    callback = callback_fn,
                                    paired=False)
        
        print("Store parameters: ", len(parameters), len(self.result.x))
        old_params = dict(zip(parameters, self.result.x))
        self.store_parameters(old_params)

        if self.plot_results:    
            visualize_result(0, costs_accuracies)
        
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
        self.fit_with_lambeq_noisyopt(X, y, X_valid = kwargs["X_valid"], save_parameters = False)
        return self


    def score(self, X, y):
        circuits = [item for sublist in X for item in sublist]
        accepted_circuits = []
        score = 0
        accepted_circuits, y_new = select_circuits(self.training_circuits, circuits, len(self.training_circuits), y)
        predict_fun_for_score = make_lambeq_pred_fn(accepted_circuits, self.parameters, self.classification)
        predictions = predict_fun_for_score(self.result.x)
        score = self.accuracy(predictions, y_new)
        print("Number of circuits: ", len(circuits), "Number of accepted circuits: ", len(accepted_circuits), "Score: ", score)
        return score