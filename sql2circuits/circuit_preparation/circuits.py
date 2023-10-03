# -*- coding: utf-8 -*-

import os
import json
import pickle
from circuit_preparation.diagrams.diagram_generators import *
from training.utils import get_symbols
from training.functions.pennylane_functions import transform_into_pennylane_circuits


def split(list_a, chunk_size):
    if list_a == []:
        return []
    for i in range(0, len(list_a), chunk_size):
        yield list_a[i:i + chunk_size]


class Circuits:
    """
    A class for generating quantum circuits from SQL queries.

    Attributes:
        id (int): The ID of the workload.
        query_file_path (str): The path to the file containing the SQL queries.
        output_folder (str): The path to the folder where the circuit diagrams will be saved.
        write_cfg_to_file (bool): Whether to write the CFG diagrams to a file.
        write_pregroup_to_file (bool): Whether to write the pregroup diagrams to a file.
        generate_cfg_png_diagrams (bool): Whether to generate diagrams as PNG pictures for the CFGs.
        generate_pregroup_png_diagrams (bool): Whether to generate diagrams as PNG pictures for the pregroups.
        generate_circuit_png_diagrams (bool): Whether to generate diagrams as PNG pictures for the circuits.
        generate_circuit_json_diagrams (bool): Whether to generate JSON diagrams for the circuits.
        classification (int): The classification of the circuit.
        layers (int): The number of layers in the circuit.
        single_qubit_params (int): The number of parameters for each single-qubit gate.
        n_wire_count (int): The number of wires in the circuit.
        queries (dict): A dictionary containing the SQL queries.
        query_data (dict): A dictionary containing the query data.
        cfg_diagrams (dict): A dictionary containing the CFG diagrams.
        pregroup_diagrams (dict): A dictionary containing the pregroup diagrams.
        capless_pregroup_diagrams (dict): A dictionary containing the capless pregroup diagrams.
        circuit_diagrams (dict): A dictionary containing the circuit diagrams.
    """

    def __init__(self, 
                 id, 
                 query_file_path, 
                 output_folder,
                 classification,
                 interface = 'auto',
                 diff_method = 'best',
                 write_cfg_to_file = False, 
                 write_pregroup_to_file = False, 
                 generate_cfg_png_diagrams = False, 
                 generate_pregroup_png_diagrams = False, 
                 generate_circuit_png_diagrams = False,
                 generate_circuit_json_diagrams = False) -> None:
        self.id = id
        self.query_file_path = query_file_path
        self.output_folder = output_folder
        self.classification = classification
        self.layers = 1
        self.single_qubit_params = 3
        self.n_wire_count = 1
        self.generate_pregroup_png_diagrams = generate_pregroup_png_diagrams
        self.generate_circuit_png_diagrams = generate_circuit_png_diagrams
        self.generate_cfg_png_diagrams = generate_cfg_png_diagrams
        self.write_cfg_to_file = write_cfg_to_file
        self.write_pregroup_to_file = write_pregroup_to_file
        self.generate_circuit_json_diagrams = generate_circuit_json_diagrams
        self.interface = interface
        self.diff_method = diff_method

        self.training_circuits = None
        self.validation_circuits = None
        self.test_circuits = None
        self.qml_training_circuits = None
        self.qml_validation_circuits = None
        self.qml_test_circuits = None
        self.qml_train_symbols = None
        self.qml_validation_symbols = None
        self.qml_test_symbols = None

        query_file = open(self.query_file_path, "r")
        self.query_data = json.load(query_file)
        self.queries = self.query_data["queries"]

        self.cfg_diagrams = dict()
        self.pregroup_diagrams = dict()
        self.capless_pregroup_diagrams = dict()
        self.circuit_diagrams = dict()

        # Check if the files exist load them from the disk
        if os.path.isfile(self.output_folder + "//cfg_diagrams_" + str(self.id) + ".json"):
            with open(self.output_folder + "//cfg_diagrams_" + str(self.id) + ".json") as json_file:
                self.cfg_diagrams = json.load(json_file)
        if os.path.isfile(self.output_folder + "//pregroup_diagrams_" + str(self.id) + ".json"):
            with open(self.output_folder + "//pregroup_diagrams_" + str(self.id) + ".json") as json_file:
                self.pregroup_diagrams = json.load(json_file)
        if os.path.isfile(self.output_folder + "//capless_pregroup_diagrams_" + str(self.id) + ".json"):
            with open(self.output_folder + "//capless_pregroup_diagrams_" + str(self.id) + ".json") as json_file:
                self.capless_pregroup_diagrams = json.load(json_file)
        if os.path.isfile(self.output_folder + "//circuit_diagrams_" + str(self.id) + ".pickle"):
            with open(self.output_folder + "//circuit_diagrams_" + str(self.id) + ".pickle", 'rb') as outfile:
                    self.circuit_diagrams = pickle.load(outfile)
                    self.training_circuits = self.circuit_diagrams["training"]
                    self.test_circuits = self.circuit_diagrams["test"]
                    self.validation_circuits = self.circuit_diagrams["validation"]
            circuit = self.training_circuits[list(self.training_circuits.keys())[0]]
            circuit.draw()
                

    def generate_pennylane_circuits(self):
        self.qml_training_circuits, self.qml_train_symbols = transform_into_pennylane_circuits(self.training_circuits, 
                                                                                               self.classification, 
                                                                                               interface = self.interface, 
                                                                                               diff_method = self.diff_method)
        self.qml_test_circuits, self.qml_test_symbols = transform_into_pennylane_circuits(self.test_circuits, 
                                                                                          self.classification, 
                                                                                          interface = self.interface, 
                                                                                          diff_method = self.diff_method)
        self.qml_validation_circuits, self.qml_val_symbols = transform_into_pennylane_circuits(self.validation_circuits, 
                                                                                               self.classification, 
                                                                                               interface = self.interface, 
                                                                                               diff_method = self.diff_method)


    def generate_cfg_diagrams(self):
        if len(self.cfg_diagrams) == 0:
            for queryset in self.queries:
                queries = self.queries[queryset]
                result = create_CFG_diagrams(queries, self.generate_cfg_png_diagrams)
                self.cfg_diagrams[queryset] = result
            if self.write_cfg_to_file:
                with open(self.output_folder + "//cfg_diagrams_" + str(self.id) + ".json", 'w') as outfile:
                    json.dump(self.cfg_diagrams, outfile, indent = 4)


    def generate_pregroup_diagrams(self):
        if len(self.pregroup_diagrams) == 0:
            for queryset in self.cfg_diagrams:
                queries = self.cfg_diagrams[queryset]
                result = create_pregroup_grammar_diagrams(queries, self.generate_pregroup_png_diagrams)
                self.pregroup_diagrams[queryset] = result
                if self.write_pregroup_to_file:
                    with open(self.output_folder + "//pregroup_diagrams_" + str(self.id) + ".json", 'w') as outfile:
                        json.dump(self.pregroup_diagrams, outfile, indent = 4)


    def generate_capless_pregroup_diagrams(self):
        if len(self.capless_pregroup_diagrams) == 0:
            for queryset in self.pregroup_diagrams:
                queries = self.pregroup_diagrams[queryset]
                result = remove_cups_and_simplify(queries, self.generate_pregroup_png_diagrams)
                self.capless_pregroup_diagrams[queryset] = result
                if self.write_pregroup_to_file:
                    with open(self.output_folder + "//capless_pregroup_diagrams_" + str(self.id) + ".json", 'w') as outfile:
                        json.dump(self.capless_pregroup_diagrams, outfile, indent = 4)


    def genereate_circuit_diagrams(self):
        if len(self.circuit_diagrams) == 0:
            for queryset in self.capless_pregroup_diagrams:
                queries = self.capless_pregroup_diagrams[queryset]
                result = create_circuit_ansatz(queries, 
                                                self.classification, 
                                                self.layers, 
                                                self.single_qubit_params,
                                                self.n_wire_count, 
                                                self.generate_circuit_png_diagrams,
                                                self.generate_circuit_json_diagrams)
                self.circuit_diagrams[queryset] = result
                with open(self.output_folder + "//circuit_diagrams_" + str(self.id) + ".pickle", 'wb') as outfile:
                    pickle.dump(self.circuit_diagrams, outfile)


    def execute_full_transformation(self):
        self.generate_cfg_diagrams()
        self.generate_pregroup_diagrams()
        self.generate_capless_pregroup_diagrams()
        self.genereate_circuit_diagrams()
        self.training_circuits = self.circuit_diagrams["training"]
        self.test_circuits = self.circuit_diagrams["test"]
        self.validation_circuits = self.circuit_diagrams["validation"]


    def get_cfg_diagrams(self):
        return self.cfg_diagrams
    
    def get_pregroup_diagrams(self):
        return self.pregroup_diagrams
    
    def get_capless_pregroup_diagrams(self):
        return self.capless_pregroup_diagrams
    
    def get_circuit_diagrams(self):
        return self.circuit_diagrams
    
    def select_circuits_with_data_point(self, training_data, validation_data, test_data):
        # Because we did not get a data point for each query (limited excution time), 
        # we need to remove the circuits that do not have a data point
        # Select all those circuits whose key is in the training_data dictionary
        self.training_circuits = {k: v for k, v in self.training_circuits.items() if k in training_data}
        self.validation_circuits = {k: v for k, v in self.validation_circuits.items() if k in validation_data}
        self.test_circuits = {k: v for k, v in self.test_circuits.items() if k in test_data}

    def get_training_circuits(self):
        return self.training_circuits
    
    def get_validation_circuits(self):
        return self.validation_circuits
    
    def get_test_circuits(self):
        return self.test_circuits
    
    def get_qml_training_circuits(self):
        return self.qml_training_circuits
    
    def get_qml_validation_circuits(self):
        return self.qml_validation_circuits
    
    def get_qml_test_circuits(self):
        return self.qml_test_circuits
    
    def get_qml_train_symbols(self):
        return self.qml_train_symbols
    
    def get_qml_val_symbols(self):
        return self.qml_val_symbols
    
    def get_qml_test_symbols(self):
        return self.qml_test_symbols
    
    def get_lambeq_symbols(self):
        return get_symbols(list(self.training_circuits.values()) + list(self.validation_circuits.values()) + list(self.test_circuits.values()))