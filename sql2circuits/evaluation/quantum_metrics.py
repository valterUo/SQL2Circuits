# -*- coding: utf-8 -*-

from matplotlib import pyplot as plt
import numpy


class Expressibility:

    def __init__(self, pennylane_circuits, params) -> None:
        self.penylane_circuits = pennylane_circuits
        self.params = params
        num_of_bins = 75
        self.bins_list = [i/(num_of_bins) for i in range(num_of_bins + 1)]
        self.bins_x = [self.bins_list[1] + self.bins_list[i] for i in range(num_of_bins - 1)]

        def P_harr(l, u, N):
            return (1-l)**(N-1)-(1-u)**(N-1)

        #Harr histogram
        P_harr_hist = [P_harr(self.bins_list[i], self.bins_list[i+1], 2) for i in range(num_of_bins)]
        self.fidelity = []

    def calculate_expressibility(self):
        for x in range(10):
            print("Progress:", x)
            for c in self.penylane_circuits:
                disco_circuit = circuits[c]
                qml_circuit = to_pennylane(disco_circuit, probabilities = True)
                current_symbols = disco_circuit.free_symbols
                current_symbols = list(sorted(current_symbols, key=default_sort_key))
                params = torch.Tensor([[2*np.pi*random.uniform(0, 1)] for i in range(len(current_symbols))]) 
                result = qml_circuit.eval(symbols=current_symbols, weights=params)
                result = [float(t) for t in result]
                #print(result)
                self.fidelity.append(result[0]/sum(result))

    def plot_expressibility(self):
        weights = numpy.ones_like(self.fidelity)/float(len(self.fidelity))
        res = plt.hist(self.fidelity, bins=self.bins_list, weights=weights, label='Result', range=[0, 1])
        plt.plot(self.bins_x, self.P_harr_hist[:-1], label='Harr random')
        plt.legend(loc='upper right')
        plt.show()


class EntanglingCapability:

    def __init__(self) -> None:
        pass