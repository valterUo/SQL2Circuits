import sys
from antlr4 import *
from SQLiteLexer import SQLiteLexer
from SQLiteParser import SQLiteParser
from tree import Tree
from discopy import Ty, Box, Functor, Id, Cap, Cup, Diagram
from lambeq import IQPAnsatz
from functools import reduce

from antlr4 import *
from SQLiteLexer import SQLiteLexer
from SQLiteParser import SQLiteParser
from SQLiteParserListener import SQLiteParserListener
import json
import os
import glob
from pathlib import Path
this_folder = os.path.abspath(os.getcwd())

def main(argv):
    
    base_name = "1b"
    input_stream = FileStream(this_folder + "\\join-order-benchmark-queries\\1b.sql")
    lexer = SQLiteLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = SQLiteParser(stream)
    tree = parser.parse()
    walker = ParseTreeWalker()
    listener = SQLiteParserListener(parser)
    walker.walk(listener, tree)
    diagram = listener.get_final_diagram().dagger()
    
if __name__ == '__main__':
    main(sys.argv)