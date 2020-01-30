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
#import pickle
from functools import partial
import logging

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

from nodes import make_dict_tree
from tree_model import TreeModel

logger = logging.getLogger(__name__)

class TreeView(QtGui.QTreeView):
    tree_clicked = QtCore.pyqtSignal(str)
    # http://www.riverbankcomputing.com/pipermail/pyqt/2009-December/025379.html
    # http://pythonically.blogspot.ie/2009/11/drag-and-drop-in-pyqt.html
    def __init__(self, parent=None, listdict=None, mainwindow=None):
        super(TreeView, self).__init__(parent)
        self.setHeaderHidden(True)
        #self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        # self.setAutoExpandDelay(400)
        self.setDragEnabled( True )
        self.setAcceptDrops( True )
        self.setDragDropMode( QtGui.QAbstractItemView.InternalMove )
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.openMenu)
        self.mainwindow = mainwindow
        #self.tree_clicked.connect(mainwindow.vtkview.createBoundingBox)
        #self.filename = filename
        if listdict:
            self.addTree(listdict)
        else:
            self.setup_empty_tree()
            #treenodes = make_listdict_tree(listdict)
            #model = TreeModel(treenodes)
            #self.setModel(model)
            #model.dataChanged.connect(mainwindow.data_changed)
            #print(self.parent().parent().parent().parent())
            ##model.dataChanged.connect(self.parent().parent().parent().parent().data_changed)
        self.clicked.connect(self.on_tree_clicked)

    def on_tree_clicked(self, idx):
        if self.model():
            print("TREE CLICKED EVENT", idx)
            data_ = self.model().data(idx, QtCore.Qt.UserRole)
            if "UUID" in data_:
                print(data_["UUID"])
                self.tree_clicked.emit(data_["UUID"])

    def setup_empty_tree(self, name="root setup by default"):
        if self.model():
            self.setModel(None)
        self.addTree({u"name":name})

    def addTree(self, listdict, replace=False):
        treenodes = make_dict_tree(listdict)
        if not self.model() or replace:
            model = TreeModel(treenodes)
            self.setModel(model)
            ##--print(self.parent().parent().parent().parent())
            model.dataChanged.connect(self.data_changed)

            self.dataMapper = QtGui.QDataWidgetMapper()
            self.dataMapper.setModel(model)
            #propseditor = self.parent().parent().parent().parent().propseditor
            ##--self.parent().parent().parent().parent().propseditor.setupDataMapper(self) # self.dataMapper
            #self.selectionModel().currentChanged.connect(propseditor.setSelection) 
            #self.selectionModel().currentChanged.connect(self.testsm)  
            ###print("self.selectionModel()=", str(self.selectionModel()))
            ###print("self.selectionModel().selectionChanged=", str(self.selectionModel().selectionChanged))
            ##self.selectionModel().selectionChanged.connect(self.setSelection)
        else:
            model = self.model()
            model.appendRow(parent=None, node=treenodes)

    """def testsm(self, selected, deselected):
        print("self.selectionModel()=", str(self.selectionModel())) """

    def data_changed(self):
        if not self.model():
            return
        self.model().on_data_changed(None)
        ##dict_ = self.model()._rootNode.to_dict()
        ##if self.mainwindow:
        ##    self.mainwindow.tree_data_changed( dict_)
        ##logger.debug("///////////VIEW data changed\\\\\\\\\\\\" )
        ##--self.parent().parent().parent().parent().viewframe.setText(pprint.pformat(dict_))       
        #self.mainwindow.treeview_data_changed(dict_)

    def openMenu(self, position):
        indexes = self.selectedIndexes()
        if len(indexes) > 0:
        
            level = 0
            index = indexes[0]
            while index.parent().isValid():
                index = index.parent()
                level += 1
        
        menu = QtGui.QMenu()
        
        nodeidx=self.indexAt(position)   # http://www.riverbankcomputing.com/pipermail/pyqt/2008-October/020720.html
        model = self.model()
        nodename = model.getNode(nodeidx)
        print(nodename)
        nodename = model.getNode(nodeidx).name   # self.datTree.model().getNode(treeidx).name() TypeError: 'unicode' object is not callable
        nodevalue = model.getNode(nodeidx)._data
        print("nodename= {}, nodevalue= {}".format(nodename.encode("utf-8"), nodevalue))
        menu.addAction("insert node", partial(self.insertNode, nodeidx))
        menu.addAction("insert node, reparent", partial(self.insertNode, nodeidx, True))
        menu.addAction("delete node", partial(self.deleteNode, nodeidx))
        menu.addAction("delete node, reparent", partial(self.deleteNode, nodeidx, True))
        menu.addAction("show data", partial(print, nodevalue))
        menu.exec_(self.viewport().mapToGlobal(position))

    def deleteNode(self, nodeidx, reparent=False):
        model = self.model()
        node = model.getNode(nodeidx)
        nodedict_ = eval(node.data(1))
        parentidx = model.parent(nodeidx)
        parent = model.itemFromIndex( parentidx )
        #print("DELETE ", nodeidx, nodeidx.row(), node, parentidx) 
        offset=0
        if reparent:
            offset = node.childCount()
            while node.childCount():
                child = node.popChild(node.childCount()-1)
                #print("node.childCount() =", node.childCount(), child)
                parent.insertChild( nodeidx.row(), child )                
                model.insertDropRows( nodeidx.row(), 1, parentidx )
                #parent.appendChild( child )
                #model.insertDropRows( parent.childCount()-1, 1, parentidx )
            model.dataChanged.emit( parentidx, parentidx )
            #print("nodeidx.row()=", nodeidx.row(), parent.childCount())
            if "_childs" in nodedict_:
                del nodedict_["_childs"]
        model.removeRows(nodeidx.row()+offset, 1, parentidx)
        model.item_deleted.emit(nodedict_)

    def insertNode(self, nodeidx, reparent=False):
        model = self.model()
        node = model.getNode(nodeidx)
        #print("node=", node, "nodeidx=", nodeidx)
        parentidx = model.parent(nodeidx)
        parent = model.itemFromIndex( parentidx )
        model.insertRows(nodeidx.row(), 1, parentidx)
        if reparent:
            newnodeidx = model.index(nodeidx.row(), 0, parentidx)
            newnode = model.getNode(newnodeidx)
            child = parent.popChild(nodeidx.row()+1)
            newnode.appendChild( child )
            model.dataChanged.emit( parentidx, parentidx )
            #model.removeRows(nodeidx.row()+1, 1, parentidx)  # not required????


class DataTreeFrame(QtGui.QFrame):
    def __init__(self, parent=None, listdict=None, mainwindow=None):
        super(DataTreeFrame, self).__init__(parent)
        #self.setAutoFillBackground(True)
        self.setStyleSheet("background-color:yellow;")
        self.treeview = TreeView(self, listdict, mainwindow=mainwindow)
        layout = QtGui.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.treeview)
        self.setLayout(layout)


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
    treeView = DataTreeFrame(listdict=dtree3)
    treeView.show()
    #treenodes = treenode_from_dict(dtree)
    #treenodes = make_dict_tree(dtree3)
    #model = TreeModel(treenodes)
    #treeView.setModel(model)
    sys.exit(app.exec_())


