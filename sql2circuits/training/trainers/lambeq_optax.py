# -*- coding: utf-8 -*-

import warnings
import os
import numpy
from training.functions.lambeq_functions import make_lambeq_cost_fn, make_lambeq_pred_fn
from training.utils import *
from sklearn.base import BaseEstimator

try:
    from jax import numpy as np
    import jax
    import optax
except ModuleNotFoundError:
    import numpy as np

warnings.filterwarnings('ignore')
this_folder = os.path.abspath(os.getcwd())
os.environ['TOKENIZERS_PARALLELISM'] = 'True'

SEED = 0
rng = numpy.random.default_rng(SEED)
numpy.random.seed(SEED)

# This avoids TracerArrayConversionError from jax
from discopy.tensor import Tensor
Tensor.np = np

class LambeqTrainerJAX(BaseEstimator):

    def __init__(self, identifier, optimizer, params, learning_rate, epochs, classification):
        self.identifier = identifier
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
            if not os.path.exists(this_folder + "/training/parameters/"):
                os.makedirs(this_folder + "/training/parameters/")
            np.save(this_folder + "/training/parameters/" + self.identifier + ".npy", self.parameters)



    def train(self, X, y, **kwargs):
        self.training_circuits = X #[item for sublist in X for item in sublist]
        print("Number of training circuits: ", len(self.training_circuits))
        validation_circuits = kwargs.get("validation_circuits", None)
        print("Number of validation circuits: ", len(validation_circuits))
        validation_labels = kwargs.get("validation_labels", None)

        pred_fn = make_lambeq_pred_fn(self.training_circuits, self.params, self.classification)
        cost_function = make_lambeq_cost_fn(pred_fn, y, self.loss_function, self.accuracy)
        #cost_function = jax.checkpoint(cost_function)
        #cost_function = jax.jit(cost_function)
        
        valid_pred_fn = make_lambeq_pred_fn(validation_circuits, self.params, self.classification)

        self.opt = optax.adam(self.learning_rate)
        opt_state = self.opt.init(self.parameters)

        for i in range(self.epochs):
            cost, grad_circuit = jax.value_and_grad(cost_function)(self.parameters)
            #grad_circuit = jax.grad(cost_function)(self.parameters)
            updates, opt_state = self.opt.update(grad_circuit, opt_state)
            self.parameters = optax.apply_updates(self.parameters, updates)
            
            if i % 10 == 0:
                training_acc = self.accuracy(pred_fn(self.parameters), y)
                valid_acc = self.accuracy(valid_pred_fn(self.parameters), validation_labels)
                
                print(f"Step {i}, Cost: {cost}")
                print("Accuracy: ", training_acc)
                print("Validation accuracy: ", valid_acc)

                log_file = this_folder + "//training//results//" + self.identifier + "//" + self.identifier + "_accuracy.json"
                if not os.path.isfile(log_file):
                    with open(log_file, "w") as f:
                        json.dump({"results": []}, f, indent=4)
                with open(log_file, "r") as f:
                    file = json.load(f)
                    file["results"].append({ "step": i, "accuracy": training_acc, "validation_accuracy": valid_acc })
                    json.dump(file, open(log_file, "w"), indent=4)

        np.save(this_folder + "//training//parameters//" + self.identifier + ".npy", self.parameters)
        return self.parameters