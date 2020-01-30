# -*- coding: utf-8
"""
Copyright © 2020 Stephen McEntee
Licensed under the MIT license. 
See LICENSE file for details https://github.com/qwilka/data-visualizer-2015/blob/master/LICENSE
"""
from __future__ import division
from __future__ import print_function
#from __future__ import unicode_literals
from future_builtins import *

import sys
import os
import json


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
#from PyQt4 import QtCore
#from PyQt4 import QtGui

from vtkframe import VtkQtFrame

class TreeDialog(QtGui.QDialog):
    def __init__(self, parent=None, datadict=None):
        super(TreeDialog, self).__init__(parent)
        self.treeWidget = TreeWidget(self, datadict)
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.treeWidget)
        self.setLayout(self.layout)


class TreeWidget(QtGui.QTreeWidget):
    # http://www.riverbankcomputing.com/pipermail/pyqt/2009-December/025379.html
    # http://pythonically.blogspot.ie/2009/11/drag-and-drop-in-pyqt.html
    def __init__(self, parent=None, datadict=None):
        super(TreeWidget, self).__init__(parent)
        self.header().setHidden(True)
        self.setSelectionMode(self.ExtendedSelection)    # ExtendedSelection  SingleSelection
        self.setDragDropMode(self.InternalMove)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        if datadict:
            self.tree_from_dict(datadict)
            ####self.datadict = datadict
        else:
            self.datadict = {"_childs":[]}
        self.taken_datadict = {}  # container to facilitate datadict changes following drag-drop
        
        self.itemChanged.connect(self.on_item_changed)

    def tree_from_dict(self, datadict, rootname=None):
        if rootname:
            root = QtGui.QTreeWidgetItem(self, 
                            QtCore.QStringList(str(rootname))  ) 
            root.setFlags(root.flags() | QtCore.Qt.ItemIsEditable)
            root.setData(1, QtCore.Qt.UserRole, None)  # ref to location in dictionary
        else:
            root = self.invisibleRootItem() 
        def walk_dict_tree(parent, dict_, location=None):
            if not location: location = []
            location.append(0)
            for ii, childd in enumerate(dict_["_childs"]):
                childitem = QtGui.QTreeWidgetItem(parent, 
                                QtCore.QStringList(childd["name"]))
                childitem.setFlags(childitem.flags() | QtCore.Qt.ItemIsEditable)
                location[-1] = ii
                #########childitem.setData(0, QtCore.Qt.UserRole, childd["name"])
                childitem.setData(1, QtCore.Qt.UserRole, location)  # ref to location in dictionary
                checkdata = childitem.data(1, QtCore.Qt.UserRole)
                #print(checkdata, childd, checkdata is childd)
                ####print(location, checkdata, checkdata.toPyObject())
                if "_childs" in childd:
                    walk_dict_tree(childitem, childd, location=location)
        walk_dict_tree(root, datadict)
        self.datadict = datadict


    def on_item_changed(self, item, col):
        #entry.setText(curr.text()) str(curr.text(0)),
        #print( str(item.text(col)), item.data(0, QtCore.Qt.DisplayRole).toPyObject(), item.data(1, QtCore.Qt.UserRole).toPyObject() )
        parent = self.datadict
        location = item.data(1, QtCore.Qt.UserRole).toPyObject()
        if col != 0 or not location:
            return    # col=1 means it's drag-drop event
        ####name = item.data(0, QtCore.Qt.UserRole).toPyObject()
        #'print(str(item.text(col)),  location, name, " col= ", col)
        for ii, row in enumerate(location): 
            parent = parent["_childs"][row]
            if ii == len(location)-1:
                parent["name"] = str(item.text(col))
                return   

            
    def dropEvent(self, event):
        if event.source() == self:
            QtGui.QAbstractItemView.dropEvent(self, event)

    def dropMimeData(self, parent, row, data, action):
        if action == QtCore.Qt.MoveAction:
            return self.moveSelection(parent, row)
        return False

    def moveSelection(self, parent, position):
        # save the selected items
        selection = [QtCore.QPersistentModelIndex(i)
                      for i in self.selectedIndexes()]
        parent_index = self.indexFromItem(parent)
        if parent_index in selection:
             return False
        # save the drop location in case it gets moved
        target = self.model().index(position, 0, parent_index).row()
        if target < 0:
            target = position
        # remove the selected items
        taken = []
        for index in reversed(selection):
            item = self.itemFromIndex(QtCore.QModelIndex(index))
            if item is None or item.parent() is None:
                tomove = self.takeTopLevelItem(index.row())
                taken.append(tomove)
                location = tomove.data(1, QtCore.Qt.UserRole).toPyObject()
                self.taken_datadict[tuple(location)] = self.pop_child_from_datadict(location)
            else:
                tomove = item.parent().takeChild(index.row())
                taken.append(tomove)
                location = tomove.data(1, QtCore.Qt.UserRole).toPyObject()
                self.taken_datadict[tuple(location)] = self.pop_child_from_datadict(location)
        # insert the selected items at their new positions
        while taken:
            if position == -1:
                # append the items if position not specified
                if parent_index.isValid():
                    parent.insertChild(
                        parent.childCount(), taken.pop(0))
                else:
                    self.insertTopLevelItem(
                        self.topLevelItemCount(), taken.pop(0))
            else:
		# insert the items at the specified position
                if parent_index.isValid():
                    parent.insertChild(min(target,
                        parent.childCount()), taken.pop(0))
                else:
                    self.insertTopLevelItem(min(target,
                        self.topLevelItemCount()), taken.pop(0))
        self.walk_tree_widget( self.invisibleRootItem() ) # self.indexFromItem( self.invisibleRootItem() )
        #pprint.pprint(self.datadict)
        #if self.taken_datadict: 
        #    print("#######self.taken_datadict IS NOT EMPTY#######")
        #    pprint.pprint(self.taken_datadict)
        return True

    def pop_child_from_datadict(self, location):
        parent = self.datadict
        for ii, row in enumerate(location):  
            if ii == len(location)-1:
                ###print("--------- ii= ", ii, "poping row ", row)
                child = parent["_childs"].pop(row)
                return child   
            else:
                child = parent["_childs"][row]       
            parent = child

    # http://stackoverflow.com/questions/11918852/python-change-values-in-dict-of-nested-dicts-using-items-in-a-list
    # http://stackoverflow.com/questions/13687924/setting-a-value-in-a-nested-python-dictionary-given-a-list-of-indices-and-value
    def insert_child_into_datadict(self, location, dict_):
        parent = self.datadict
        for ii, row in enumerate(location): 
            if ii == len(location)-1:
                if "_childs" in parent:
                    parent["_childs"].insert(row, dict_)
                else:
                    parent["_childs"] = [dict_]
                return    
            else:
                child = parent["_childs"][row]       
            parent = child

    def walk_tree_widget(self, parent, location=None):
        if not location: 
            location = [0]
        #location.append(0)
        #print("location=", location, "number childen= ", parent.childCount())
        for ii in range( parent.childCount()):
            location[-1] = ii
            child = parent.child(ii)
            old_location = child.data(1, QtCore.Qt.UserRole).toPyObject()
            #if location != old_location:
            if tuple(old_location) in self.taken_datadict:
                ##print("removing ", old_location, " from taken_datadict ", self.taken_datadict)
                self.insert_child_into_datadict( location, 
                           self.taken_datadict.pop(tuple(old_location))  )
            child.setData(1, QtCore.Qt.UserRole, location)
            ##print(child.data(1, QtCore.Qt.UserRole).toPyObject())
            if child.childCount():
                location.append(0)
                self.walk_tree_widget(child, location=location)
                location.pop()

    def closeEvent(self, event):
        print(self.datadict)


