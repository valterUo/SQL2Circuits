from pathlib import Path
import matplotlib.pyplot as plt
import pickle
import math
#import numpy as np
from jax import numpy as np
import sys
import pennylane as qml
from sympy import default_sort_key
from discopy.quantum.pennylane import to_pennylane
np.set_printoptions(threshold=sys.maxsize)
i = 0


def get_symbols(circs):
    return set([sym for circuit in circs.values() for sym in circuit.free_symbols])


def construct_data_and_labels(circuits, labels):
    circuits_l = []
    data_labels_l = []
    for key in circuits:
        if key in labels:
            circuits_l.append(circuits[key])
            data_labels_l.append(labels[key])
    return circuits_l, data_labels_l


def select_circuits(base_circuits, selected_circuits):
    res = {}
    syms = get_symbols(base_circuits)
    for c in selected_circuits:
        s_syms = set(selected_circuits[c].free_symbols)
        if s_syms.difference(syms) == set():
            res[c] = selected_circuits[c]
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
        

def create_labeled_classes(data, classification, workload):
    labeled_data = {}
    if workload == "execution_time":
        sorted_data = sorted(data, key=lambda d: d["time"])
    elif workload == "cardinality":
        sorted_data = sorted(data, key=lambda d: d["cardinality"])
    chunk_size = math.ceil(len(sorted_data)/2**classification)
    for i, clas in enumerate(chunks(sorted_data, chunk_size)):
        label = [0]*(2**classification)
        label[i] = 1
        for elem in clas:
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


def transform_into_pennylane_circuits(circuits, n_qubits, dev):
    qml_circuits = []
    symbols = set([elem for c in circuits for elem in c.free_symbols])
    symbols = list(sorted(symbols, key=default_sort_key))

    for circuit_diagram in circuits:
        pennylane_circuit = to_pennylane(circuit_diagram)
        params = pennylane_circuit.params
        pennylane_wires = pennylane_circuit.wires
        ops = pennylane_circuit.ops
        param_symbols = [[sym[0].as_ordered_factors()[2]] if len(sym) > 0 else [] for sym in params]
        symbol_to_index = {}

        for sym in param_symbols:
            if len(sym) > 0:
                symbol_to_index[sym[0]] = symbols.index(sym[0])

        @qml.qnode(dev)
        def qml_circuit(circ_params):
            for op, param, wires in zip(ops, param_symbols, pennylane_wires):
                if len(param) > 0:
                    param = param[0]
                    op(circ_params[symbol_to_index[param]], wires = wires)
                else:
                    op(wires = wires)
            return qml.sample()

        qml_circuits.append(qml_circuit)

    return qml_circuits, symbols