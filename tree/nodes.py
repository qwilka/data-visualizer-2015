"""
Copyright © 2020 Stephen McEntee
Licensed under the MIT license. 
See LICENSE file for details https://github.com/qwilka/data-visualizer-2015/blob/master/LICENSE
"""

class Node:

    def __init__(self, name, parent=None, data=None):
        self._name = name
        self._parent = parent
        self._childs = []
        self._data = []    #  [name]
        if data and isinstance(data, (list, tuple) ):
            self._data.extend(data)
        else:                     
            self._data.append(data)
        if parent is not None:
            parent.appendChild(self)

    def appendChild(self, child):
        self._childs.append(child)
        child._parent = self

    def insertChild(self, idx, child):
        if idx<0 or idx>len(self._childs): 
            return False
        self._childs.insert(idx, child)
        child._parent = self
        return True

    def removeChild(self, idx):
        if idx<0 or idx>=len(self._childs):     # if idx<0 or idx>len(self._childs):
            return False
        child = self._childs.pop(idx)
        child._parent = None
        return True

    def popChild(self, idx):
        if idx<0 or idx>len(self._childs):     # if idx<0 or idx>len(self._childs):
            return False
        child = self._childs.pop(idx)
        child._parent = None
        return child

    def child(self, idx):
        if idx<0 or idx>=len(self._childs):  # if idx<0 or idx>len(self._childs):
            return False
        return self._childs[idx]

    def childCount(self):
        return len(self._childs)

    def columnCount(self):
        return len(self._data) + 1  # name and data

    def parent(self):
        return self._parent

    def row(self):         
        if self._parent is not None:
            return self._parent._childs.index(self)

    def data(self, colidx):
        if colidx is 0:
            return self._name
        elif colidx is 1:
            return str(self._data[0])  
        """try:
            return self._data[colidx]
        except IndexError:
            raise IndexError("data/row[{}] not read in Node instance {}".format(colidx, self._name))"""

    def setData(self, colidx, value):
        if colidx is 0:
            if hasattr(value, 'toPyObject'):
                #self._name = str(value.toPyObject())
                self._name = str(value)
            else:
                self._name = unicode(value)  
        if colidx is 1:
            #self._data[0] = str(value.toPyObject())
            self._data[0] = str(value)
        """try:
            self._data[colidx] = value
        except IndexError:
            raise IndexError("data/row[{}] not set in Node instance {}".format(colidx, self._name))"""

    def name():
        def fget(self): return self._name
        def fset(self, value): self._name = value
        return locals()
    name = property(**name())

    def to_dict(self): 
        dict_ = {"name":self._name}
        dict_.update({"_data":self._data})
        if self._childs:
            dict_["_childs"] = []
            for child in self._childs:
                dd = child.to_dict()
                dict_["_childs"].append(dd)
        return dict_ 


class ListDictNode(Node):
    
    def __init__(self, name, parent=None, data=None):
        super(ListDictNode, self).__init__(name, parent, None)
        #self._data = {} #  {"name":name}
        if data and isinstance(data, dict):
            #self._data.update(data)
            self._data = data
            if "name" in self._data:
                del self._data["name"]
        else:
            self._data = {}

    def columnCount(self):
        return 1

    def data(self, column):
        if   column is 0:
            return self._name
        elif column is 1:
            return str(self._data)   # str(self._data) QtCore.QVariant( (self._data,) )

    def setData(self, column, value):
        if column is 0:
            if hasattr(value, 'toPyObject'):
                #self._name = str(value.toPyObject())
                self._name = str(value)  
            else:
                self._name = unicode(value)
                #self._data["name"] = str(value)       
        if column is 1:
            self._data = eval(value)
            """if isinstance(value, tuple) and len(value)==2:
                if value[0] in self._data:
                    self._data[value[0]] = value[1]"""
            #self.value = str(value)

    def to_dict(self): 
        dict_ = {"name":self.name}
        dict_.update(self._data)
        if self._childs:
            dict_["_childs"] = []
            for child in self._childs:
                dd = child.to_dict()
                dict_["_childs"].append(dd)
        return dict_

    def to_listdict(self): # needs to be the root node
        listdict = []
        for child in self._childs:
            dd = child.to_dict()
            listdict.append(dd)
        return listdict    


