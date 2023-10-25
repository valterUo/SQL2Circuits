from discopy.grammar.pregroup import Box, Ty, Id, Cup
from functools import reduce

def cup_remove_arrow_mapping(box):
    if box.name.lower() == 'select':
        return box
    elif not box.cod:
        domain = box.dom
        raised_leg = domain[0]
        new_domain = reduce(lambda x, y : x @ y, domain[1:], Ty())
        new_box = Id(raised_leg) @ Box(box.name, new_domain, raised_leg.l)>> Cup(raised_leg, raised_leg.l)
        return new_box
    return box

def cup_remove_arrow_mapping2(box):
    if box.cod == box.dom == Ty('n'):
        return Id(box.cod)
    return box