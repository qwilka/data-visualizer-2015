

import sys
import os
import json
import pprint
#import pickle
#from functools import partial


from PyQt5.QtWidgets import (QMainWindow, QWidget, QTextEdit, QGroupBox, 
    QFormLayout, QLabel, QLineEdit, QScrollArea, QVBoxLayout, QSplitter,
    QAction, QFileDialog)
from PyQt5 import QtGui 
from PyQt5.QtCore import Qt   #, QCoreApplication

from tree.tree_view import DataTreeFrame


class PropsEditor(QWidget):

    def __init__(self, parent=None):
        super(PropsEditor, self).__init__(parent)
        self._parent = parent
        self.setupLayout()

    def setupLayout(self):
        groupbox = QGroupBox('edit data')
        formlayout = QFormLayout()
        self.label1 = QLabel('item data')
        self.lineedit1 = QLineEdit("no data here")
        formlayout.addRow(self.label1, self.lineedit1)
        groupbox.setLayout(formlayout)
        scroll = QScrollArea()
        scroll.setWidget(groupbox)
        scroll.setWidgetResizable(True)
        #scroll.setFixedHeight(400)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)
        self.setLayout(layout)
        self.wid = scroll
        self.wid.setVisible(False)
           

    def setupDataMapper(self, treeview):
        self._dataMapper = treeview.dataMapper
        #self._dataMapper.addMapping(self.label1, 0)
        self._dataMapper.addMapping(self.lineedit1, 1)
        treeview.selectionModel().currentChanged.connect(self.setSelection)
        self.wid.setVisible(True)


    def setSelection(self, current):
        parent = current.parent()
        self._dataMapper.setRootIndex(parent)
        self._dataMapper.setCurrentModelIndex(current) 

    def clearData(self, layout=None):
        self._dataMapper.clearMapping()
        self.wid.setVisible(False)
        """if not layout:
            layout = self.layout()
        while layout.count():
            child = layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()
            elif child.layout() is not None:
                self.clearLayout(child.layout())"""


