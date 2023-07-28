from pathlib import Path
import matplotlib.pyplot as plt
import pickle
import math
from jax import numpy as np
#import numpy as np
import sys
import numpy
#import covalent as ct

np.set_printoptions(threshold=sys.maxsize)
i = 0


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
        if key in labels:
            circuits_l.append(circuits[key])
            data_labels_l.append(labels[key])
    return circuits_l, data_labels_l


def select_circuits(base_circuits, select_from_circuits, n_circuits = -1):
    res = {}
    syms = get_symbols(base_circuits)
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
            if len(res) == n_circuits:
                break
    return res


def select_pennylane_circuits(base_circuits, select_from_circuits, n_circuits = -1):
    res = {}
    syms = set()
    for c in base_circuits:
        for sym in base_circuits[c].get_param_symbols():
            for s in sym:
                syms.add(s)
    for c in select_from_circuits:
        s_syms = set()
        for sym in select_from_circuits[c].get_param_symbols():
            for s in sym:
                s_syms.add(s)
        if s_syms.difference(syms) == set():
            res[c] = select_from_circuits[c]
        if len(res) == n_circuits:
            break
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
    y = np.array(y)
    return (np.sum(np.round(y_hat) == y) / len(y)) / 2


def bin_class_loss(y_hat, y):
    y_hat = np.array(y_hat)
    y = np.array(y)
    return -np.sum(y * np.log(y_hat)) / len(y)


def multi_class_acc(y_hat, y):
    total_acc = 0
    for pair in zip(y_hat, y):
        y_meas = np.array(pair[0]).flatten()
        max_index = np.argmax(y_meas)
        total_acc += int(int(pair[1][max_index]) == 1)
    return total_acc / len(y)


def multi_class_loss(y_hat, y):
    total_loss = 0
    if len(y_hat) != len(y):
        raise Exception("Length of predictions and labels must be equal")
    for pair in zip(y_hat, y):
        x = np.array(pair[1])
        y_pred = np.array(numpy.array(pair[0]).flatten())
        if y_pred.size != x.size:
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