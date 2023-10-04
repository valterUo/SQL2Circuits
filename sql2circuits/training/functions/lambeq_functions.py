# -*- coding: utf-8 -*-

try:
    from jax import numpy as np
except ModuleNotFoundError:
    import numpy as np
import multiprocessing
from discopy.quantum import Circuit

def cross_entropy(predictions, targets):
    N = predictions.shape[0]
    ce = -np.sum(targets*np.log(predictions+1e-9))/N
    return ce

def predict_circuit(circuit_fn, params):
    output = Circuit.eval(*circuit_fn(*params))
    predictions = np.abs(output.array) + 1e-9
    ratio = predictions / predictions.sum()
    return ratio

def make_lambeq_pred_fn(circuits, parameters, classification):

    circuit_fns = [circuit.lambdify(*parameters) for circuit in circuits]

    def predict(params):
        outputs = Circuit.eval(*(c(*params) for c in circuit_fns), dtype=float)
        res = []
        for output in outputs:
            predictions = np.abs(output.array) + 1e-9 # type: ignore
            ratio = predictions / predictions.sum()
            res.append(ratio)
        return np.array(res)
    
    # For some reason multiprocessing does not work with lambeq + noisyopt?
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
        return results
            
    return predict


def make_lambeq_cost_fn(pred_fn, labels, loss_fn, accuracy_fn, costs_accuracies = None, type = None):
    
    def cost_fn(params, **kwargs):
        predictions = pred_fn(params)
        #cost = loss_fn(predictions, labels)
        cost = cross_entropy(np.array(predictions), np.array(labels))
        accuracy = accuracy_fn(predictions, labels)
        if costs_accuracies is not None and type is not None:
            costs_accuracies.add_cost(cost, type)
            costs_accuracies.add_accuracy(accuracy, type)
        return cost

    return cost_fn