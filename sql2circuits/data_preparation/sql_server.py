# -*- coding: utf-8 -*-

import re
import pyodbc
import os
import xml.etree.ElementTree as ET

class SQLServerDatabase:
    """
    A class representing a SQL Server database. This class provides methods for generating data for quantum computing
    experiments, specifically for the purpose of testing quantum algorithms for database query languages. The class
    includes methods for generating data on query execution time and query cardinality, and can be initialized with
    custom database credentials connecting to a SQL Server database.
    """

    def __init__(self, name, credentials = None) -> None:
        # Database credentials
        self.name = name
        self.port = "1433"
        self.sql_server_name = "localhost"
        self.sql_server_db_name = "imdb2017"
        self.sql_server_user = "root"
        self.sql_server_pw = "0000"
        self.file_path = "C://Users//valte//Documents//frozendata"
        self.created_data_files = dict()
        self.this_folder = os.path.abspath(os.getcwd())

        if credentials is not None:
            self.port = credentials["port"]
            self.sql_server_name = credentials["sql_server_name"]
            self.sql_server_db_name = credentials["sql_server_db_name"]
            self.sql_server_user = credentials["sql_server_user"]
            self.sql_server_pw = credentials["sql_server_pw"]
            self.file_path = credentials["file_path"]

        self.sql_server_connection = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+self.sql_server_name+';DATABASE='+self.sql_server_db_name+';' + 'Trusted_Connection=yes;')
        
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
        cursor = self.sql_server_connection.cursor()
        try:
            cursor.execute("SET SHOWPLAN_XML ON;")
            cursor.execute(query)
            res = cursor.fetchall()[0][0]
            cursor.execute("SET SHOWPLAN_XML OFF;")
            # Get the StatementEstRows from res XML tree
            tree = ET.ElementTree(ET.fromstring(res))
            root = tree.getroot()
            stmt_simple = root.find(".//{http://schemas.microsoft.com/sqlserver/2004/07/showplan}StmtSimple")
            cardinality_estimation = int(float(stmt_simple.get('StatementEstRows')))
            return cardinality_estimation

        except (Exception, pyodbc.Error) as error:
            print("Error while fetching data from SQL Server", error)
            print(query)


    def get_cost_estimation(self, query):
        cursor = self.sql_server_connection.cursor()
        try:
            cursor.execute("SET SHOWPLAN_ALL ON")
            cursor.execute(query)
            res = cursor.fetchall()
            cursor.execute("SET SHOWPLAN_ALL OFF")
            cost_estimation = float(re.findall("TotalSubtreeCost=\"(\d+.\d+)\"", res[0][0])[0])
            print(cost_estimation)
            return cost_estimation

        except (Exception, pyodbc.Error) as error:
            print("Error while fetching data from SQL Server", error)
            print(query)
