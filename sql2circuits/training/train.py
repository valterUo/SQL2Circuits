# -*- coding: utf-8 -*-

import warnings
import json
import os
from jax import numpy as np
from sympy import default_sort_key
import numpy
from jax import jit
from noisyopt import minimizeSPSA, minimizeCompass
from training.utils import *
from discopy.quantum import Circuit
from discopy.tensor import Tensor
#from pytket.extensions.qiskit import AerBackend
#from pytket.extensions.qulacs import QulacsBackend
#from pytket.extensions.cirq import CirqStateSampleBackend
backend = None
warnings.filterwarnings('ignore')
this_folder = os.path.abspath(os.getcwd())
os.environ['TOKENIZERS_PARALLELISM'] = 'true'
#os.environ["JAX_PLATFORMS"] = "cpu"

# This avoids TracerArrayConversionError from jax
Tensor.np = np

SEED = 0
rng = numpy.random.default_rng(SEED)
numpy.random.seed(SEED)

class SQL2CircuitsTrainer:

    def __init__(self, id, circuits, data_prep, workload = "execution_time", classification = 2, a = 0.01, c = 0.01):
        self.id = id
        self.circuits = circuits
        self.data_prep = data_prep
        self.workload = workload # execution_time or cardinality
        self.classification = classification
        self.plot_results = True
        diagrams = self.circuits.get_circuit_diagrams()
        self.stats = {}

        self.a = a
        self.c = c
        self.optimization_method = "SPSA"
        self.epochs = 1000
        self.initial_number_of_circuits = 20
        self.optimization_interval = 20
        self.result = None

        # Training, test and validation circuits
        self.training_circuits = diagrams["training"]
        self.test_circuits = diagrams["test"]
        self.validation_circuits = diagrams["validation"]

        # Training, test and validation data
        self.training_data = self.data_prep.get_training_data()
        self.test_data = self.data_prep.get_test_data()
        self.validation_data = self.data_prep.get_validation_data()

        self.training_data_list = [{"id": k, "cardinality": v} for k, v in self.training_data.items()]
        self.test_data_list= [{"id": k, "cardinality": v} for k, v in self.test_data.items()]
        self.validation_data_list = [{"id": k, "cardinality": v} for k, v in self.validation_data.items()]

        # Because we did not get a data point for each query (limited excution time), we need to remove the circuits that do not have a data point
        # Select all those circuits whose key is in the training_data dictionary
        self.training_circuits = {k: v for k, v in self.training_circuits.items() if k in self.training_data}
        self.test_circuits = {k: v for k, v in self.test_circuits.items() if k in self.test_data}
        self.validation_circuits = {k: v for k, v in self.validation_circuits.items() if k in self.validation_data}

        self.all_training_keys = list(self.training_circuits.keys())

        # Check that the keys of the circuits and the data are the same
        #print(set(self.training_circuits.keys()) - set(self.training_data.keys()))
        #print(set(self.test_circuits.keys()) - set(self.test_data.keys()))
        #print(set(self.validation_circuits.keys()) - set(self.validation_data.keys()))

        self.training_data_labels, classes = create_labeled_training_classes(self.training_data_list, self.classification, workload)
        self.test_data_labels = create_labeled_test_validation_classes(self.test_data_list, classes, workload)
        self.validation_data_labels = create_labeled_test_validation_classes(self.validation_data_list, classes, workload)

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
                "initial_number_of_circuits": self.initial_number_of_circuits,
                "classification": 2**self.classification,
                "workload": self.workload,
                "optimization_medthod": self.optimization_method
            }
        
        self.store_and_log("hyperparameters", hyperparameters, self.hyperparameters_file)

        self.run = 0
        
        initial_circuit_keys = self.all_training_keys[:self.initial_number_of_circuits + 1]
        self.current_training_circuits = {}
        for k in initial_circuit_keys:
            self.current_training_circuits[k] = self.training_circuits[k]
            
        self.syms = get_symbols(self.current_training_circuits)
        self.parameters = sorted(self.syms, key = default_sort_key)
        self.read_parameters()
    

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
        new_values = list(numpy.array(rng.random(len(new_params))))
        old_param_dict = {}
        for p, v in zip(old_params, old_values):
            old_param_dict[p] = v
            
        parameters = sorted(set(old_params + new_params), key=default_sort_key)
        values = []
        for p in parameters:
            if p in old_param_dict:
                values.append(old_param_dict[p])
            else:
                values.append(new_values.pop())
                
        return parameters, np.array(values)

    
    def make_pred_fn(self, circuits):
        circuit_fns = [circuit.lambdify(*self.parameters) for circuit in circuits]
        def predict(params):
            outputs = Circuit.eval(*(c(*params) for c in circuit_fns), backend = backend)
            res = []
            
            for output in outputs:
                predictions = np.abs(output.array) + 1e-9 # type: ignore
                ratio = predictions / predictions.sum()
                res.append(ratio)
                
            return np.array(res)
        return predict
    
    def make_cost_fn(self, predict, labels):
        def cost_fn(params, **kwargs):
            predictions = predict(params)
            cost = self.loss_function(predictions, labels)
            accuracy = self.accuracy(predictions, labels)
            costs.append(cost)
            accuracies.append(accuracy)
            return cost

        costs, accuracies = [], []
        return cost_fn, costs, accuracies
    

    def make_callback_fn(self, i, dev_cost_fn, train_costs, train_accs, dev_accs):
        def callback_fn(xk):
            valid_loss = dev_cost_fn(xk)
            valid_loss = numpy.around(float(valid_loss), 4)
            train_loss = numpy.around(min(float(train_costs[-1]), float(train_costs[-2])), 4)
            train_acc = numpy.around(min(float(train_accs[-1]), float(train_accs[-2])), 4)
            valid_acc = numpy.around(float(dev_accs[-1]), 4)
            iters = int(len(train_accs)/2)
            if iters % 200 == 0:
                stats_data = {"iters": iters, 
                            "train/loss": train_loss, 
                            "train/acc": train_acc, 
                            "valid/loss": valid_loss, 
                            "valid/acc": valid_acc}
                self.store_and_log(i, stats_data, self.stats_iter_file)
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
    
    def train(self):

        for i, key in enumerate(self.all_training_keys[self.initial_number_of_circuits:]):
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
            
            if self.result == None or self.run % self.optimization_interval == 0:
            
                train_pred_fn = jit(self.make_pred_fn(training_circuits_l))
                dev_pred_fn = jit(self.make_pred_fn(validation_circuits_l))
                test_pred_fn = self.make_pred_fn(test_circuits_l)

                train_cost_fn, train_costs, train_accs = self.make_cost_fn(train_pred_fn, training_data_labels_l)
                dev_cost_fn, dev_costs, dev_accs = self.make_cost_fn(dev_pred_fn, validation_data_labels_l)

                callback_fn = self.make_callback_fn(i, dev_cost_fn, train_costs, train_accs, dev_accs)
                
                # Actual optimization
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
                
                # Visualize the result
                if self.plot_results:
                    figure_path = "training//results//" + str(self.id) + "//" + str(self.id) + "_" + str(i) + ".png"
                    visualize_result_noisyopt(train_costs,
                                              train_accs,
                                              dev_costs,
                                              dev_accs,
                                              figure_path)
                
                # Evaluate the result on the test set
                test_cost_fn, _, test_accs = self.make_cost_fn(test_pred_fn, test_data_labels_l)
                test_cost_fn(self.result.x) # type: ignore
                self.store_and_log(i, {"test_accuracy": test_accs[0]}, self.result_file)
                self.store_parameters(self.result.x)
            
            # Extend for the next optimization round
            self.run += 1
            self.syms = get_symbols(self.current_training_circuits)
            self.current_training_circuits[key] = self.training_circuits[key]
            new_parameters = sorted(get_symbols({key: self.training_circuits[key]}), key = default_sort_key)
            self.parameters, self.init_params_spsa = self.initialize_parameters(self.parameters, self.result.x, new_parameters)