import sys
from antlr4 import *
from SQLiteLexer import SQLiteLexer
from SQLiteParser import SQLiteParser

def main(argv):
    #input = "SELECT column1, column2 FROM table1, table2;"
    input = FileStream(argv[1])
    lexer = SQLiteLexer(input)
    stream = CommonTokenStream(lexer)
    parser = SQLiteParser(stream)
    tree = parser.parse()
    print(tree.toStringTree(recog=parser))

if __name__ == '__main__':
    main(sys.argv)