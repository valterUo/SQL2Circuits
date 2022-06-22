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
    
    input_stream = FileStream(this_folder + "\\join-order-benchmark-queries\\1b.sql")
    lexer = SQLiteLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = SQLiteParser(stream)
    tree = parser.parse()

    print("Whole parse tree: ")
    print(tree.toStringTree(recog=parser))
    
    
    
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
    
    
    def remove_leaf_cups(diagram):
        # Remove cups to reduce post-selection in the circuit, for faster execution

        diags = []
        for box, offset in zip(diagram.boxes, diagram.offsets):
            #print('Box and offset: ', box, offset)
            if not box.dom:  # word box
                diags.insert(offset, box)
            else:  # cup (the only other type of box in these diagrams)
                i = 0
                off = offset
                #print('len(diags[i].cod) - 1: ', len(diags[i].cod) - 1)
                while off > len(diags[i].cod) - 1:
                    #print('In loop')
                    off -= len(diags[i].cod)
                    i += 1
                if len(diags) > 1:
                    left, right = diags[i:i+2]
                    #print(diags)
                    #print('left: ', left)
                    #print('right: ', right)

                    if len(left.cod) == 1:
                        new_diag = right >> (left.r.dagger() @ Id(right.cod[1:]))
                    else:
                        if len(right.cod) == 1:
                            new_diag = left >> Id(s) @ right.l.dagger() @ Id(left.cod[offset + 1:])
                        else:
                            # The following code does not change the diagram now
                            # This case will be handled after all leaf cups have been removed
                            new_diag = left >> Id(s) @ right @ Id(left.cod[1:]) >> box @ Id(right.cod[1:]) @ Id(left.cod[1:])

                    diags[i:i+2] = [new_diag]
                else:
                    #print(box)
                    diags[0] = diags[0] >> Id(s) @ Id(diags[0].cod[:offset - 1]) @ box @ Id(diags[0].cod[offset + 1:])
                    #print(diags)
                    #print('what what')

        assert len(diags) == 1
        return diags[0]
    
    
    def remove_non_leaf_cups(diagram):
        # Remove cups to reduce post-selection in the circuit, for faster execution

        diags = []
        for box, offset in zip(diagram.boxes, diagram.offsets):
            #print('Box and offset: ', box, offset)
            if not box.dom:  # word box
                diags.insert(offset, box)
            else:  # cup (the only other type of box in these diagrams)
                i = 0
                off = offset
                #print('len(diags[i].cod) - 1: ', len(diags[i].cod) - 1)
                while off > len(diags[i].cod) - 1:
                    #print('In loop')
                    off -= len(diags[i].cod)
                    i += 1
                if len(diags) > 1:
                    left, right = diags[i:i+2]
                    #print(diags)
                    #print('left: ', left)
                    #print('right: ', right)

                    if len(left.cod) == 1:
                        new_diag = right >> (left.r.dagger() @ Id(right.cod[1:]))
                    elif len(right.cod) == 1:
                        new_diag = left >> Id(s) @ right.l.dagger() @ Id(left.cod[offset + 1:])
                    elif len(right.cod) > 1:
                        #print("we should be here always!")
                        assert offset == 0
                        #print(right, left, left.width())
                        #right.dagger().draw()
                        right1 = collect_right(right, diagram)#.dagger()
                        right1.draw()
                        new_diag = left >> Id(s) @ right @ Id(left.cod[1:]) >> box @ Id(right.cod[1:]) @ Id(left.cod[1:])

                    diags[i:i+2] = [new_diag]
                else:
                    #print(box)
                    diags[0] = diags[0] >> Id(s) @ Id(diags[0].cod[:offset - 1]) @ box @ Id(diags[0].cod[offset + 1:])
                    #print(diags)
                    #print('what what')

        assert len(diags) == 1
        return diags[0]
    
    
    def remove_cups(diagram):
        diagram = diagram.normal_form()
        diagram = remove_leaf_cups(diagram)
        #diagram = remove_non_leaf_cups(diagram)
        return diagram
    
    s, e, n, i = Ty('s'), Ty('e'), Ty('n'), Ty('n')
    
    snake = Box('Start', Ty(), e) @ Cap(e.r, e) \
    >> Id(e @ e.r @ e) \
    >> Cup(e, e.r) @ Box('End', Ty(), e)[::-1]
    
    where_diagram = Box('True', e, Ty())[::-1] \
    >> Box('WHERE', s.r @ s @ e.l, Ty())[::-1] @ Id(e) \
    >> Id(s.r @ s) @ Cup(e.l, e)
    
    from_diagram = Box('reality_2', n, Ty())[::-1] \
    >> Box('reality_1', n, Ty())[::-1] @ Id(n) \
    >> Box('FROM', s.r @ s @ n.l @ n.l, Ty())[::-1] @ Id(n @ n) \
    >> Id(s.r @ s @ i.l) @ Cup(i.l, i) @ Id(i) \
    >> Id(s.r @ s) @ Cup(i.l, i)
    
    from_diagram = Box('reality_2', n, Ty())[::-1] \
    >> Box('reality_1', n, Ty())[::-1] @ Id(n) \
    >> Box('FROM', n.l @ n.l, Ty())[::-1] @ Id(n @ n) \
    >> Id(i.l) @ Cup(i.l, i) @ Id(i) \
    >> Cup(i.l, i)
    
    from_diagram = Box('reality_2', n, Ty())[::-1] \
    >> Box('reality_1', n, Ty())[::-1] @ Id(n) \
    >> Box('FROM', n.l @ n.l, Ty())[::-1] @ Id(n @ n) \
    >> Id(i.l) @ Cup(i.l, i) @ Id(i) \
    >> Cup(i.l, i)
    
    diagram1 = Box('True', e, Ty())[::-1] \
    >> Box('WHERE', s.r @ s @ e.l, Ty())[::-1] @ Id(e) \
    >> Id(s.r @ s) @ Cup(e.l, e) \
    >> Box('reality_2', n, Ty())[::-1] @ Id(s.r @ s) \
    >> Box('reality_1', n, Ty())[::-1] @ Id(n @ s.r @ s) \
    >> Box('FROM', s.r @ s @ n.l @ n.l, Ty())[::-1] @ Id(n @ n @ s.r @ s) \
    >> Id(s.r @ s @ i.l) @ Cup(i.l, i) @ Id(i @ s.r @ s) \
    >> Id(s.r @ s) @ Cup(i.l, i) @ Id(s.r @ s) \
    >> Box('morty', n, Ty())[::-1] @ Id(s.r @ s @ s.r @ s) \
    >> Box('rick', n, Ty())[::-1] @ Id(n @ s.r @ s @ s.r @ s) \
    >> Box('SELECT', s @ n.l @ n.l, Ty())[::-1] @ Id(n @ n @ s.r @ s @ s.r @ s) \
    >> Id(s @ n.l) @ Cup(n.l, n) @ Id(n @ s.r @ s @ s.r @ s) \
    >> Id(s) @ Cup(n.l, n) @ Id(s.r @ s @ s.r @ s) \
    >> Cup(s, s.r) @ Cup(s, s.r) @ Id(s)
    
    diagram = Box('reality_2', n, Ty())[::-1] \
    >> Box('reality_1', n, Ty())[::-1] @ Id(n) \
    >> Box('FROM', s.r @ s @ n.l @ n.l, Ty())[::-1] @ Id(n @ n) \
    >> Id(s.r @ s @ i.l) @ Cup(i.l, i) @ Id(i) \
    >> Id(s.r @ s) @ Cup(i.l, i) \
    >> Box('morty', n, Ty())[::-1] @ Id(s.r @ s) \
    >> Box('rick', n, Ty())[::-1] @ Id(n @ s.r @ s) \
    >> Box('SELECT', s @ n.l @ n.l, Ty())[::-1] @ Id(n @ n @ s.r @ s) \
    >> Id(s @ n.l) @ Cup(n.l, n) @ Id(n @ s.r @ s) \
    >> Id(s) @ Cup(n.l, n) @ Id(s.r @ s) \
    >> Cup(s, s.r) @ Id(s)
    
    diagram = Box('reality_2', n, Ty())[::-1] \
    >> Box('reality_1', n, Ty())[::-1] @ Id(n) \
    >> Box('FROM', s.r @ s @ n.l @ n.l, Ty())[::-1] @ Id(n @ n) \
    >> Id(s.r @ s @ i.l) @ Cup(i.l, i) @ Id(i) \
    >> Id(s.r @ s) @ Cup(i.l, i) \
    >> Box('morty', n, Ty())[::-1] @ Id(s.r @ s) \
    >> Box('rick', n, Ty())[::-1] @ Id(n @ s.r @ s) \
    >> Box('SELECT', s @ n.l @ n.l, Ty())[::-1] @ Id(n @ n @ s.r @ s) \
    >> Id(s @ n.l) @ Cup(n.l, n) @ Id(n @ s.r @ s) \
    >> Id(s) @ Cup(n.l, n) @ Id(s.r @ s) \
    >> Cup(s, s.r) @ Id(s)
    
    
    #ob = {n: n, s: s}
    #ar = {Alice: Alice,
    #  Bob: Bob,
    #  loves: Cap(n.r, n) @ Cap(n, n.l) >> Diagram.id(n.r) @ love_box @ Diagram.id(n.l),
    #  is_rich: Cap(n.r, n) >> Diagram.id(n.r) @ is_rich_box,
    #  who: Cap(n.r, n) >> Diagram.id(n.r) @ (copy >> Diagram.id(n) @ Cap(s, s.l) @ Diagram.id(n) >>
    #                                         update @ Diagram.id(s.l @ n)) }
    
    def cup_remove_arrow_mapping(box):
        # Assumption is that every box contains a connection to a cup
        # On the other hand, the SELECT-box does not need to be changed
        # Thus for every box (which is not a cup) we "raise the first leg on top of the box"
        # This process creates snakes which the normalization process automatically removes
        # This rewriting process ensures that we can use less qubits
        
        if box.name.lower() == 'select':
            print("select")
            print(box.dom, box.cod)
            return box
        elif not box.cod:
            #box.draw()
            domain = box.dom
            raised_leg = Ty(domain[0])
            #print(raised_leg)
            new_domain = reduce(lambda x, y : x @ Ty(y), domain[1:], Ty())
            #(Id(raised_leg) @ Box(box.name, raised_leg.l, new_domain)).draw()
            #(Cup(raised_leg, raised_leg.l)).draw()
            new_box = Id(raised_leg) @ Box(box.name, new_domain, raised_leg.l)\
            >> Cup(raised_leg, raised_leg.l)
            #print(box.name)
            #print(new_box.dom, new_box.cod)
            #new_box.draw()
            return new_box
        return box

    cup_removal_functor = Functor(ob = lambda x: x, ar = lambda f: cup_remove_arrow_mapping(f))
    
    
    #print(type(Box('reality_2', n @ n, Ty()).dom[0]))
    #diagram1.normal_form().dagger().draw()
    diagram = cup_removal_functor(diagram1.normal_form()).normal_form()
    
    #for elem in (n @ e @ n):
    #    print(elem)
    
    #(Id(s @ s.r) @ Box('FROM', Ty(), s.r @ s @ n.l @ n.l)[::-1] @ Id(n.l @ n.l) 
    # >> Id(s) @ Cap(s.r, s.r.r) @ Id(n.l @ n.l)).draw()
    
    #diagram = Box('SELECT', s @ n @ n, Ty())[::-1] \
    #>> Id(s) @ Box('FROM', s.r @ s @ n @ n, Ty())[::-1] @ Id(n) @ Id(n) \
    #>> Cup(s, s.r) @ Id(s) @ Box('rick', n, Ty()) @ Box('morty', n, Ty()) @ Box('reality_1', n, Ty()) @ Box('reality_2', n, Ty())
    
    #diagram = from_diagram
    #diagram = diagram.normal_form()
    
    #diagram = remove_cups(diagram1)
    #diagram.draw()
    
    #snake.draw()
    #snake.normal_form().draw()
    
    #def collect_right(right, diagram):
    #    right.draw()
    #    diagram.draw()
    #    new_diagram = right
    #    start_level = 0
    #    number_of_right_types = right.width() - 1
    #    for index, box in enumerate(diagram.boxes):
    #        if box == right:
    #            start_level = index + 1
    #            #print("Start level", start_level)
    #        if index > start_level:
    #            print(diagram[index][0])
    #            #new_diagram.draw()
    #            #diagram[index][:right.width()].draw()
    #            if not box.dom:  # word box
    #                print("this is... ", diagram[index].cod[right.width() - 2:])
    #                print("and ", right.width() - 2)
    #                new_diagram = new_diagram >> Id(s.r) @ box @ Id(right.cod[right.width() - 2:])
    #                print('new diagram ', new_diagram)
    #            else:
    #                new_diagram = new_diagram >> Cup(s, s.r) @ Id(right.cod[right.width() - 2:])
    #                print('new diagram ', new_diagram)
    #    return new_diagram
    
    #for index, elem in enumerate(diagram):
    #    print(index, elem)
    #    print(elem.boxes)
        # Every layer contains one box which is either a box with codomain type Ty() or a cup
    #    if len(elem.boxes) == 1:
    #        box = elem.boxes[0]
    #        if not box.dom:  # box that is not a cup box and has codomain type Ty()
                # Based on the normal form and the problem, the first leg of the box is 
                # always connected to a cup and the others define the offset
    #            offset = offset + len(box.cod.objects) - 1
    #            print(offset)
    #        else: # cups
                # Based on the normal form, there is always a box before a cup
                # The cup always connects the two previous boxes in the iteration
                # We select the box just before the cup and everything in the diagram after that
                # we then turn it around which removes the cup
                
     #           continue
    
    
    #diagram.draw()
    
    #diagram = Id(Ty('x')) @ Id(Ty('x'))
    #diagram.draw()
    
    #print(diagram.cod)
    
    #from_diagram = remove_cups(from_diagram)
    #where_diagram = remove_cups(where_diagram)
    
    #diagram = from_diagram #.dagger()
    
    #diagram = diagram.normal_form()
    
    #def mirror_layer(layer):
    #    mirrored_layer = None
    #    for box in layer.boxes.reverse():
    #        mirrored_layer = mirrored_layer @ box
    #    return mirrored_layer
    
    #def mirror_diagram(diagram):
    #    mirrored_diagram = None
    #    for layer in diagram:
    #        mirrored_diagram = mirrored_diagram >> mirror_layer(layer)
    #    return mirrored_diagram
    
    #def remove_offset_from_right(diagram, offset):
    #    new_diagram = None
    #    for elem in diagram:
    #        new_layer_dom = Ty()
    #        new_layer_cod = Ty()
    #        new_layer_ids_boxes = []
    #        layer_width = elem.width()
    #        for i, dom_obj in enumerate(elem.dom.objects):
    #            if layer_width - i == offset:
    #                break
    #            else:
    #                new_layer_dom = new_layer_dom @ Ty(dom_obj)
    #        for i, cod_obj in enumerate(elem.cod.objects):
    #            if layer_width - i == offset:
    #                break
    #            else:
    #                new_layer_cod = new_layer_cod @ Ty(cod_obj)
    #        for i, box in enumerate(elem.boxes):
    #            box_cod = box.cod
    #            box_dom = box.dom
    #            for i in range(layer_width - offset):
    #                continue
               
        #return new_diagram
    
    #offset = 0
    #diagram_width = diagram.width()
    #print(diagram_width)
    
    #for index, elem in enumerate(diagram):
        #print(index, elem)
        #print(elem.boxes)
    #    if len(elem.boxes) == 1:
    #        box = elem.boxes[0]
    #        if not box.dom:  # box that is not a cup box
                # Based on the normal form and the problem, the first leg of the box is 
                # always connected to a cup and the others define the offset
    #            offset = offset + len(box.cod.objects) - 1
                #print(offset)
    #        else: # cups
                # Based on the normal form, there is always a box before a cup
                # The cup always connects the two previous boxes in the iteration
                # We select the box just before the cup and everything in the diagram after that
                # we then turn it around which removes the cup
                
                #print(diagram.dom.objects[0] == diagram.cod.objects[0])
    #            new_diagram = new_diagram >> Id(diagram.dom.objects[0]) @ diagram.boxes[0]
    #            new_diagram_width = new_diagram.width()
    #            for j in range(diagram_width - new_diagram_width - offset):
    #                new_diagram = new_diagram @ Id(diagram.dom.objects[0])
                    
                    
    #            new_diagram.draw()
    #            print("----------------------------")
                    
                
                #box_before_cup.dagger().draw()
        

    n, s, e = Ty('n'), Ty('s'), Ty('e')
    ansatz = IQPAnsatz({n: 1, s: 1, e: 1}, n_layers=1, n_single_qubit_params=3)
    circuit_diagram = ansatz(diagram)
    circuit_diagram.draw(figsize=(20, 20))
    
    #remove_cups(diagram).draw()

if __name__ == '__main__':
    main(sys.argv)