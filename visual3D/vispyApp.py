# -*- coding: utf-8
"""
Copyright © 2020 Stephen McEntee
Licensed under the MIT license. 
See LICENSE file for details https://github.com/qwilka/data-visualizer-2015/blob/master/LICENSE
"""

import sys
import os
import json
import numpy as np

try:
    from sip import setapi
    setapi('QDate', 2)
    setapi('QDateTime', 2)
    setapi('QString', 2)
    setapi('QtextStream', 2)
    setapi('Qtime', 2)
    setapi('QUrl', 2)
    setapi('QVariant', 2)
except ImportError:
    pass

vispy_backend = 'pyqt4'    # 'pyqt4' 'pyqt5' 'pyside' 'PyQt4'  'PyQt5'
import vispy.app
qtapp = vispy.app.use_app(vispy_backend) 

"""QtCore = qtapp.backend_module.QtCore 
QtGui = qtapp.backend_module.QtGui 
if vispy_backend.lower() == 'pyqt5':
    QtWidgets = qtapp.backend_module.QtWidgets
else:
    QtWidgets = QtGui"""

from PyQt4 import QtCore
from PyQt4 import QtGui
QtWidgets = QtGui

from tree_widget import TreeWidget
from vispy_frame import VispyCanvas


class VispyApp(QtGui.QMainWindow):
    
    def __init__(self, parent=None, filepath=None):
        super(VispyApp, self).__init__(parent)
        self.parent = parent
        self.filename = filepath
        self.workingdir = '.'
        self.open_files_list = []

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        #self.setMinimumSize(500, 300)
        self.resize(700, 500)
        pixmap = QtGui.QPixmap(22, 22)
        pixmap.fill( QtGui.QColor(73, 201, 47) )
        self.setWindowIcon( QtGui.QIcon(pixmap) )
        self.setWindowTitle( ("VispyViewer - {}").format(self.filename) ) 

        self.dataTree = TreeWidget(self)
        self.vispyframe = VispyCanvas(self)
        #self.vispyframe.create_native()
        #self.vispyframe.native.setParent(self)
        ##self.dataTree.rejected.connect(self.dataTreePos)
        ##self.dataTree.hide()

        vsplitter = QtGui.QSplitter(QtCore.Qt.Vertical)
        vsplitter.addWidget(self.dataTree)
        vsplitter.addWidget(QtGui.QTextEdit())
        hsplitter = QtGui.QSplitter(QtCore.Qt.Horizontal)
        hsplitter.addWidget(vsplitter)
        hsplitter.addWidget(self.vispyframe)
        hsplitter.setStretchFactor(1, 10)
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
        #fileMenu.addAction(self.saveStateAct)
        fileMenu.addSeparator() 
        fileMenu.addAction(self.quitAct)
        #viewMenu = menubar.addMenu('&View')
        #viewMenu.addAction(self.viewPlanAct)
        #viewMenu.addAction(self.showTreeAct)

    def createActions(self):
        self.quitAct = QtGui.QAction(
                "&Quit", self, shortcut=QtGui.QKeySequence.Quit,
                statusTip="Quit the application", triggered=self.close)
                
        self.openFileAct = QtGui.QAction(                                 
                "open file", self, shortcut=QtGui.QKeySequence.Open,
                statusTip="Open a PLY file", triggered=self.openFile)

        self.importFileAct = QtGui.QAction(                           
                "Import obj file", self, shortcut="i",
                statusTip="Import obj file", triggered=self.importFile)

        """self.showTreeAct = QtGui.QAction(                         
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
                statusTip="save current state", triggered=self.saveState)"""

    def openFile(self, fpath=None):
        if not fpath:
            fpath = QtGui.QFileDialog.getOpenFileName(self, 'Open file', 
                    self.workingdir, "JSON (*.json);;All files (*.*)")
            fpath = str(fpath)
            self.workingdir = os.path.dirname(fpath)
        if fpath.upper().endswith(".JSON"):
            self.loadState(fpath)

    def importFile(self, fpath=None):
        self.vispyframe.import_obj(fpath)







        

     


if __name__ == '__main__':
    if True:
        app = QtGui.QApplication(sys.argv)
        app.setStyle("plastique")  
        mainwindow =  VispyApp()     
        mainwindow.show()
        sys.exit(app.exec_())
