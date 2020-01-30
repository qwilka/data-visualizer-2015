"""
Copyright © 2020 Stephen McEntee
Licensed under the MIT license. 
See LICENSE file for details https://github.com/qwilka/data-visualizer-2015/blob/master/LICENSE
"""
# from __future__ import division
# from __future__ import print_function
# #from __future__ import unicode_literals # causes problems for drag/drop when tree contrains unicode characters (pickle problem)
# from future_builtins import *

import sys
import os
import json
import logging
import pprint
#import pickle
from functools import partial


from PyQt5.QtWidgets import ( QMainWindow, QMessageBox, QFileDialog, 
    QDockWidget, QWidget, QVBoxLayout, QItemDelegate, QGroupBox,
    QFormLayout, QLabel, QLineEdit, QSplitter, QScrollArea, QAction)
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5 import QtGui 

import resources_rc
from tree.tree_view import DataTreeFrame
from visual3D.vtkframe import VtkQtFrame
from utilities import make_uuid, make_timestamp, timestamp_to_timestring

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.openfilename = None
        self.workdir = '.'
        self.open_files_list = []

        self.app = QCoreApplication.instance()
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.resize(800, 500)
        pixmap = QtGui.QPixmap(22, 22)
        pixmap.fill( QtGui.QColor(73, 201, 47) )
        self.setWindowIcon( QtGui.QIcon(pixmap) )
        self.setWindowTitle( "{0} v{1} ".format(
          str(self.app.applicationName()), 
          str(self.app.applicationVersion())  ))

        self.datatree = DataTreeFrame(mainwindow=self)    
        self.vtkview = VtkQtFrame()
        #self.datatree.treeview.tree_clicked.connect(self.vtkview.createBoundingBox_UUID)
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
        hsplitter.addWidget(self.vtkview)
        hsplitter.setStretchFactor(1, 10)
        self.setCentralWidget(hsplitter)

        
        self.createActions()
        self.createMenuBar()
        

    def treeview_data_changed(self, newdata):
        model = self.datatree.treeview.model()
        #dict_ = model._rootNode.to_dict()
        #self.vtkview.setText(pprint.pformat(newdata))
        self.propseditor.data_changed(model)
        

    def createMenuBar(self):
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(self.openFileAct) 
        fileMenu.addAction(self.importFileAct)
        fileMenu.addAction(self.saveFileAct) 
        fileMenu.addAction(self.closeFileAct)
        fileMenu.addSeparator() 
        fileMenu.addAction(self.quitAct)
        """viewMenu = menubar.addMenu('&View')
        viewMenu.addAction(self.viewPlanAct)
        viewMenu.addAction(self.showTreeAct)"""

    def createActions(self):
        self.quitAct = QAction(
                "&Quit", self, shortcut="Ctrl+Q",  # shortcut=QtGui.QKeySequence.Quit
                statusTip="Quit the application", triggered=self.close)
                
        self.openFileAct = QAction(                                 
                "open file", self, shortcut=QtGui.QKeySequence.Open,
                statusTip="Open a PLY file", triggered=self.openFile)

        self.importFileAct = QAction(                                 
                "import file", self, 
                statusTip="import a file", triggered=self.importFile)

        self.saveFileAct = QAction(                         
                "save", self, shortcut=QtGui.QKeySequence.Save,
                statusTip="save current state", triggered=self.saveFile)

        self.closeFileAct = QAction(                         
                "close", self, shortcut=QtGui.QKeySequence.Close,
                statusTip="close current file after saving", triggered=self.closeFile)


    def openFile(self, fpath=None, replace=True):
        if not fpath:
            fpath = QFileDialog.getOpenFileName(self, 'Open file', 
                    self.workdir, "JSON (*.json);;All files (*.*)")
            if isinstance(fpath, tuple):  # possible bug in pyside
                fpath = str(fpath[0])
            else:
                fpath = str(fpath)
            self.workdir = os.path.dirname(fpath)
            self.openfilename = fpath
        if os.path.isfile(fpath):
            try:
                with open(fpath, 'r') as jfile:
                    dict_ = json.load(jfile)
            except IOError:
                logger.warning("cannot open JSON file: %s" % fpath)
        else:
            logger.warning("cannot open file %s" % fpath)
            return
        if replace:
            reply = self.closeFile()  
            if reply == QMessageBox.Cancel:
                return
            self.openfilename = fpath
            self.setWindowTitle( ("VisinumVTKviewer - {}").format(
                     os.path.basename(self.openfilename)) )
        self.addTree(dict_, replace)


    def importFile(self, fpath=None):
        if not fpath:
            fpath = QFileDialog.getOpenFileName(self, 'Import file', 
                    self.workdir, "PLY (*.ply);;JSON (*.json);;All files (*.*)")
            if isinstance(fpath, tuple):
                fpath = str(fpath[0])
            else:
                fpath = str(fpath)
            self.workdir = os.path.dirname(fpath)
        if os.path.isfile(fpath):
            filetype = os.path.splitext(fpath)[1].lower()
            if filetype in '.ply':
                self.importPLY(fpath)
            else:
                self.openFile(fpath, replace=False)
        else:
            logger.warning("cannot import file %s" % fpath)
            return
        #self.addTree(dict_)



    def saveFile(self):
        model = self.datatree.treeview.model()
        fpath = self.openfilename
        if not fpath or not os.path.isfile(fpath):
            fpath = QFileDialog.getSaveFileName(self, 'specify file to save', 
                self.workdir, "JSON (*.json);;All files (*.*)")
            logger.debug("saveFile filepath= %s %s" % (str(type(fpath)), fpath) )
            if isinstance(fpath, tuple):
                fpath = str(fpath[0])
            else:
                fpath = str(fpath)
        dict_ = model._rootNode.to_dict()
        with open(fpath, 'w') as jfile:
            json.dump(dict_, jfile)
        self.openfilename = fpath
        self.workdir = os.path.dirname(fpath)
        self.setWindowTitle( ("VisinumVTKviewer - {}").format(
                 os.path.basename(self.openfilename)) )
        if model.dirty:
            model.dirty = False

    def closeFile(self):
        model = self.datatree.treeview.model()
        if model and model.dirty:
            reply = QMessageBox.question(self, 'Message',
                     "There are unsaved changes. " +
                     "Do you want to save the changes, " +
                     "or close and discard the changes?",
                     QMessageBox.Save, QMessageBox.Close)
            if reply == QMessageBox.Cancel:
                return QMessageBox.Cancel
            if reply == QMessageBox.Save:
                self.saveFile()
                model.dirty = False
        self.datatree.treeview.setModel(None)    # setModel(None) setup_empty_tree()
        self.datatree.treeview.setup_empty_tree()        
        self.propseditor.clearData()
        self.vtkview.clearData()
        self.openfilename = None
        self.setWindowTitle( "{0} v{1} ".format(
          str(self.app.applicationName()), 
          str(self.app.applicationVersion())  ))

    def addTree(self, dict_, replace=False):
        treeview = self.datatree.treeview
        #treeview.tree_clicked.connect(self.vtkview.createBoundingBox)
        model = treeview.model()
        #model.dataChanged.connect(self.tree_data_changed)
        #if model and replace:
        if replace:
            #treeview.setup_empty_tree()
            treeview.addTree(dict_, replace=True)
        else:
            treeview.addTree(dict_, replace=False)
        model = treeview.model()
        model.model_updated.connect(self.vtkview.on_model_updated)
        model.item_deleted.connect(self.vtkview.on_item_deleted)
        model.model_updated.emit(dict_)
        treeview.tree_clicked.connect(self.vtkview.createBoundingBox_UUID)
        self.propseditor.setupDataMapper(treeview)    
        #self.vtkview.setText(pprint.pformat(dict_))

    def tree_data_changed(self, dict_):
        print("============Mainwindow tree_data_changed===========")
        #self.vtkview.setText(pprint.pformat(dict_))

    def closeEvent(self, event):
        model = self.datatree.treeview.model()
        if model and model.dirty:
            reply = self.closeFile()
            if reply == QMessageBox.Cancel:
                event.ignore()
        else:
            quit_msg = "Are you sure you want to exit the program?"
            reply = QMessageBox.question(self, 'Message', 
                             quit_msg, QMessageBox.Yes, QMessageBox.No)
        
            if reply == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()

    def importPLY(self, fpath=None):
        if not fpath or not os.path.isfile(fpath):
            fpath=QFileDialog.getOpenFileName(self,'Open PLY','.',"PLY files (*.ply);;All files (*.*)")
        if not fpath:
            return
        #self.vtkview.addPLYactor(fpath)
        #self.vtkview.showScene()
        fname = os.path.split(fpath)[1]
        UUID = make_uuid()
        timestamp = make_timestamp()
        datadict_ = {"name":fname, "fname":fname,"fpath":fpath, 
          "ftype":"PLY", "dtype":"polymesh", "stype":"", "UUID":UUID, 
          "timestamp":timestamp}
        self.addTree(datadict_)  
        self.vtkview.importActor(datadict_)
        self.vtkview.showScene()
 
       
