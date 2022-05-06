import sys
from antlr4 import *
from SQLiteLexer import SQLiteLexer
from SQLiteParser import SQLiteParser
from tree import Tree
from discopy import Ty, Box, Functor, Id, Cap, Cup

def main(argv):
    #input = "SELECT column1, column2 FROM table1, table2;"
    #input = FileStream(argv[1])
    #lexer = SQLiteLexer(input)
    #stream = CommonTokenStream(lexer)
    #parser = SQLiteParser(stream)
    #tree = parser.parse()
    #print(tree.toStringTree(recog=parser))
    #tree = Tree('parse', Ty('statement'), 1)
    #print(tree)
    #subtree = Tree('sql_stmt', Ty('statement'), 1)
    #print(subtree)
    #tree.append_to_tree(subtree)
    #tree.print_tree()
    
    #one = Box('one', Ty('zero'), Ty('one'))
    #two = Box('two', Ty('one'), Ty('two'))
    #three = Box('three', Ty('zero'), Ty('two'))
    #diagram = one >> two
    #Rewriter = Functor(ob = lambda x: x @ x, ar = lambda f : f @ f)
    #second_diagram = Rewriter(diagram)
    #second_diagram.draw()
    
    #def fun(boxes, value, i):
    #    for box in boxes:
    #        print(box.name == value)
    #        if box.name == value:
    #            i.append(value)
    
    #i = []
    #for elem in second_diagram:
    #    elem.fmap(lambda x : fun(x.boxes, 'two', i))
    #print(len(i))
    
    #x, y, z = Ty('x'), Ty('y'), Ty('z')
    #f, g = Box('f', x, y), Box('g', y, z)
    #ob, ar = {x: y, y: z, z: y}, {f: g, g: g[::-1]}
    #diagram = f >> g
    #F = Functor(ob, ar)(diagram)
    #F.draw()
    s, e, n, i = Ty('s'), Ty('e'), Ty('n'), Ty('n')
    #diagram = Box('True', e, Ty())[::-1] >> Box('WHERE', s.r @ s @ e.l, Ty())[::-1] @ Id(e) >> Id(s.r @ s) @ Cup(e.l, e)
    diagram = Box('True', e, Ty())[::-1] >> Box('WHERE', s.r @ s @ e.l, Ty())[::-1] @ Id(e) >> Id(s.r @ s) @ Cup(e.l, e) >> Box('reality_2', n, Ty())[::-1] @ Id(s.r @ s) >> Box('reality_1', n, Ty())[::-1] @ Id(n @ s.r @ s) >> Box('FROM', s.r @ s @ n.l @ n.l, Ty())[::-1] @ Id(n @ n @ s.r @ s) >> Id(s.r @ s @ i.l) @ Cup(i.l, i) @ Id(i @ s.r @ s) >> Id(s.r @ s) @ Cup(i.l, i) @ Id(s.r @ s) >> Box('morty', n, Ty())[::-1] @ Id(s.r @ s @ s.r @ s) >> Box('rick', n, Ty())[::-1] @ Id(n @ s.r @ s @ s.r @ s) >> Box('SELECT', s @ n.l @ n.l, Ty())[::-1] @ Id(n @ n @ s.r @ s @ s.r @ s) >> Id(s @ n.l) @ Cup(n.l, n) @ Id(n @ s.r @ s @ s.r @ s) >> Id(s) @ Cup(n.l, n) @ Id(s.r @ s @ s.r @ s) >> Cup(s, s.r) @ Cup(s, s.r) @ Id(s)
    diagram.draw()

if __name__ == '__main__':
    main(sys.argv)