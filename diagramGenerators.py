from antlr4 import *
from SQLiteLexer import SQLiteLexer
from SQLiteParser import SQLiteParser
from SQLiteParserListener import SQLiteParserListener
import json
import os
import pickle
from pathlib import Path
from discopy import Ty, Functor
from discopy.utils import dumps, loads
from lambeq import IQPAnsatz
from flipped_IQPansatz import IQPAnsatzFlipped
from pregroupFunctorMappings import count_boxes, object_mapping, arrow_mapping
from cupRemoveFunctorMappings import cup_remove_arrow_mapping, cup_remove_arrow_mapping2

this_folder = os.path.abspath(os.getcwd())

cup_removal_functor = Functor(ob = lambda x: x, ar = lambda f: cup_remove_arrow_mapping(f))
cup_removal_functor2 = Functor(ob = lambda x: x, ar = lambda f: cup_remove_arrow_mapping2(f))

n, s = Ty('n'), Ty('s')
#ansatz = IQPAnsatz({n: 1, s: 1}, n_layers=1, n_single_qubit_params=3)
ansatz = IQPAnsatzFlipped({n: 1, s: 1}, n_layers=1, n_single_qubit_params=3)


def create_CFG_diagrams(queries, output_folder_name):
    
    for count, query in enumerate(queries):
        print("Process: ", count, " out of ", len(queries))
        base_name = Path(query).stem
        output = this_folder + "\\" + output_folder_name + "\\" + base_name
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
            diagram.draw(figsize=(dim, dim), path = output + ".png")
            
            with open(output + ".json", 'w') as outfile:
                json.dump(json.loads(dumps(diagram)), outfile)
        except:
            print("Query: ", base_name, " failed to parse and construct CFG-diagram.")
            
def create_pregroup_grammar_diagrams(cfg_diagrams, pregroup_folder_name):
    
    for count, serialized_diagram in enumerate(cfg_diagrams):
        print("Process: ", count, " out of ", len(cfg_diagrams))
        base_name = Path(serialized_diagram).stem
        f = open(serialized_diagram, "r")
        data = f.read()
        diagram = loads(data)
        output = this_folder + "\\" + pregroup_folder_name + "\\" + base_name
        
        num_of_result_columns = count_boxes(diagram, "result-column")
        num_of_result_columns += count_boxes(diagram, "result-column-with-alias")
        num_of_tables = count_boxes(diagram, "table")
        num_of_tables += count_boxes(diagram, "table-with-alias")
        
        Rewriter = Functor(ob = lambda x: object_mapping(x, num_of_result_columns, num_of_tables), 
                           ar = lambda f: arrow_mapping(f, num_of_result_columns, num_of_tables))
        
        try:
            pregroup_diagram = Rewriter(diagram)
            width = diagram.width()
            height = diagram.depth()
            dim = 3*max(width, height)
            pregroup_diagram.draw(figsize=(dim, dim), path = output + ".png")

            with open(output + ".json", 'w') as outfile:
                json.dump(json.loads(dumps(pregroup_diagram)), outfile)
        except:
            print("Query: ", base_name, " failed to map to a pregroup grammar diagram.")

def remove_cups_and_simplify(pregroup_diagrams, cup_removed_pregroup_folder_name):
    
    for count, serialized_diagram in enumerate(pregroup_diagrams):
        print("Process: ", count, " out of ", len(pregroup_diagrams))
        base_name = Path(serialized_diagram).stem
        f = open(serialized_diagram, "r")
        data = f.read()
        pregroup_diagram = loads(data)
        output = this_folder + "\\" + cup_removed_pregroup_folder_name + "\\" + base_name
        
        try:
            cupless_pregroup_diagram = cup_removal_functor(pregroup_diagram.normal_form()).normal_form()
            cupless_pregroup_diagram = cup_removal_functor2(cupless_pregroup_diagram).normal_form()
            width = cupless_pregroup_diagram.width()
            height = cupless_pregroup_diagram.depth()
            dim = 2*max(width, height)
            cupless_pregroup_diagram.draw(figsize=(dim, dim), path = output + ".png")

            with open(output + ".json", 'w') as outfile:
                json.dump(json.loads(dumps(cupless_pregroup_diagram)), outfile)
        except:
            print("Query: ", base_name, " failed to remove cups.")           
                                      
    
def create_circuit_ansatz(pregroup_diagrams, circuit_folder):
    
    for count, serialized_diagram in enumerate(pregroup_diagrams):
        print("Process: ", count, " out of ", len(pregroup_diagrams))
        base_name = Path(serialized_diagram).stem
        f = open(serialized_diagram, "r")
        data = f.read()
        cupless_pregroup_diagram = loads(data)
        output_folder = this_folder + "\\" + circuit_folder + "\\" + base_name
        
        #try:
        circuit_diagram = ansatz(cupless_pregroup_diagram)
        width = circuit_diagram.width()
        height = circuit_diagram.depth()
        dim = 3*max(width, height)
        circuit_diagram.draw(figsize=(dim, dim), path = output_folder + ".png")

        with open(output_folder + ".json", 'w') as outfile:
            json.dump(json.loads(dumps(cupless_pregroup_diagram)), outfile)
        with open(output_folder + ".p", "wb") as outfile:
            pickle.dump(circuit_diagram, outfile)
        #except:
        #    print("Query: ", base_name, " failed to transform into a circuit.") 