import sys
import os

addPythonPath = '/home/develop/Projects/dataApp/develop/python'
if addPythonPath not in sys.path:
    sys.path.insert(0, addPythonPath)
from MBES.MBESlib import segment_line
from MBES.MBESlib import XL_to_pipeXYZ, pipeXYZ_to_PLY

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

PLYprefix = "5pt_L21_"
PLYsuffix = "_2013-02-20.ply"
    
segment_length, num_segments, segments_list = segment_line(line_length, 
                      target_segment_len, maxret=True)

print("Number of segments= {}, segment length= {}".format(num_segments, segment_length))
for ii, KPs in enumerate(segments_list):
    print("Segment {} KPs = {},{}".format(ii, KPs[0], KPs[1]))

    tmpXYZfile = XL_to_pipeXYZ(XLfile=fivepointfile, 
                                wsname=fivepointwsheet, Xcol=3, Ycol=4, Zcol=7, KPcol=6,
                                data_row_1st=8, data_row_last=None,
                                Xshift=Xshift, Yshift=Yshift, Zshift=Zshift, Zfactor=Zfactor,
                                KP_bounds=KPs, 
                                OPsep=" "  )
    PLYfilename = PLYprefix + \
     "KP{:d}-KP{:d}".format(int(KPs[0]*1000), int(KPs[1]*1000))  \
                 + PLYsuffix
    print("Making PLY file {}".format(PLYfilename))
    pipeXYZ_to_PLY(tmpXYZfile, 
                   OD = OD, 
                   OPfile=PLYfilename,
                   colour=(204, 204, 255))
    os.remove(tmpXYZfile)


    
    






