# -*- coding: utf-8
"""
Copyright © 2020 Stephen McEntee
Licensed under the MIT license. 
See LICENSE file for details https://github.com/qwilka/data-visualizer-2015/blob/master/LICENSE
"""
from PyQt4 import QtCore
from PyQt4 import QtGui

class TreeNode(object):

    def __init__(self, name, parent=None, data=None):
        self._name = name
        self._parent = parent
        self._childs = []
        self._data = [name]
        if data and isinstance(data, (list, tuple) ):
            self._data.extend(data)
        else:                     
            self._data.append(data)
        if parent is not None:
            parent.addChild(self)

    def rowCount(self, parent=None):  ############
        return 5

    def addChild(self, child):
        self._childs.append(child)

    def insertChild(self, idx, child):
        if idx<0 or idx>len(self._childs):
            return False
        self._childs.insert(idx, child)
        child._parent = self
        return True

    def removeChild(self, idx):
        if idx<0 or idx>len(self._children):
            return False
        self._childs.pop(idx)
        child._parent = None
        return True

    def child(self, idx):
        return self._childs[idx]

    def childCount(self):
        return len(self._childs)

    def columnCount(self):
        return len(self._data)

    def parent(self):
        return self._parent

    def row(self):         
        if self._parent is not None:
            return self._parent._childs.index(self)

    def data(self, colidx):
        try:
            return self._data[colidx]
        except IndexError:
            raise IndexError("data/row[{}] not read in Node instance {}".format(colidx, self._name))

    def setData(self, colidx, value):
        try:
            self._data[colidx] = value
        except IndexError:
            raise IndexError("data/row[{}] not set in Node instance {}".format(colidx, self._name))



class TreeModel(QtCore.QAbstractItemModel):

    def __init__(self, root, parent=None):
        super(TreeModel, self).__init__(parent)
        self._rootNode = root
        self.rootidx = QtCore.QModelIndex() ##

    def rowCount(self, parent=None):
        """the number of rows is the number of children"""
        if not parent:
            parent = self.rootidx
        if not parent.isValid():
            parentNode = self._rootNode
        else:
            parentNode = parent.internalPointer()
        return parentNode.childCount()

    def columnCount(self, parent):
        # 
        if parent and parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return self._rootNode.columnCount()  # return len(HORIZONTAL_HEADERS)

    def data(self, index, role):
        """returns the data requested by the view"""
        if not index.isValid():
            return None

        node = index.internalPointer()

        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            return node.data(index.column())     ## node.row(index.column())

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        """this method gets called when the user changes data"""
        if index.isValid():
            if role == QtCore.Qt.EditRole:
                node = index.internalPointer()
                node.setData(index.column(), value)
                return True
        return False

    def headerData(self, section, orientation, role):
        """returns the name of the requested column"""
        if role == QtCore.Qt.DisplayRole:
            if section == 0:
                return "Key"
            if section == 1:
                return "Value"

    def flags(self, index):
        """everything is editable"""
        return (QtCore.Qt.ItemIsEnabled |
                QtCore.Qt.ItemIsSelectable |
                QtCore.Qt.ItemIsEditable)

    def parent(self, index):
        """returns the parent from given index"""
        node = self.getNode(index)
        parentNode = node.parent()
        if parentNode == self._rootNode:
            return QtCore.QModelIndex()
        return self.createIndex(parentNode.row(), 0, parentNode)

    def index(self, row, column, parent):
        """returns an index from given row, column and parent"""
        parentNode = self.getNode(parent)
        childItem = parentNode.child(row)

        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def getNode(self, index):
        """returns a Node() from given index"""
        if index.isValid():
            node = index.internalPointer()
            if node:
                return node
        return self._rootNode

    def insertRows(self, position, numrows, parent=None):
        """insert rows from starting position (row index) and number given by nrows"""
        if not parent:
            parent = self.rootidx
        parentNode = self.getNode(parent)

        self.beginInsertRows(parent, position, position + numrows - 1)

        for row in range(numrows):
            nrows = parentNode.childCount()
            childNode = TreeNode("untitled" + str(nrows))
            success = parentNode.insertChild(nrows, childNode)

        self.endInsertRows()
        return success

    def removeRows(self, position, rows, parent=None):
        """remove the rows from position to position+rows"""
        if not parent:
            parent = self.rootidx
        parentNode = self.getNode(parent)
        self.beginRemoveRows(parent, position, position + rows - 1)

        for row in range(rows):
            success = parentNode.removeChild(position)

        self.endRemoveRows()
        return success

    def to_dict(self):
        return self._rootNode.to_dict()

    def appendRow(self, parent=None, data=None):
        if not parent:
            parent = self.rootidx
        nrows = self.rowCount(parent)
        self.insertRows(nrows, 1, parent)


if __name__ == "__main__":
    import sys
    from tree_node import treenode_from_dict   # TreeNode, 

    dtree = {'First name': 'Maximus',
        'Last name': 'Mustermann',
        'Nickname': 'Max',
        'Address':{
            'Street': 'Musterstr.',
            'House number': 13,
            'Place': 'Orthausen',
            'Zipcode': 76123},
        'An Object': "i am a 'float'",
        'Great-grandpa':{
        'Grandpa':{
        'Pa': 'Child'}}
    }

    #with open("testdata.json", 'w') as jfile:
    #    json.dump(d, jfile)
    #del d
    #with open("testdata.json", 'r') as jfile:
    #    dtree = json.load(jfile)
    #traverse_tree(dtree)
    #dtree = import_json("datatree.json")

    app = QtGui.QApplication(sys.argv)
    app.setStyle("plastique")
    treeView = QtGui.QTreeView()
    treeView.show()
    treeNode = treenode_from_dict(dtree)
    #treeNode = json_to_Nodetree("testdata.json")
    model = TreeModel(treeNode)
    treeView.setModel(model)
    sys.exit(app.exec_())

