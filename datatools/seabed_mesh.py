import sys
import os

addPythonPath = '/home/develop/Projects/dataApp/develop/python'
if addPythonPath not in sys.path:
    sys.path.insert(0, addPythonPath)
from MBES.MBESlib import segment_line
from MBES.MBESlib import bbox_from_KP_in_XL, segment_XYZ
from MBES.MBESlib import seabedXYZ_to_PLY_CC,  seabedXYZ_to_PLY

filedir = os.path.dirname(os.path.realpath(__file__))
print(filedir)

OD = 0.2731 + (0.3+0.3+9.4+32.0+3.0+33.0+4.0)*2/1000
print("OD = {}".format(OD))
fivepointfile = "18-F-2814 (L21) SKL21 5pt Lisitng.xls"
fivepointwsheet="SKL21"
XYZfiles = ("PAPJ1-SKL21-SKR21.zip", "PAPJ1-SKL21-SKR21.xyz")
Xshift=-430000.
Yshift=-7280000.
Zshift=-OD/2
Zfactor=-1.0

target_segment_len = 500.
line_length = 4179.

PLYprefix = "MBES_L21_"
PLYsuffix = "_2013-02-20_VTK.ply"
    
segment_length, num_segments, segments_list = segment_line(line_length, 
                      target_segment_len, maxret=True)

print("Number of segments= {}, segment length= {}".format(num_segments, segment_length))
for ii, KPs in enumerate(segments_list):
    print("Segment {} KPs = {},{}".format(ii, KPs[0], KPs[1]))
    bbox = bbox_from_KP_in_XL(XLfile=fivepointfile,
                          wsname=fivepointwsheet, Ecol=3, Ncol=4, KPcol=6, 
                          data_row_1st=8, KP_bounds=KPs, 
                          Eextend=10, Nextend=10 )
    print("bounding box= {}".format(bbox))
    tmpXYZfile = segment_XYZ(XYZfiles, 
                             bbox=bbox, 
                    data_row_1st=4, 
                    Xshift=Xshift, Yshift=Yshift, Zshift=0, Zfactor=1.0,
                    XYZsep=" ",
                    OPfile=None, OPsep=" ")
    PLYfilename = PLYprefix + \
     "KP{:d}-KP{:d}".format(int(KPs[0]*1000), int(KPs[1]*1000))  \
                 + PLYsuffix
    print("Making PLY file {}".format(PLYfilename))
    seabedXYZ_to_PLY(tmpXYZfile, 
                   OPfile=PLYfilename,
                   alpha=0.8 )

    os.remove(tmpXYZfile)
    
    






