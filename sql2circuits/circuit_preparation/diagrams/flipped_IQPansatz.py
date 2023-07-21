"""
BSD 3-Clause License

Copyright (c) 2019, Oxford Quantum Group
All rights reserved.

Original source: https://github.com/oxford-quantum-group/discopy/blob/main/discopy/quantum/circuit.py


This reimplements the IQP classes to make sure that hadamards and rotations 
are in correct order in this special SQL transformation case.
"""

from __future__ import annotations

__all__ = ['CircuitAnsatz', 'IQPAnsatz']

from collections.abc import Mapping
from typing import Any, Callable, Optional

from discopy.quantum.circuit import (Circuit, Discard, Functor, Id, qubit)
from discopy.quantum.gates import Bra, Ket, Rx, Rz
from discopy.rigid import Box, Diagram, Ty
import numpy as np

import random
from itertools import takewhile, chain

from discopy import messages, monoidal, rigid, tensor
from discopy.cat import AxiomError
from discopy.tensor import Dim, Tensor
from math import pi
from functools import reduce, partial

from lambeq.ansatz import BaseAnsatz, Symbol
from lambeq import CircuitAnsatz

_ArMapT = Callable[[Box], Circuit]

class FlippedIQPansatz(Circuit):
    
    def __init__(self, n_qubits, params):
        from discopy.quantum.gates import H, Rx, Rz, CRz

        def layer(thetas):
            hadamards = Id(0).tensor(*(n_qubits * [H]))
            rotations = Id(n_qubits).then(*(
                Id(i) @ CRz(thetas[i]) @ Id(n_qubits - 2 - i)
                for i in range(n_qubits - 1)))
            
            # Modified line:
            return rotations >> hadamards
        
        if n_qubits == 1:
            circuit = Rx(params[0]) >> Rz(params[1]) >> Rx(params[2])
        elif len(Tensor.np.shape(params)) != 2\
                or Tensor.np.shape(params)[1] != n_qubits - 1:
            raise ValueError(
                "Expected params of shape (depth, {})".format(n_qubits - 1))
        else:
            depth = Tensor.np.shape(params)[0]
            circuit = Id(n_qubits).then(*(
                layer(params[i]) for i in range(depth)))
        super().__init__(
            circuit.dom, circuit.cod, circuit.boxes, circuit.offsets)

        
        
        
        
""" 
Copyright 2021-2022 Cambridge Quantum Computing Ltd.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

"""
Circuit Ansatz
==============
Original source: https://cqcl.github.io/lambeq/_modules/lambeq/ansatz/circuit.html#IQPAnsatz
A circuit ansatz converts a DisCoCat diagram into a quantum circuit.
"""


class IQPAnsatzFlipped(CircuitAnsatz):

    def __init__(self,
                 ob_map: Mapping[Ty, int],
                 n_layers: int,
                 n_single_qubit_params: int = 3,
                 discard: bool = False,
                 special_cases: Optional[Callable[[_ArMapT], _ArMapT]] = None):
        
        super().__init__(ob_map=ob_map, n_layers=n_layers,
                         n_single_qubit_params=n_single_qubit_params)

        if special_cases is None:
            special_cases = self._special_cases

        self.n_layers = n_layers
        self.n_single_qubit_params = n_single_qubit_params
        self.discard = discard
        self.functor = Functor(ob=self.ob_map,
                               ar=special_cases(self._ar))

    def _ar(self, box: Box) -> Circuit:
        label = self._summarise_box(box)
        dom, cod = self._ob(box.dom), self._ob(box.cod)
        
        n_qubits = max(dom, cod)
        n_layers = self.n_layers
        n_1qubit_params = self.n_single_qubit_params
        circuit = None
        
        if n_qubits == 0:
            circuit = Id()
        elif n_qubits == 1:
            syms = [Symbol(f'{label}_{i}') for i in range(n_1qubit_params)]
            rots = [Rx, Rz]
            circuit = Id(qubit)
            for i, sym in enumerate(syms):
                circuit >>= rots[i % 2](sym)
        else:
            if n_qubits == 2:
                syms = [Symbol(f'{label}_{i}') for i in range(2*n_1qubit_params)]
                rots = [Rx, Rz]
                circuit = Id(qubit) @ Id(qubit)
                for i in range(0, len(syms) - 1, 2):
                    circuit >>= rots[i % 2](syms[i]) @ rots[i % 2](syms[i + 1])
            n_params = n_layers * (n_qubits-1)
            syms = [Symbol(f'{label}_{i}') for i in range(n_params)]
            params: np.ndarray[Any, np.dtype[Any]] = np.array(syms).reshape(
                    (n_layers, n_qubits-1))
            if n_qubits == 2:
                circuit >>= FlippedIQPansatz(n_qubits, params)
            else:
                circuit = FlippedIQPansatz(n_qubits, params)

        if cod > dom:
            circuit <<= Id(dom) @ Ket(*[0]*(cod - dom))
        elif self.discard:
            circuit >>= Id(cod) @ Discard(dom - cod)
        else:
            circuit >>= Id(cod) @ Bra(*[0]*(dom - cod))
        return circuit