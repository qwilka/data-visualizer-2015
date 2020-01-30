from __future__ import division

import os
import csv
import inspect
import math
from tempfile import NamedTemporaryFile
import subprocess
import sys
import zipfile

#import numpy as np
import xlrd
import vtk

#sys.path.insert(0, 'C:/Users/mcens0/Documents/data/develop/python/misc')
from misc.miscfunclib import is_number


def XL_to_pipeXYZ(XLfile, wsname, 
                         Xcol, Ycol, Zcol, KPcol, 
             data_row_1st, data_row_last=None,
             Xshift=0, Yshift=0, Zshift=0, Zfactor=1.0, 
             KP_bounds=None, OPfile=None, OPsep=",", dataname=None, OPdir=None):
    """
    XLSfile name of Excel file containing 5-point data
    wsname 
    Xcol, Ycol, Zcol column number in XLSfile containing x, y, z data respectively. NOTE: first column (A) is 1.
    KPcol column number in XLSfile containing KP data. NOTE: first column (A) is 1.
    start_row row number for first data point (1-based)
    end_row  row number for last data point. DEFAULT: read data to the end of the worksheet.
    KP_bounds tuple specifying KP boundary values (KPstart, KPend). This will over-ride start_row and end_row. Data needs to be in ascending order 
    """
    if not OPdir:
        # http://stackoverflow.com/a/6628348 
        # http://stackoverflow.com/questions/7150998/where-is-module-being-imported-from
        # http://doughellmann.com/2012/04/determining-the-name-of-a-process-from-python-2.html
        OPdir = os.path.dirname(os.path.realpath(inspect.stack()[1][1]))

    wb = xlrd.open_workbook(XLfile, on_demand=True)
    ws = wb.sheet_by_name(wsname)

    # re-aligning column indices from Excel form (1-based) to xlrd form (0-based)
    Xidx = Xcol - 1   
    Yidx = Ycol - 1
    Zidx = Zcol - 1
    KPidx = KPcol - 1
    data_row_1st_idx = data_row_1st - 1
    if not data_row_last:
        data_row_last = ws.nrows
    data_row_last_idx = data_row_last - 1
    if not dataname:
        dataname = wsname

    if KP_bounds:
        KPupper_min = KPlower_min = 1e6
        for ii in range(ws.nrows):
            aa = ws.cell(ii, KPidx).value
            if is_number(aa):
                if abs(aa-KP_bounds[0]) < KPlower_min:
                    data_row_1st_idx = ii
                    KPlower_min = abs(aa-KP_bounds[0])
                if abs(aa-KP_bounds[1]) < KPupper_min:
                    data_row_last_idx = ii
                    KPupper_min = abs(aa-KP_bounds[1])
        if data_row_1st_idx > data_row_last_idx:
            data_row_1st_idx, data_row_last_idx = data_row_last_idx, data_row_1st_idx            
   
    if OPfile:
        OPfileh = open(OPfile, "wt")
    else:
        OPfileh = NamedTemporaryFile(mode='w+t', suffix=".pipe.xyz", 
                                     prefix=dataname, delete=False, dir=OPdir)

    for ii in range(data_row_1st_idx, data_row_last_idx+1):
        X = ws.cell(ii, Xidx).value
        Y = ws.cell(ii, Yidx).value
        Z = ws.cell(ii, Zidx).value
        if not is_number(X) or not is_number(Y) or not is_number(Z):
            continue
        if ii in (data_row_1st_idx, data_row_last_idx):
            print("row{} KP{:.3f} E{} N{} depth{}".format(ii+1, 
                  ws.cell(ii, KPidx).value, X, Y, Z) )
        X = X + Xshift
        Y = Y + Yshift
        Z = Z*Zfactor + Zshift
        OPfileh.write("{0:.3f}{sep}{1:.3f}{sep}{2:.3f}\n".format(X, Y, Z, sep=OPsep))
    
    OPfileh.close()
    wb.unload_sheet(wsname)
    return OPfileh.name


