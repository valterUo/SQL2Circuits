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

    def __init__(self, ops, params, pennylane_wires, n_qubits, param_symbols, symbol_to_index, symbols, valid_states, measurement, interface, diff_method) -> None:
        self.ops = ops
        self.params = params
        self.pennylane_wires = pennylane_wires
        self.n_qubits = n_qubits
        if measurement == "state":
            self.dev = qml.device("default.qubit", 
                              wires=range(n_qubits))
        elif measurement == "sample":
            self.dev = qml.device("default.qubit", 
                              wires=range(n_qubits), 
                              shots=100000)
        elif measurement == "iqm":
            #from iqm.qiskit_iqm import IQMProvider
            #from iqm.qiskit_iqm import IQMFakeApollo
            
            #provider = IQMProvider("https://qc.vtt.fi/leena/cocos")
            #backend = IQMFakeApollo() #provider.get_backend()
            #self.dev = qml.device('qiskit.remote', wires=range(n_qubits), backend=backend, shots=400000)
            self.dev = qml.device("default.qubit", 
                              wires=range(n_qubits), 
                              shots=400000)
            #print(self.dev.capabilities())
        self.param_symbols = param_symbols
        self.symbol_to_index = symbol_to_index
        self.symbols = symbols
        self.measurement = measurement
        self.interface = interface
        self.diff_method = diff_method
        self.valid_states = valid_states
    

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
    
    def qml_circuit_with_density_matrix_meas(self, circ_params):
        for op, param, wires in zip(self.ops, self.param_symbols, self.pennylane_wires):
            if len(param) > 0:
                param = param[0]
                op(circ_params[self.symbol_to_index[param]], wires = wires)
            else:
                op(wires = wires)
        return qml.density_matrix(wires=range(self.n_qubits))
    
    
    def qml_circuit_with_probs_meas(self, circ_params):
        for op, param, wires in zip(self.ops, self.param_symbols, self.pennylane_wires):
            if len(param) > 0:
                param = param[0]
                op(circ_params[self.symbol_to_index[param]], wires = wires)
            else:
                op(wires = wires)
        return qml.probs(wires = range(self.n_qubits))
    

    def eval_qml_circuit_with_post_selection(self, circ_params):
        circuit = qml.QNode(self.qml_circuit_with_state_meas, 
                            self.dev, 
                            interface = 'jax',
                            diff_method = 'backprop')
        #fig, ax = qml.draw_mpl(circuit)(circ_params)
        #fig.savefig("test" + str(self.__hash__) + ".png")
        #raise Exception
        states = circuit(circ_params)
        post_selected_states = np.array(states)[self.valid_states]
        post_states = np.array([np.abs(x)**2 for x in post_selected_states], dtype=np.float32)
        sum = np.sum(post_states)
        result = post_states / sum
        return result


    def get_QNode_with_sample(self):
        return qml.QNode(self.qml_circuit, self.dev)
    
    def get_QNode_with_state(self):
        return qml.QNode(self.qml_circuit_with_state_meas, self.dev)
    
    def get_QNode_with_density_matrix(self):
        return qml.QNode(self.qml_circuit_with_density_matrix_meas, self.dev)
    
    def get_QNode_with_probs(self):
        return qml.QNode(self.qml_circuit_with_probs_meas, self.dev)
    
    def get_n_qubits(self):
        return self.n_qubits
    
    def get_param_symbols(self):
        return self.param_symbols
    
    def get_valid_states(self):
        return self.valid_states