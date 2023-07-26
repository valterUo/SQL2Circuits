import collections
#from jax import numpy as np
import numpy as np
from discopy.quantum.pennylane import to_pennylane
import covalent as ct
#from jax import jit
#from jax import config
#config.update("jax_enable_x64", True)

def genbin(n, bs=''):
    if len(bs) == n:
        return bs
    else:
        return np.array([genbin(n, bs + '0'), genbin(n, bs + '1')]).flatten()

def post_selection(circuit_samples, n_qubits, post_selection):
    selected_samples = []
    post_select_array = np.array([0]*(n_qubits - post_selection))
    for circuit_sample in circuit_samples:
        if np.array_equal(circuit_sample[post_selection - 1 :-1], post_select_array):
            res = circuit_sample[0:post_selection]
            selected_samples.append(res)
            #if circuit_sample[0] == 1:
            #    selected_samples.append(1)
            #else:
            #    selected_samples.append(0)
    return selected_samples

def make_pennylane_pred_fn(circuits, parameters, classification):
    
    def predict2(params):
        predictions = {}
        for c in circuits:
            disco_circuit = circuits[c]
            qml_circuit = to_pennylane(disco_circuit)
            result = qml_circuit.post_selected_circuit(params)
            predictions[c] = result
        return predictions
    
    @ct.lattice
    @ct.electron
    def predict(params):
        predictions = []
        #i = 0
        for pennylane_circuit in circuits:
            circuit = pennylane_circuit.get_QNode()
            n_qubits = pennylane_circuit.get_n_qubits()
            post_selected_samples = []
            while len(post_selected_samples) == 0:
                measurement = circuit(params)
                post_selected_samples = post_selection(measurement, n_qubits, classification)
                post_selected_samples = [tuple(map(int, t)) for t in post_selected_samples]
                counts = collections.Counter(post_selected_samples)
                if len(post_selected_samples) == 0:
                    print(counts)
                    continue
                predicted = counts.most_common(1)[0][0]
                binary_string = ''.join(str(bit) for bit in predicted[::-1])
                binary_int = int(binary_string, 2)
                result = np.array([1e-9]*2**classification)
                result[binary_int] = 1
                #print(predicted, binary_int, result)
                predictions.append(list(result))
        return predictions
    return predict


def make_pennylane_cost_fn(pred_fn, labels, loss_fn, accuracy_fn):
    costs, accuracies = [], []
    
    @ct.lattice
    def cost_spsa(params, **kwargs):
        predictions = pred_fn(params)
        #print(predictions, labels)
        
        cost = loss_fn(predictions, labels)
        print("Cost in cost_spsa function: ", cost)
        accuracy = accuracy_fn(predictions, labels)
        costs.append(cost)
        accuracies.append(accuracy)
        
        return cost
    return cost_spsa, costs, accuracies