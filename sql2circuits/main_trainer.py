# -*- coding: utf-8 -*-

import warnings
import os
#from jax import numpy as np
import numpy
#from jax import jit
from circuit_preparation.circuits import Circuits
from data_preparation.database import Database
from data_preparation.prepare import DataPreparation
from data_preparation.queries import QueryGenerator
from training.data_preparation_manager import DataPreparationManager
from training.trainers.lambeq_noisyopt import LambeqTrainer
from training.trainers.pennylane_noisyopt import PennylaneTrainer
from training.trainers.pennylane_optax import PennylaneTrainerJAX
from training.utils import *
#from discopy.tensor import Tensor

warnings.filterwarnings('ignore')
this_folder = os.path.abspath(os.getcwd())
SEED = 0
rng = numpy.random.default_rng(SEED)
numpy.random.seed(SEED)


class SQL2Circuits():

    def __init__(self, run_id, classification, seed_file, qc_framework, classical_optimizer, measurement, workload_type, initial_number_of_circuits, number_of_circuits_to_add, iterative):

        print("The selected configuration is: ")
        print("Run id: ", run_id)
        print("Seed file: ", seed_file)
        print("Quantum circuit framework: ", qc_framework)
        print("Classical optimizer: ", classical_optimizer)
        print("Measurement: ", measurement)
        print("Workload type: ", workload_type)
        print("Initial number of circuits: ", initial_number_of_circuits)
        print("Number of circuits to add: ", number_of_circuits_to_add)
        print("Iterative: ", iterative)
        print("Classification: ", classification)

        self.run_id = run_id
        self.classification = classification
        self.seed_file = seed_file
        self.qc_framework = qc_framework
        self.classical_optimizer = classical_optimizer
        self.measurement = measurement
        self.workload_type = workload_type
        self.initial_number_of_circuits = initial_number_of_circuits
        self.number_of_circuits_to_add = number_of_circuits_to_add
        self.iterative = iterative
        self.identifier = str(run_id) + "_" + qc_framework + "_" + classical_optimizer + "_" + measurement + "_" + workload_type
        self.result = None
        
        database = Database("IMDB")
        generator = QueryGenerator(self.run_id, workload_type = self.workload_type, database = "IMDB", query_seed_file_path = self.seed_file)
        query_file = generator.get_query_file()
        self.data_preparator = DataPreparation(run_id, query_file, database = database, workload_type = self.workload_type, classification = self.classification)
        self.total_number_of_circuits = len(self.data_preparator.get_training_data_labels())

        output_folder = this_folder + "//circuit_preparation//data//circuits//" + str(run_id) + "//"
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            print("The new directory: ", output_folder, " is created for circuits.")

        self.results_folder = this_folder + "//training//results//" + self.identifier + "//"
        if not os.path.exists(self.results_folder):
            os.makedirs(self.results_folder)
            print("The new directory: ", self.results_folder, " is created for results.")

        self.circuits = Circuits(run_id, query_file, output_folder, write_cfg_to_file = True, write_pregroup_to_file=True, generate_circuit_png_diagrams = True)
        self.circuits.execute_full_transformation()


    def train(self):
        if self.iterative and self.classical_optimizer == "noisyopt":
            self.iterative_train_noisyopt()
        elif not self.iterative and self.classical_optimizer == "noisyopt":
            self.single_train_noisyopt()
        elif self.iterative and self.classical_optimizer == "optax":
            self.iterative_train_optax()
        

    def iterative_train_noisyopt(self, a = 0.1, c = 0.1, epochs = 500, hyperparameter_file = None):
        for i in range(self.initial_number_of_circuits, 
                       self.total_number_of_circuits + self.number_of_circuits_to_add, 
                       self.number_of_circuits_to_add):
            if i > self.total_number_of_circuits:
                i = self.total_number_of_circuits
            self.train_noisyopt(i, a, c, epochs, hyperparameter_file)


    def single_train_noisyopt(self, a = 0.1, c = 0.1, epochs = 500, hyperparameter_file = None):
        self.train_noisyopt(self.total_number_of_circuits, a, c, epochs, hyperparameter_file)


    def train_noisyopt(self, number_of_selected_circuits, a = 0.1, c = 0.1, epochs = 500, hyperparameter_file = None):
        if hyperparameter_file is not None:
            # "training//results//" + str(run_id) + "//" + str(i) + "_" + str(run_id) + "_cv_results_.json"
            with open(hyperparameter_file, "r") as f:
                param_file = json.load(f)
                a = param_file["best_params"]["a"]
                c = param_file["best_params"]["c"]

        sf = DataPreparationManager(self.run_id, self.data_preparator, self.circuits, number_of_selected_circuits, self.qc_framework)
        X_train = sf.get_X_train()
        X_valid = sf.get_X_valid()
        y = sf.get_y()

        if self.qc_framework == "lambeq":
            trainer = LambeqTrainer(self.run_id,
                                circuits = self.circuits,
                                workload_type = self.workload_type,
                                classification = 2,
                                a = a,
                                c = c,
                                epochs = epochs,
                                qc_framework = self.qc_framework,
                                classical_optimizer = self.classical_optimizer,
                                measurement = self.measurement)
            self.result = trainer.fit_with_lambeq_noisyopt(X_train, y, X_valid = X_valid, save_parameters = True)

        elif self.qc_framework == "pennylane":
            trainer = PennylaneTrainer(self.run_id,
                                circuits = self.circuits,
                                workload_type = self.workload_type,
                                classification = 2,
                                a = a,
                                c = c,
                                epochs = epochs,
                                qc_framework = self.qc_framework,
                                classical_optimizer = self.classical_optimizer,
                                measurement = self.measurement)
            self.result = trainer.fit_with_pennylane_noisyopt(X_train, y, X_valid = X_valid, save_parameters = True)


    def train_optax(self, number_of_circuits):
        sf = DataPreparationManager(self.run_id, self.data_preparator, self.circuits, number_of_circuits, self.qc_framework)
        params = sf.get_qml_train_symbols()
        X_train = sf.get_X_train()
        X_valid = sf.get_X_valid()
        y = sf.get_y()

        trainer = PennylaneTrainerJAX(self.classical_optimizer, params, epochs = 500)

        self.result = trainer.train(X_train, y, X_valid = X_valid)
        print(self.result)
        # Store the results to pickled file
        with open(self.results_folder + str(number_of_circuits) + "_optax_results_.pkl", "wb") as f:
            pickle.dump(self.result, f)

        #store_to_json(self.result, self.results_folder + str(number_of_circuits) + "_optax_results_.json")
        #store_hyperparameter_opt_results("main_pennylane_jax_" + str(i), opt)

    def iterative_train_optax(self):
        for i in range(self.initial_number_of_circuits, 
                       self.total_number_of_circuits + self.number_of_circuits_to_add, 
                       self.number_of_circuits_to_add):
            if i > self.total_number_of_circuits:
                i = self.total_number_of_circuits
            self.train_optax(i)