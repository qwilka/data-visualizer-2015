# -*- coding: utf-8
"""
Copyright © 2020 Stephen McEntee
Licensed under the MIT license. 
See LICENSE file for details https://github.com/qwilka/data-visualizer-2015/blob/master/LICENSE
"""
# http://www.widecodes.com/0QygjVePPW/how-to-crop-from-one-image-and-paste-into-another-with-pil.html
# http://www8.mplayerhq.hu/DOCS/HTML/en/menc-feat-enc-images.html
# http://www.mplayerhq.hu/MPlayer/DOCS/HTML/en/menc-feat-mpeg.html
# mplayer -vo png:z=0 201308150151470\@Port.mpg
# ls *.png > filelist.txt
# mencoder mf://@filelist.txt -mf w=768:h=576:fps=25:type=png -ovc lavc -lavcopts vcodec=mpeg4:mbd=2:trell -oac copy -o output.avi

from __future__ import print_function
import glob
import os
from PIL import Image

def im_copy_paste(im, x1, y1, x2, y2, ycopyoffset=120):
    x, y, w, h = (x1, y1+ycopyoffset, x2-x1, y2-y1)
    copybox = (x, y, x + w, y + h)
    copyregion = im.crop(copybox)
    x, y, w, h = (x1, y1, x2-x1, y2-y1)
    x, y, w, h = (x1, y1, x2-x1, y2-y1)
    pastebox = (x, y, x + w, y + h)
    im.paste(copyregion, pastebox)

"""ii = Image.open("shot0001.png")
x1, y1 = 35, 26
x2, y2 = 125, 43
ycopyoffset=120
x, y, w, h = (x1, y1+ycopyoffset, x2-x1, y2-y1)
box = (x, y, x + w, y + h)
#box = (70, 70, 30, 30)
region = ii.crop(box)
#ii.close()
#io = Image.open("shot0001a.png")
x, y, w, h = (x1, y1, x2-x1, y2-y1)
box = (x, y, x + w, y + h)
#io.paste(region, box)
#io.save("output.png")
#io.close()"""

def cover_overlay(image_filename):
    ii = Image.open(image_filename)
    im_copy_paste(ii, 35, 26, 125, 43, ycopyoffset=120)
    im_copy_paste(ii, 34, 47, 112, 62, ycopyoffset=120)    # heading
    im_copy_paste(ii, 249, 28, 308, 41, ycopyoffset=120)   # UTC
    im_copy_paste(ii, 476, 27, 522, 44, ycopyoffset=120)   # E
    im_copy_paste(ii, 646, 27, 701, 43, ycopyoffset=120)   # N
    im_copy_paste(ii, 519, 49, 553, 63, ycopyoffset=120)   # depth
    im_copy_paste(ii, 33, 88, 650, 102, ycopyoffset=130)   # task
    im_copy_paste(ii, 595, 48, 714, 62, ycopyoffset=130)   # KP
    im_copy_paste(ii, 623, 68, 726, 82, ycopyoffset=140)   # DCC
    im_copy_paste(ii, 308, 68, 421, 81, ycopyoffset=130)   # CP
    im_copy_paste(ii, 35, 69, 201, 81, ycopyoffset=120)   # location
    im_copy_paste(ii, 35, 109, 76, 121, ycopyoffset=90)   # tag
    im_copy_paste(ii, 80, 109, 178, 122, ycopyoffset=87)   # tag no
    im_copy_paste(ii, 663, 88, 753, 103, ycopyoffset=90)   # ID
    im_copy_paste(ii, 50, 530, 136, 545, ycopyoffset=20) # vessel cpy
    im_copy_paste(ii, 150, 530, 319, 545, ycopyoffset=20) # vessel name
    im_copy_paste(ii, 622, 528, 724, 541, ycopyoffset=20) # dive no
    im_copy_paste(ii, 625, 508, 668, 525, ycopyoffset=40) # ROV id
    im_copy_paste(ii, 682, 509, 710, 525, ycopyoffset=40) # ROV id no
    ii.save("temp_output_image.png")
    ii.close()
    os.rename("temp_output_image.png", image_filename)

filelist = glob.glob('*.png')
total_no_files = len(filelist)

for jj, imagename in enumerate(filelist):
    print("processing file {} {:>8d}/{}".format(imagename, jj+1, total_no_files))
    cover_overlay(imagename)
