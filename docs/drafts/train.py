# -*- coding: utf-8 -*-

import warnings
import os
#from jax import numpy as np
import numpy as np
from sympy import default_sort_key
import numpy
#from jax import jit
from noisyopt import minimizeSPSA
from training.functions.lambeq_functions import make_lambeq_cost_fn, make_lambeq_pred_fn
from training.functions.pennylane_functions import make_pennylane_cost_fn, make_pennylane_pred_fn
from training.cost_accuracy import CostAccuracy
from training.utils import *
#from discopy.tensor import Tensor
from sklearn.base import BaseEstimator
from discopy.quantum.circuit import Circuit

warnings.filterwarnings('ignore')
this_folder = os.path.abspath(os.getcwd())
SEED = 0
rng = numpy.random.default_rng(SEED)
numpy.random.seed(SEED)


class SQL2CircuitsEstimator(BaseEstimator):

    def __init__(self, 
                id,
                circuits,
                workload_type, 
                classification,
                a, 
                c, 
                epochs,
                qc_framework,
                classical_optimizer,
                measurement,
                plot_results = True,):
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
        self.training_circuits = self.circuits.get_qml_training_circuits()
        self.parameters = []
        self.executions = 0
        self.qc_framework = qc_framework
        self.classical_optimizer = classical_optimizer
        self.measurement = measurement

        if classification == 1:
            self.loss_function = bin_class_loss
            self.accuracy = bin_class_acc
        
        # If the folder "result//" + str(self.id) does not exist, create it
        if not os.path.exists("training//results//" + str(self.id)):
            os.makedirs("training//results//" + str(self.id))

        self.result_file = "training//results//" + str(self.id) + "//" + str(self.id) + "_result.json"
        self.stats_iter_file = "training//results//" + str(self.id) + "//" + str(self.id) + "_stats_iteration_level.json"
        self.hyperparameters_file = "training//results//" + str(self.id) + "//" + str(self.id) + "_hyperparameters.json"

        hyperparameters = {
                "id": self.id,
                "a": a,
                "c": c,
                "epochs": self.epochs,
                "classification": 2**self.classification,
                "workload": self.workload,
                "optimization_medthod": self.classical_optimizer
            }
        
        store_and_log(self.executions, hyperparameters, self.hyperparameters_file)
    

    def store_parameters(self, params):
        stored_parameters = "training//checkpoints//" + str(self.id) + ".npz"
        with open(stored_parameters, "wb") as f:
            np.savez(f, params)
        print("Storing parameters in file " + stored_parameters)
    

    def read_parameters(self, circuits, all_params = None):
        syms = set()
        if type(get_element(circuits, 0)) == Circuit:
            syms = get_symbols(circuits)
        else:
            for circ in circuits:
                for symbols in circ.get_param_symbols():
                    for sym in symbols:
                        syms.add(sym)
        new_params = sorted(syms, key = default_sort_key)
        stored_parameters = "training//checkpoints//" + str(self.id) + ".npz"
        if os.path.exists(stored_parameters):
            with open(stored_parameters, "rb") as f:
                npzfile = np.load(f, allow_pickle=True)
                old_params = npzfile['arr_0'] # type: ignore
                print("Loading parameters from file " + stored_parameters)
                if type(old_params) == np.ndarray:
                    old_params = dict(old_params.item())
                    self.parameters = sorted(set(list(old_params.keys()) + new_params), key = default_sort_key)
                elif type(old_params) == dict:
                    self.parameters = sorted(set(list(old_params.keys()) + new_params), key = default_sort_key)
                values = []
                for p in self.parameters:
                    if p in old_params:
                        values.append(old_params[p])
                    else:
                        values.append(rng.random())
                self.init_params_spsa = values
        else:
            print("Initializing new parameters")
            self.parameters = new_params
            print(len(all_params))
            self.init_params_spsa = np.array(rng.random(len(all_params)))


    def initialize_parameters(self, old_params, old_values, new_params):
        old_param_dict = {}
        for p, v in zip(old_params, old_values):
            old_param_dict[p] = v
            
        parameters = sorted(set(old_params + new_params), key = default_sort_key)
        values = []
        for p in parameters:
            if p in old_param_dict:
                values.append(old_param_dict[p])
            else:
                values.append(rng.random())
                
        return parameters, np.array(values)
    

    def make_callback_fn(self, dev_cost_fn, costs_accuracies):
        def callback_fn(xk):
            #print(xk)
            valid_loss = dev_cost_fn(xk)
            valid_loss = numpy.around(float(valid_loss), 4)
            train_loss = costs_accuracies.get_train_loss()
            train_acc = costs_accuracies.get_train_acc()
            valid_acc = costs_accuracies.get_dev_acc()
            iters = int(len(costs_accuracies.get_train_costs())/2)
            if iters % 20 == 0:
                stats_data = {"iters": iters, 
                            "train/loss": train_loss, 
                            "train/acc": train_acc, 
                            "valid/loss": valid_loss, 
                            "valid/acc": valid_acc}
                store_and_log(self.executions, stats_data, self.stats_iter_file)
            return valid_loss
        return callback_fn


    def visualize_result(self, i, costs_accuracies):
        if self.plot_results:
            train_costs = costs_accuracies.get_train_costs()
            train_accs = costs_accuracies.get_train_accs()
            dev_costs = costs_accuracies.get_dev_costs()
            dev_accs = costs_accuracies.get_dev_accs()
            figure_path = "training//results//" + str(self.id) + "//" + str(self.id) + "_" + str(i) + ".png"
            visualize_result_noisyopt(train_costs, train_accs, dev_costs, dev_accs, figure_path)
            

    def evaluate_on_test_set(self, test_pred_fn, test_data_labels_l, costs_accuracies):
        if self.classical_optimizer == "lambeq":
            test_cost_fn = make_lambeq_cost_fn(test_pred_fn, test_data_labels_l, self.loss_function, self.accuracy, costs_accuracies, "test")
        elif self.classical_optimizer == "pennylane":
            test_cost_fn = make_pennylane_cost_fn(test_pred_fn, test_data_labels_l, self.loss_function, self.accuracy, costs_accuracies, "test")
        test_cost_fn(self.result.x) # type: ignore
        test_accs = costs_accuracies.get_test_accs()
        store_and_log(self.executions, { "test_accuracy": test_accs[0] }, self.result_file)
    

    def fit_with_lambeq_noisyopt(self, X, y, X_valid, save_parameters = True):
        self.training_circuits = [data[0] for data in X]
        training_data_labels = y

        validation_circuits = [data[0] for data in X_valid]
        validation_data_labels = [data[1] for data in X_valid]

        current_validation_circuits = select_circuits(self.training_circuits, validation_circuits, len(self.training_circuits))
        current_validation_labels = []
        for circuit in current_validation_circuits:
            current_validation_labels.append(validation_data_labels[validation_circuits.index(circuit)])

        self.read_parameters(self.training_circuits)

        print(len(self.training_circuits), len(training_data_labels))

        train_pred_fn = make_lambeq_pred_fn(self.training_circuits, self.parameters, self.classification)
        val_pred_fn = make_lambeq_pred_fn(current_validation_circuits, self.parameters, self.classification)
        #test_pred_fn = self.make_pred_fn(test_circuits, self.parameters, self.classification)

        costs_accuracies = CostAccuracy()

        train_cost_fn = jit(make_lambeq_cost_fn(train_pred_fn, training_data_labels, self.loss_function, self.accuracy, costs_accuracies, "train"))
        dev_cost_fn = jit(make_lambeq_cost_fn(val_pred_fn, current_validation_labels, self.loss_function, self.accuracy, costs_accuracies, "dev"))

        callback_fn = self.make_callback_fn(dev_cost_fn, costs_accuracies)
        
        self.result = minimizeSPSA(train_cost_fn,
                                x0 = self.init_params_spsa,
                                a = self.a,
                                c = self.c,
                                niter = self.epochs,
                                callback = callback_fn)
        
        if save_parameters:
            print("Store parameters: ", len(self.parameters), len(self.result.x))
            old_params = dict(zip(self.parameters, self.result.x))
            self.store_parameters(old_params)
                
        #self.visualize_result(0, costs_accuracies)
        #self.evaluate_on_test_set(test_pred_fn, test_data_labels_l, costs_accuracies)


    def fit_with_pennylane_noisyopt(self, X, y, X_valid, save_parameters = True):
        costs_accuracies = CostAccuracy()
        self.executions += 1
        self.training_circuits = [data[0] for data in X]
        training_data_labels = y

        validation_circuits = [data[0] for data in X_valid]
        validation_data_labels = [data[1] for data in X_valid]

        current_validation_circuits = select_pennylane_circuits(self.training_circuits, validation_circuits, len(self.training_circuits))
        current_validation_labels = []
        for circuit in current_validation_circuits:
            current_validation_labels.append(validation_data_labels[validation_circuits.index(circuit)])

        self.read_parameters(self.training_circuits, self.circuits.get_qml_train_symbols())

        print("Number of training circuits: ", len(self.training_circuits))

        train_pred_fn = make_pennylane_pred_fn(self.training_circuits, self.parameters, self.classification)
        print("Number of current validation circuits: ", len(current_validation_circuits))
        dev_pred_fn = make_pennylane_pred_fn(current_validation_circuits, self.parameters, self.classification)
        #test_pred_fn = make_pennylane_pred_fn(test_circuits_l, self.test_symbols, self.classification)
        
        train_cost_fn = make_pennylane_cost_fn(train_pred_fn, training_data_labels, self.loss_function, self.accuracy, costs_accuracies, "train")
        dev_cost_fn = make_pennylane_cost_fn(dev_pred_fn, current_validation_labels, self.loss_function, self.accuracy, costs_accuracies, "dev")

        callback_fn = self.make_callback_fn(dev_cost_fn, costs_accuracies)
        
        self.result = minimizeSPSA(train_cost_fn,
                                   x0 = self.init_params_spsa,
                                   a = self.a,
                                   c = self.c,
                                   niter = self.epochs,
                                   callback = callback_fn)
        
        if save_parameters:
            print("Store parameters: ", len(self.parameters), len(self.result.x))
            old_params = dict(zip(self.parameters, self.result.x))
            self.store_parameters(old_params)

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
        if self.classical_optimizer == "lambeq":
            self.fit_with_lambeq_noisyopt(X, y, X_valid = kwargs["X_valid"], save_parameters = False)
        elif self.classical_optimizer == "pennylane":
            self.fit_with_pennylane_noisyopt(X, y, X_valid = kwargs["X_valid"], save_parameters = True)
        return self


    def score(self, X, y):
        circuits = [item for sublist in X for item in sublist]
        accepted_circuits = []
        score = 0
        if self.classical_optimizer == "pennylane":
            accepted_circuits, y_new = select_pennylane_circuits(self.training_circuits, circuits, len(self.training_circuits), y)
            predict_fun_for_score = make_pennylane_pred_fn(accepted_circuits, self.parameters, self.classification)
            predictions = predict_fun_for_score(self.result.x)
            score = self.accuracy(predictions, y_new)
        else:
            accepted_circuits, y_new = select_circuits(self.training_circuits, circuits, len(self.training_circuits), y)
            predict_fun_for_score = make_lambeq_pred_fn(accepted_circuits, self.parameters, self.classification)
            predictions = predict_fun_for_score(self.result.x)
            score = self.accuracy(predictions, y_new)
        print("Number of circuits: ", len(circuits), "Number of accepted circuits: ", len(accepted_circuits), "Score: ", score)
        return score