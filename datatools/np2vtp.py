# -*- coding: utf-8
#from __future__ import division
from __future__ import print_function
#from future_builtins import *

import vtk
import numpy as np
import time
import array

try:
    from vtk.util.numpy_support import numpy_to_vtk
except ImportError:
    numpy_to_vtk = None

start_time = time.time()

ddata = np.load("../../../source_code/example_code/VTK/L21_KP0-KP522_2013-02-20.npz") # L2seabed.npy R53_reduced.npz
pts = ddata["vertices"]
faces = ddata["faces"]

print("load data {}".format(time.time()-start_time))
start_time = time.time()



add_vtkvertices = False
compute_normals = False

#if not compute_normals:
#    norms = ddata["vnormals"]

vtkpoints = vtk.vtkPoints()
if add_vtkvertices:
    vtkvertices = vtk.vtkCellArray()
for i in range(pts.shape[0]):
    id_ = vtkpoints.InsertNextPoint(pts[i,0], pts[i,1], pts[i,2])
    if add_vtkvertices:
        vtkvertices.InsertNextCell(1)
        vtkvertices.InsertCellPoint(id_)

print("make vtkPoints {}".format(time.time()-start_time))
start_time = time.time()



#numpy_to_vtk = None
if numpy_to_vtk:
    # http://public.kitware.com/pipermail/vtkusers/2014-July/084638.html
    numpts = faces.shape[0]
    aa = array.array('l', [])
    for i in range(numpts):
        aa.extend([3, faces[i,0], faces[i,1], faces[i,2]])
    vtktriangles = vtk.vtkCellArray()
    vtktriangles.SetCells(int(len(aa)/4),
    numpy_to_vtk(aa, deep=1, array_type=vtk.VTK_ID_TYPE)
    )
else:
    if True:
        vtktriangles = vtk.vtkCellArray()
        for i in range(faces.shape[0]):
            triangle = vtk.vtkTriangle()
            #triangle.GetPointIds().SetId(0, faces[i,0])
            #triangle.GetPointIds().SetId(1, faces[i,1])
            #triangle.GetPointIds().SetId(2, faces[i,2])
            ids = triangle.GetPointIds()
            #ids.SetNumberOfIds(3)
            ids.SetId(0, faces[i,0])
            ids.SetId(1, faces[i,1])
            ids.SetId(2, faces[i,2])
            vtktriangles.InsertNextCell(triangle)
    else:
        # crashes in VTK6
        # http://www.vtk.org/gitweb?p=VTK.git;a=blob;f=Examples/Infovis/Python/programmable_pipeline.py
        # https://xrunhprof.wordpress.com/2012/02/06/array-exchange-between-vtk-and-python/
        #arr2 = vtk.vtkIdTypeArray.CreateDataArray(vtk.VTK_ID_TYPE) # VTK_UNSIGNED_INT VTK_FLOAT
        arr2 = vtk.vtkIdTypeArray()
        numpts = faces.shape[0]
        aa = array.array('l', [])
        for i in range(numpts):
            aa.extend([3, faces[i,0], faces[i,1], faces[i,2]])
        arr2.SetVoidArray(aa, len(aa), 1)
        vtktriangles = vtk.vtkCellArray()
        vtktriangles.SetCells(int(len(aa)/4), arr2)


print("make triangles {}".format(time.time()-start_time))
start_time = time.time()
print("vtktriangles size {}, cells {}".format(vtktriangles.GetSize(), vtktriangles.GetNumberOfCells()) )

polydata = vtk.vtkPolyData()
polydata.SetPoints(vtkpoints)
polydata.SetPolys(vtktriangles)
del vtktriangles

if add_vtkvertices:
    polydata.SetVerts(vtkvertices)

print("make polydata {}".format(time.time()-start_time))
start_time = time.time()

if compute_normals:
    polydata_normals = vtk.vtkPolyDataNormals()
    polydata_normals.SetInputData(polydata)
    polydata_normals.ComputePointNormalsOn()
    polydata_normals.ComputeCellNormalsOff()
    polydata_normals.ConsistencyOn()
    """ http://www.vtk.org/Wiki/VTK/Examples/Cxx/PolyData/PolyDataExtractNormals
    Optional settings
        normalGenerator->SetFeatureAngle(0.1);
        normalGenerator->SetSplitting(1);
        normalGenerator->SetConsistency(0);
        normalGenerator->SetAutoOrientNormals(0);
        normalGenerator->SetComputePointNormals(1);
        normalGenerator->SetComputeCellNormals(0);
        normalGenerator->SetFlipNormals(0);
        normalGenerator->SetNonManifoldTraversal(1);
    """
    polydata_normals.Update()
    del polydata
    polydata = polydata_normals.GetOutput()
elif "vnormals" in ddata:
    norms = ddata["vnormals"]
    # http://www.vtk.org/Wiki/VTK/Examples/Cxx/PolyData/PolyDataPointNormals
    arr = vtk.vtkDataArray.CreateDataArray(vtk.VTK_FLOAT)  # VTL_DOUBLE
    arr.SetNumberOfComponents(3)
    numpts = polydata.GetNumberOfPoints()
    arr.SetNumberOfTuples(numpts)
    for i in range(numpts):
        arr.SetTuple(i, norms[i])
    polydata.GetPointData().SetNormals(arr)

print("make normals {}".format(time.time()-start_time))
start_time = time.time()

writer = vtk.vtkXMLPolyDataWriter()
writer.SetFileName("../../../source_code/example_code/VTK/testmesh.vtp")
#writer.SetDataModeToBinary()
#print("file ext:   ",writer.GetDefaultFileExtension())
#writer.SetCompressorTypeToZLib()
writer.SetInputData(polydata)
writer.Write()

print("write polydata file {}".format(time.time()-start_time))
start_time = time.time()
