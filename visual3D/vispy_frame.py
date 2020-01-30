# -*- coding: utf-8
"""
Copyright © 2020 Stephen McEntee
Licensed under the MIT license. 
See LICENSE file for details https://github.com/qwilka/data-visualizer-2015/blob/master/LICENSE
"""


#import pickle
#import dill as pickle
import os
import sys
import numpy as np

try:
    from sip import setapi
    setapi("QVariant", 2)
    setapi("QString", 2)
except ImportError:
    pass


from vispy import scene
import vispy.io
import vispy.geometry
from vispy.geometry.generation import create_sphere
from vispy.color.colormap import get_colormaps
import vispy.app
#from colorsys import hsv_to_rgb


vispy_backend = 'pyqt4'    # 'pyqt4' 'pyqt5' 'pyside' 'PyQt4'  'PyQt5'
qtapp = vispy.app.use_app(vispy_backend) 

from vispy.app.backends import qt_lib
print("qt_lib= ", qt_lib)
import vispy.app.qt as vispyqt

QtCore = qtapp.backend_module.QtCore 
QtGui = qtapp.backend_module.QtGui 
if vispy_backend.lower() == 'pyqt5':
    QtWidgets = qtapp.backend_module.QtWidgets
else:
    QtWidgets = QtGui










class VispyCanvas(vispyqt.QtSceneCanvas):

    def __init__(self, parent=None):
        super(VispyCanvas, self).__init__(parent=parent, bgcolor='navajowhite', 
                                       keys='interactive', app=qtapp )


        #self.create_native()
        #self.native.setParent(parent)
        self.size = 800, 600
        self.view = self.central_widget.add_view()
        self.view.camera = scene.TurntableCamera(up='+z') # scene.ArcballCamera(up='+z')
        self.radius = 2.0
        self.workingdir = None
        self.items_bounds = None



    def import_obj(self, fpath):
        if not fpath:
            fpath = QtGui.QFileDialog.getOpenFileName(self, 'Open file', 
                    self.workingdir, "OBJ (*.obj);;All files (*.*)")
            fpath = str(fpath)
            self.workingdir = os.path.dirname(fpath)
        vertices, tris, norms, texs = vispy.io.read_mesh(fpath)
        np.savez(os.path.splitext(fpath)[0], vertices=vertices, faces=tris, vnormals=norms)
        #vertex_colors = np.random.random(8 * len(vertices))
        #vertex_colors = np.array([hsv_to_rgb(c, 1, 1) for c in vertex_colors])
        meshd = vispy.geometry.MeshData(vertices=vertices, faces=tris)
        bnds = meshd.get_bounds()
        print(bnds)
        if self.items_bounds:
            #for ii, jj in enumerate(self.items_bounds()):
            #    if bnds[ii][0] < jj[0]
            self.items_bounds = bnds
        else:
            self.items_bounds = bnds
        mesh = scene.visuals.Mesh(meshdata=meshd,   # vertex_colors=vertex_colors, 
                                 mode='triangles', shading='smooth',
                                 parent=self.view.scene)
        self.view.add(mesh)
        self.view.camera.set_range(bnds[0], bnds[1])
        #self.view.draw()
        

    def set_data(self, n_levels, cmap):
        self.iso.set_color(cmap)
        cl = np.linspace(-self.radius, self.radius, n_levels + 2)[1:-1]
        self.iso.levels = cl

    def add_object(self, fname, bounds=False):
        ddata = np.load(fname)
        vertices = ddata["vertices"]
        tris = ddata["tris"]
        meshd = vispy.geometry.MeshData(vertices=vertices, faces=tris)
        mesh = scene.visuals.Mesh(meshdata=meshd,   # vertices=vertices, faces=tris, meshdata=meshd,    
                                         color='red', mode='triangles', shading='smooth',
                                         parent=self.view.scene)
        self.view.add(mesh)
        if bounds:
            bb = meshd.get_bounds()
            self.view.camera.set_range(bb[0], bb[1])


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    #appQt = QtGui.QApplication(sys.argv)
    qtapp.create() 
    canvas = VispyCanvas()
    canvas.show()
    #canvas.add_object("/home/develop/Projects/src/source_code/example_code/vispy/L2seabed.npz",True)
    canvas.add_object("/home/develop/Projects/src/source_code/example_code/vispy/L2pipeline.npz",True)
    #appQt.exec_()
    qtapp.run() 
