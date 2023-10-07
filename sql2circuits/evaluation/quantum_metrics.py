# -*- coding: utf-8 -*-

import os
import random
from matplotlib import pyplot as plt
import numpy as np
import torch
from qiskit.quantum_info import partial_trace, Statevector
from scipy.special import kl_div
from scipy.spatial.distance import jensenshannon
this_folder = os.path.abspath(os.getcwd())

class Expressibility:

    def __init__(self, circuits, classification) -> None:
        self.pennylane_circuits = circuits.get_all_qml_circuits()
        self.params = circuits.get_qml_symbols()
        self.num_of_bins = 75
        self.classification = classification
        self.bins_list = [i/(self.num_of_bins) for i in range(self.num_of_bins + 1)]
        self.bins_x = [self.bins_list[1] + self.bins_list[i] for i in range(self.num_of_bins - 1)]
        
        #Harr histogram
        self.P_harr_hist = [self.P_harr(self.bins_list[i], self.bins_list[i+1], 2**classification) for i in range(self.num_of_bins)]
        self.fidelity = []


    def P_harr(self, l, u, N):
        return (1-l)**(N-1)-(1-u)**(N-1)


    def calculate_expressibility(self):
        for x in range(10):
            print("Progress:", x)
            for c in self.pennylane_circuits:
                circuit = self.pennylane_circuits[c].get_QNode_with_probs()
                #qml_circuit = to_pennylane(disco_circuit, probabilities = True)
                #current_symbols = disco_circuit.free_symbols
                #current_symbols = list(sorted(current_symbols, key=default_sort_key))
                params = [2*np.pi*random.uniform(0, 1) for i in range(len(self.params))]
                result = circuit(params) #qml_circuit.eval(symbols=current_symbols, weights=params)
                # Take only valid states which correspond to indices in self.pennylane_circuits[c].get_valid_states()
                valid_states = []
                for i in self.pennylane_circuits[c].get_valid_states():
                    valid_states.append(result[i])
                valid_states = np.array(valid_states)
                valid_states = valid_states / np.sum(valid_states)
                #for i, prob in enumerate(valid_states):
                #    self.fidelity[i] = self.fidelity[i] + prob
                #self.fidelity = self.fidelity / sum(self.fidelity)
                self.fidelity.append(valid_states[0])


    def plot_expressibility(self):
        weights = np.ones_like(self.fidelity)/float(len(self.fidelity))
        res = plt.hist(self.fidelity, bins=self.bins_list, weights=weights, label='Result', range=[0, 1])
        plt.plot(self.bins_x, self.P_harr_hist[:-1], label='Harr random')
        plt.legend(loc='upper right')
        plt.savefig("expressibility_" + str(self.classification) + '.png')  # Save the histogram plot as a PNG file
        plt.show()
        
        # Save the histogram data to a CSV file
        csv_file = this_folder + "//evaluation//results//expressibility_" + str(self.classification) + ".csv"
        np.savetxt(csv_file, np.column_stack((res[1][:-2], res[0][:-1], self.bins_x, self.P_harr_hist[:-1])), delimiter=',', header='bin,fidelity,bins_x,P_harr_hist')
       
        
    def calculate_kl_div(self):
        weights = np.ones_like(self.fidelity)/float(len(self.fidelity))
        P_I_hist = np.histogram(self.fidelity, bins = self.bins_list, weights = weights, range=[0, 1])[0]
        kl_pq = kl_div(P_I_hist, self.P_harr_hist)
        print('KL(P || Q): %.3f nats' % sum(kl_pq))
        
        
    def calculate_js_div(self):
        weights = np.ones_like(self.fidelity)/float(len(self.fidelity))
        P_I_hist = np.histogram(self.fidelity, bins = self.bins_list, weights = weights, range=[0, 1])[0]
        js_pq = jensenshannon(P_I_hist, self.P_harr_hist)
        print('JS(P || Q): %.3f nats' % js_pq)



class EntanglingCapability:

    def __init__(self, circuits) -> None:
        self.pennylane_circuits = circuits.get_all_qml_circuits()
        self.params = circuits.get_qml_symbols()
    
    def mw_engtanglement(self, sample_size):
        engtanglement_values = {}
        for i, c in enumerate(self.pennylane_circuits):
            print("Progress:", i/len(self.pennylane_circuits))
            entropies = []
            for i in range(sample_size):
                entropy = 0
                n_qubits = self.pennylane_circuits[c].get_n_qubits() #len(self.pennylane_circuits[c].get_valid_states())
                qubit_list = list(range(n_qubits))
                params = [2*np.pi*random.uniform(0, 1) for i in range(len(self.params))]
                circuit = self.pennylane_circuits[c].get_QNode_with_state()
                result = circuit(params)
                state_vector = Statevector(result)
                
                for j in range(n_qubits):
                    rest = qubit_list[:j] + qubit_list[j+1:]
                    dens = partial_trace(state_vector, rest).data       
                    trace = np.trace(np.matmul(dens, dens))
                    entropy += trace.real
                entropy = entropy / n_qubits
                entropies.append(1.0 - entropy)
                
            Q = 2*np.sum(entropies)/sample_size
            print("Engtanglement:", Q)
            engtanglement_values[c] = Q
        
        return engtanglement_values