from antlr4 import *
from SQLiteLexer import SQLiteLexer
from SQLiteParser import SQLiteParser
from SQLiteParserListener import SQLiteParserListener
import json
import os
import glob
from pathlib import Path
from discopy import Ty, Box, Functor
from functools import reduce
from discopy.utils import dumps, loads
import multiprocessing

from pregroup_functor_mappings import count_boxes, object_mapping, arrow_mapping

this_folder = os.path.abspath(os.getcwd())


def create_CFG_diagrams(queries, output_folder_name):
    
    for count, query in enumerate(queries):
        print("Process: ", count, " out of ", len(queries))
        base_name = Path(query).stem
        try:
            input_stream = FileStream(query)
            lexer = SQLiteLexer(input_stream)
            stream = CommonTokenStream(lexer)
            parser = SQLiteParser(stream)
            tree = parser.parse()
            walker = ParseTreeWalker()
            listener = SQLiteParserListener(parser)
            walker.walk(listener, tree)
            diagram = listener.get_final_diagram().dagger()
            width = diagram.width()
            height = diagram.depth()
            dim = 3*max(width, height)
            diagram.draw(figsize=(dim, dim), path = this_folder + "\\" + output_folder_name + "\\" + base_name + ".png")
            with open(this_folder + "\\" + output_folder_name + "\\" + base_name + ".json", 'w') as outfile:
                json.dump(json.loads(dumps(diagram)), outfile)
        except:
            print("Query: ", base_name, " failed.")
            
def create_pregroup_grammar_diagrams(cfg_diagrams, pregroup_folder_name):
    
    for count, serialized_diagram in enumerate(cfg_diagrams):
        print("Process: ", count, " out of ", len(cfg_diagrams))
        base_name = Path(serialized_diagram).stem
        f = open(serialized_diagram, "r")
        data = f.read()
        diagram = loads(data)
        
        num_of_result_columns = count_boxes(diagram, "result-column")
        num_of_result_columns += count_boxes(diagram, "result-column-with-alias")
        num_of_tables = count_boxes(diagram, "table")
        num_of_tables += count_boxes(diagram, "table-with-alias")
        
        Rewriter = Functor(ob = lambda x: object_mapping(x, num_of_result_columns, num_of_tables), ar = lambda f: arrow_mapping(f, num_of_result_columns, num_of_tables))
        
        try:
            pregroup_diagram = Rewriter(diagram)
            width = diagram.width()
            height = diagram.depth()
            dim = 3*max(width, height)
            pregroup_diagram.draw(figsize=(dim, dim), path = this_folder + "\\" + pregroup_folder_name + "\\" + base_name + ".png")

            with open(this_folder + "\\" + pregroup_folder_name + "\\" + base_name + ".json", 'w') as outfile:
                    json.dump(json.loads(dumps(pregroup_diagram)), outfile)
        except:
            print("Query: ", base_name, " failed.")