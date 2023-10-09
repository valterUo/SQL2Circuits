# -*- coding: utf-8 -*-

import itertools

from training.utils import construct_data_and_labels, select_circuits, store_and_log, select_pennylane_circuits


class DataPreparationManager:

    def __init__(self, id, data_preparator, circuits, number_of_circuits, qc_framework = "lambeq"):
        self.id = id
        self.stats_circuits_file = "training//results//" + str(self.id) + "//" + str(self.id) + "_stats_circuits_level.json"
        training_data = data_preparator.get_training_data()
        validation_data = data_preparator.get_validation_data()
        test_data = data_preparator.get_test_data()

        training_classes = data_preparator.get_training_data_labels()
        validation_classes = data_preparator.get_validation_data_labels()
        test_classes = data_preparator.get_test_data_labels()

        circuits.select_circuits_with_data_point(training_data, validation_data, test_data)

        # Training, validation and test circuits
        training_circuits = circuits.get_training_circuits()
        validation_circuits = circuits.get_validation_circuits()
        test_circuits = circuits.get_test_circuits()
        self.lambeq_symbols = circuits.get_lambeq_symbols()

        if qc_framework == "pennylane":
            circuits.generate_pennylane_circuits()
            circuits.select_qml_circuits_with_data_point(training_data, validation_data, test_data)
            training_circuits = circuits.get_qml_training_circuits()
            validation_circuits = circuits.get_qml_validation_circuits()
            test_circuits = circuits.get_qml_test_circuits()
            self.qml_train_symbols = circuits.get_qml_train_symbols()

        if number_of_circuits == "all":
            number_of_circuits = len(training_circuits)

        # Select the first circuits
        self.current_training_circuits = dict(itertools.islice(training_circuits.items(), number_of_circuits))
        print("Number of training circuits is ", len(self.current_training_circuits))
        if qc_framework == "pennylane":
            self.current_validation_circuits = select_pennylane_circuits(self.current_training_circuits, validation_circuits, number_of_circuits)
            self.current_test_circuits = select_pennylane_circuits(self.current_training_circuits, test_circuits, number_of_circuits)
        else:
            self.current_validation_circuits = select_circuits(self.current_training_circuits, validation_circuits, number_of_circuits)
            self.current_test_circuits = select_circuits(self.current_training_circuits, test_circuits, number_of_circuits)

        # Construct the data and labels for the training, validation and test circuits
        self.training_circuits_X, self.training_labels_y = construct_data_and_labels(self.current_training_circuits, training_classes)
        self.validation_circuits_X, self.validation_labels_y = construct_data_and_labels(self.current_validation_circuits, validation_classes)
        self.test_circuits_X, self.test_labels_y = construct_data_and_labels(self.current_test_circuits, test_classes)

    def get_X_train(self):
        return self.training_circuits_X
    
    def get_training_labels(self):
        return self.training_labels_y
    
    def get_X_valid(self):
        return self.validation_circuits_X
    
    def get_validation_labels(self):
        return self.validation_labels_y
    
    def get_X_test(self):
        return self.test_circuits_X
    
    def get_test_labels(self):
        return self.test_labels_y
    
    def save_stats(self):
        n_circs = len(self.current_training_circuits)
        stats = {}
        stats = {"number_of_training_circuits": n_circs, 
                "number_of_validation_circuits": len(self.current_validation_circuits), 
                "number_of_test_circuits": len(self.current_test_circuits), 
                "number_of_parameters_in_model": len(set([sym for circuit in self.current_training_circuits for sym in circuit.free_symbols]))}
        
        store_and_log(n_circs, stats, self.stats_circuits_file)

    def get_qml_train_symbols(self):
        return self.qml_train_symbols
    
    def get_lambeq_symbols(self):
        return self.lambeq_symbols