class PropsEditor(QWidget):

    def __init__(self, parent=None):
        super(PropsEditor, self).__init__(parent)
        self._parent = parent
        self.setupLayout()

    def setupLayout(self):
        groupbox = QGroupBox('edit data')
        formlayout = QFormLayout()
        self.label_name = QLabel('name')
        self.lineedit_name = QLineEdit("no data here")
        self.lineedit_name.setObjectName('name')
        formlayout.addRow(self.label_name, self.lineedit_name)
        self.label_ftype = QLabel('file format')
        self.lineedit_ftype = QLineEdit("no data here")
        self.lineedit_ftype.setObjectName('ftype')
        formlayout.addRow(self.label_ftype, self.lineedit_ftype)
        self.label_dtype = QLabel('data type')
        self.lineedit_dtype = QLineEdit("no data here")
        self.lineedit_dtype.setObjectName('dtype')
        formlayout.addRow(self.label_dtype, self.lineedit_dtype)
        self.label_stype = QLabel('structure type')
        self.lineedit_stype = QLineEdit("no data here")
        self.lineedit_stype.setObjectName('stype')
        formlayout.addRow(self.label_stype, self.lineedit_stype)      
        self.label_fpath = QLabel('file path')
        self.lineedit_fpath = QLineEdit("no data here")
        self.lineedit_fpath.setObjectName('fpath')
        formlayout.addRow(self.label_fpath, self.lineedit_fpath)
        self.label_timestamp = QLabel('timestamp')
        self.lineedit_timestamp = QLineEdit("no data here")
        self.lineedit_timestamp.setReadOnly(True)
        self.lineedit_timestamp.setObjectName('timestamp')
        formlayout.addRow(self.label_timestamp, self.lineedit_timestamp)
        self.label_UUID = QLabel('UUID')
        self.lineedit_UUID = QLineEdit("no data here")
        self.lineedit_UUID.setObjectName('UUID')
        formlayout.addRow(self.label_UUID, self.lineedit_UUID)
        self.label_datadict = QLabel('data dictionary')
        self.lineedit_datadict = QLineEdit("no data here")
        self.lineedit_datadict.setObjectName("datadict")
        formlayout.addRow(self.label_datadict, self.lineedit_datadict)
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
        self._dataMapper.setItemDelegate(PropsEditDelegate(self))
        #self._dataMapper.addMapping(self.label1, 0)
        self._dataMapper.addMapping(self.lineedit_name, 0)
        self._dataMapper.addMapping(self.lineedit_dtype, 1)
        self._dataMapper.addMapping(self.lineedit_ftype, 1)
        self._dataMapper.addMapping(self.lineedit_stype, 1)
        self._dataMapper.addMapping(self.lineedit_fpath, 1)
        self._dataMapper.addMapping(self.lineedit_timestamp, 1)
        self._dataMapper.addMapping(self.lineedit_UUID, 1)
        self._dataMapper.addMapping(self.lineedit_datadict, 1)
        treeview.selectionModel().currentChanged.connect(self.setSelection)
        self.wid.setVisible(True)


    def setSelection(self, current):
        parent = current.parent()
        self._dataMapper.setRootIndex(parent)
        self._dataMapper.setCurrentModelIndex(current) 

    def clearData(self, layout=None):
        if hasattr(self, "_dataMapper"):
            self._dataMapper.clearMapping()
        self.wid.setVisible(False)




