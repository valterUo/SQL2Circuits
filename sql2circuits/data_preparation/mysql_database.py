# -*- coding: utf-8 -*-

import re
try:
    import mysql.connector
except ModuleNotFoundError:
    print("mysql-connector-python not found. Please install it with 'pip install mysql-connector-python' and try again.")
import os

class MySQLDatabase:
    """
    A class representing a MySQL database. This class provides methods for generating data for quantum computing
    experiments, specifically for the purpose of testing quantum algorithms for database query languages. The class
    includes methods for generating data on query execution time and query cardinality, and can be initialized with
    custom database credentials connecting to a MySQL database.
    """

    def __init__(self, name, credentials = None) -> None:
        # Database credentials
        self.name = name
        self.port = "3306"
        self.mysql_db_name = "imdb2017"
        self.mysql_user = "root"
        self.mysql_pw = "0000"
        self.file_path = "C://Users//valte//Documents//frozendata"
        self.host = "localhost"
        self.created_data_files = dict()
        self.this_folder = os.path.abspath(os.getcwd())

        if credentials is not None:
            self.port = credentials["port"]
            self.mysql_db_name = credentials["mysql_db_name"]
            self.mysql_user = credentials["mysql_user"]
            self.mysql_pw = credentials["mysql_pw"]
            self.file_path = credentials["file_path"]
            self.host = credentials["host"]

        self.mysql_connection = mysql.connector.connect(user=self.mysql_user, 
                                                         password=self.mysql_pw, 
                                                         host=self.host, 
                                                         port=self.port, 
                                                         database=self.mysql_db_name)
        
    def supports_cardinality_estimation(self):
        return True
    
    def supports_cost_estimation(self):
        return False
    
    def supports_latency_estimation(self):
        return False
    
    def select_estimations_numbers(self, tuples):
        max_first_element = max(t[0] for t in tuples)
        matching_tuples = [t for t in tuples if t[0] == max_first_element]
        if not matching_tuples:
            print("No cardinality estimation found?")
        return [t[9] for t in matching_tuples]


    def get_cardinality_estimation(self, query):
        cursor = self.mysql_connection.cursor()
        try:
            cursor.execute("EXPLAIN " + query)
            res = cursor.fetchall()
            #print(res)
            cardinality_estimation = self.select_estimations_numbers(res)
            cardinality_estimation = [x for x in cardinality_estimation if x is not None]
            return cardinality_estimation

        except (Exception, mysql.connector.Error) as error:
            print("Error while fetching data from MySQL", error)
            print(query)


    def get_cost_estimation(self, query):
        cursor = self.mysql_connection.cursor()
        try:
            cursor.execute("EXPLAIN " + query)
            res = cursor.fetchall()
            cost_estimation = float(re.findall("cost=(\d+.\d+)", res[0][9])[0])
            print(cost_estimation)
            return cost_estimation

        except (Exception, mysql.connector.Error) as error:
            print("Error while fetching data from MySQL", error)
            print(query)
