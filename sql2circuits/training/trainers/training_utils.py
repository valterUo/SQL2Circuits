import json
import os
import numpy as np
from sympy import default_sort_key
from discopy.quantum.circuit import Circuit

from training.utils import get_element, get_symbols, store_and_log, visualize_result_noisyopt

this_folder = os.path.abspath(os.getcwd())
SEED = 0
rng = np.random.default_rng(SEED)
np.random.seed(SEED)


def make_callback_fn(dev_cost_fn, costs_accuracies, identifier):
    def callback_fn(xk):
        #print(xk)
        valid_loss = dev_cost_fn(xk)
        valid_loss = np.around(float(valid_loss), 4)
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
            log_file = this_folder + "//training//results//" + identifier + "//" + identifier + "_accuracy.json"
            if not os.path.isfile(log_file):
                with open(log_file, "w") as f:
                    json.dump({"results": []}, f, indent=4)
            with open(log_file, "r") as f:
                file = json.load(f)
                file["results"].append(stats_data)
                json.dump(file, open(log_file, "w"), indent=4)
        return valid_loss
    return callback_fn


def store_parameters(id, params):
    stored_parameters = "training//checkpoints//" + str(id) + ".npz"
    with open(stored_parameters, "wb") as f:
        np.savez(f, params)
    print("Storing parameters in file " + stored_parameters)


def initialize_parameters(old_params, old_values, new_params):
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


def visualize_result(id, i, costs_accuracies):
    train_costs = costs_accuracies.get_train_costs()
    train_accs = costs_accuracies.get_train_accs()
    dev_costs = costs_accuracies.get_dev_costs()
    dev_accs = costs_accuracies.get_dev_accs()
    figure_path = "training//results//" + str(id) + "//" + str(id) + "_" + str(i) + ".png"
    visualize_result_noisyopt(train_costs, train_accs, dev_costs, dev_accs, figure_path)


def read_parameters(id, circuits):
    syms = set()
    parameters = []
    init_params_spsa = []
    if type(get_element(circuits, 0)) == Circuit:
        syms = get_symbols(circuits)
    else:
        syms = set(all_params.keys())
    new_params = sorted(syms, key = default_sort_key)
    stored_parameters = "training//checkpoints//" + str(id) + ".npz"
    if os.path.exists(stored_parameters):
        with open(stored_parameters, "rb") as f:
            npzfile = np.load(f, allow_pickle=True)
            old_params = npzfile['arr_0'] # type: ignore
            print("Loading parameters from file " + stored_parameters)
            if type(old_params) == np.ndarray:
                old_params = dict(old_params.item())
                parameters = sorted(set(list(old_params.keys()) + new_params), key = default_sort_key)
            elif type(old_params) == dict:
                parameters = sorted(set(list(old_params.keys()) + new_params), key = default_sort_key)
            values = []
            for p in parameters:
                if p in old_params:
                    values.append(old_params[p])
                else:
                    values.append(rng.random())
            init_params_spsa = values
    else:
        print("Initializing new parameters: ", len(new_params))
        parameters = new_params
        init_params_spsa = np.array(rng.random(len(new_params)))
        
    return parameters, init_params_spsa