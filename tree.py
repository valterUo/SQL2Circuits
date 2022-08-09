from discopy import Ty, Box

class Tree():
    
    def __init__(self, root_name, root_type, children_count, children = None):
        self.root_name = root_name
        self.root_type = root_type
        self.children_count = children_count
        if children == None:
            self.children = []
        else: 
            self.children = children
        self.children_types = []
        
        for child in self.children:
            self.children_types.append(child.get_type())
        
        if children_count == 0:
            self.full = True
        else:
            self.full = False
            
        if self.children_count == len(self.children):
            if all([child.is_full() for child in self.children]):
                self.full = True
    
    def get_root_name(self):
        return self.root_name
    
    def get_root_type(self):
        return self.root_type
        
    def is_full(self):
        return self.full
    
    def get_type(self):
        return self.root_type
    
    def get_children(self):
        return self.children
        
    def append_to_tree(self, tree):
        if self.full:
            return False
        if len(self.children) == 0:
            self.children.append(tree)
            self.children_types.append(tree.get_type())
        else:
            success = False
            for child in self.children:
                if not child.is_full():
                    success = child.append_to_tree(tree)
                    if success:
                        break
            if not success:
                if self.children_count > len(self.children):
                    self.children.append(tree)
                    self.children_types.append(tree.get_type())
                    return True
                else:
                    if all([child.is_full() for child in self.children]):
                        self.full = True
                    return False
        
        return True
    
    def print_tree(self):
        print(self.root_name, self.root_type)
        for child in self.children:
            child.print_tree()
            
    def get_diagram(self):
        legs = None
        cod_type = Ty()
        # SQL uses implicitly the actual table name as alias if the user does not define a new alias
        # Hack to fix the problem that when table_name appears with column_name in the same product rule, table_name type should be table_alias
        # This is not correctly in SQLite grammar although it must work there
        # Anyway, it does not work here because the typing breaks
        if self.root_name == "table-column-expr":
            for ty in self.children_types:
                if ty.name == "table_name":
                    cod_type = Ty('table_alias') @ cod_type
                else:
                    cod_type = ty @ cod_type
            for child in self.children:
                if not legs:
                    if child.get_root_type().name == "table_name":
                        legs = Box(child.get_root_name(), Ty("table_alias"), Ty())
                    else:
                        legs = child.get_diagram()
                else:
                    if child.get_root_type().name == "table_name":
                        legs = Box(child.get_root_name(), Ty("table_alias"), Ty()) @ legs
                    else:
                        legs = child.get_diagram() @ legs
            if legs:
                return Box(self.root_name, self.root_type, cod_type) >> legs
            return Box(self.root_name, self.root_type, cod_type)
        else:
            for ty in self.children_types:
                cod_type = cod_type @ ty
            for child in self.children:
                if not legs:
                    legs = child.get_diagram()
                else:
                    legs = legs @ child.get_diagram()
            if legs:
                return Box(self.root_name, self.root_type, cod_type) >> legs
            return Box(self.root_name, self.root_type, cod_type)