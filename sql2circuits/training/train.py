# -*- coding: utf-8 -*-

import warnings
import json
import os
import sys
import glob
from math import ceil
from pathlib import Path
from jax import numpy as np
from sympy import default_sort_key
import numpy
import pickle
import matplotlib.pyplot as plt

import jax
from jax import jit
from noisyopt import minimizeSPSA, minimizeCompass

from discopy.quantum import Circuit
from discopy.tensor import Tensor
from discopy.utils import loads
#from pytket.extensions.qiskit import AerBackend
#from pytket.extensions.qulacs import QulacsBackend
#from pytket.extensions.cirq import CirqStateSampleBackend
backend = None

from training.utils import *
#from sklearn.metrics import accuracy_score, recall_score, precision_score, f1_score

warnings.filterwarnings('ignore')
this_folder = os.path.abspath(os.getcwd())
os.environ['TOKENIZERS_PARALLELISM'] = 'true'
#os.environ["JAX_PLATFORMS"] = "cpu"

SEED = 0

# This avoids TracerArrayConversionError from jax
Tensor.np = np

rng = numpy.random.default_rng(SEED)
numpy.random.seed(SEED)

class SQL2CircuitsTrainer:

    def __init__(self, circuits, data_prep, workload = "execution_time", classification = 2):
        self.circuits = circuits
        self.data_prep = data_prep
        self.workload = workload # execution_time or cardinality
        self.classification = classification
        diagrams = self.circuits.get_circuit_diagrams()

        # Training, test and validation circuits
        self.training_circuits = diagrams["training"]
        self.test_circuits = diagrams["test"]
        self.validation_circuits = diagrams["validation"]

        # Training, test and validation data
        self.training_data = self.data_prep.get_training_data()
        self.test_data = self.data_prep.get_test_data()
        self.validation_data = self.data_prep.get_validation_data()

        self.training_data_list = [{"id": k, "cardinality": v} for k, v in self.training_data.items()]
        self.test_data_list= [{"id": k, "cardinality": v} for k, v in self.test_data.items()]
        self.validation_data_list = [{"id": k, "cardinality": v} for k, v in self.validation_data.items()]

        # Because we did not get a data point for each query (limited excution time), we need to remove the circuits that do not have a data point
        # Select all those circuits whose key is in the training_data dictionary
        self.training_circuits = {k: v for k, v in self.training_circuits.items() if k in self.training_data}
        self.test_circuits = {k: v for k, v in self.test_circuits.items() if k in self.test_data}
        self.validation_circuits = {k: v for k, v in self.validation_circuits.items() if k in self.validation_data}

        # Check that the keys of the circuits and the data are the same
        #print(set(self.training_circuits.keys()) - set(self.training_data.keys()))
        #print(set(self.test_circuits.keys()) - set(self.test_data.keys()))
        #print(set(self.validation_circuits.keys()) - set(self.validation_data.keys()))

        self.training_data_labels, classes = create_labeled_training_classes(self.training_data_list, self.classification, workload)
        self.test_data_labels = create_labeled_test_validation_classes(self.test_data_list, classes, workload)
        self.validation_data_labels = create_labeled_test_validation_classes(self.validation_data_list, classes, workload)

        
