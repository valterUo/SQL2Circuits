# -*- coding: utf-8 -*-

import json
import os
from itertools import combinations
import random
random.seed(0)

class QueryGenerator:
    """
    A class that generates SQL queries by combining filters, joins, and selects from a query seed file. 
    The generated queries are used for training, testing, and validation of SQL2Circuits model.
    """

    def __init__(self, id, workload_type, database = "IMDB", query_seed_file_path = "", total_number_of_queries = 100, test_query_ratio = 0.2, validation_query_ratio = 0.2) -> None:
        self.id = id
        self.database = database
        self.workload_type = workload_type
        self.total_number_of_queries = total_number_of_queries
        self.test_query_ratio = test_query_ratio
        self.validation_query_ratio = validation_query_ratio
        self.this_folder = os.path.abspath(os.getcwd())
        query_seed_file = open(self.this_folder + "//" + query_seed_file_path, "r")
        self.query_seed = json.load(query_seed_file)

        self.path_for_queries = self.this_folder + "//data_preparation//queries//" + self.workload_type + "//"

        final_queries = self.query_generator(max_num_of_filters = 2, max_num_of_joins = 2, max_num_of_tables = 2)
        self.queries = self.construct_queries(final_queries)
        self.query_file = self.path_for_queries + str(self.id) + ".json"

        with open(self.query_file, "w") as output:
            json.dump(self.queries, output, indent = 4)

    
    def get_query_file(self):
        return self.query_file
    

    def query_generator(self, max_num_of_filters, max_num_of_joins, max_num_of_tables):
        """
        Generates a list of SQL queries by combining filters, joins, and selects from the query seed file.
        
        Args:
        - max_num_of_filters: maximum number of filters to be used in a query
        - max_num_of_joins: maximum number of joins to be used in a query
        - max_num_of_tables: maximum number of tables to be used in a query
        
        Returns:
        - A list of dictionaries containing filters, joins, selects, and table aliases for each query.
        """
        queries, final_queries = [], []
        filters = self.query_seed["filters"]
        joins = self.query_seed["joins"]
        selects = self.query_seed["selects"]
        
        filter_combs, join_combs = [], []
        for i in range(1, max_num_of_filters + 1):
            filter_combs.append(list(combinations(filters, i)))
        for i in range(1, max_num_of_joins + 1):
            join_combs.append(list(combinations(joins, i)))
        
        for f in filter_combs:
            for c1 in f:
                for j in join_combs:
                    for c2 in j:
                        table_aliases = list(set([v["table_alias"] for v in c1] + [v["table_alias1"] for v in c2] + [v["table_alias2"] for v in c2]))
                        if len(table_aliases) < max_num_of_tables + 1:
                            queries.append({"filters": c1, "joins": c2, "table_aliases": table_aliases})
                            
        for s in selects:
            for q in queries:
                if s["table_alias"] in q["table_aliases"]:
                    final_queries.append({"select": s, "joins": q["joins"], "filters": q["filters"], "table_aliases": q["table_aliases"]})
        
        return final_queries
    

    def construct_queries(self, queries):
        """
        Constructs SQL queries from the given queries and generates training, test and validation queries based on the given ratios.
        
        Args:
        - queries: list of dictionaries containing filters, joins, selects and table aliases
        
        Returns:
        - A dictionary containing the statistics of the generated queries and the generated queries themselves.
        """
        aliases_to_tables = self.query_seed["table_aliases"]
        result_queries = []
        for i, q in enumerate(queries):
            from_part = " FROM "
            where_part = " WHERE "
            for alias in q["table_aliases"]:
                from_part += aliases_to_tables[alias] + " AS " + alias + ", "
            for f in q["filters"]:
                where_part += f["filter"] + " AND "
            for j in q["joins"]:
                where_part += j["join"] + " AND "

            query = "SELECT " + q["select"]["select"] + from_part[:-2] + where_part[:-5] + ";"

            result_queries.append(query)

        probabilities = [1.0 - self.test_query_ratio - self.validation_query_ratio, 
                         self.test_query_ratio, 
                         self.validation_query_ratio]

        result = random.choices(population=[1, 2, 3], weights=probabilities, k=len(result_queries))

        query_range = range(len(result_queries))

        training_queries = [ { "id": i, "query": result_queries[i] } for i in query_range if result[i] == 1]
        test_queries = [{ "id": i, "query": result_queries[i] } for i in query_range if result[i] == 2]
        validation_queries = [{ "id": i, "query": result_queries[i] } for i in query_range if result[i] == 3]


        return {"stats": {"total_number_of_queries": len(result_queries),
                        "number_of_training_queries": len(training_queries), 
                        "number_of_test_queries": len(test_queries), 
                        "number_of_validation_queries": len(validation_queries)},
                "queries": { 
                        "training": training_queries, 
                        "test": test_queries, 
                        "validation": validation_queries
                        }}