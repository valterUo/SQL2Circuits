# -*- coding: utf-8 -*-

from concurrent.futures import ThreadPoolExecutor
import numpy as np

class QNodeCollection:

    def __init__(self, pennylane_circuits, processors = 16):
        self.pennylane_circuits = pennylane_circuits
        self.processors = processors


    def simulate_parallel(self, params):
        results = []
        with ThreadPoolExecutor(self.processors) as executor:
            futures = { str(i) : executor.submit(circuit.get_QNode(), params) for i, circuit in enumerate(self.pennylane_circuits)}
        results = { key : future.result() for key, future in futures.items() }
        result = [np.array(results[key]) for key in sorted(results.keys())]
        return result, [circuit.get_n_qubits() for circuit in self.pennylane_circuits]