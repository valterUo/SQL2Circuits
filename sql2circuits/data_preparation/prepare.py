# -*- coding: utf-8 -*-

import os
import json

from training.utils import create_labeled_test_validation_classes, create_labeled_training_classes

this_folder = os.path.abspath(os.getcwd())

class DataPreparation:

    def __init__(self, id, query_file_path, database, workload_type, classification) -> None:
        self.query_file_path = query_file_path
        self.database = database
        self.this_folder = os.path.abspath(os.getcwd())
        query_file = open(self.query_file_path, "r")
        self.queries = json.load(query_file)

        stats = self.queries["stats"]
        queries = self.queries["queries"]

        print("Number of training queries is ", stats["number_of_training_queries"])
        print("Number of test queries is ", stats["number_of_test_queries"])
        print("Number of validation queries is ", stats["number_of_validation_queries"])
        print(workload_type)
        
        self.data_file = self.database.generate_data(id, queries, workload_type)
        print("Data file is ", self.data_file)
        self.data = dict()
        with open(self.data_file) as json_file:
            self.data = json.load(json_file)

        self.training_data = self.data["training"]
        self.test_data = self.data["test"]
        self.validation_data = self.data["validation"]

        self.training_data_labels, self.classes = create_labeled_training_classes(self.training_data, classification, workload_type)
        self.validation_data_labels = create_labeled_test_validation_classes(self.validation_data, self.classes, workload_type)
        self.test_data_labels = create_labeled_test_validation_classes(self.test_data, self.classes, workload_type)


    def get_data_file(self):
        return self.data_file
    
    def get_training_data(self):
        return self.training_data
    
    def get_test_data(self):
        return self.test_data
    
    def get_validation_data(self):
        return self.validation_data
    
    def get_training_data_labels(self):
        return self.training_data_labels
    
    def get_test_data_labels(self):
        return self.test_data_labels
    
    def get_validation_data_labels(self):
        return self.validation_data_labels
    
    def get_classes(self):
        return self.classes
    
    def get_data(self):
        return self.data