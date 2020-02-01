# -*- coding: utf-8
"""
Copyright © 2020 Stephen McEntee
Licensed under the MIT license. 
See LICENSE file for details https://github.com/qwilka/data-visualizer-2015/blob/master/LICENSE
"""
import sys
import os
import json

from PyQt5.QtWidgets import (QMainWindow, QWidget, QTextEdit, QGroupBox, 
    QFormLayout, QLabel, QLineEdit, QScrollArea, QVBoxLayout, QSplitter,
    QAction, QFileDialog)
from PyQt5 import QtGui 
from PyQt5.QtCore import Qt   #, QCoreApplication


from vtkframe import VtkQtFrame
from tree_widget import TreeWidget


class visinumVtkViewer(QMainWindow):
    
    def __init__(self, parent=None, filepath=None):
        super(visinumVtkViewer, self).__init__(parent)
        self.parent = parent
        self.filename = filepath
        self.workingdir = '.'
        self.open_files_list = []

        self.setAttribute(Qt.WA_DeleteOnClose)
        #self.setMinimumSize(500, 300)
        self.resize(700, 500)
        pixmap = QtGui.QPixmap(22, 22)
        pixmap.fill( QtGui.QColor(73, 201, 47) )
        self.setWindowIcon( QtGui.QIcon(pixmap) )
        self.setWindowTitle( ("VisinumVTKviewer - {}").format(self.filename) ) 

        self.dataTree = TreeWidget(self)
        self.vtkframe = VtkQtFrame(self)
        ##self.dataTree.rejected.connect(self.dataTreePos)
        ##self.dataTree.hide()

        vsplitter = QSplitter(Qt.Vertical)
        vsplitter.addWidget(self.dataTree)
        vsplitter.addWidget(QTextEdit())
        hsplitter = QSplitter(Qt.Horizontal)
        hsplitter.addWidget(vsplitter)
        hsplitter.addWidget(self.vtkframe)
        self.setCentralWidget(hsplitter)

        
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
        self.quitAct = QAction(
                "&Quit", self, shortcut=QtGui.QKeySequence.Quit,
                statusTip="Quit the application", triggered=self.close)
                
        self.openFileAct = QAction(                                 
                "open file", self, shortcut=QtGui.QKeySequence.Open,
                statusTip="Open a PLY file", triggered=self.openFile)

        self.importFileAct = QAction(                           
                "Import PLY", self, shortcut="i",
                statusTip="Import a PLY file", triggered=self.importFile)

        self.showTreeAct = QAction(                         
                "show tree", self, shortcut="Ctrl+i",
                statusTip="show data tree", triggered=self.showDataTree)

        self.addTriadAct = QAction(               
                "add axes triad", self, shortcut="Ctrl+t",
                statusTip="add axes triad", triggered=self.vtkframe.addAxes)

        self.viewPlanAct = QAction(                    
                "plan view", self, shortcut="1",
                statusTip="view in plan (from above)", triggered=self.vtkframe.viewPlan)

        self.saveStateAct = QAction(                         
                "save", self, shortcut=QtGui.QKeySequence.Save,
                statusTip="save current state", triggered=self.saveState)

    def openFile(self, fpath=None):
        if not fpath:
            fpath = QFileDialog.getOpenFileName(self, 'Open file', 
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
            fpath = QFileDialog.getOpenFileName(self, 'Open file', 
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
            fpath = QFileDialog.getSaveFileName(self, 'specify file to save', 
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

    from PyQt5.QtWidgets import QApplication

    app = QtGui.QApplication(sys.argv)
    app.setStyle("plastique")  
    mainwindow =  visinumVtkViewer()     
    mainwindow.show()
    sys.exit(app.exec_())


