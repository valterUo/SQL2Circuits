# -*- coding: utf-8 -*-

#from jax import numpy as np
import multiprocessing
import numpy as np
from discopy.quantum import Circuit
from discopy.tensor import Tensor
Tensor.np = np

# Maybe explore these backends later
#from pytket.extensions.qiskit import AerBackend
#from pytket.extensions.qulacs import QulacsBackend
#from pytket.extensions.cirq import CirqStateSampleBackend

def predict_circuit(circuit_fn, params):
    output = Circuit.eval(*circuit_fn(*params))
    predictions = np.abs(output.array) + 1e-9
    ratio = predictions / predictions.sum()
    return ratio

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
    

    def predict2(params):
        args = [(circuit_fn, params) for circuit_fn in circuit_fns]
        results = []
        queue = multiprocessing.Queue()
        with multiprocessing.Pool(processes=8) as pool:
            for arg in args:
                pool.apply_async(predict_circuit, arg, callback=queue.put)
            pool.close()
            pool.join()
        while not queue.empty():
            results.append(queue.get())
            
    return predict2


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