def pipeXYZ_to_PLY(XYZfile, OD, OPfile=None, tubenumsides=20, colour=None):
    if not OPfile:
        filename, fileext = os.path.splitext(XYZfile)
        OPfile = filename + ".ply"
    if not colour:
        colour = (255, 255, 0)
    reader = vtk.vtkSimplePointsReader()
    reader.SetFileName(XYZfile)
    print("Creating {} using pipe XYZ data {}".format(OPfile, reader.GetFileName()) )
    reader.Update()
    polydata_points = reader.GetOutput() # vtkPolyData
    num_points = polydata_points.GetNumberOfPoints()
    
    cellarray = vtk.vtkCellArray()
    cellarray.InsertNextCell(num_points)
    for ii in range(num_points):
        cellarray.InsertCellPoint(ii)
    
    polydata_points.SetLines(cellarray) 
    
    splinefilter = vtk.vtkSplineFilter()
    if vtk.VTK_MAJOR_VERSION <= 5:
        splinefilter.SetInput(polydata_points)
    else:
        splinefilter.SetInputData(polydata_points)
    splinefilter.SetNumberOfSubdivisions(5*num_points)
    splinefilter.Update()
    
    tubefilter = vtk.vtkTubeFilter()
    tubefilter.SetRadius(OD/2)
    tubefilter.SetNumberOfSides(tubenumsides)
    tubefilter.SidesShareVerticesOn()
    tubefilter.SetOnRatio(1)
    tubefilter.UseDefaultNormalOn()
    tubefilter.SetInputConnection(splinefilter.GetOutputPort())
    tubefilter.Update()
    
    trianglefilter = vtk.vtkTriangleFilter()
    trianglefilter.SetInputConnection(tubefilter.GetOutputPort())
    
    plywriter = vtk.vtkPLYWriter()
    plywriter.SetInputConnection(trianglefilter.GetOutputPort())
    plywriter.SetFileName(OPfile)
    plywriter.SetFileTypeToBinary()
    plywriter.SetColorModeToUniformColor()
    plywriter.SetColor(*colour)
    plywriter.Write()


def seabedXYZ_to_PLY(XYZfile, OPfile=None, alpha=1.0):
    if not OPfile:
        filename, fileext = os.path.splitext(XYZfile)
        OPfile = filename + ".ply"
    reader = vtk.vtkSimplePointsReader()
    reader.SetFileName(XYZfile)
    print("Creating {} using seabed XYZ data {}".format(OPfile, reader.GetFileName()) )
    reader.Update()
    points = reader.GetOutput()
    delaunay = vtk.vtkDelaunay2D()
    if vtk.VTK_MAJOR_VERSION <= 5:
        delaunay.SetInput(points)
    else:
        delaunay.SetInputData(points)
    delaunay.Update()
    delaunay.SetAlpha(alpha)
    plywriter = vtk.vtkPLYWriter()
    plywriter.SetFileName(OPfile)
    plywriter.SetInputConnection( delaunay.GetOutputPort() )
    plywriter.Write()


def seabedXYZ_to_PLY2(XYZfile, XYZsep=" ", OPfile=None, alpha=1.0, 
                      HaveHeaders=False, NumericColumns=True):
    # alternative procedure using vtkDelimitedTextReader
    # produces poor visualisation, pronounced rows/strips in mesh
    # seems to be a cell connectivity problem, successive rows change connectivity
    # see wireframe model
    if not OPfile:
        filename, fileext = os.path.splitext(XYZfile)
        OPfile = filename + ".ply"
    reader = vtk.vtkDelimitedTextReader()
    reader.SetFileName(XYZfile)
    reader.SetFieldDelimiterCharacters(XYZsep)
    reader.SetHaveHeaders(HaveHeaders)
    reader.SetDetectNumericColumns(NumericColumns)
    print("Creating {} using seabed XYZ data {}".format(OPfile, reader.GetFileName()) )
    reader.Update()    
    polyData = vtk.vtkTableToPolyData()
    polyData.SetInput(reader.GetOutput() )
    polyData.SetXColumnIndex(0)
    polyData.SetYColumnIndex(1)
    polyData.SetZColumnIndex(2)
    #polyData.SetPreserveCoordinateColumnsAsDataArrays(True)
    polyData.SetOutput( vtk.vtkPolyData() ) # need this to ensure output is a vtkDataObject
    polyData.Update()    
    delaunay = vtk.vtkDelaunay2D()
    # NOTE if not using polyData.SetOutput( vtk.vtkPolyData() )
    # need to use polyData.GetOutput() to produce a vtkPolyData object
    # avoids TypeError: argument 1: method requires a vtkDataObject, a vtkTableToPolyData was provided.
    #delaunay.SetInput( polyData.GetOutput() )
    delaunay.SetInputConnection( polyData.GetOutputPort() )
    delaunay.SetAlpha(alpha)
    #delaunay.SetTolerance(1.e-3)
    delaunay.Update()
    plywriter = vtk.vtkPLYWriter()
    plywriter.SetFileName(OPfile)
    plywriter.SetInputConnection( delaunay.GetOutputPort() )
    plywriter.Write()