class MainWindow(QMainWindow):
    
    def __init__(self, parent=None, data=None):
        super(MainWindow, self).__init__(parent)
        self.parent = parent
        self.openfilename = None
        self.workingdir = '.'
        self.open_files_list = []

        self.setAttribute(Qt.WA_DeleteOnClose)
        #self.setMinimumSize(500, 300)
        self.resize(700, 500)
        pixmap = QtGui.QPixmap(22, 22)
        pixmap.fill( QtGui.QColor(73, 201, 47) )
        self.setWindowIcon( QtGui.QIcon(pixmap) )
        self.setWindowTitle( ("DictEd - {}").format(self.openfilename) ) 

        self.datatree = DataTreeFrame(mainwindow=self)    
        self.viewframe = QTextEdit()
        self.propseditor = PropsEditor(self)
        ##self.dataTree.rejected.connect(self.dataTreePos)
        ##self.dataTree.hide()

        vsplitter = QSplitter(Qt.Vertical)
        vsplitter.addWidget(self.datatree)
        vsplitter.addWidget(self.propseditor)
        vsplitter.setSizes ([250, 250])
        vsplitter.setStretchFactor(1, 1)
        hsplitter = QSplitter(Qt.Horizontal)
        hsplitter.addWidget(vsplitter)
        hsplitter.addWidget(self.viewframe)
        hsplitter.setStretchFactor(1, 10)
        self.setCentralWidget(hsplitter)

        
        self.createActions()
        self.createMenuBar()
        if data:
            self.addTree(data)
        # else:
        #     self.addTree({})
        

    def treeview_data_changed(self, newdata):
        model = self.datatree.treeview.model()
        #dict_ = model._rootNode.to_dict()
        self.viewframe.setText(pprint.pformat(newdata))
        self.propseditor.data_changed(model)
        

    def createMenuBar(self):
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(self.openFileAct) 
        fileMenu.addAction(self.saveFileAct) 
        fileMenu.addAction(self.closeFileAct)
        fileMenu.addSeparator() 
        fileMenu.addAction(self.quitAct)
        """viewMenu = menubar.addMenu('&View')
        viewMenu.addAction(self.viewPlanAct)
        viewMenu.addAction(self.showTreeAct)"""

    def createActions(self):
        self.quitAct = QAction(
                "&Quit", self, shortcut=QtGui.QKeySequence.Quit,
                statusTip="Quit the application", triggered=self.close)
                
        self.openFileAct = QAction(                                 
                "open file", self, shortcut=QtGui.QKeySequence.Open,
                statusTip="Open a PLY file", triggered=self.openFile)

        self.saveFileAct = QAction(                         
                "save", self, shortcut=QtGui.QKeySequence.Save,
                statusTip="save current state", triggered=self.saveFile)

        self.closeFileAct = QAction(                         
                "close", self, shortcut=QtGui.QKeySequence.Close,
                statusTip="close current file after saving", triggered=self.closeFile)


    def openFile(self, fpath=None):
        if not fpath:
            fpath = QFileDialog.getOpenFileName(self, 'Open file', 
                    self.workingdir, "JSON (*.json);;All files (*.*)")
            if isinstance(fpath, tuple):  # possible bug in pyside
                fpath = str(fpath[0])
            else:
                fpath = str(fpath)
            self.workingdir = os.path.dirname(fpath)
        if os.path.isfile(fpath):
            with open(fpath, 'r') as jfile:
                dict_ = json.load(jfile)
            if not self.openfilename:
                self.openfilename = fpath
                self.setWindowTitle( ("VisinumVTKviewer - {}").format(
                         os.path.basename(self.openfilename)) )
        else:
            print("Warning cannot open file {}".format(fpath))
            return
        self.addTree(dict_)


    def saveFile(self):
        model = self.datatree.treeview.model()
        filename = self.openfilename
        if not filename or not os.path.isfile(filename):
            fpath = QFileDialog.getSaveFileName(self, 'specify file to save', 
                self.workingdir, "JSON (*.json);;All files (*.*)")
            print(type(fpath), fpath)
            if not os.path.isdir(os.path.dirname(fpath[0])):
                return False
            if isinstance(fpath, tuple):
                fpath = str(fpath[0])
            else:
                fpath = str(fpath)
            filename = fpath
            self.workingdir = os.path.dirname(fpath)
        dict_ = model._rootNode.to_dict()
        print("dict_=", dict_)
        print(filename)
        with open(filename, 'w') as jfile:
            json.dump(dict_, jfile)

    def closeFile(self):
        self.saveFile()
        self.datatree.treeview.setModel(None)
        self.viewframe.clear()
        self.propseditor.clearData()
        self.openfilename = None
        self.setWindowTitle( ("DictEd - {}").format(self.openfilename) )

    def addTree(self, dict_):
        treeview = self.datatree.treeview
        model = treeview.model()
        #model.dataChanged.connect(self.tree_data_changed)
        treeview.addTree(dict_)
        self.propseditor.setupDataMapper(treeview)
        self.viewframe.setText(pprint.pformat(dict_))

    def tree_data_changed(self, dict_):
        self.viewframe.setText(pprint.pformat(dict_))
        
        


if __name__ == '__main__':
    dict_ = {'First name': 'Maximus',
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

    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    app.setStyle("plastique")  
    mainwindow =  MainWindow(data=dtree3) 
    #mainwindow =  MainWindow()    
    mainwindow.show()
    #treeNode = treenode_from_dict(dict_)
    ##treeNode = make_listdict_tree(dtree2)
    ##model = TreeModel(treeNode)
    ##mainwindow.dataTree.treeWidget.setModel(model)
    #mainwindow.dataTree.addTree(dtree2)
    #mainwindow.datatree.treeview.addTree(dtree4)
    ##print(treeNode.to_dict())
    # http://stackoverflow.com/questions/28092837/how-to-control-other-widgets-with-an-qabstracttablemodel-model
    #model.dataChanged.connect(mainwindow.data_changed)
    sys.exit(app.exec_())
    