class PropsEditDelegate(QItemDelegate):
    #http://www.qtcentre.org/threads/41409-PyQt-QTableView-with-comboBox
    def __init__(self, parent):
        super(PropsEditDelegate, self).__init__(parent)

    def setEditorData(self, editor, idx):
        if editor.objectName() in ['ftype', 'dtype', 'stype', 'fpath', 'UUID', 'timestamp']:
            modeldata = idx.data(Qt.DisplayRole)
            if hasattr(modeldata, "toPyObject"):
                dict_ = idx.data(Qt.DisplayRole).toPyObject()
            else:
                dict_ = eval(modeldata)
            if editor.objectName() in dict_:
                if editor.objectName() == 'timestamp':
                    editor.setText( timestamp_to_timestring(dict_[editor.objectName()]) )
                else:
                    editor.setText(dict_[editor.objectName()])
            else:
                editor.setText(editor.objectName() + " not set")
        else:
            QItemDelegate.setEditorData(self, editor, idx)

    def setModelData(self, editor, model, idx):
        # operate on model here depending on index or call default delegate:
        if editor.objectName() in ['ftype', 'dtype', 'stype', 'fpath', 'UUID']:
            modeldata = idx.data(Qt.DisplayRole)
            if hasattr(modeldata, "toPyObject"):
                dict_ = idx.data(Qt.DisplayRole).toPyObject()
            else:
                dict_ = eval(modeldata)
            newvalue = editor.text()
            dict_[editor.objectName()] = newvalue
            model.setData(idx, str(dict_))
        elif editor.objectName() in ['timestamp']:
            return
        else:
            QItemDelegate.setModelData(self, editor, model, idx)


def icon_solid_fill(R=0, G=0, B=0, size=26):
    pixmap = QtGui.QPixmap(size, size)
    pixmap.fill( QtGui.QColor(R, G, B) )
    return QtGui.QIcon(pixmap)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("Visinum-Data-Visualizer")
    app.setOrganizationName("Qwilka")
    app.setOrganizationDomain("qwilka.github.io")
    app.setStyle("plastique")
    mainwindow = MainWindow()
    mainwindow.show()
    sys.exit(app.exec_())
    
