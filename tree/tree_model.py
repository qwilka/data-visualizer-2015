# -*- coding: utf-8
"""
Copyright © 2020 Stephen McEntee
Licensed under the MIT license. 
See LICENSE file for details https://github.com/qwilka/data-visualizer-2015/blob/master/LICENSE
"""
from __future__ import division
from __future__ import print_function
#from __future__ import unicode_literals # causes problems for drag/drop when tree contrains unicode characters (pickle problem)
from future_builtins import *

#import sys
#import os
#import json
#import pprint
import logging
import pickle
#from functools import partial

PS = False

if PS:
    from PySide import QtCore
    from PySide import QtGui
else:
    import sip    # http://cyrille.rossant.net/making-pyqt4-pyside-and-ipython-work-together/
    sip.setapi('QDate', 2)
    sip.setapi('QDateTime', 2)
    sip.setapi('QString', 2)
    sip.setapi('QtextStream', 2)
    sip.setapi('Qtime', 2)
    sip.setapi('QUrl', 2)
    sip.setapi('QVariant', 2)
    from PyQt4 import QtCore
    from PyQt4 import QtGui

from nodes import Node, ListDictNode

logger = logging.getLogger(__name__)

class TreeModel(QtCore.QAbstractItemModel):
    model_updated = QtCore.pyqtSignal(dict)
    item_deleted = QtCore.pyqtSignal(dict)

    def __init__(self, root, parent=None):
        super(TreeModel, self).__init__(parent)
        self._rootNode = root
        self.rootidx = QtCore.QModelIndex() ##
        self.dirty = False
        
        def makedict(idx):  #  def makedict(idx, idx2):
            #print(self.getNode(idx))
            #print(self.getNode(idx).to_dict())
            dict_ = self._rootNode.to_dict()
            #print(dict_)
        
        self.dataChanged.connect(self.on_data_changed)  # makedict
        self.rowsInserted.connect(self.on_data_changed)
        self.model_updated.connect(self.on_model_updated)
        #self.model_updated.connect(self.vtkview.on_model_updated)
        self.model_updated.emit({})

    def on_model_updated(self, dict_):
        logger.debug(">>>>>>>>>>> MODEL updated <<<<<<<<<<<<<<< \n"  )

    def on_data_changed(self, idx):
        #print(self.getNode(idx))
        #print(self.getNode(idx).to_dict())
        #if not idx:
        #    parent = QtCore.QModelIndex()
        logger.debug("-------MODEL data changed--------- \n%s" % (str(idx), ) )
        dict_ = self._rootNode.to_dict()
        self.dirty = True  
        self.model_updated.emit({})

    def on_row_inserted(self, idx):
        logger.debug("~~~~~~~~~~ ROW inserted ~~~~~~~~~~~ \n%s" % (str(idx), ) )

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
        elif role == QtCore.Qt.UserRole:
            return eval(node.data(1))

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        """this method gets called when the user changes data"""
        if index.isValid():
            if role == QtCore.Qt.EditRole:
                node = index.internalPointer()
                node.setData(index.column(), value)
                self.dataChanged.emit(index, index)
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
                QtCore.Qt.ItemIsEditable |
                QtCore.Qt.ItemIsDropEnabled |
                QtCore.Qt.ItemIsDragEnabled)

    def supportedDropActions( self ):
        '''Items can be moved and copied (but we only provide an interface for moving items in this example.'''
        return QtCore.Qt.MoveAction | QtCore.Qt.CopyAction

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

    def insertRows(self, position, numrows, parent=None, nodes=None):
        """insert rows from starting position (row index) and number given by nrows"""
        if not parent:
            parent = self.rootidx
        parentNode = self.getNode(parent)

        if nodes and isinstance(nodes, Node):  # ListDictNode
            listnodes = [nodes]
        elif isinstance(nodes, list):
            listnodes = nodes
        #else:
        #    raise TypeError ("attribute nodes must be Node or list of Nodes")

        self.beginInsertRows(parent, position, position + numrows - 1)

        for row in range(numrows):
            nrows = parentNode.childCount()
            if nodes:
                childNode = listnodes[row]
                success = parentNode.insertChild(nrows, childNode)
            else:
                childNode = ListDictNode("new node" + str(nrows+1))
                success = parentNode.insertChild(position+row, childNode)
            #success = parentNode.insertChild(nrows, childNode)

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

    def appendRow(self, parent=None, node=None):
        if not parent:
            parent = self.rootidx
        nrows = self.rowCount(parent)
        self.insertRows(nrows, 1, parent, node)

    # http://kylemr.blogspot.ie/2013/04/pyqt-drag-and-drop-outliner-like.html

    def insertDropRows(self, position, numrows, parent=None):
        """insert rows from starting position (row index) and number given by nrows"""
        if not parent:
            parent = self.rootidx
        parentNode = self.getNode(parent)

        self.beginInsertRows(parent, position, position + numrows - 1)
        #success = parentNode.insertChild(numrows, childNode)
        self.endInsertRows()
        return True #success

    def mimeTypes( self ):
        '''The MimeType for the encoded data.'''
        if hasattr(QtCore, 'QStringList'):
            types = QtCore.QStringList( 'application/x-pynode-item-instance' )
        else:
            types = ['application/x-pynode-item-instance']
        return types
     
    def mimeData( self, indices ):
        '''Encode serialized data from the item at the given index into a QMimeData object.'''
        data = ''
        item = self.itemFromIndex( indices[0] )
        try:
            print("item to pickle=", item, str(item.__dict__))
            data += pickle.dumps( item )
        except:
            print("WARNING: no pickle!!")
            pass
        mimedata = QtCore.QMimeData()
        mimedata.setData( 'application/x-pynode-item-instance', data )
        #print("pickle data=", data)
        return mimedata
     
    def dropMimeData( self, mimedata, action, row, column, parentIndex ):
        '''Handles the dropping of an item onto the model.
         
        De-serializes the data into a TreeItem instance and inserts it into the model.
        '''
        if not mimedata.hasFormat( 'application/x-pynode-item-instance' ):
            return False
        item = pickle.loads( str( mimedata.data( 'application/x-pynode-item-instance' ) ) )
        dropParent = self.itemFromIndex( parentIndex )
        if row>=0:   # drop between nodes
            dropParent.insertChild(row, item)
            self.insertDropRows( row, 1, parentIndex )
        else:    # drop on top of a node
            dropParent.appendChild( item )
            self.insertDropRows( dropParent.childCount()-1, 1, parentIndex )
        self.dataChanged.emit( parentIndex, parentIndex )
        return True

    def itemFromIndex( self, index ):
        '''Returns the TreeItem instance from a QModelIndex.'''
        #return index.internalPointer() if index.isValid() else self.root
        return index.internalPointer() if index.isValid() else self._rootNode


if __name__ == "__main__":
    import sys
    from tree_node import make_dict_tree, treenode_from_dict  

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
    dtree2 = {"name":"TopLevel2", 
    "_childs":[
    {"name":"nep10"},
    {"name":"nic20"},
    {"name":"nep1"}, 
    {"name":"nic2"}, 
    {"name":"child3", 
    "_childs":[
    {"name":"nic4"}, 
    {"name":"nep5"}]} 
    ]}
    dtree4 = {
    "_childs":[
    {"name":"nep10"},
    {"data":"useless data"},
    {"name":"nep1"}, 
    {"name":"nic2"}, 
    {"name":"child3", 
    "_childs":[
    {"name":"nic4"}, 
    {"name":"nep5"}]} 
    ]}
    dtree3 = [dtree1, dtree2]

    app = QtGui.QApplication(sys.argv)
    app.setStyle("plastique")
    treeView = QtGui.QTreeView()
    treeView.show()
    treenodes = treenode_from_dict(dtree)
    #treenodes = make_dict_tree(dtree3)
    model = TreeModel(treenodes)
    treeView.setModel(model)
    sys.exit(app.exec_())