def bbox_from_KP_in_XL(XLfile, wsname, Ecol, Ncol, KPcol, 
                       data_row_1st, data_row_last=None, KP_bounds=None,
                       Eextend=0, Nextend=0):
    """
    return bounding box coordinates from 5-point file Excel
    """
    print(KP_bounds)
    wb = xlrd.open_workbook(XLfile, on_demand=True)  # on_demand=True 
    ws = wb.sheet_by_name(wsname)

    Eidx = Ecol - 1   
    Nidx = Ncol - 1
    KPidx = KPcol - 1
    data_row_1st_idx = data_row_1st - 1
    if not data_row_last:
        data_row_last = ws.nrows
    data_row_last_idx = data_row_last - 1

    if KP_bounds:
        KPupper_min = KPlower_min = 1e6
        for ii in range(ws.nrows):
            aa = ws.cell(ii, KPidx).value
            if is_number(aa):
                if abs(aa-KP_bounds[0]) < KPlower_min:
                    data_row_1st_idx = ii
                    KPlower_min = abs(aa-KP_bounds[0])
                if abs(aa-KP_bounds[1]) < KPupper_min:
                    data_row_last_idx = ii
                    KPupper_min = abs(aa-KP_bounds[1])
        if data_row_1st_idx > data_row_last_idx:
            data_row_1st_idx, data_row_last_idx = data_row_last_idx, data_row_1st_idx            

    Emax = Emin = ws.cell(data_row_1st_idx, Eidx).value
    Nmax = Nmin = ws.cell(data_row_1st_idx, Nidx).value
    for ii in range(data_row_1st_idx+1, data_row_last_idx+1):
        E = ws.cell(ii, Eidx).value
        N = ws.cell(ii, Nidx).value
        if not is_number(E) or not is_number(N):
            continue
        if E < Emin: Emin = E
        if E > Emax: Emax = E
        if N < Nmin: Nmin = N
        if N > Nmax: Nmax = N

    # Extend bounding box.  Calculate the centre of the box first. 
    if Eextend or Nextend:  
        Ecentre = (Emin + Emax)/2
        Ncentre = (Nmin + Nmax)/2
        Emin = Emin + math.copysign(Eextend, Emin - Ecentre)
        Nmin = Nmin + math.copysign(Nextend, Nmin - Ncentre)
        Emax = Emax + math.copysign(Eextend, Emax - Ecentre)
        Nmax = Nmax + math.copysign(Nextend, Nmax - Ncentre)
    
    return [[Emin, Nmin], [Emax, Nmax] ]


def segment_XYZ(XYZfiles,  
                 bbox=None, Xcol=1, Ycol=2, Zcol=3,
                data_row_1st=1, 
                Xshift=0, Yshift=0, Zshift=0, Zfactor=1.0,  XYZsep=",",
                OPfile=None, OPsep=",", OPdir=None):
    if not OPdir:
        OPdir = os.path.dirname(os.path.realpath(inspect.stack()[1][1]))
    #if zipname and type(zipname).__name__=="bool":
    #    filename, fileext = os.path.splitext(XYZfile)
    #    zipname = filename + ".zip"
    #if not dataname:
    #    dataname = os.path.basename(os.path.splitext(XYZfile)[0])
    if type(XYZfiles).__name__ != 'list':
        XYZfiles = [XYZfiles]

    Xidx = Xcol - 1   
    Yidx = Ycol - 1
    Zidx = Zcol - 1
    data_row_1st_idx = data_row_1st - 1

    if bbox and len(bbox)==2:
        bbox = [bbox[0], (bbox[1][0], bbox[0][1]), bbox[1], (bbox[0][0], bbox[1][1]) ]
    
    if OPfile:
        OPfileh = open(OPfile, "wt")
    else:
        OPfileh = NamedTemporaryFile(mode='w+t', suffix=".xyz", 
                                     prefix="XYZdata", delete=False, dir=OPdir)

    #if zipname:
    #    ziparc = zipfile.ZipFile(zipname, 'r')

    for XYZf in XYZfiles:
        if type(XYZf).__name__ == 'tuple':
            inziparc = True
            ziparc = zipfile.ZipFile(XYZf[0], 'r')
            XYZh = ziparc.open(XYZf[1], 'r')
        else:
            inziparc = False
            XYZh = open(XYZf, 'r')
        # filter(lambda nl: not(nl.lstrip().startswith("#")), datah) 
        XYZreader = csv.reader( XYZh,  delimiter=XYZsep, 
                                quoting=csv.QUOTE_NONE,
                                 skipinitialspace=True)
        for ii, row in enumerate(XYZreader):
            if ii < data_row_1st_idx:
                continue
            X = float(row[Xidx])
            Y = float(row[Yidx])
            if bbox and not point_in_poly(X, Y, bbox):
                continue
            X = X + Xshift
            Y = Y + Yshift
            Z = float(row[Zidx])*Zfactor + Zshift
            OPfileh.write("{0:.3f}{sep}{1:.3f}{sep}{2:.3f}\n".format(X, Y, Z, sep=OPsep))
        XYZh.close()            
        if inziparc:
            ziparc.close()

    OPfileh.close()
    return OPfileh.name


