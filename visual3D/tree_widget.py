"""
Copyright © 2020 Stephen McEntee
Licensed under the MIT license. 
See LICENSE file for details https://github.com/qwilka/data-visualizer-2015/blob/master/LICENSE
"""

import sys
import os
import json

from PyQt5.QtWidgets import (QTreeWidget, QTreeWidgetItem, QDialog, 
    QVBoxLayout, QAbstractItemView )
from PyQt5.QtCore import Qt


class TreeDialog(QDialog):
    def __init__(self, parent=None, datadict=None):
        super(TreeDialog, self).__init__(parent)
        self.treeWidget = TreeWidget(self, datadict)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.treeWidget)
        self.setLayout(self.layout)


class TreeWidget(QTreeWidget):
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
            # https://www.howtobuildsoftware.com/index.php/how-do/byrj/python-python-3x-import-qstring-pyqt5-qstringlist-in-pyqt5
            #root = QTreeWidgetItem(self, QtCore.QStringList(str(rootname))  ) 
            root = QTreeWidgetItem(self, [str(rootname)]  ) 
            root.setFlags(root.flags() | Qt.ItemIsEditable)
            root.setData(1, Qt.UserRole, None)  # ref to location in dictionary
        else:
            root = self.invisibleRootItem() 
        def walk_dict_tree(parent, dict_, location=None):
            if not location: location = []
            location.append(0)
            for ii, childd in enumerate(dict_["_childs"]):
                childitem = QTreeWidgetItem(parent, 
                                [ childd["name"] ])
                childitem.setFlags(childitem.flags() | Qt.ItemIsEditable)
                location[-1] = ii
                #########childitem.setData(0, Qt.UserRole, childd["name"])
                childitem.setData(1, Qt.UserRole, location)  # ref to location in dictionary
                checkdata = childitem.data(1, Qt.UserRole)
                #print(checkdata, childd, checkdata is childd)
                ####print(location, checkdata, checkdata.toPyObject())
                if "_childs" in childd:
                    walk_dict_tree(childitem, childd, location=location)
        walk_dict_tree(root, datadict)
        self.datadict = datadict


    def on_item_changed(self, item, col):
        #entry.setText(curr.text()) str(curr.text(0)),
        #print( str(item.text(col)), item.data(0, Qt.DisplayRole).toPyObject(), item.data(1, Qt.UserRole).toPyObject() )
        parent = self.datadict
        #location = item.data(1, Qt.UserRole).toPyObject()
        location = item.data(1, Qt.UserRole)
        if col != 0 or not location:
            return    # col=1 means it's drag-drop event
        ####name = item.data(0, Qt.UserRole).toPyObject()
        #'print(str(item.text(col)),  location, name, " col= ", col)
        for ii, row in enumerate(location): 
            parent = parent["_childs"][row]
            if ii == len(location)-1:
                parent["name"] = str(item.text(col))
                return   

            
    def dropEvent(self, event):
        if event.source() == self:
            QAbstractItemView.dropEvent(self, event)

    def dropMimeData(self, parent, row, data, action):
        if action == Qt.MoveAction:
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
                location = tomove.data(1, Qt.UserRole).toPyObject()
                self.taken_datadict[tuple(location)] = self.pop_child_from_datadict(location)
            else:
                tomove = item.parent().takeChild(index.row())
                taken.append(tomove)
                location = tomove.data(1, Qt.UserRole).toPyObject()
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
            old_location = child.data(1, Qt.UserRole).toPyObject()
            #if location != old_location:
            if tuple(old_location) in self.taken_datadict:
                ##print("removing ", old_location, " from taken_datadict ", self.taken_datadict)
                self.insert_child_into_datadict( location, 
                           self.taken_datadict.pop(tuple(old_location))  )
            child.setData(1, Qt.UserRole, location)
            ##print(child.data(1, Qt.UserRole).toPyObject())
            if child.childCount():
                location.append(0)
                self.walk_tree_widget(child, location=location)
                location.pop()

    def closeEvent(self, event):
        print(self.datadict)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication, QFileDialog
    import pprint
    app = QApplication(sys.argv)
    if True:
        dict_ = {"name":"rootLevel", "_childs":[{"name":"child10"},{"name":"child20"},{"name":"child1"}, {"name":"child2"}, {"name":"child3", "_childs":[{"name":"child4"}, {"name":"child5"}]} ]}
    else:
        fpath = QFileDialog.getOpenFileName(None, 'Open file', 
                        '.', "JSON (*.json);;All files (*.*)")
        with open(str(fpath), 'r') as jfile:
            dict_ = json.load(jfile)
    mainwindow =  TreeDialog(None, dict_)      # TreeWidget(None, dict_)  
    mainwindow.show()
    sys.exit(app.exec_())
