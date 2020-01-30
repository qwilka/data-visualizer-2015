"""
Copyright © 2020 Stephen McEntee
Licensed under the MIT license. 
See LICENSE file for details https://github.com/qwilka/data-visualizer-2015/blob/master/LICENSE
"""
import copy
import sys
import os
import json
import logging

# PS = False

# if PS:
#     from PySide import QtCore
#     from PySide import QtGui
#     from QVTKRenderWindowInteractor_PS import QVTKRenderWindowInteractor
# else:
#     import sip    # http://cyrille.rossant.net/making-pyqt4-pyside-and-ipython-work-together/
#     sip.setapi('QDate', 2)
#     sip.setapi('QDateTime', 2)
#     sip.setapi('QString', 2)
#     sip.setapi('QtextStream', 2)
#     sip.setapi('Qtime', 2)
#     sip.setapi('QUrl', 2)
#     sip.setapi('QVariant', 2)
#     from PyQt4 import QtCore
#     from PyQt4 import QtGui
#     from vtk.qt4.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy, QAction
from PyQt5.QtCore import pyqtSlot, QTimer

import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import numpy as np

#from ..tree.nodes import traverse_tree_yield_data
from tree.nodes import traverse_tree_yield_data

logger = logging.getLogger(__name__)


class VtkQtFrame(QWidget):   # QWidget   QtGui.QFrame
    #keyPressed = QtCore.pyqtSignal()
    #http://www.paraview.org/Wiki/VTK/Examples/Python/Widgets/EmbedPyQt   Why use a QFrame to embed vtk? 
    def __init__(self, parent=None):
        super().__init__(parent)
        self._actors = {}
        #self._state = {"_childs":[]}
        

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
    
        self.ren = vtk.vtkRenderer()   
        self.ren.SetBackground(0.75, 0.6, 0.8)
        self.ren.SetViewport( 0, 0, 1, 1)

        self.renWin = vtk.vtkRenderWindow()
        self.renWin.AddRenderer(self.ren)    
        self.iren = QVTKRenderWindowInteractor(self,rw=self.renWin)
        self.iren.SetInteractorStyle(MyInteractorStyle(parent=self))
        self.layout.addWidget(self.iren)

        self.VTKCamera = vtk.vtkCamera()
        self.VTKCamera.SetClippingRange(0.1,1000)
        self.ren.SetActiveCamera(self.VTKCamera)
        
        #self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        #self.customContextMenuRequested.connect(self.openMenu)
        ##self.VTKInteractorStyleSwitch = vtk.vtkInteractorStyleSwitch()
        ##self.VTKInteractorStyleSwitch.SetCurrentStyleToTrackballCamera()
        ##self.iren.SetInteractorStyle(self.VTKInteractorStyleSwitch)
        ##self.iren.SetInteractorStyle(MyInteractorStyle())
        ###self.iren.Initialize()
        ###self.iren.Initialize()
        ##interactorstyle = vtk.vtkInteractorStyleTrackballCamera()
        #self.iren.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())
        #self.iren.AddObserver("MiddleButtonPressEvent", self.middleButtonPressEvent)
        #self.iren.AddObserver("MiddleButtonReleaseEvent", self.middleButtonReleaseEvent)
        #self.iren.AddObserver("KeyPressEvent", self.keyPressEvent)

        #self.picker = vtk.vtkCellPicker()
        #self.picker.AddObserver("EndPickEvent", self.objPicker)
        #self.iren.SetPicker(self.picker)

        # Must wait until Qt event loop starts before rendering VTK window
        # otherwise get a segfault
        # zero timeout, wait until event loop starts
        QTimer.singleShot(0, self.renderVTKwindow)  
        self.iren.GetInteractorStyle().setParent(self) # crazy, but necessary to retain reference to widget in MyInteractorStyle       
        
        self.createActions()


    """def keyPressEvent(self, evt):
        ##super(VtkQtFrame, self).keyPressEvent(evt)
        ##self.keyPressed.emit()
        #self.iren.keyPressEvent(evt)
        #self.keyPressed.emit()
        print(evt)
        if int(evt.modifiers()) == QtCore.Qt.AltModifier:
            if evt.key() == QtCore.Qt.Key_F:
                self.openMenu()
                #msg = QtGui.QMessageBox( QtGui.QMessageBox.Information,
                #    'w00t','You pressed alt+f' )
                #msg.exec_()"""

    def saveState(self):
        pass

    def addPLYactor(self, PLYfilename):
        reader = vtk.vtkPLYReader()
        reader.SetFileName(str(PLYfilename))
        reader.Update()
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(reader.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        self.ren.AddActor(actor)
        #self._actors.append(actor)
        #self._state["_childs"].append({"filepath":PLYfilename, "type":"PLY"})

    def importActor(self, data):
        if data['UUID'] in self._actors:
            logger.warning("import failed, actor %s already in VTKscene" % data['UUID'])
        if 'ftype' in data and data['ftype'].upper() in ('PLY',):
            if data['ftype'].upper() == 'PLY':
                reader = vtk.vtkPLYReader()
            else:
                logger.warning("Error in VTKframe importActor %s" % data['name'])
                return
        else:
            logger.warning("VTKframe cannot import item %s" % data['name'])
            return
        fpath = os.path.normpath(data['fpath'])
        if not os.path.isfile(fpath):
            logger.warning("VTKframe cannot import item %s" % data['name'])
            return  
        reader.SetFileName(fpath)
        reader.Update()
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(reader.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        self.ren.AddActor(actor)    
        #self._actors[data['UUID']] = {'actor':actor, 'fpath':fpath}
        self._actors[data['UUID']] = actor



    def showScene(self):
        self.ren.ResetCamera()
        self.ren.GetRenderWindow().Render()


    def addAxes(self):
        if "axes" in self._actors:
            self.ren.RemoveActor( self._actors["axes"])
            del self._actors["axes"]            
        else:
            axes = vtk.vtkAxesActor()
            self.ren.AddActor(axes)
            self.ren.ResetCamera()
            self.renWin.Render()     
            self._actors["axes"] = axes

    def renderVTKwindow(self):
        self.renWin.Render()  

    def viewPlan(self):
        # http://public.kitware.com/pipermail/vtkusers/2010-May/059972.html
        #ren = self.VTKviewframe.ren
        ren = self.ren
        cam = ren.GetActiveCamera()
        fp = cam.GetFocalPoint()
        p = cam.GetPosition()
        dist = np.sqrt( (p[0]-fp[0])**2 + (p[1]-fp[1])**2 + (p[2]-fp[2])**2 )
        cam.SetPosition(fp[0], fp[1], fp[2]+dist)
        cam.SetViewUp(0.0, 1.0, 0.0)
        ren.ResetCamera()
        ren.GetRenderWindow().Render()

    def objPicker(self, object_, event):
        #selPt = self.picker.GetSelectionPoint()
        pickPos = self.picker.GetPickPosition()
        print("(%.6f, %.6f, %.6f)"%pickPos)
        pickAct = self.picker.GetActor()
        print(pickAct.GetZRange())
        print(pickAct.GetBounds())
        self.setupScalarBar(pickAct)
        #print(pickAct.GetMapper())
        #self.ren.RemoveActor(pickAct)        

    def remove_actor(self, actor_name):
        if actor_name in self._actors:
            self.ren.RemoveActor( self._actors[actor_name] )
            del self._actors[actor_name]
        else:
            logger.warning("VTKframe cannot remove actor %s" % actor_name)

    @pyqtSlot(str)   # http://stackoverflow.com/questions/2585442/sending-custom-pyqt-signals
    def createBoundingBox_UUID(self, UUID):
        if UUID in self._actors:
            self.createBoundingBox(self._actors[UUID], colour=(1.0, 1.0, 0))

    def createBoundingBox(self, actor, colour=None):
        # http://www.vtk.org/Wiki/VTK/Examples/Python/Outline
        # http://stackoverflow.com/questions/28232393/access-vtkactor-construction-object-and-append-new-data
        """if isinstance(actor, vtk.vtkActor):
            _actor = actor
        elif isinstance(actor, str) and actor in self._actors:
            print("createBoundingBox actor is ", self._actors[actor])
            _actor = self._actors[actor]
        else:
            return"""
        if "boundingbox" in self._actors:
            self.remove_actor("boundingbox")    
        mapper = actor.GetMapper()
        source = mapper.GetInputAlgorithm() 
        outline = vtk.vtkOutlineFilter()
        outline.SetInputConnection(source.GetOutputPort())
        # outline.SetInputConnection(source.GetOutputPort())
        #outlineActor.SetMapper(mapper.GetOutputPort())
        bbmapper = vtk.vtkPolyDataMapper()
        bbmapper.SetInputConnection(outline.GetOutputPort())
        bbactor = vtk.vtkActor()
        bbactor.SetMapper(bbmapper)
        if colour:
            bbactor.GetProperty().SetColor(colour)
        #bbactor.SetMapper(outline.GetOutputPort())
        self.ren.AddActor(bbactor)
        self.ren.ResetCamera()
        self.ren.GetRenderWindow().Render()
        self._actors["boundingbox"] = bbactor

    def setupScalarBar(self, actor):
        # https://github.com/nipy/pbrain/blob/master/eegview/grid_manager.py
        # mcc: create a ScalarBarActor to be used in interactor. we need
        # to call SetLookupTable() and give it a pointer to a lookup
        # table used by one of the "actors" in the "scene".

        mapper = actor.GetMapper()
        inp = mapper.GetInput()
        lo, hi = actor.GetZRange()

        roundto  = 5.0
        lo = round(lo/roundto)*roundto
        hi = round(hi/roundto)*roundto
        print(lo, hi)
        elev = vtk.vtkElevationFilter()
        elev.SetInputData(inp)
        elev.SetLowPoint(0, 0, lo)
        elev.SetHighPoint(0, 0, hi)
        #elev.SetScalarRange(lo, hi) ###### scalarbar problems start here 
        #elev.ReleaseDataFlagOn()

        normals = vtk.vtkPolyDataNormals()
        normals.SetInputConnection(elev.GetOutputPort())
        normals.SetFeatureAngle(60)
        normals.ConsistencyOff()
        normals.SplittingOff()
        normals.ReleaseDataFlagOn()

        """lut = vtk.vtkLookupTable()
        lut.SetScaleToLinear()
        lut.SetNumberOfTableValues(10)
        lut.SetTableRange(lo, hi)
        lut.SetValueRange(lo, hi)
        lut.Build()"""
        
        mapper.SetInputConnection(elev.GetOutputPort())
        #mapper.SetScalarModeToUsePointData()
        #mapper.SetLookupTable(lut)
        mapperLUT = mapper.GetLookupTable()
        mapperLUT.SetRange(lo, hi)   # doesn't jhelp
        #mapperLUT.ForceBuild() 
        #mapperLUT.Build()
        #print(dir(mapperLUT))
        #ran = mapperLUT.GetTableRange()
        #print("vtkLookupTable=", ran)

        scalarBar = vtk.vtkScalarBarActor()
        scalarBar.SetLookupTable(mapperLUT)
        #self.scalarBar.SetWidth(0.15)
        #self.scalarBar.SetHeight(0.5)
        scalarBar.SetTitle("depth")
        #scalarBar.SetLabelFormat ("%-#6.f")
        #scalarBar.GetTitleTextProperty().SetColor(1.0,1.0,1.0)
        #scalarBar.SetPosition(0.8,0.2)
        scalarBar.VisibilityOn()    # self.scalarBar.VisibilityOff()
        self.ren.AddActor(scalarBar)
        #scalar_bar_widget = vtk.vtkScalarBarWidget()
        #scalar_bar_widget.SetInteractor(self.iren)
        #scalar_bar_widget.SetScalarBarActor(scalarBar)
        #scalar_bar_widget.On()
        self.ren.ResetCamera()
        self._actors["scalarbar"] = scalarBar

    def createActions(self):
        self.openFileAct = QAction(                                 #QtGui.QIcon(':/resources/application-vnd.ms-powerpoint.svg'),
                "open file", self, shortcut="o",
                statusTip="Open a PLY file", triggered=self.openFile)

        self.addTriadAct = QAction(                                 #QtGui.QIcon(':/resources/application-vnd.ms-powerpoint.svg'),
                "add axes triad", self, shortcut="0",
                statusTip="add axes triad", triggered=self.addAxes)

        self.viewPlanAct = QAction(                                 #QtGui.QIcon(':/resources/application-vnd.ms-powerpoint.svg'),
                "plan view", self, shortcut="1",
                statusTip="view in plan (from above)", triggered=self.viewPlan)

        self.saveStateAct = QAction(                                 #QtGui.QIcon(':/resources/application-vnd.ms-powerpoint.svg'),
                "save", self, shortcut="u",
                statusTip="save current state", triggered=self.saveState)

    def openFile(self):
        fpath = QtGui.QFileDialog.getOpenFileName(self, 'Open file', 
                self.curdir, "PLY files (*.ply);;All files (*.*)")
        self.curdir = os.path.dirname(str(fpath))
        self.showPLY(fpath)
        #self.treeviewpane.getDefaultTree().addFilename(os.path.basename(str(fpath)))
        #self.treeviewpane.getDefaultTree().addFilename(str(fpath))

    def openMenu(self, position=None):
        menu = QtGui.QMenu()
        menu.addAction(self.openFileAct)
        menu.addAction(self.saveStateAct)
        #menu.addAction(self.addTriadAct)
        if position:
            menu.exec_(self.mapToGlobal(position))
        else:
            # http://stackoverflow.com/questions/12041980/properly-positioning-popup-widgets-in-pyqt
            point = self.rect().center()
            global_point = self.mapToGlobal(point)
            menu.exec_(global_point)   # bottomRight() topLeft  self.rect().center()

    def setupDataMapper(self, treeview):
        self._dataMapper = treeview.dataMapper
        self._dataMapper.setItemDelegate(PropsEditDel(self))
        #self._dataMapper.addMapping(self.label1, 0)
        self._dataMapper.addMapping(self.lineedit1, 1)
        self._dataMapper.addMapping(self.lineedit2, 1)
        treeview.selectionModel().currentChanged.connect(self.setSelection)
        self.wid.setVisible(True)


    def setSelection(self, current):
        parent = current.parent()
        self._dataMapper.setRootIndex(parent)
        self._dataMapper.setCurrentModelIndex(current) 


    def clearData(self):
        while self._actors:
            for k in self._actors.keys():
                self.ren.RemoveActor(self._actors.pop(k))
                break
        # for k in self._actors.keys(): # RuntimeError: dictionary changed size during iteration
        #     #if "actor" in self._actors[k]:
        #     #    self.ren.RemoveActor( self._actors[k]["actor"])
        #     self.ren.RemoveActor( self._actors[k] )
        #     del self._actors[k]
        self.viewPlan()
        self.ren.ResetCamera()
        if hasattr(self, "_dataMapper"):
            self._dataMapper.clearMapping()

    def on_model_updated(self, dict_):
        logger.debug("?????????? in VTKframe on_model_updated ???????????? " )
        #print(dict_)
        gener = traverse_tree_yield_data(dict_)
        for d_ in gener:
            if 'UUID' not in d_ or d_['UUID'] in self._actors:
                continue
            if 'ftype' in d_ and d_['ftype'].upper() == 'PLY':
                self.importActor(d_)
        self.showScene()

    def on_item_deleted(self, dict_):
        logger.debug("?????????? in VTKframe on_item_deleted ???????????? " )
        gener = traverse_tree_yield_data(dict_)
        for d_ in gener:
            if 'UUID' not in d_ or d_['UUID'] not in self._actors:
                continue
            elif d_['UUID'] in self._actors:
                self.ren.RemoveActor( self._actors[d_['UUID']])
                del self._actors[d_['UUID']]
        self.showScene()        


class MyInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    # http://www.vtk.org/Wiki/VTK/Examples/Python/Interaction/MouseEvents
    # https://code.google.com/p/vtkpythonext/source/browse/trunk/spare/src/jolly/jolly_vtk/vtkPythonInteractorStyle.py?r=34
    
    def __init__(self, parent=None):
        ###super(MyInteractorStyle, self).__init__()  # blows up
        self.parent = parent # this gets deleted, thus setParent method below
        self.AddObserver("MiddleButtonPressEvent",self.middleButtonPressEvent)
        self.AddObserver("MiddleButtonReleaseEvent",self.middleButtonReleaseEvent)
        self.AddObserver(vtk.vtkCommand.KeyPressEvent, self.keyPressed)  # vtk.vtkCommand.KeyPressEvent = "KeyPressEvent" ?

        picker = vtk.vtkCellPicker()
        picker.AddObserver("EndPickEvent", self.objPicker)
        self.parent.iren.SetPicker(picker)
 
    def setParent(self, parent):
        # something is deleting attributes in this class
        # this is required to retain a reference to the parent widget  
        # http://www.vtk.org/Wiki/VTK/Tutorials/InteractorStyleSubclass
        self.parent = parent
    
    def middleButtonPressEvent(self,obj,event):
        print("Middle Button pressed")
        self.OnMiddleButtonDown()
        return
 
    def middleButtonReleaseEvent(self,obj,event):
        print("Middle Button released")
        self.OnMiddleButtonUp()
        return

    def keyPressed(self, obj, event):
        # works best for single key events, not much good with modifiers
        # For info:
        # pos = interactor.GetEventPosition()   # get mouse position
        #key = self.parent.iren.GetKeyCode() # this works after setParent
        #key = event.key() # does not work because "event" is a string # print(event, type(event))
        #alt = interactor.GetAltKey() # usless does not work
        #ctrl = interactor.GetControlKey()  # works, but cannot be used as a key modifier  
        # keysym = interactor.GetKeySym() # not clear what this is for    
        interactor = self.GetInteractor()
        key = interactor.GetKeyCode()
        if key == "#":
            self.parent.openMenu()
        if key in ["o", "O"]:
            self.parent.openFile()
        if key in ["u", "U"]:
            self.parent.saveState()
        if key == "0":
            self.parent.addAxes()
        if key == "1":
            self.parent.viewPlan()
        if key == "x":
            self.pickertest()
        #if key != '3': # do not want useless "stereo mode"
        #    print("key={}".format(key))
        #    self.OnChar()
        return
 
    def pickertest(self):
        picker = vtk.vtkCellPicker()

    def objPicker(self, object_, event):
        # http://public.kitware.com/pipermail/vtkusers/2007-September/042928.html
        #selPt = self.picker.GetSelectionPoint()
        interactor = self.parent.iren    # self.GetInteractor()
        picker = self.GetInteractor().GetPicker()
        pickPos = picker.GetPickPosition()
        print("(%.6f, %.6f, %.6f)"%pickPos)
        pickAct = picker.GetActor()
        col = pickAct.GetProperty().GetColor()
        print("colour=", col)
        print(pickAct.GetZRange())
        print(pickAct.GetBounds())
        ##self.parent.setupScalarBar(pickAct)
        self.parent.createBoundingBox(pickAct)
        #print(pickAct.GetMapper())
        #self.ren.RemoveActor(pickAct)   


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    visVtkWidg =  VtkQtFrame()     
    visVtkWidg.show()
    sys.exit(app.exec_())
