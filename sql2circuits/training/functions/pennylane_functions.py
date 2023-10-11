# -*- coding: utf-8 -*-

import collections
import multiprocessing
try:
    from jax import numpy as np
except ModuleNotFoundError:
    try:
        from pennylane import numpy as np
    except ModuleNotFoundError:
        import numpy as np
        
from discopy.quantum.pennylane import to_pennylane
from sympy.core.symbol import Symbol
from sympy import default_sort_key
from itertools import product
from discopy.quantum.pennylane import to_pennylane

from training.pennylane_circuit import PennylaneCircuit

# This avoids TracerArrayConversionError from jax
try:
    from discopy.tensor import Tensor
    Tensor.np = np
except:
    pass

def get_valid_states(n_qubits, post_selection):
    keep_indices = []
    fixed = ['0' if post_selection.get(i, 0) == 0 else
                '1' for i in range(n_qubits)]
    open_wires = set(range(n_qubits)) - post_selection.keys()
    permutations = [''.join(s) for s in product('01', repeat=len(open_wires))]
    for perm in permutations:
        new = fixed.copy()
        for i, open in enumerate(open_wires):
            new[open] = perm[i]
        keep_indices.append(int(''.join(new), 2))
    return keep_indices
    

def transform_into_pennylane_circuits(circuits, classification, measurement, interface = 'best', diff_method = 'best'):
    qml_circuits = {}
    symbols = set([Symbol(str(elem)) for c in circuits.values() for elem in c.free_symbols])
    symbols = list(sorted(symbols, key = default_sort_key))
    full_symbol_to_index = {}

    for circ_key in circuits:
        circuit = circuits[circ_key]
        pennylane_circuit = to_pennylane(circuit)
        ops = pennylane_circuit._ops
        params = pennylane_circuit._params
        pennylane_wires = pennylane_circuit._wires
        n_qubits = pennylane_circuit._n_qubits
        param_symbols = [[sym[0].as_ordered_factors()[1]] if len(sym) > 0 else [] for sym in params]
        symbol_to_index = {}

        for sym in param_symbols:
            if len(sym) > 0:
                symbol_to_index[sym[0]] = symbols.index(sym[0])
        full_symbol_to_index.update(symbol_to_index)

        # Produces a dictionary like {2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0} 
        # where the wires 0 and 1 are the classifying wires
        post_selection = dict([(i, 0) for i in range(classification, n_qubits)])
        valid_states = np.array(get_valid_states(n_qubits, post_selection))
        qml_circuits[circ_key] = PennylaneCircuit(ops, 
                                                  params, 
                                                  pennylane_wires, 
                                                  n_qubits, 
                                                  param_symbols, 
                                                  symbol_to_index, 
                                                  symbols, 
                                                  valid_states,
                                                  measurement,
                                                  interface, 
                                                  diff_method)

    return qml_circuits, full_symbol_to_index


def post_selection(circuit_samples, n_qubits, post_selection):
    selected_samples = []
    post_select_array = np.array([0]*(n_qubits - post_selection))
    selected_samples = circuit_samples[np.all(circuit_samples[:, post_selection - 1 :-1] == post_select_array, axis = 1)]
    return selected_samples[:, :post_selection].tolist()


def predict_circuit(circuit, params, n_qubits, classification):
    measurement = circuit(params)
    post_selected_samples = post_selection(np.array(measurement), n_qubits, classification)
    post_selected_samples = [tuple(map(int, t)) for t in post_selected_samples]
    counts = collections.Counter(post_selected_samples)
    if len(post_selected_samples) == 0:
        return [1e-9]*(2**classification)
    try:
        predicted = counts.most_common(1)[0][0]
        binary_string = ''.join(str(bit) for bit in predicted[::-1])
        binary_int = int(binary_string, 2)
        result = [1e-9]*2**classification
        result[binary_int] = 1
        print(result)
        return result
    except Exception as e:
        print("Error in prediction circuit 1", e)
        return [1e-9]*(2**classification)


def make_pennylane_pred_fn(circuits, parameters, classification):
    
    def predict(params):
        predictions = []
        for pennylane_circuit in circuits:
            circuit = pennylane_circuit.get_QNode_with_sample()
            n_qubits = pennylane_circuit.get_n_qubits()
            post_selected_samples = []
            measurement = circuit(params)
            post_selected_samples = post_selection(measurement, n_qubits, classification)
            post_selected_samples = [tuple(map(int, t)) for t in post_selected_samples]
            counts = collections.Counter(post_selected_samples)
            if len(post_selected_samples) == 0:
                print("No samples")
                predictions.append([1e-9]*(2**classification))
                continue
            try:
                predicted = counts.most_common(1)[0][0]
                binary_string = ''.join(str(bit) for bit in predicted[::-1])
                binary_int = int(binary_string, 2)
                result = [1e-9]*2**classification
                result[binary_int] = 1
                predictions.append(result)
            except Exception as e:
                print("Error in prediction circuit 1", e)
                return [1e-9]*(2**classification)
        return predictions
    

    def predict_parallel(params):
        args = [(circuit.get_QNode_with_sample(), params, circuit.get_n_qubits(), classification) for circuit in circuits]
        results = []
        queue = multiprocessing.Queue()
        with multiprocessing.Pool(processes=8) as pool:
            for arg in args:
                pool.apply_async(predict_circuit, arg, callback=queue.put)
            pool.close()
            pool.join()
        while not queue.empty():
            results.append(queue.get())
        return results

    return predict

def cross_entropy(predictions, targets):
    N = predictions.shape[0]
    ce = -np.sum(targets*np.log(predictions+1e-9))/N
    return ce


def make_pennylane_cost_fn(pred_fn, labels, loss_fn, accuracy_fn = None, costs_accuracies = None, type = None):
    
    def cost_fn(params, **kwargs):
        predictions = pred_fn(params)
        #cost = loss_fn(predictions, labels)
        #print("Predictions: ", predictions)
        #print("Labels: ", labels)
        cost = cross_entropy(np.array(predictions), np.array(labels))
        if costs_accuracies is not None and type is not None:
            accuracy = accuracy_fn(predictions, labels)
            costs_accuracies.add_cost(cost, type)
            costs_accuracies.add_accuracy(accuracy, type)
        return cost

    return cost_fn


def make_pennylane_pred_fn_for_gradient_descent(circuits):

    def predict(params):
        predictions = []
        for pennylane_circuit in circuits:
            pred = pennylane_circuit.eval_qml_circuit_with_post_selection(params)
            predictions.append(pred)
        return predictions
    
    return predict
