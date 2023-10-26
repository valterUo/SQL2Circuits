try:
    from antlr4 import *
except ModuleNotFoundError:
    print("Please install antlr4-python3-runtime to use the parser.")
import json
import os
from discopy import Ty, Functor
from discopy.utils import dumps, loads
from circuit_preparation.diagrams.pregroupFunctorMappings import count_boxes, object_mapping, arrow_mapping
from circuit_preparation.diagrams.cupRemoveFunctorMappings import cup_remove_arrow_mapping, cup_remove_arrow_mapping2

this_folder = os.path.abspath(os.getcwd())

cup_removal_functor = Functor(ob = lambda x: x, ar = lambda f: cup_remove_arrow_mapping(f))
cup_removal_functor2 = Functor(ob = lambda x: x, ar = lambda f: cup_remove_arrow_mapping2(f))

n, s = Ty('n'), Ty('s')

def create_CFG_diagrams(queries, generate_cfg_png_diagrams):
    print(queries)
    output_dict = dict()
    for count, query in enumerate(queries):
        print("Processing: ", count, " out of ", len(queries))
        id = query["id"]
        query = query["query"]
        try:
            from circuit_preparation.diagrams.parser.SQLiteLexer import SQLiteLexer
            from circuit_preparation.diagrams.parser.SQLiteParser import SQLiteParser
            from circuit_preparation.diagrams.parser.SQLiteParserListener import SQLiteParserListener
            input_stream = InputStream(query)
            lexer = SQLiteLexer(input_stream)
            stream = CommonTokenStream(lexer)
            parser = SQLiteParser(stream)
            tree = parser.parse()
            walker = ParseTreeWalker()
            listener = SQLiteParserListener(parser)
            walker.walk(listener, tree)
            diagram = listener.get_final_diagram().dagger()
            
            if generate_cfg_png_diagrams and count < 10:
                width = diagram.width() # type: ignore
                height = diagram.depth() # type: ignore
                dim = 3*max(width, height)
                diagram.draw(figsize=(dim, dim), path = id + ".png") # type: ignore
            output_dict[id] = dict(json.loads(dumps(diagram)))
        except:
            print("Query: ", str(id), " failed to parse and construct CFG-diagram.")
    return output_dict
            
def create_pregroup_grammar_diagrams(cfg_diagrams, generate_pregroup_png_diagrams):
    diagrams = dict()
    for count, key in enumerate(cfg_diagrams):
        print("Process: ", count, " out of ", len(cfg_diagrams))

        diagram = loads(json.dumps(cfg_diagrams[key]))
        num_of_result_columns = count_boxes(diagram, "result-column")
        num_of_result_columns += count_boxes(diagram, "result-column-with-alias")
        num_of_tables = count_boxes(diagram, "table")
        num_of_tables += count_boxes(diagram, "table-with-alias")
        
        Rewriter = Functor(ob = lambda x: object_mapping(x, num_of_result_columns, num_of_tables), 
                           ar = lambda f: arrow_mapping(f, num_of_result_columns, num_of_tables))
        
        try:
            pregroup_diagram = Rewriter(diagram)
            diagrams[key] = dict(json.loads(dumps(pregroup_diagram)))

            if generate_pregroup_png_diagrams and count < 10:
                width = diagram.width() # type: ignore
                height = diagram.depth() # type: ignore
                dim = 3*max(width, height)
                pregroup_diagram.draw(figsize=(dim, dim), path = key + ".png") # type: ignore
        except:
            print("Query: ", key, " failed to map to a pregroup grammar diagram.")
    return diagrams

def remove_cups_and_simplify(pregroup_diagrams, generate_pregroup_png_diagrams):
    diagrams = dict()
    for count, key in enumerate(pregroup_diagrams):
        print("Process: ", count, " out of ", len(pregroup_diagrams))
        pregroup_diagram = loads(json.dumps(pregroup_diagrams[key]))
        
        try:
            cupless_pregroup_diagram = cup_removal_functor(pregroup_diagram.normal_form()).normal_form() # type: ignore
            cupless_pregroup_diagram = cup_removal_functor2(cupless_pregroup_diagram).normal_form() # type: ignore
            diagrams[key] = dict(json.loads(dumps(cupless_pregroup_diagram)))

            if generate_pregroup_png_diagrams and count < 10:
                width = cupless_pregroup_diagram.width()
                height = cupless_pregroup_diagram.depth()
                dim = 2*max(width, height)
                cupless_pregroup_diagram.draw(figsize=(dim, dim), path = key + ".png")
        except:
            print("Query: ", key, " failed to remove cups.")
    return diagrams         
                                      
    
def create_circuit_ansatz(pregroup_diagrams,
                          classification, 
                          layers, 
                          single_qubit_params, 
                          n_wire_count, 
                          generate_circuit_png_diagrams, 
                          generate_circuit_json_diagrams):
    circuit_diagrams = dict()

    from circuit_preparation.diagrams.flipped_IQPansatz import IQPAnsatzFlipped
    ansatz = IQPAnsatzFlipped({n: n_wire_count, 
                            s: classification}, 
                            n_layers = layers, 
                            n_single_qubit_params = single_qubit_params)
    for count, key in enumerate(pregroup_diagrams):
        print("Process: ", count, " out of ", len(pregroup_diagrams))
        cupless_pregroup_diagram = loads(json.dumps(pregroup_diagrams[key]))
        circuit_diagram = ansatz(cupless_pregroup_diagram) # type: ignore
        circuit_diagrams[key] = circuit_diagram

        if generate_circuit_png_diagrams and count < 10:
            width = circuit_diagram.width()
            height = circuit_diagram.depth()
            dim = 3*max(width, height)
            circuit_diagram.draw(figsize=(dim, dim), path = str(key) + ".png")

        if generate_circuit_json_diagrams:
            with open(key + ".json", 'w') as outfile:
                json.dump(json.loads(dumps(circuit_diagram)), outfile)

    return circuit_diagrams