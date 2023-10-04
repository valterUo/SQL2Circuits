import json
import os
from pathlib import Path
import matplotlib.pyplot as plt
import pickle
import math
import sys

try:
    from jax import numpy as np
except ModuleNotFoundError:
    try:
        from pennylane import numpy as np
    except ModuleNotFoundError:
        import numpy as np

np.set_printoptions(threshold=sys.maxsize)
i = 0

def get_element(obj, index):
    if isinstance(obj, list):
        return obj[index]
    elif isinstance(obj, dict):
        return obj[list(obj.keys())[index]]
    else:
        raise TypeError("Object must be a list or a dictionary")

def flatten(l):
    return [item for sublist in l for item in sublist]


def get_symbols(circs):
    if type(circs) == dict:
        return set([sym for circuit in circs.values() for sym in circuit.free_symbols])
    elif type(circs) == list:
        syms = set()
        for circuit in circs:
            syms.update(circuit.free_symbols)
        return syms


def construct_data_and_labels(circuits, labels):
    circuits_l = []
    data_labels_l = []
    for key in circuits:
        if str(key) in labels:
            circuits_l.append(circuits[key])
            data_labels_l.append(labels[str(key)])
    return circuits_l, data_labels_l


def select_circuits(base_circuits, select_from_circuits, n_circuits = -1, y = None):
    res = {}
    syms = get_symbols(base_circuits)
    selected_data = []
    if type(select_from_circuits) == dict:
        for c in select_from_circuits:
            s_syms = set(select_from_circuits[c].free_symbols)
            if s_syms.difference(syms) == set():
                res[c] = select_from_circuits[c]
            if len(res) == n_circuits:
                break
    elif type(select_from_circuits) == list:
        for c in select_from_circuits:
            s_syms = set(c.free_symbols)
            if s_syms.difference(syms) == set():
                res[c] = c
                if y is not None:
                    selected_data.append(y[i])
            if len(res) == n_circuits:
                break
    if y is not None:
        return res, selected_data
    return res


def select_pennylane_circuits(base_circuits, select_from_circuits, n_circuits = -1, y = None):
    res = {}
    syms = set()
    selected_data = []
    if type(base_circuits) == dict:
        for c in base_circuits:
            for sym in base_circuits[c].get_param_symbols():
                for s in sym:
                    syms.add(s)
    elif type(base_circuits) == list:
        for c in base_circuits:
            for sym in c.get_param_symbols():
                for s in sym:
                    syms.add(s)
    if type(select_from_circuits) == dict:
        for c in select_from_circuits:
            s_syms = set()
            for sym in select_from_circuits[c].get_param_symbols():
                for s in sym:
                    s_syms.add(s)
            if s_syms.difference(syms) == set():
                res[c] = select_from_circuits[c]
            if len(res) == n_circuits:
                break
    elif type(select_from_circuits) == list:
        for i, c in enumerate(select_from_circuits):
            s_syms = set()
            for sym in c.get_param_symbols():
                for s in sym:
                    s_syms.add(s)
            if s_syms.difference(syms) == set():
                res[c] = c
                if y is not None:
                    selected_data.append(y[i])
            if len(res) == n_circuits:
                break
    if y is not None:
        return res, selected_data
    return res


def visualize_results(model, trainer, test_circuits_l, test_data_labels_l, acc, figure_path):

    fig, ((ax_tl, ax_tr), (ax_bl, ax_br)) = plt.subplots(2, 2, sharex=True, sharey='row', figsize=(10, 6))
    ax_tl.set_title('Training set')
    ax_tr.set_title('Development set')
    ax_bl.set_xlabel('Iterations')
    ax_br.set_xlabel('Iterations')
    ax_bl.set_ylabel('Accuracy')
    ax_tl.set_ylabel('Loss')

    colours = iter(plt.rcParams['axes.prop_cycle'].by_key()['color'])
    ax_tl.plot(trainer.train_epoch_costs[::10], color=next(colours))
    ax_bl.plot(trainer.train_results['acc'][::10], color=next(colours))
    ax_tr.plot(trainer.val_costs[::10], color=next(colours))
    ax_br.plot(trainer.val_results['acc'][::10], color=next(colours))

    test_acc = acc(model(test_circuits_l), test_data_labels_l)
    print('Test accuracy:', test_acc)
    plt.savefig(figure_path)
    
    
