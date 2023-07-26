# -*- coding: utf-8 -*-

from jax import numpy as np
from discopy.quantum import Circuit

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


def make_lambeq_cost_fn(pred_fn, labels, loss_fn, accuracy_fn):
    def cost_fn(params, **kwargs):
        predictions = pred_fn(params)
        cost = loss_fn(predictions, labels)
        accuracy = accuracy_fn(predictions, labels)
        costs.append(cost)
        accuracies.append(accuracy)
        return cost

    costs, accuracies = [], []
    return cost_fn, costs, accuracies