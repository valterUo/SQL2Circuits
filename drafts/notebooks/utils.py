from pathlib import Path
import matplotlib.pyplot as plt
import pickle
import math
#import numpy as np
from jax import numpy as np
import sys
import copy
import pennylane as qml
from sympy import default_sort_key
from discopy.quantum.pennylane import to_pennylane
np.set_printoptions(threshold=sys.maxsize)
i = 0


def flatten(l):
    return [item for sublist in l for item in sublist]


def get_symbols(circs):
    return set([sym for circuit in circs.values() for sym in circuit.free_symbols])


def construct_data_and_labels(circuits, labels):
    circuits_l = []
    data_labels_l = []
    if len(circuits) <= len(labels):
        for key in circuits:
            if key in labels:
                circuits_l.append(circuits[key])
                data_labels_l.append(labels[key])
    else:
        for key in labels:
            if key in circuits:
                circuits_l.append(circuits[key])
                data_labels_l.append(labels[key])
    return circuits_l, data_labels_l


def select_circuits(base_circuits, selected_circuits, max_circuits = -1):
    res = {}
    syms = get_symbols(base_circuits)
    for c in selected_circuits:
        s_syms = set(selected_circuits[c].free_symbols)
        if s_syms.difference(syms) == set():
            res[c] = selected_circuits[c]
        if len(res) == max_circuits:
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

    #for e in model(test_circuits_l):
    #    print(e)
    #for e in test_data_labels_l:
    #    print(e)

    # Print test accuracy
    test_acc = acc(model(test_circuits_l), test_data_labels_l)
    print('Test accuracy:', test_acc)
    plt.savefig(figure_path)
    
    
def visualize_result_noisyopt(result, make_cost_fn, test_pred_fn, test_data_labels_l, train_costs, train_accs, dev_costs, dev_accs, figure_path, result_file):
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

    # Print test accuracy
    test_cost_fn, _, test_accs = make_cost_fn(test_pred_fn, test_data_labels_l)
    test_cost_fn(result.x)
    
    with open("results//" + result_file + ".txt", "a") as f:
        f.write('Test accuracy: ' + str(test_accs[0]) + "\n")
    
    with open("points//" + result_file + ".npz", "wb") as f:
        np.savez(f, result.x)
        
    print('Test accuracy:', test_accs[0])

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
    stats = []
    if workload == "execution_time":
        sorted_data = sorted(data, key=lambda d: d["time"])
    elif workload == "cardinality":
        sorted_data = sorted(data, key=lambda d: d["cardinality"])
    chunk_size = math.ceil(len(sorted_data)/(2**classification))
    for i, clas in enumerate(chunks(sorted_data, chunk_size)):
        if workload == "execution_time":
            classes.append((clas[0]["time"], clas[-1]["time"]))
        elif workload == "cardinality":
            classes.append((clas[0]["cardinality"], clas[-1]["cardinality"]))
        label = [0]*(2**classification)
        label[i] = 1
        if workload == "execution_time":
            stats.append((clas[0]["time"], clas[-1]["time"]))
        elif workload == "cardinality":
            stats.append((clas[0]["cardinality"], clas[-1]["cardinality"]))
        for elem in clas:
            labeled_data[elem["name"]] = label
    return labeled_data, classes

def create_labeled_training_classes_new(data, classification):
    labeled_data = {}
    classes = []

    sorted_data = sorted(data, key=lambda d: d["time"])

    # classes.append((0, 2000))
    # classes.append((2000, 14251.7399))
    # for i, clas in enumerate(sorted_data):
                
    #     label = [0, 0]

    #     if clas["time"]>=2000:
    #         label[1] = 1
    #     else: label[0] = 1
        
    #     labeled_data[clas["name"]] = label

    classes.append((0, 2000))
    classes.append((4000, 7200))
    classes.append((7200, 11000))
    classes.append((11000, 14251.7399))
    for i, clas in enumerate(sorted_data):
                
        label = [0, 0, 0, 0]

        if clas["time"]<=2000:
            label[0] = 1
        elif 4000 < clas["time"] < 7200: 
            label[1] = 1
        elif 7200 < clas["time"] < 11000: 
            label[2] = 1
        elif 11000 < clas["time"] < 14251.7399: 
            label[3] = 1
        
        labeled_data[clas["name"]] = label


    return labeled_data, classes


def create_labeled_test_validation_classes(data, classes, workload):
    labeled_data = {}
    classification = len(classes)
    
    if workload == "execution_time":
        sorted_data = sorted(data, key=lambda d: d["time"])
    elif workload == "cardinality":
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
            #print(data_value)
            
        labeled_data[elem["name"]] = label
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
    #global i
    total_loss = 0
    if len(y_hat) != len(y):
        return 0
    for pair in zip(y_hat, y):
        x = np.array(pair[1])
        y_pred = np.array(pair[0]).flatten()
        #if i % 100 == 0:
        #    print(y_pred, x)
        if len(y_pred) != len(x):
            return 0
        total_loss += -np.sum(x * np.log(y_pred)) / len(x)
    #i+=1
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


def transform_into_pennylane_circuits(circuits):
    qml_circuits = {}
    symbols = set([elem for c in circuits.values() for elem in c.free_symbols])
    symbols = list(sorted(symbols, key=default_sort_key))

    for circ_key in circuits:
        circuit = circuits[circ_key]

        pennylane_circuit = to_pennylane(circuit)
        params = pennylane_circuit._params

        ops = pennylane_circuit._ops
        param_symbols = [[sym[0].as_ordered_factors()[0]] if len(sym) > 0 else [] for sym in params]
        pennylane_wires = pennylane_circuit._wires

        circuit_elements = list(zip(ops, param_symbols, pennylane_wires))
        circuit_elements.reverse()

        symbol_to_index = {}
        symbols = [str(x) for x in symbols]
        for sym in param_symbols:
            if len(sym) > 0:
                symbol_to_index[sym[0]] = symbols.index(str(sym[0]))

        qml_circuits[circ_key] = { "circuit_elements": circuit_elements, "symbol_to_index": symbol_to_index, "n_qubits": pennylane_circuit._n_qubits }

    return qml_circuits, symbols