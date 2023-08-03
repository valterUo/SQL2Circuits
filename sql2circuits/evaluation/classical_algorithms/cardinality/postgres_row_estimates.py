# -*- coding: utf-8 -*-

# Implements evaluation on the cardinality estimation of PostgreSQL
# https://www.postgresql.org/docs/current/row-estimation-examples.html

import json


class PostgresCardinalityEstimation:

    def __init__(self, query_file, true_cardinalities, database, classes):
        self.query_file = query_file
        self.database = database
        self.true_cardinalities = true_cardinalities
        self.cardinality_estimations = dict()
        self.classes = classes

    def create_postgres_cardinality_estimates(self):
        with open(self.query_file, "r") as file:
            queries = json.load(file)
            for query_set in queries["queries"]:
                self.cardinality_estimations[query_set] = dict()
                for query in queries["queries"][query_set]:
                    estimation = self.database.get_cardinality_estimation(query["query"])
                    if estimation is not None:
                        self.cardinality_estimations[query_set][query["id"]] = estimation
    
    def get_postgres_cardinality_estimates(self):
        return self.cardinality_estimations
    
    def is_in_intervals(self, element):
        intervals = self.classes
        for i, interval in enumerate(intervals):
            if element >= interval[0] and element <= interval[1]:
                return i
        if element <= intervals[0][0]:
            return 0
        elif element >= intervals[-1][1]:
            return len(intervals) - 1
    
    def evaluate_accuracy(self):
        self.results = dict()
        for query_set in self.cardinality_estimations:
            accuracy = 0
            for query_id in self.cardinality_estimations[query_set]:
                if str(query_id) in self.true_cardinalities[query_set]:
                    postgres_estimate = int(self.cardinality_estimations[query_set][query_id])
                    true_value = self.true_cardinalities[query_set][str(query_id)]
                    postgres_classification = self.is_in_intervals(postgres_estimate)
                    true_class = self.is_in_intervals(true_value)
                    if postgres_classification == true_class:
                        accuracy += 1
            self.results[query_set] = accuracy/len(self.true_cardinalities[query_set])
    
    def get_accuracy(self):
        return self.results
                
        

