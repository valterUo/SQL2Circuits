from discopy.rigid import Diagram, Cup, Cap, Id, Ty, Box
import json

functor_data = None
with open('pregroup_functor_data.json') as json_file:
    functor_data = json.load(json_file)
    
def count_boxes(diagram, box_name):
    i = []
    def fun(boxes, box_name, i):
        for box in boxes:
            if box.name == box_name:
                i.append(box_name)
    
    for elem in diagram:
        elem.fmap(lambda x : fun(x.boxes, box_name, i))
    return len(i)


def object_mapping(obj, num_of_result_columns, num_of_tables):
    dom_ty_name = obj.name
    dom_ty = Ty()
    if dom_ty_name in functor_data["object_function"].keys():
        for ty in functor_data["object_function"][dom_ty_name]:
            if "." in ty:
                ty = ty.split(".")
                if ty[1] == "l":
                    dom_ty = dom_ty @ Ty(ty[0]).l
                elif ty[1] == "r":
                    dom_ty = dom_ty @ Ty(ty[0]).r
            else:
                dom_ty = dom_ty @ Ty(ty)
    elif dom_ty_name == "select-keyword":
        dom_ty = dom_ty @ Ty('s')
        for i in range(num_of_result_columns):
            dom_ty = dom_ty @ Ty('n').l
    elif dom_ty_name == "from-keyword":
        dom_ty = dom_ty @ Ty('s').r @ Ty('s')
        for i in range(num_of_tables):
            dom_ty = dom_ty @ Ty('n').l
    else:
        cod_name = dom_name
    return dom_ty


def arrow_mapping(box, num_of_result_columns, num_of_tables):
    name = box.name
    result = Id(Ty())
    if name in functor_data["arrow_function"].keys():
        cup = False
        for i in range(len(functor_data["arrow_function"][name])):
            box = functor_data["arrow_function"][name][i]
            if box["box"] == "Id":
                if "." in box["type"]:
                    ty = box["type"].split(".")
                    if ty[1] == "l":
                        result = result @ Id(Ty(ty[0]).l)
                    elif ty[1] == "r":
                        result = result @ Id(Ty(ty[0]).r)
                else:
                    result = result @ Id(Ty(box["type"]))
            elif box["box"] == "Cup":
                if cup:
                    cup = False
                    continue
                else:
                    cup = True
                left, right = None, None
                
                if "." in box["type"]:
                    ty = box["type"].split(".")
                    if ty[1] == "l":
                        left = Ty(ty[0]).l
                    elif ty[1] == "r":
                        left = Ty(ty[0]).r
                else:
                    left = Ty(box["type"])
                    
                box = functor_data["arrow_function"][name][i + 1]
                
                if "." in box["type"]:
                    ty = box["type"].split(".")
                    if ty[1] == "l":
                        right = Ty(ty[0]).l
                    elif ty[1] == "r":
                        right = Ty(ty[0]).r
                else:
                    right = Ty(box["type"])
                    
                result = result @ Cap(left, right)
            elif box["box"] == "Cups":
                left = Ty()
                for t in box["cups"]:
                    left = left @ Ty(t)
                result = result @ Diagram.caps(left.l, left)
                
    elif name == "select-clause":
        result = Id(Ty('s'))
        left = Ty()
        for i in range(num_of_result_columns):
            left = left @ Ty('n')
        result = result @ Diagram.caps(left.l, left)
    elif name == "from-clause":
        result = Id(Ty('s').r) @ Id(Ty('s'))
        left = Ty()
        for i in range(num_of_tables):
            left = left @ Ty('n')
        result = result @ Diagram.caps(left.l, left)
    elif type(box.cod) == Ty:
        if box.dom == Ty('literal_value'):
            result = Box(name, Ty('e'), Ty())
        elif box.dom == Ty('where_keyword'):
            result = Box(name, Ty('s').r @ Ty('s') @ Ty('e').l, Ty())
        elif box.dom == Ty('select_keyword'):
            dom_ty = Ty('s')
            for i in range(num_of_result_columns):
                dom_ty = dom_ty @ Ty('n').l
            result = Box(name, dom_ty, Ty())
        elif box.dom == Ty('from_keyword'):
            dom_ty = Ty('s').r @ Ty('s')
            for i in range(num_of_tables):
                dom_ty = dom_ty @ Ty('n').l
            result = Box(name, dom_ty, Ty())
        elif box.dom == Ty('column_alias'):
            result = Box(box.name, Ty('n').r @ Ty('n'), Ty())
        elif box.dom == Ty('table_alias'):
            result = Box(box.name, Ty('n').r @ Ty('n'), Ty())
        elif box.dom == Ty('binary_operator'):
            result = Box(box.name, Ty('e') @ Ty('e').l @ Ty('n').l, Ty())
        else:
            result = Box(name, Ty('n'), Ty())
    return result