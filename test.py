import sys
from antlr4 import *
from SQLiteLexer import SQLiteLexer
from SQLiteParser import SQLiteParser
from tree import Tree
from discopy import Ty, Box

def main(argv):
    #input = "SELECT column1, column2 FROM table1, table2;"
    #input = FileStream(argv[1])
    #lexer = SQLiteLexer(input)
    #stream = CommonTokenStream(lexer)
    #parser = SQLiteParser(stream)
    #tree = parser.parse()
    #print(tree.toStringTree(recog=parser))
    tree = Tree('parse', Ty('statement'), 1)
    print(tree)
    subtree = Tree('sql_stmt', Ty('statement'), 1)
    print(subtree)
    tree.append_to_tree(subtree)
    tree.print_tree()

if __name__ == '__main__':
    main(sys.argv)