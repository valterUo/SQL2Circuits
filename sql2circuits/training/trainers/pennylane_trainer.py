# -*- coding: utf-8 -*-

import collections
import multiprocessing
import time
#from jax import numpy as np
import numpy
import numpy as np
from discopy.quantum.pennylane import to_pennylane
import pennylane as qml
from sympy.core.symbol import Symbol
from sympy import default_sort_key
from discopy.quantum.pennylane import to_pennylane

class PennylaneCircuit:

    def __init__(self, ops, params, pennylane_wires, n_qubits, param_symbols, symbol_to_index, symbols) -> None:
        self.ops = ops
        self.params = params
        self.pennylane_wires = pennylane_wires
        self.n_qubits = n_qubits
        self.dev = qml.device("default.qubit", wires=range(n_qubits), shots=10000)
        self.param_symbols = param_symbols
        self.symbol_to_index = symbol_to_index
        self.symbols = symbols

    def qml_circuit(self, circ_params):
        for op, param, wires in zip(self.ops, self.param_symbols, self.pennylane_wires):
            if len(param) > 0:
                param = param[0]
                op(circ_params[self.symbol_to_index[param]], wires = wires)
            else:
                op(wires = wires)
        return qml.sample()
    

    def get_QNode(self):
        return qml.QNode(self.qml_circuit, self.dev)
    
    def get_n_qubits(self):
        return self.n_qubits
    
    def get_param_symbols(self):
        return self.param_symbols
    

def transform_into_pennylane_circuits(circuits):
    qml_circuits = {}
    symbols = set([Symbol(str(elem)) for c in circuits.values() for elem in c.free_symbols])
    symbols = list(sorted(symbols, key = default_sort_key))

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

        qml_circuits[circ_key] = PennylaneCircuit(ops, params, pennylane_wires, n_qubits, param_symbols, symbol_to_index, symbols)

    return qml_circuits, symbols


def post_selection(circuit_samples, n_qubits, post_selection):
    selected_samples = []
    post_select_array = numpy.array([0]*(n_qubits - post_selection))
    selected_samples = circuit_samples[numpy.all(circuit_samples[:, post_selection - 1 :-1] == post_select_array, axis = 1)]
    return selected_samples[:, :post_selection].tolist()


def make_pennylane_pred_fn(circuits, parameters, classification):
    
    def predict(params):
        predictions = []
        for pennylane_circuit in circuits:
            circuit = pennylane_circuit.get_QNode()
            n_qubits = pennylane_circuit.get_n_qubits()
            post_selected_samples = []
            measurement = circuit(params)
            post_selected_samples = post_selection(measurement, n_qubits, classification)
            post_selected_samples = [tuple(map(int, t)) for t in post_selected_samples]
            counts = collections.Counter(post_selected_samples)
            if len(post_selected_samples) == 0:
                predictions.append([1] + [1e-9]*(2**classification - 1))
                continue
            try:
                predicted = counts.most_common(1)[0][0]
                binary_string = ''.join(str(bit) for bit in predicted[::-1])
                binary_int = int(binary_string, 2)
                result = [1e-9]*2**classification
                result[binary_int] = 1
                predictions.append(result)
            except:
                predictions.append([1] + [1e-9]*(2**classification - 1))
        return predictions

    #def predict_parallel(params):        
    #    args = [(circuit.get_QNode(), params, circuit.get_n_qubits(), classification) for circuit in circuits]
    #    results = []
    #    with multiprocessing.Pool(processes=16) as pool:
    #        results = pool.starmap(predict_circuit, args)
    #        pool.close()
    #        pool.join()
    #    return results

    def predict_parallel(params):
        args = [(circuit.get_QNode(), params, circuit.get_n_qubits(), classification) for circuit in circuits]
        results = []
        queue = multiprocessing.Queue()
        with multiprocessing.Pool(processes=16) as pool:
            pool.starmap_async(predict_circuit, args, callback=queue.put)
            pool.close()
            pool.join()
        while not queue.empty():
            results += queue.get()
        return results

    return predict_parallel


def predict_circuit(circuit, params, n_qubits, classification):
        measurement = circuit(params)
        post_selected_samples = post_selection(numpy.array(measurement), n_qubits, classification)
        post_selected_samples = [tuple(map(int, t)) for t in post_selected_samples]
        counts = collections.Counter(post_selected_samples)
        if len(post_selected_samples) == 0:
            return [1e-9]*(2**classification)
            #return [1] + [1e-9]*(2**classification - 1)
        try:
            predicted = counts.most_common(1)[0][0]
            binary_string = ''.join(str(bit) for bit in predicted[::-1])
            binary_int = int(binary_string, 2)
            result = [1e-9]*2**classification
            result[binary_int] = 1
            return result
            #queue.put(result)
        except:
            return [1e-9]*(2**classification)
            #return [1] + [1e-9]*(2**classification - 1)


def make_pennylane_cost_fn(pred_fn, labels, loss_fn, accuracy_fn, costs_accuracies = None, type = None):
    
    def cost_fn(params, **kwargs):
        predictions = pred_fn(params)
        cost = loss_fn(predictions, labels)
        accuracy = accuracy_fn(predictions, labels)
        if costs_accuracies is not None and type is not None:
            costs_accuracies.add_cost(cost, type)
            costs_accuracies.add_accuracy(accuracy, type)
        return cost

    return cost_fn
