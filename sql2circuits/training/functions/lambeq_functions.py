# -*- coding: utf-8 -*-

#from jax import numpy as np
import numpy as np
from discopy.quantum import Circuit
from discopy.tensor import Tensor
Tensor.np = np

# Maybe explore these backends later
#from pytket.extensions.qiskit import AerBackend
#from pytket.extensions.qulacs import QulacsBackend
#from pytket.extensions.cirq import CirqStateSampleBackend

def make_lambeq_pred_fn(circuits, parameters, classification):

    circuit_fns = [circuit.lambdify(*parameters) for circuit in circuits]

    def predict(params):
        outputs = Circuit.eval(*(c(*params) for c in circuit_fns))
        res = []
        
        for output in outputs:
            predictions = np.abs(output.array) + 1e-9 # type: ignore
            ratio = predictions / predictions.sum()
            res.append(ratio)
            
        return np.array(res)
    
    return predict


def make_lambeq_cost_fn(pred_fn, labels, loss_fn, accuracy_fn, costs_accuracies = None, type = None):
    
    def cost_fn(params, **kwargs):
        predictions = pred_fn(params)
        cost = loss_fn(predictions, labels)
        accuracy = accuracy_fn(predictions, labels)
        if costs_accuracies is not None and type is not None:
            costs_accuracies.add_cost(cost, type)
            costs_accuracies.add_accuracy(accuracy, type)
        return cost

    return cost_fn