def segment_XYZ_oldzip(XYZfile, zipname=False, 
                 bbox=None, Xcol=1, Ycol=2, Zcol=3,
                data_row_1st=1, 
                Xshift=0, Yshift=0, Zshift=0, Zfactor=1.0,  XYZsep=",",
                OPfile=None, OPsep=",", OPdir=None):
    if not OPdir:
        OPdir = os.path.dirname(os.path.realpath(inspect.stack()[1][1]))
    if zipname and type(zipname).__name__=="bool":
        filename, fileext = os.path.splitext(XYZfile)
        zipname = filename + ".zip"
    #if not dataname:
    #    dataname = os.path.basename(os.path.splitext(XYZfile)[0])
    if type(XYZfile).__name__ not in ['list', 'tuple']:
        XYZfile = [XYZfile]
    Xidx = Xcol - 1   
    Yidx = Ycol - 1
    Zidx = Zcol - 1
    data_row_1st_idx = data_row_1st - 1

    if bbox and len(bbox)==2:
        bbox = [bbox[0], (bbox[1][0], bbox[0][1]), bbox[1], (bbox[0][0], bbox[1][1]) ]
    
    if OPfile:
        OPfileh = open(OPfile, "wt")
    else:
        OPfileh = NamedTemporaryFile(mode='w+t', suffix=".xyz", 
                                     prefix="XYZdata", delete=False, dir=OPdir)

    if zipname:
        ziparc = zipfile.ZipFile(zipname, 'r')

    for XYZf in XYZfile:
        if zipname:
            XYZh = ziparc.open(XYZf, 'r')
        else:
            XYZh = open(XYZf, 'r')
        # filter(lambda nl: not(nl.lstrip().startswith("#")), datah) 
        XYZreader = csv.reader( XYZh,  delimiter=XYZsep, 
                                quoting=csv.QUOTE_NONE,
                                 skipinitialspace=True)
        for ii, row in enumerate(XYZreader):
            if ii < data_row_1st_idx:
                continue
            X = float(row[Xidx])
            Y = float(row[Yidx])
            if bbox and not point_in_poly(X, Y, bbox):
                continue
            X = X + Xshift
            Y = Y + Yshift
            Z = float(row[Zidx])*Zfactor + Zshift
            OPfileh.write("{0:.3f}{sep}{1:.3f}{sep}{2:.3f}\n".format(X, Y, Z, sep=OPsep))
        XYZh.close()            

    if zipname:
        ziparc.close()

    OPfileh.close()
    return OPfileh.name


def point_in_poly(x,y,poly):
    """
    Determine if a point is inside a given polygon or not
    Polygon is a list of (x,y) pairs. This function
    returns True or False.  The algorithm is called
    the "Ray Casting Method".
    
    code by Joel Lawhead, author of "Learning Geospatial Analysis with Python"
    http://geospatialpython.com/2011/01/point-in-polygon.html
    see also:
    http://en.wikipedia.org/wiki/Point_in_polygon
    http://rosettacode.org/wiki/Ray-casting_algorithm
    """
    n = len(poly)
    inside = False

    p1x,p1y = poly[0]
    for i in range(n+1):
        p2x,p2y = poly[i % n]
        if y > min(p1y,p2y):
            if y <= max(p1y,p2y):
                if x <= max(p1x,p2x):
                    if p1y != p2y:
                        xints = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                    if p1x == p2x or x <= xints:
                        inside = not inside
        p1x,p1y = p2x,p2y

    return inside

