# -*- coding: utf-8 -*-

import itertools

from training.utils import construct_data_and_labels, select_circuits


class SampleFeaturePreparator:

    def __init__(self, data_preparator, circuits, number_of_circuits):
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

        if number_of_circuits == "all":
            number_of_circuits = len(training_circuits)

        # Select the first circuits
        current_training_circuits = dict(itertools.islice(training_circuits.items(), number_of_circuits))
        current_validation_circuits = select_circuits(current_training_circuits, validation_circuits, number_of_circuits)
        current_test_circuits = select_circuits(current_training_circuits, test_circuits, number_of_circuits)

        # Construct the data and labels for the training, validation and test circuits
        training_circuits_X, training_labels_y = construct_data_and_labels(current_training_circuits, training_classes)
        validation_circuits_X, validation_labels_y = construct_data_and_labels(current_validation_circuits, validation_classes)
        test_circuits_X, test_labels_y = construct_data_and_labels(current_test_circuits, test_classes)

        self.X_train = [[circuit] for circuit in training_circuits_X]
        self.X_valid = list(zip(validation_circuits_X, validation_labels_y))
        self.y = training_labels_y

    def get_X_train(self):
        return self.X_train
    
    def get_X_valid(self):
        return self.X_valid
    
    def get_y(self):
        return self.y