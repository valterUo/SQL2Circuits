# -*- coding: utf-8 -*-

import warnings
import json
import os
from jax import numpy as np
#import numpy as np
from sympy import default_sort_key
import numpy
from jax import jit
from noisyopt import minimizeSPSA, minimizeCompass
from training.cost_accuracy import CostAccuracy
from training.utils import *
from discopy.tensor import Tensor
from sklearn.base import BaseEstimator

from training.trainers.lambeq_trainer import make_lambeq_pred_fn, make_lambeq_cost_fn
from training.trainers.pennylane_trainer import make_pennylane_pred_fn, make_pennylane_cost_fn, transform_into_pennylane_circuits

warnings.filterwarnings('ignore')
this_folder = os.path.abspath(os.getcwd())
os.environ['TOKENIZERS_PARALLELISM'] = 'True'
#os.environ["JAX_PLATFORMS"] = "cpu"

# This avoids TracerArrayConversionError from jax
Tensor.np = np

SEED = 0
rng = numpy.random.default_rng(SEED)
numpy.random.seed(SEED)


class SQL2CircuitsEstimator(BaseEstimator):

    def __init__(self, 
                 id, 
                 workload = "execution_time", 
                 classification = 2, 
                 a = 0.01, 
                 c = 0.01, 
                 optimization_method = "SPSA", 
                 epochs = 1000, 
                 plot_results = True):
        self.id = id
        self.workload = workload
        self.classification = classification
        self.plot_results = plot_results
        self.stats = {}
        self.a = a
        self.c = c
        self.optimization_method = optimization_method
        self.epochs = epochs
        self.run = 0
        self.result = None
        self.make_pred_fn = make_lambeq_pred_fn
        self.make_cost_fn = make_lambeq_cost_fn
        self.loss_function = multi_class_loss
        self.accuracy = multi_class_acc

        if classification == 1:
            self.loss_function = bin_class_loss
            self.accuracy = bin_class_acc
        
        # If the folder "result//" + str(self.id) does not exist, create it
        if not os.path.exists("training//results//" + str(self.id)):
            os.makedirs("training//results//" + str(self.id))

        self.result_file = "training//results//" + str(self.id) + "//" + str(self.id) + "_result.json"
        self.stats_circuits_file = "training//results//" + str(self.id) + "//" + str(self.id) + "_stats_circuits_level.json"
        self.stats_iter_file = "training//results//" + str(self.id) + "//" + str(self.id) + "_stats_iteration_level.json"
        self.hyperparameters_file = "training//results//" + str(self.id) + "//" + str(self.id) + "_hyperparameters.json"

        hyperparameters = {
                "id": self.id,
                "a": self.a,
                "c": self.c,
                "epochs": self.epochs,
                "classification": 2**self.classification,
                "workload": self.workload,
                "optimization_medthod": self.optimization_method
            }
        
        self.store_and_log("hyperparameters", hyperparameters, self.hyperparameters_file)
    

    def store_parameters(self, params):
        stored_parameters = "training//checkpoints//" + str(self.id) + ".npz"
        with open(stored_parameters, "wb") as f:
            np.savez(f, params)
        print("Storing parameters in file " + stored_parameters)
    

    def read_parameters(self):
        stored_parameters = "training//checkpoints//" + str(self.id) + ".npz"
        if os.path.exists(stored_parameters):
            with open(stored_parameters, "rb") as f:
                npzfile = np.load(f)
                self.init_params_spsa = npzfile['arr_0'] # type: ignore
                print("Loading parameters from file " + stored_parameters)
        else:
            print("Initializing new parameters")
            self.init_params_spsa = np.array(rng.random(len(self.parameters)))


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
                self.store_and_log(iters, stats_data, self.stats_iter_file)
            return valid_loss
        return callback_fn
    

    def store_and_log(self, iteration, data, file):
        info = ""
        for k, v in data.items():
            info += k + ": " + str(v) + "\n"
        print(info, file = sys.stderr)

        current_data = data
        if os.path.exists(file):
            with open(file, 'r') as f:
                current_data = json.load(f)
            current_data[iteration] = data
            with open(file, 'w') as f:
                json.dump(current_data, f, indent = 4)
        else:
            with open(file, 'w') as f:
                json.dump({str(iteration) : current_data}, f, indent = 4)


    def visualize_result(self, i, costs_accuracies):
        if self.plot_results:
            train_costs = costs_accuracies.get_train_costs()
            train_accs = costs_accuracies.get_train_accs()
            dev_costs = costs_accuracies.get_dev_costs()
            dev_accs = costs_accuracies.get_dev_accs()
            figure_path = "training//results//" + str(self.id) + "//" + str(self.id) + "_" + str(i) + ".png"
            visualize_result_noisyopt(train_costs, train_accs, dev_costs, dev_accs, figure_path)
            

    def evaluate_on_test_set(self, test_pred_fn, test_data_labels_l, costs_accuracies):
        if self.optimization_method == "SPSA":
            test_cost_fn = make_lambeq_cost_fn(test_pred_fn, test_data_labels_l, self.loss_function, self.accuracy, costs_accuracies, "test")
        elif self.optimization_method == "Pennylane":
            test_cost_fn = make_pennylane_cost_fn(test_pred_fn, test_data_labels_l, self.loss_function, self.accuracy, costs_accuracies, "test")
        test_cost_fn(self.result.x) # type: ignore
        test_accs = costs_accuracies.get_test_accs()
        self.store_and_log(i, { "test_accuracy": test_accs[0] }, self.result_file)
        self.store_parameters(self.result.x) # type: ignore
    

    def fit_with_lambeq_noisyopt(self, X, y, X_valid):

        """for i, key in enumerate(self.all_training_keys[self.initial_number_of_circuits:]):
            print("Progress: ", round((i + self.initial_number_of_circuits)/len(self.all_training_keys), 3))
            
            if len(self.syms) == len(get_symbols(self.current_training_circuits)) and i > 0:
                if i != len(self.all_training_keys[1:]):
                    self.current_training_circuits[key] = self.training_circuits[key]
                    new_parameters = sorted(get_symbols({ key: self.training_circuits[key] }), key = default_sort_key)
                    if self.result:
                        self.parameters, self.init_params_spsa = self.initialize_parameters(self.parameters, self.result.x, new_parameters)
                    else:
                        self.syms = get_symbols(self.current_training_circuits)
                        self.parameters = sorted(self.syms, key=default_sort_key)
                        self.init_params_spsa = np.array(rng.random(len(self.parameters)))
            else:
                self.run += 1
            
            # Select those circuits from test and validation circuits which share the parameters with the current training circuits
            current_validation_circuits = select_circuits(self.current_training_circuits, self.validation_circuits)
            current_test_circuits = select_circuits(self.current_training_circuits, self.test_circuits)
            
            if len(current_validation_circuits) == 0 or len(current_test_circuits) == 0:
                continue
            
            # Create lists with circuits and their corresponding label
            training_circuits_l, training_data_labels_l = construct_data_and_labels(self.current_training_circuits, self.training_data_labels)
            validation_circuits_l, validation_data_labels_l = construct_data_and_labels(current_validation_circuits, self.validation_data_labels)
            test_circuits_l, test_data_labels_l = construct_data_and_labels(current_test_circuits, self.test_data_labels)

        self.stats[i] = {"number_of_training_circuits": len(training_circuits_l), 
                            "number_of_validation_circuits": len(validation_circuits_l), 
                            "number_of_test_circuits": len(test_circuits_l), 
                            "number_of_parameters_in_model": len(set([sym for circuit in training_circuits_l for sym in circuit.free_symbols]))}
        
        self.store_and_log(i, self.stats[i], self.stats_circuits_file)
        
        # Train if there is no result yet or if the optimization interval is reached or if this is the last circuit
        if self.result == None or self.run % self.optimization_interval == 0 or i == len(self.all_training_keys[self.initial_number_of_circuits:]) - 1:"""
        
        training_circuits = [data[0] for data in X]
        training_data_labels = [data[1] for data in X]

        validation_circuits = [data[0] for data in X_valid]
        validation_data_labels = [data[1] for data in X_valid]

        test_circuits = [data[0] for data in y]

        syms = get_symbols(training_circuits)
        self.parameters = sorted(syms, key = default_sort_key)
        self.read_parameters()

        print(len(training_circuits), len(training_data_labels))

        train_pred_fn = jit(self.make_pred_fn(training_circuits, self.parameters, self.classification))
        val_pred_fn = jit(self.make_pred_fn(validation_circuits, self.parameters, self.classification))
        test_pred_fn = self.make_pred_fn(test_circuits, self.parameters, self.classification)

        costs_accuracies = CostAccuracy()

        train_cost_fn = make_lambeq_cost_fn(train_pred_fn, training_data_labels, self.loss_function, self.accuracy, costs_accuracies, "train")
        dev_cost_fn = make_lambeq_cost_fn(val_pred_fn, validation_data_labels, self.loss_function, self.accuracy, costs_accuracies, "dev")

        callback_fn = self.make_callback_fn(dev_cost_fn, costs_accuracies)
        
        self.result = minimizeSPSA(train_cost_fn,
                                x0 = self.init_params_spsa,
                                a = self.a,
                                c = self.c,
                                niter = self.epochs,
                                callback = callback_fn)
                
        """self.result = minimizeCompass(train_cost_fn, 
                                        x0 = self.init_params_spsa,
                                        redfactor=2.0, 
                                        deltainit=1.0, 
                                        deltatol=0.001, 
                                        feps=1e-15, 
                                        errorcontrol=True, 
                                        funcNinit=30, 
                                        funcmultfactor=2.0, 
                                        paired=True, 
                                        alpha=0.05, 
                                        callback=callback_fn)"""
                
                #self.visualize_result(0, costs_accuracies)
                #self.evaluate_on_test_set(test_pred_fn, test_data_labels_l, costs_accuracies)
            
            # Extend for the next optimization round
            #self.run += 1
            #self.syms = get_symbols(self.current_training_circuits)
            #self.current_training_circuits[key] = self.training_circuits[key]
            #new_parameters = sorted(get_symbols({key: self.training_circuits[key]}), key = default_sort_key)
            #self.parameters, self.init_params_spsa = self.initialize_parameters(self.parameters, self.result.x, new_parameters)


    def fit_with_pennylane_noisyopt(self, X, y):
        costs_accuracies = CostAccuracy()

        #self.training_circuits_limited = {}
        #for key in self.all_training_keys[:10]:
        #    self.training_circuits_limited[key] = self.training_circuits[key]

         # Select those circuits from test and validation circuits which share the parameters with the current training circuits
        #validation_circuits_limited = select_pennylane_circuits(self.training_circuits_limited, self.validation_circuits, 10)
        #test_circuits_limited = select_pennylane_circuits(self.training_circuits_limited, self.test_circuits, 10)

        #self.validation_circuits = validation_circuits_limited
        #self.test_circuits = test_circuits_limited

        #training_circuits_l, training_data_labels_l = construct_data_and_labels(self.training_circuits, self.training_data_labels)
        #validation_circuits_l, validation_data_labels_l = construct_data_and_labels(self.validation_circuits, self.validation_data_labels)
        #test_circuits_l, test_data_labels_l = construct_data_and_labels(self.test_circuits, self.test_data_labels)

        train_pred_fn = jit(make_pennylane_pred_fn(training_circuits_l, self.train_symbols, self.classification))
        dev_pred_fn = jit(make_pennylane_pred_fn(validation_circuits_l, self.val_symbols, self.classification))
        #test_pred_fn = make_pennylane_pred_fn(test_circuits_l, self.test_symbols, self.classification)
        
        train_cost_fn = make_pennylane_cost_fn(train_pred_fn, training_data_labels_l, self.loss_function, self.accuracy, costs_accuracies, "train")
        dev_cost_fn = make_pennylane_cost_fn(dev_pred_fn, validation_data_labels_l, self.loss_function, self.accuracy, costs_accuracies, "dev")

        callback_fn = self.make_callback_fn(dev_cost_fn, costs_accuracies)
        
        self.result = minimizeSPSA(train_cost_fn,
                                   x0 = self.init_params_spsa,
                                   a = self.a,
                                   c = self.c,
                                   niter = self.epochs,
                                   callback = callback_fn)
        
        #self.visualize_result(0, costs_accuracies)
        #self.evaluate_on_test_set(test_pred_fn, test_data_labels_l, costs_accuracies)


    def predict_with_pennylane_noisyopt(self, X):
        predict_fun = make_pennylane_pred_fn([X], [], self.classification)
        return predict_fun(self.result.x)
    

    def predict_with_lambeq_noisyopt(self, X):
        predict_fun = make_lambeq_pred_fn([X], self.parameters, self.classification)
        return predict_fun(self.result.x)


    def fit(self, X, y, **kwargs):
        """
        Parameters
        X       array-like of shape (n_samples, n_features)
        y       array-like of shape (n_samples,)
        kwargs  optional data-dependent parameters
        """
        if self.optimization_method == "SPSA":
            self.fit_with_lambeq_noisyopt(X, y, X_valid = kwargs["X_valid"])
        elif self.optimization_method == "PennyLane":
            self.fit_with_pennylane_noisyopt(X, y, X_valid = kwargs["X_valid"])
        return self
    

    def predict(self, X):
        if self.optimization_method == "SPSA":
            return self.predict_with_lambeq_noisyopt(X)
        elif self.optimization_method == "PennyLane":
            return self.predict_with_pennylane_noisyopt(X)