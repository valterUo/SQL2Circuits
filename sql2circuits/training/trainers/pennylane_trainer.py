import collections
#from jax import numpy as np
import numpy as np
from discopy.quantum.pennylane import to_pennylane
#from jax import jit
import pennylane as qml
from sympy.core.symbol import Symbol
from sympy import default_sort_key
from discopy.quantum.pennylane import to_pennylane

from QNodeCollection import QNodeCollection
import concurrent.futures
#import time
#from jax import config
#config.update("jax_enable_x64", True)

class PennylaneCircuit:

    def __init__(self, ops, params, pennylane_wires, n_qubits, param_symbols, symbol_to_index, symbols) -> None:
        self.ops = ops
        self.params = params
        self.pennylane_wires = pennylane_wires
        self.n_qubits = n_qubits
        self.param_symbols = param_symbols
        self.symbol_to_index = symbol_to_index
        self.dev = qml.device("lightning.qubit", wires=range(n_qubits), shots=10000)
        self.symbols = symbols

        #@jit
        @qml.qnode(self.dev)
        def qml_circuit(circ_params):
            for op, param, wires in zip(self.ops, self.param_symbols, self.pennylane_wires):
                if len(param) > 0:
                    param = param[0]
                    op(circ_params[self.symbol_to_index[param]], wires = wires)
                else:
                    op(wires = wires)
            return qml.sample()
        
        self.qml_circuit = qml_circuit


    def get_QNode(self):
        return self.qml_circuit
    

    def get_n_qubits(self):
        return self.n_qubits
    

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
    post_select_array = np.array([0]*(n_qubits - post_selection))
    selected_samples = circuit_samples[np.all(circuit_samples[:, post_selection - 1 :-1] == post_select_array)]
    return selected_samples[:, :post_selection].tolist()


def make_pennylane_pred_fn(circuits, parameters, classification):
    
    def predict2(params):
        predictions = {}
        for c in circuits:
            disco_circuit = circuits[c]
            qml_circuit = to_pennylane(disco_circuit)
            result = qml_circuit.post_selected_circuit(params)
            predictions[c] = result
        return predictions
    

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
    

    def predict_new_new(params):
        predictions = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            for pennylane_circuit in circuits:
                circuit = pennylane_circuit.get_QNode()
                n_qubits = pennylane_circuit.get_n_qubits()
                futures.append(executor.submit(predict_circuit, circuit, params, n_qubits, classification))
            for future in concurrent.futures.as_completed(futures):
                predictions.append(future.result())
        return predictions


    def predict_circuit(circuit, params, n_qubits, classification):
        measurement = circuit(params)
        post_selected_samples = post_selection(np.array(measurement), n_qubits, classification)
        post_selected_samples = [tuple(map(int, t)) for t in post_selected_samples]
        counts = collections.Counter(post_selected_samples)
        if len(post_selected_samples) == 0:
            return [1] + [1e-9]*(2**classification - 1)
        try:
            predicted = counts.most_common(1)[0][0]
            binary_string = ''.join(str(bit) for bit in predicted[::-1])
            binary_int = int(binary_string, 2)
            result = [1e-9]*2**classification
            result[binary_int] = 1
            return result
        except:
            return [1] + [1e-9]*(2**classification - 1)
    
    

    def predict_new(params):
        predictions = []
        qnodes = QNodeCollection(circuits)
        samples, qubits = qnodes.simulate_parallel(params)
        for sample, n_qubits in zip(samples, qubits):
            print(np.array(sample))
            post_selected_samples = post_selection(np.array(sample), n_qubits, classification)
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

    return predict


def make_pennylane_cost_fn(pred_fn, labels, loss_fn, accuracy_fn, costs_accuracies, type):
    
    def cost_fn(params, **kwargs):
        predictions = pred_fn(params)
        cost = loss_fn(predictions, labels)
        accuracy = accuracy_fn(predictions, labels)
        costs_accuracies.add_cost(cost, type)
        costs_accuracies.add_accuracy(accuracy, type)
        return cost

    return cost_fn