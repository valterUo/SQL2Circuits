from discopy import Diagram, Ty

def alias_object_mapping(obj):
    return obj

def alias_morphism_mapping(f):
    result = f
    if f.name == "result-column-with-alias":
        left = Ty('column_expr')
        right = Ty('column_alias')
        result = f >> Diagram.swap(left, right)\
        >> Diagram.swap(right, left)
    return result