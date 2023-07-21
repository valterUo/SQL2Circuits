# -*- coding: utf-8 -*-

import glob
import os
import re
import json
import psycopg2
from pathlib import Path

this_folder = os.path.abspath(os.getcwd())

class DataPreparation:

    def __init__(self, id, query_file_path, database, workload_type) -> None:
        self.query_file_path = query_file_path
        self.database = database
        self.this_folder = os.path.abspath(os.getcwd())

        # Read the json file containing the queries
        query_file = open(self.query_file_path, "r")
        self.queries = json.load(query_file)

        stats = self.queries["stats"]
        queries = self.queries["queries"]

        print("Number of training queries is ", stats["number_of_training_queries"])
        print("Number of test queries is ", stats["number_of_test_queries"])
        print("Number of validation queries is ", stats["number_of_validation_queries"])

        self.data_file = self.database.generate_data(id, queries, workload_type)