# -*- coding: utf-8 -*-

# Implements evaluation on the cardinality estimation of PostgreSQL
# https://www.postgresql.org/docs/current/row-estimation-examples.html

import json


class PostgresCardinalityEstimation:

    def __init__(self, query_file, true_cardinalities, database):
        self.query_file = query_file
        self.database = database
        self.true_cardinalities = true_cardinalities
        self.cardinality_estimations = dict()

    def get_postgres_cardinality_estimates(self):
        with open(self.query_file, "r") as file:
            queries = json.load(file)
            for query_set in queries:
                self.cardinality_estimations[query_set] = dict()
                for query in queries[query_set]:
                    estimation = self.database.get_cardinality_estimation(query)
                    if estimation is not None:
                        self.cardinality_estimations[query_set][query] = estimation