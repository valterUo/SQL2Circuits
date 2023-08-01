# -*- coding: utf-8 -*-

import itertools

from training.utils import construct_data_and_labels, select_circuits, store_and_log, select_pennylane_circuits


class SampleFeaturePreparator:

    def __init__(self, id, data_preparator, circuits, number_of_circuits, optimization_method):
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

        if optimization_method == "Pennylane":
            circuits.generate_pennylane_circuits()
            training_circuits = circuits.get_qml_training_circuits()
            validation_circuits = circuits.get_qml_validation_circuits()
            test_circuits = circuits.get_qml_test_circuits()

        if number_of_circuits == "all":
            number_of_circuits = len(training_circuits)

        # Select the first circuits
        self.current_training_circuits = dict(itertools.islice(training_circuits.items(), number_of_circuits))
        if optimization_method == "Pennylane":
            self.current_validation_circuits = select_pennylane_circuits(self.current_training_circuits, validation_circuits, number_of_circuits)
            self.current_test_circuits = select_pennylane_circuits(self.current_training_circuits, test_circuits, number_of_circuits)
        else:
            self.current_validation_circuits = select_circuits(self.current_training_circuits, validation_circuits, number_of_circuits)
            self.current_test_circuits = select_circuits(self.current_training_circuits, test_circuits, number_of_circuits)

        # Construct the data and labels for the training, validation and test circuits
        training_circuits_X, training_labels_y = construct_data_and_labels(self.current_training_circuits, training_classes)
        validation_circuits_X, validation_labels_y = construct_data_and_labels(self.current_validation_circuits, validation_classes)
        test_circuits_X, test_labels_y = construct_data_and_labels(self.current_test_circuits, test_classes)

        self.X_train = [[circuit] for circuit in training_circuits_X]
        self.X_valid = list(zip(validation_circuits_X, validation_labels_y))
        self.y = training_labels_y

    def get_X_train(self):
        return self.X_train
    
    def get_X_valid(self):
        return self.X_valid
    
    def get_y(self):
        return self.y
    
    def save_stats(self):
        n_circs = len(self.current_training_circuits)
        stats = {}
        stats = {"number_of_training_circuits": n_circs, 
                "number_of_validation_circuits": len(self.current_validation_circuits), 
                "number_of_test_circuits": len(self.current_test_circuits), 
                "number_of_parameters_in_model": len(set([sym for circuit in self.current_training_circuits for sym in circuit.free_symbols]))}
        
        store_and_log(n_circs, stats, self.stats_circuits_file)