class PrintTreeNode(Node):

    def __init__(self, name, parent=None):
        super(PrintTreeNode, self).__init__(name, parent)
        
    def _print(self, tabLevel=-1):
        output     = ""
        tabLevel += 1        
        for i in range(tabLevel):
            output += "\t"        
        output += "|------" + self._name + "\n"        
        for child in self._childs:
            output += child._print(tabLevel)         
        return output

    def __repr__(self):
        return self._print()


def make_listdict_tree(listdict_data, root_node=None, parent=None):
    """converts a dictionary (or list of dictionaries) to tree objects for used by TreeModel"""
    if not parent:
        root_node = ListDictNode('Root of listdict tree')
        parent = root_node
    if isinstance(listdict_data, dict):
        datalist = [listdict_data]
    elif isinstance(listdict_data, list):
        datalist = listdict_data
    else:
        raise TypeError('Function make_datatree: first argument incorrectly specified')
    for dd in datalist:
        if "name" in dd:  # remove subordinate/child nodes from data
            if "_childs" in dd:
                nochilds = dd.copy()
                del nochilds["_childs"]
            else:
                nochilds = dd
            node = ListDictNode(dd["name"], parent, nochilds)
            if "_childs" in dd:
                make_listdict_tree(dd["_childs"], root_node, node)
    return root_node


def make_dict_tree(dict_, root_node=None, parent=None):
    """converts a dictionary to tree objects for used by TreeModel"""
    #if makeroot: # if the top level is a list of dictionaries
    #    root_node = ListDictNode('Root of dict tree')
    if isinstance(dict_, list): # if the top level is a list of dictionaries
        return make_listdict_tree(dict_)
    #    parent = root_node
    if "_childs" in dict_:
        nochilds = dict_.copy()
        del nochilds["_childs"]
    else:
        nochilds = dict_
    nodename = dict_["name"] if "name" in dict_ else (
              "nameless node" if root_node else "root"  )
    node = ListDictNode(nodename, parent, nochilds)
    if not root_node:
        root_node = node
    if "_childs" in dict_:
        for child in dict_["_childs"]:
            make_dict_tree(child, root_node, node)
    return root_node


def treenode_from_dict(datadict, root_node=None, parent=None):
    """converts a dictionary to a TreeNode object for used by TreeModel"""
    if not parent:
        root_node = Node('Root')
        parent = root_node
    for name, value in datadict.items():
        node = Node(name, parent, value)
        if isinstance(value, dict):
            node = treenode_from_dict(value, root_node, node)
    return root_node


def traverse_tree_yield_data(dict_tree):
    if "_childs" in dict_tree:
        nochilds = dict_tree.copy()
        del nochilds["_childs"]
    else:
        nochilds = dict_tree
    yield nochilds # yielding from here preserves order
    if "_childs" in dict_tree:
        #http://stackoverflow.com/questions/8407760/python-how-to-make-a-recursive-generator-function
        # Note that as of Python 3.3, you can use the new "yield from" syntax
        for child in dict_tree["_childs"]:
            for data_ in traverse_tree_yield_data(child):
                yield data_
    #yield nochilds


if __name__ == '__main__':
    
    rootNode   = PrintTreeNode("toplevel")
    childNode0 = PrintTreeNode("RightPirateLeg",        rootNode)
    childNode1 = PrintTreeNode("RightPirateLeg_END",    childNode0)
    childNode2 = PrintTreeNode("LeftFemur",             rootNode)
    childNode3 = PrintTreeNode("LeftTibia",             childNode2)
    childNode4 = PrintTreeNode("LeftFoot",              childNode3)
    childNode5 = PrintTreeNode("LeftFoot_END",          childNode4)

    print(rootNode)

    dtree1 = {"name":"TopLevel-notroot", "number":123,
    "_childs":[
    {"name":"child10"},
    {"name":"child20"},
    {"name":"child1", "anumber":321}, 
    {"name":"child2"}, 
    {"name":"child3", 
    "_childs":[
    {"name":"child4"}, 
    {"name":"child5"}]} 
    ]}
    gener = traverse_tree_yield_data(dtree1)
    for i in gener:
        print(i)
    #print(traverse_tree_yield_data(dtree1).next())
    
