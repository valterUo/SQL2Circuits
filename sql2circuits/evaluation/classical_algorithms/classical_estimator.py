# -*- coding: utf-8 -*-

# Implements evaluation on the cardinality estimation of PostgreSQL
# https://www.postgresql.org/docs/current/row-estimation-examples.html

import json

class ClassicalEstimator:

    def __init__(self, query_file, true_cardinalities, database, classes):
        self.query_file = query_file
        self.database = database
        self.true_cardinalities = true_cardinalities
        self.classes = classes

        self.results = dict()
        self.cardinality_estimations = dict()
        self.latency_estimations = dict()
        self.cost_estimations = dict()


    def get_cardinality_estimates(self):
        return self.cardinality_estimations
    
    def get_latency_estimates(self):
        return self.latency_estimations
    
    def get_cost_estimates(self):
        return self.cost_estimations
    
    def get_results(self):
        return self.results


    def create_estimates(self, estimation_type):
        with open(self.query_file, "r") as file:
            queries = json.load(file)
            for query_set in queries["queries"]:
                self.cardinality_estimations[query_set] = dict()
                for query in queries["queries"][query_set]:
                    estimation = None
                    
                    if estimation_type == "cardinality":
                        estimation = self.database.get_cardinality_estimation(query["query"])
                    elif estimation_type == "latency":
                        estimation = self.database.get_latency_estimation(query["query"])
                    elif estimation_type == "cost":
                        estimation = self.database.get_cost_estimation(query["query"])

                    if estimation is not None:
                        self.cardinality_estimations[query_set][query["id"]] = estimation
                    else:
                        print("No cardinality estimation for query ", query["id"])
    

    def is_in_intervals(self, element):
        intervals = self.classes
        for i, interval in enumerate(intervals):
            if element >= interval[0] and element <= interval[1]:
                return i
        if element <= intervals[0][0]:
            return 0
        elif element >= intervals[-1][1]:
            return len(intervals) - 1
    

    def evaluate_accuracy_of_estimations(self, estimation_type):
        estimations = dict()
        self.results[estimation_type] = dict()
        if estimation_type == "cardinality":
            estimations = self.cardinality_estimations
        elif estimation_type == "latency":
            estimations = self.latency_estimations
        elif estimation_type == "cost":
            estimations = self.cost_estimations

        for query_set in estimations:
            accuracy = 0
            for query_id in estimations[query_set]:
                if str(query_id) in self.true_cardinalities[query_set]:
                    estimate = estimations[query_set][query_id]
                    true_value = self.true_cardinalities[query_set][str(query_id)]

                    if type(estimate) == list:
                        # Select the estimate closer to the true value
                        estimate = min(estimate, key=lambda x:abs(x-true_value), default=None)
                    if estimate is not None:
                        classification = self.is_in_intervals(estimate)
                        true_class = self.is_in_intervals(true_value)
                        if classification == true_class:
                            accuracy += 1
            self.results[estimation_type][query_set] = accuracy/len(self.true_cardinalities[query_set])
        total = 0
        for query_set in self.results[estimation_type]:
            total += self.results[estimation_type][query_set]
        self.results[estimation_type]["total"] = total/len(self.results[estimation_type])