def visualize_result_noisyopt(train_costs, train_accs, dev_costs, dev_accs, figure_path):
    fig, ((ax_tl, ax_tr), (ax_bl, ax_br)) = plt.subplots(2, 2, sharex=True, sharey='row', figsize=(10, 6))
    ax_tl.set_title('Training set')
    ax_tr.set_title('Development set')
    ax_bl.set_xlabel('Iterations')
    ax_br.set_xlabel('Iterations')
    ax_bl.set_ylabel('Accuracy')
    ax_tl.set_ylabel('Loss')

    colours = iter(plt.rcParams['axes.prop_cycle'].by_key()['color'])
    ax_tl.plot(train_costs[1::2], color=next(colours))  # training evaluates twice per iteration
    ax_bl.plot(train_accs[1::2], color=next(colours))   # so take every other entry
    ax_tr.plot(dev_costs, color=next(colours))
    ax_br.plot(dev_accs, color=next(colours))

    plt.savefig(figure_path)    

    
def read_diagrams(circuit_paths):
    circuits = {}
    for serialized_diagram in circuit_paths:
        base_name = Path(serialized_diagram).stem
        f = open(serialized_diagram, "rb")
        diagram = pickle.load(f)
        circuits[base_name] = diagram
    return circuits


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
        
        
def normalise(predictions):
    # apply smoothing to predictions
    predictions = np.abs(predictions) + 1e-9
    return predictions / predictions.sum()
        

def create_labeled_training_classes(data, classification, workload):
    labeled_data = {}
    classes = []
    sorted_data = []
    if workload == "execution_time" or workload == "E":
        if type(data) != list:
            data = [{"id": k, "time": v} for k, v in data.items()]
        sorted_data = sorted(data, key=lambda d: d["time"])
    elif workload == "cardinality" or workload == "C":
        if type(data) != list:
            data = data = [{"id": k, "cardinality": v} for k, v in data.items()]
        sorted_data = sorted(data, key=lambda d: d["cardinality"])
    chunk_size = math.ceil(len(sorted_data)/(2**classification))
    for i, clas in enumerate(chunks(sorted_data, chunk_size)):
        if workload == "execution_time":
            classes.append((clas[0]["time"], clas[-1]["time"]))
        elif workload == "cardinality":
            classes.append((clas[0]["cardinality"], clas[-1]["cardinality"]))
        label = [0]*(2**classification)
        label[i] = 1
        for elem in clas:
            labeled_data[elem["id"]] = label
    return labeled_data, classes


def create_labeled_test_validation_classes(data, classes, workload):
    labeled_data = {}
    classification = len(classes)
    sorted_data = dict()
    data_value = None

    if workload == "execution_time":
        if type(data) != list:
            data = [{"id": k, "time": v} for k, v in data.items()]
        sorted_data = sorted(data, key=lambda d: d["time"])
    elif workload == "cardinality":
        if type(data) != list:
            data = data = [{"id": k, "cardinality": v} for k, v in data.items()]
        sorted_data = sorted(data, key=lambda d: d["cardinality"])
    
    for elem in sorted_data:
        if workload == "execution_time":
            data_value = float(elem["time"])
        elif workload == "cardinality":
            data_value = float(elem["cardinality"])
        
        index = None
        for i, clas in enumerate(classes):
            if data_value >= clas[0] and data_value <= clas[1]:
                index = i
        
        label = [0]*classification
        try:
            label[index] = 1
        except:
            label[-1] = 1
            
        labeled_data[elem["id"]] = label
    return labeled_data


