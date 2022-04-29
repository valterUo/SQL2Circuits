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
            print(child.get_type())
            self.children_types.append(child.get_type())
        
        if children_count == 0:
            self.full = True
        else:
            self.full = False
            
        if len(self.children) > 0:
            if all([child.is_full() for child in self.children]):
                self.full = True
        
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
            if not success:
                if self.children_count != len(self.children):
                    self.children.append(tree)
                    self.children_types.append(tree.get_type())
                    return True
                else:
                    self.full = True
                    return False
        
        if all([child.is_full() for child in self.children]):
            self.full = True
        
        return True
    
    def print_tree(self):
        print(self.root_name, self.root_type)
        for child in self.children:
            child.print_tree()
            
    def get_diagram(self):
        legs = None
        cod_type = Ty()
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