class visinumVtkViewer(QtGui.QMainWindow):
    
    def __init__(self, parent=None, filepath=None):
        super(visinumVtkViewer, self).__init__(parent)
        self.parent = parent
        self.filename = filepath
        self.workingdir = '.'
        self.open_files_list = []

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setMinimumSize(500, 300)        
        pixmap = QtGui.QPixmap(22, 22)
        pixmap.fill( QtGui.QColor(73, 201, 47) )
        self.setWindowIcon( QtGui.QIcon(pixmap) )
        self.setWindowTitle( ("VisinumVTKviewer - {}").format(self.filename) ) 

        self.vtkframe = VtkQtFrame(self)
        self.setCentralWidget(self.vtkframe)
        self.dataTree = TreeDialog(self)
        self.dataTree.rejected.connect(self.dataTreePos)
        self.dataTree.hide()
        
        self.createActions()
        self.createMenuBar()


    def showDataTree(self):
        if self.dataTree.isVisible():
            self.dataTreePosition = self.dataTree.pos()
            self.dataTree.hide()
        else:
            self.dataTree.show()
            if hasattr(self, "dataTreePosition"):
                self.dataTree.move(self.dataTreePosition)
            self.dataTree.raise_()
            self.dataTree.activateWindow()       

    def dataTreePos(self):
        self.dataTreePosition = self.dataTree.pos()

    def createMenuBar(self):
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(self.openFileAct)  
        fileMenu.addAction(self.importFileAct)
        fileMenu.addAction(self.saveStateAct)
        fileMenu.addSeparator() 
        fileMenu.addAction(self.quitAct)
        viewMenu = menubar.addMenu('&View')
        viewMenu.addAction(self.viewPlanAct)
        viewMenu.addAction(self.showTreeAct)

    def createActions(self):
        self.quitAct = QtGui.QAction(
                "&Quit", self, shortcut=QtGui.QKeySequence.Quit,
                statusTip="Quit the application", triggered=self.close)
                
        self.openFileAct = QtGui.QAction(                                 
                "open file", self, shortcut=QtGui.QKeySequence.Open,
                statusTip="Open a PLY file", triggered=self.openFile)

        self.importFileAct = QtGui.QAction(                           
                "Import PLY", self, shortcut="i",
                statusTip="Import a PLY file", triggered=self.importFile)

        self.showTreeAct = QtGui.QAction(                         
                "show tree", self, shortcut="Ctrl+i",
                statusTip="show data tree", triggered=self.showDataTree)

        self.addTriadAct = QtGui.QAction(               
                "add axes triad", self, shortcut="Ctrl+t",
                statusTip="add axes triad", triggered=self.vtkframe.addAxes)

        self.viewPlanAct = QtGui.QAction(                    
                "plan view", self, shortcut="1",
                statusTip="view in plan (from above)", triggered=self.vtkframe.viewPlan)

        self.saveStateAct = QtGui.QAction(                         
                "save", self, shortcut=QtGui.QKeySequence.Save,
                statusTip="save current state", triggered=self.saveState)

    def openFile(self, fpath=None):
        if not fpath:
            fpath = QtGui.QFileDialog.getOpenFileName(self, 'Open file', 
                    self.workingdir, "JSON (*.json);;All files (*.*)")
            fpath = str(fpath)
            self.workingdir = os.path.dirname(fpath)
        if fpath.upper().endswith(".JSON"):
            self.loadState(fpath)
        #elif fpath.upper().endswith(".PLY"):
        #    self.showPLY(fpath)
        #self.vtkframe.showPLY(fpath)
        #self.open_files.append(fpath)
        #self.treeviewpane.getDefaultTree().addFilename(os.path.basename(str(fpath)))
        #self.treeviewpane.getDefaultTree().addFilename(str(fpath))

    def importFile(self, fpath=None):
        if not fpath:
            fpath = QtGui.QFileDialog.getOpenFileName(self, 'Open file', 
                    self.workingdir, "PLY files (*.ply);;All files (*.*)")
            fpath = str(fpath)
            self.workingdir = os.path.dirname(fpath)
        if fpath.upper().endswith(".PLY"):
            self.registerFile(fpath)
            self.vtkframe.showScene()

    def registerFile(self, fpath):
        fname = os.path.basename(str(fpath))
        if fpath.upper().endswith(".PLY"):
            self.vtkframe.addPLYactor(fpath)
            self.open_files_list.append({"name":fname, "filepath":fpath,
                                        "type":"PLY"}) 

    def saveState(self):
        if not self.filename or not os.path.isfile(self.filename):
            fpath = QtGui.QFileDialog.getSaveFileName(self, 'specify file to save', 
                self.workingdir, "JSON (*.json);;All files (*.*)")
            fpath = str(fpath)
            self.filename = fpath
            self.workingdir = os.path.dirname(fpath)
        statedict = {"_application":"VISINUM",
                 "_childs":self.open_files_list,
                 "current_directory":self.workingdir}
        with open(self.filename, 'w') as jfile:
            json.dump(statedict, jfile)

    def loadState(self, fpath):
        if os.path.isfile(fpath):
            with open(fpath, 'r') as jfile:
                statedict = json.load(jfile)
        else:
            print("Warning cannot open file {}".format(fpath))
            return
        self.filename = fpath
        self.workingdir = os.path.dirname(fpath) 
        for obj in statedict["_childs"]:
            fpath = obj["filepath"]
            if any([fpath.lower().endswith(ext) for ext in (".ply",)]):
                self.registerFile(fpath)
        self.vtkframe.showScene()
        self.setWindowTitle( ("VisinumVTKviewer - {}").format(os.path.basename(self.filename)) )
        if hasattr(self, "dataTree"):
            self.dataTree.treeWidget.tree_from_dict(statedict)
        

    #def showPLY(self, fpath):
    #    self.vtkframe.addPLYactor(fpath)
    #    name = os.path.basename(str(fpath))
    #    self.open_files_list.append({"name":name, "filepath":fpath,
    #                                "type":"PLY"})        


if __name__ == '__main__':
    # test main window visinumVtkViewer
    if True:
        app = QtGui.QApplication(sys.argv)
        app.setStyle("plastique")  
        mainwindow =  visinumVtkViewer()     
        mainwindow.show()
        sys.exit(app.exec_())

    # test TreeWidget
    if False:
        import pprint
        app = QtGui.QApplication(sys.argv)
        if True:
            dict_ = {"name":"rootLevel", "_childs":[{"name":"child10"},{"name":"child20"},{"name":"child1"}, {"name":"child2"}, {"name":"child3", "_childs":[{"name":"child4"}, {"name":"child5"}]} ]}
        else:
            fpath = QtGui.QFileDialog.getOpenFileName(None, 'Open file', 
                            '.', "JSON (*.json);;All files (*.*)")
            with open(str(fpath), 'r') as jfile:
                dict_ = json.load(jfile)
        mainwindow =  TreeDialog(None, dict_)      # TreeWidget(None, dict_)  
        mainwindow.show()
        sys.exit(app.exec_())