def bin_class_acc(y_hat, y):
    y_hat = np.array(y_hat)
    # If yhat shape is (10, 2, 2) make it to (10, 2)

    y = np.array(y)
    return (np.sum(np.round(y_hat) == y) / len(y)) / 2


def bin_class_loss(y_hat, y):
    #print("y_hat", y_hat, "y", y)
    y_hat = np.array(y_hat)
    y = np.array(y)
    return -np.sum(y * np.log(y_hat)) / len(y)


def multi_class_acc(y_hat, y):
    total_acc = 0
    if len(y_hat) != len(y):
        print("y_hat: ", len(y_hat), "y: ", len(y))
        raise Exception("Length of predictions and labels must be equal")
    if len(y) == 0 or len(y_hat) == 0:
        print("y", y, " y_hat", y_hat)
        return 0
    for pair in zip(y_hat, y):
        y_meas = np.array(pair[0]).flatten()
        max_index = np.argmax(y_meas)
        total_acc += int(int(pair[1][max_index]) == 1)
    return total_acc / len(y)


def multi_class_loss(y_hat, y):
    total_loss = 0
    print("y_hat", y_hat, "y", y)
    if len(y_hat) != len(y):
        print("y_hat: ", len(y_hat), "y: ", len(y))
        raise Exception("Length of predictions and labels must be equal")
    for pair in zip(y_hat, y):
        x = np.array(pair[1])
        y_pred = np.array(pair[0]).flatten()
        if y_pred.size != x.size:
            print("y_pred: ", y_pred.size, "x: ", x.size)
            raise Exception("Length of prediction and label vectors must be equal")
        total_loss += -np.sum(x * np.log(y_pred)) / x.size
    return total_loss


def acc_from_dict(dict_predictions, dict_labels):
    total_acc = 0
    for query_id in dict_predictions:
        y_meas = np.array(dict_predictions[query_id]).flatten()
        max_index = np.argmax(y_meas)
        total_acc += int(int(dict_labels[query_id][max_index]) == 1)
    return total_acc / len(dict_predictions)


def loss_from_dict(dict_predictions, dict_labels):
    total_loss = 0
    for query_id in dict_predictions:
        x = np.array(dict_labels[query_id])
        y_pred = np.array(dict_predictions[query_id]).flatten()
        total_loss += -np.sum(x * np.log(y_pred)) / len(x)
    return total_loss


def store_and_log(execution, data, file):
    info = ""
    for k, v in data.items():
        info += k + ": " + str(v) + "\n"
    print(info)
    
    execution = str(execution)
    current_data = data
    if os.path.exists(file):
        with open(file, 'r') as f:
            current_data = json.load(f)
            if execution not in current_data:
                current_data[execution] = []
            current_data[execution].append(data)
        with open(file, 'w') as f:
            json.dump(current_data, f, indent = 4)
    else:
        with open(file, 'w') as f:
            json.dump({ execution : [ current_data ]}, f, indent = 4)


def store_hyperparameter_opt_results(run_id, opt):
    results = dict(opt.cv_results_)
    for key, value in results.items():
        if isinstance(value, np.ndarray):
            results[key] = value.tolist()
    best_params = dict(opt.best_params_)
    for key, value in best_params.items():
        if isinstance(value, np.ndarray):
            best_params[key] = value.tolist()
    results["best_params"] = best_params
    with open("training//results//" + str(run_id) + "_cv_results.json", "w") as f:
        # If results contains ndarray, convert them to list
        for key, value in results.items():
            if isinstance(value, np.ndarray):
                results[key] = value.tolist()
        try:
            json.dump(results, f, indent = 4)
        except TypeError:
            print("TypeError: ", results)
            # Store results as pickle
            with open("training//results//" + str(run_id) + "_cv_results.pickle", "wb") as f:
                pickle.dump(results, f)