# -*- coding: utf-8 -*-

"""
Interface with PennyLane.

This module is inspired by 
https://github.com/discopy/discopy/blob/main/discopy/quantum/pennylane.py

"""

#from pennylane import numpy as np
from jax import numpy as np
import pennylane as qml
from itertools import product

class PennylaneCircuit:

    def __init__(self, ops, params, pennylane_wires, n_qubits, param_symbols, symbol_to_index, symbols, post_selection, interface, diff_method) -> None:
        self.ops = ops
        self.params = params
        self.pennylane_wires = pennylane_wires
        self.n_qubits = n_qubits
        self.dev = qml.device("default.qubit", 
                              wires=range(n_qubits))
        self.param_symbols = param_symbols
        self.symbol_to_index = symbol_to_index
        self.symbols = symbols
        self.post_selection = post_selection
        self.interface = interface
        self.diff_method = diff_method
        self.valid_states = np.array(self.get_valid_states())


    def get_valid_states(self):
        keep_indices = []
        fixed = ['0' if self.post_selection.get(i, 0) == 0 else
                 '1' for i in range(self.n_qubits)]
        open_wires = set(range(self.n_qubits)) - self.post_selection.keys()
        permutations = [''.join(s) for s in product('01', repeat=len(open_wires))]
        for perm in permutations:
            new = fixed.copy()
            for i, open in enumerate(open_wires):
                new[open] = perm[i]
            keep_indices.append(int(''.join(new), 2))
        return keep_indices
    

    def qml_circuit(self, circ_params):
        for op, param, wires in zip(self.ops, self.param_symbols, self.pennylane_wires):
            if len(param) > 0:
                param = param[0]
                op(circ_params[self.symbol_to_index[param]], wires = wires)
            else:
                op(wires = wires)
        return qml.sample()
    

    def qml_circuit_with_state_meas(self, circ_params):
        for op, param, wires in zip(self.ops, self.param_symbols, self.pennylane_wires):
            if len(param) > 0:
                param = param[0]
                op(circ_params[self.symbol_to_index[param]], wires = wires)
            else:
                op(wires = wires)
        return qml.state()
    

    def eval_qml_circuit_with_post_selection(self, circ_params):
        circuit = qml.QNode(self.qml_circuit_with_state_meas, self.dev, interface = self.interface, diff_method = self.diff_method)
        states = circuit(circ_params)
        post_selected_states = states[self.valid_states]
        post_states = np.array([np.linalg.norm(x)**2 for x in post_selected_states], dtype=np.float32)
        sum = np.sum(post_states, axis=0)
        result = post_states / sum
        return result


    def get_QNode(self):
        return qml.QNode(self.qml_circuit, self.dev)
    

    def get_n_qubits(self):
        return self.n_qubits
    

    def get_param_symbols(self):
        return self.param_symbols