# 2015-04-28 -----------------------------------------------------------
def shift_XYZfile(XYZfile,  
                data_row1=1, commentflag="",
                Xshift=0, Yshift=0, Zshift=0, Zfactor=1.0,  XYZsep=",",
                OPfile=None, OPsep=",", OPdir="."):
    if OPdir==".":
        pass
        #OPdir = os.path.dirname(os.path.realpath(inspect.stack()[1][1]))
    if OPfile:
        OPfileh = open(OPfile, "wt")
    else:
        OPfileh = NamedTemporaryFile(mode='w+t', suffix=".xyz", 
                                     prefix="XYZdata", delete=False, dir=OPdir)
    if type(XYZfile).__name__ == 'tuple':
        inziparc = True
        ziparc = zipfile.ZipFile(XYZf[0], 'r')
        XYZh = ziparc.open(XYZf[1], 'r')
    else:
        inziparc = False
        XYZh = open(XYZfile, 'r')
    XYZreader = csv.reader( XYZh,  delimiter=XYZsep, 
                            quoting=csv.QUOTE_NONE,
                             skipinitialspace=True)
    data_row1_idx = data_row1 - 1
    for ii, row in enumerate(XYZreader):
        if ii < data_row1_idx:
            continue
        if commentflag and row[0][0]==commentflag:
            continue
        X = float(row[0]) + Xshift
        Y = float(row[1]) + Yshift
        Z = float(row[2])*Zfactor + Zshift
        OPfileh.write("{0:.3f}{sep}{1:.3f}{sep}{2:.3f}\n".format(X, Y, Z, sep=OPsep))
    XYZh.close()            
    if inziparc:
        ziparc.close()

    OPfileh.close()
    return OPfileh.name

def seabedXYZ_to_PLY_CC(XYZfile, PLYfile=None, MAX_EDGE_LENGTH=None,
            CCexe = "CloudCompare",
            PLY_EXPORT_FMT = None, returncmd=False):
    # warning: CC will over-write existing PLY file named XYZfile.ply
    # todo: check CCexe is in path
    CCoptions =  " -COMPUTE_NORMALS"
    CCoptions += " -NO_TIMESTAMP"
    CCoptions += " -O " + XYZfile  # -SKIP 3 -GLOBAL_SHIFT -430000 -7280000 0
    CCoptions += " -DELAUNAY -AA" #  -AA -MAX_EDGE_LENGTH 0.6
    if MAX_EDGE_LENGTH:
        Coptions +=  " -MAX_EDGE_LENGTH " + str(MAX_EDGE_LENGTH)
    CCoptions += " -M_EXPORT_FMT PLY -PLY_EXPORT_FMT ASCII "   # -PLY_EXPORT_FMT BINARY_LE -PLY_EXPORT_FMT ASCII
    if PLY_EXPORT_FMT:
        Coptions +=  " -PLY_EXPORT_FMT " + str(PLY_EXPORT_FMT)
    CCoptions += " -SAVE_MESHES"
    arglist = [CCexe,]
    arglist.extend(CCoptions.split())
    rtnstr = subprocess.check_output(arglist , 
                          stderr=subprocess.STDOUT,
                          shell=False)
    if PLYfile:
        filename, fileext = os.path.splitext(XYZfile)
        CCPLYfile = filename + ".ply"
        os.rename(CCPLYfile, PLYfile)
    return rtnstr

def segment_line(linelen, target_seglen, len2KPconv=1.e-3, maxret=False):
    """Segment a line equally into a number of sections based on a target line
    segment length. 
    Returns segment length, and number of segments, and list of segment KPs"""
    #  from __future__ import division  # required in Py2 to avoid error if lengths are integers
    if linelen<target_seglen:
        return linelen, 1
    num_segments = int(round(linelen/target_seglen))
    segment_length = linelen/num_segments
    if not maxret:
        return segment_length
    segments_list = []
    KPmax = 0.0
    for ii in range(num_segments):
        KPmin = KPmax
        KPmax = KPmin+segment_length
        segments_list.append( (KPmin*len2KPconv, KPmax*len2KPconv) )
    return segment_length, num_segments, segments_list

