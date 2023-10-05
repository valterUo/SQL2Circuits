# -*- coding: utf-8 -*-

"""
Interface with PennyLane.

This module is inspired by 
https://github.com/discopy/discopy/blob/main/discopy/quantum/pennylane.py

"""

try:
    from jax import numpy as np
except ModuleNotFoundError:
    try:
        from pennylane import numpy as np
    except ModuleNotFoundError:
        import numpy as np
        
import pennylane as qml

# This avoids TracerArrayConversionError from jax
#from discopy.tensor import Tensor
#Tensor.np = np

class PennylaneCircuit:

    def __init__(self, ops, params, pennylane_wires, n_qubits, param_symbols, symbol_to_index, symbols, valid_states, interface, diff_method) -> None:
        self.ops = ops
        self.params = params
        self.pennylane_wires = pennylane_wires
        self.n_qubits = n_qubits
        self.dev = qml.device("default.qubit", 
                              wires=range(n_qubits)) #,
                              #shots=10000)
        self.param_symbols = param_symbols
        self.symbol_to_index = symbol_to_index
        self.symbols = symbols
        self.interface = interface
        self.diff_method = diff_method
        self.valid_states = valid_states
        #print(self.post_selection)
    

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
        circuit = qml.QNode(self.qml_circuit_with_state_meas, 
                            self.dev, 
                            interface = self.interface, 
                            diff_method = self.diff_method)
        #fig, ax = qml.draw_mpl(circuit)(circ_params)
        #fig.savefig("test" + str(self.__hash__) + ".png")
        #raise Exception
        states = circuit(circ_params)
        post_selected_states = np.array(states)[self.valid_states]
        post_states = np.array([np.abs(x)**2 for x in post_selected_states], dtype=np.float32)
        sum = np.sum(post_states)
        result = post_states / sum
        return result


    def get_QNode(self):
        return qml.QNode(self.qml_circuit, self.dev)
    

    def get_n_qubits(self):
        return self.n_qubits
    

    def get_param_symbols(self):
        return self.param_symbols