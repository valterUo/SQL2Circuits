# -*- coding: utf-8 -*-

import json
import re
import psycopg2
import os

class Database:
    """
    A class representing a PostgreSQL database. This class provides methods for generating data for quantum computing
    experiments, specifically for the purpose of testing quantum algorithms for database query languages. The class
    includes methods for generating data on query execution time and query cardinality, and can be initialized with
    custom database credentials connecting to a PostSQL database.
    """

    def __init__(self, name, credentials = None) -> None:
        # Database credentials
        self.name = name
        self.port = "5432"
        self.pg_db_name = "imdb2017"
        self.pg_user = "postgres"
        self.pg_pw = "0000"
        self.file_path = "C://Users//valte//Documents//frozendata"
        self.host = "localhost"
        self.created_data_files = dict()
        self.this_folder = os.path.abspath(os.getcwd())

        if credentials is not None:
            self.port = credentials["port"]
            self.pg_db_name = credentials["pg_db_name"]
            self.pg_user = credentials["pg_user"]
            self.pg_pw = credentials["pg_pw"]
            self.file_path = credentials["file_path"]
            self.host = credentials["host"]

        self.pg_connection = "postgresql://" + self.pg_user + ":" + self.pg_pw + "@localhost:" + self.port + "/" + self.pg_db_name


    def get_name(self):
        return self.name
    
    
    def generate_data(self, id, queries, workload, statement_timeout = 20000):
        connection = None
        try:
            connection = psycopg2.connect(user=self.pg_user, 
                                        password=self.pg_pw, 
                                        host=self.host, 
                                        port=self.port, 
                                        database=self.pg_db_name)
            cursor = connection.cursor()
            cursor.execute("SET statement_timeout = " + str(statement_timeout) + "; COMMIT;")
        except (Exception, psycopg2.Error) as error:
            print("Error while fetching data from PostgreSQL", error)
        file_name = ""

        if workload == "E":
            file_name = self.genereta_data_execution_time(id, queries, connection)
        elif workload == "C":
            file_name = self.genereta_data_cardinality(id, queries, connection)
        else:
            print("Unknown workload type!")
        
        self.created_data_files[id] = file_name
        return file_name
    

    def genereta_data_execution_time(self, id, queries, connection):
        shots_per_query = 10
        result = dict()
        cursor = None
        file_name = self.this_folder + "//data_preparation//data//execution_time//" + str(id) + "_data.json"
        if os.path.isfile(file_name):
            if connection:
                connection.close()
            return file_name

        for query_set in queries:
            data = dict()
            for query in queries[query_set]:
                try:
                    total_running_time = 0.0
                    for _ in range(shots_per_query):
                        cursor = connection.cursor()
                        cursor.execute("EXPLAIN ANALYZE " + query['query'])
                        res = cursor.fetchall()
                        ex_time = float(re.findall("\d+\.\d+", res[-1][0])[0])
                        plan_time = float(re.findall("\d+\.\d+", res[-2][0])[0])
                        total_running_time += ex_time + plan_time
                    data[query['id']] = round(total_running_time / shots_per_query, 4)
                except (Exception, psycopg2.Error) as error:
                    print("Error while fetching data from PostgreSQL ", error)
                    print("Error happened when executing ", query)
            result[query_set] = data

        if connection and cursor:
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")
            
        with open(file_name, 'w') as outfile:
            json.dump(result, outfile, indent = 4)
        
        self.created_data_files[id] = file_name
        
        return file_name
    
    
    def genereta_data_cardinality(self, id, queries, connection):
        result = dict()
        cursor = None
        file_name = self.this_folder + "//data_preparation//data//cardinality//" + str(id) + "_data.json"
        if os.path.isfile(file_name):
            if connection:
                connection.close()
            return file_name
        
        for query_set in queries:
            data = dict()
            for query in queries[query_set]:
                try:
                    cursor = connection.cursor()
                    cursor.execute("EXPLAIN ANALYZE " + query['query'])
                    res = cursor.fetchall()
                    cardinality = int(re.findall("rows=(\d+)", res[0][0])[1])
                    data[query['id']] = cardinality

                except (Exception, psycopg2.Error) as error:
                    print("Error while fetching data from PostgreSQL", error)
                    print(query)
            result[query_set] = data

        if connection and cursor:
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")
            
        with open(file_name, 'w') as outfile:
            json.dump(result, outfile)
        
        return file_name


    def create_indices(self):
        if self.name == "IMDB":
            command = """
                    create index company_id_movie_companies on movie_companies(company_id);
                    create index company_type_id_movie_companies on movie_companies(company_type_id);
                    create index info_type_id_movie_info on movie_info(info_type_id);
                    create index info_type_id_person_info on person_info(info_type_id);
                    create index keyword_id_movie_keyword on movie_keyword(keyword_id);
                    create index kind_id_aka_title on aka_title(kind_id);
                    create index kind_id_title on title(kind_id);
                    create index linked_movie_id_movie_link on movie_link(linked_movie_id);
                    create index link_type_id_movie_link on movie_link(link_type_id);
                    create index movie_id_aka_title on aka_title(movie_id);
                    create index movie_id_cast_info on cast_info(movie_id);
                    create index movie_id_complete_cast on complete_cast(movie_id);
                    create index movie_id_movie_companies on movie_companies(movie_id);
                    create index movie_id_movie_keyword on movie_keyword(movie_id);
                    create index movie_id_movie_link on movie_link(movie_id);
                    create index movie_id_movie_info on movie_info(movie_id);
                    create index person_id_aka_name on aka_name(person_id);
                    create index person_id_cast_info on cast_info(person_id);
                    create index person_id_person_info on person_info(person_id);
                    create index person_role_id_cast_info on cast_info(person_role_id);
                    create index role_id_cast_info on cast_info(role_id);
                    """

            test_query = "EXPLAIN ANALYZE SELECT * FROM title LIMIT 2;"
            connection = None
            cursor = None
            try:
                connection = psycopg2.connect(user = self.pg_user, 
                                            password = self.pg_pw, 
                                            host = self.host, 
                                            port = self.port, 
                                            database = self.pg_db_name)
                cursor = connection.cursor()
                cursor.execute(command)
                res = cursor.fetchall()
                print(res)

            except (Exception, psycopg2.Error) as error:
                print("Error while fetching data from PostgreSQL", error)

            finally:
                # closing database connection.
                if connection and cursor:
                    cursor.close()
                    connection.close()
                    print("PostgreSQL connection is closed")
