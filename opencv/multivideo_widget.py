# -*- coding: utf-8
"""
Copyright © 2020 Stephen McEntee
Licensed under the MIT license. 
See LICENSE file for details https://github.com/qwilka/data-visualizer-2015/blob/master/LICENSE
"""
from __future__ import division
import os
import sys
import cv2

from PyQt4 import QtCore
from PyQt4 import QtGui


class OpenCVQImage(QtGui.QImage):
    # https://rafaelbarreto.wordpress.com/2011/08/27/a-pyqt-widget-for-opencv-camera-preview/
    # see also https://matthewshotton.wordpress.com/2011/03/31/python-opencv-iplimage-to-pyqt-qimage/
    def __init__(self, opencvBgrImg):
        depth, nChannels = opencvBgrImg.depth, opencvBgrImg.nChannels
        if depth != cv2.cv.IPL_DEPTH_8U or nChannels != 3:
            raise ValueError("the input image must be 8-bit, 3-channel")
        w, h = cv2.cv.GetSize(opencvBgrImg)
        opencvRgbImg = cv2.cv.CreateImage((w, h), depth, nChannels)
        # it's assumed the image is in BGR format
        cv2.cv.CvtColor(opencvBgrImg, opencvRgbImg, cv2.cv.CV_BGR2RGB)
        self._imgData = opencvRgbImg.tostring()
        super(OpenCVQImage, self).__init__(self._imgData, w, h, \
            QtGui.QImage.Format_RGB888)


class VideoSource(QtCore.QObject):
 
    _DEFAULT_FPS = 25 
    newFrame = QtCore.pyqtSignal(cv2.cv.iplimage)
 
    def __init__(self, vidfile=0, parent=None):
        super(VideoSource, self).__init__(parent)
 
        if isinstance(vidfile, str) and os.path.exists(vidfile):
            self._videoCap = cv2.cv.CaptureFromFile(vidfile)
        else:
            raise AttributeError("Error VideoSource: attribute vidfile not specified correctly")
 
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._queryFrame)
        self._timer.setInterval(1000/self.fps)
        
        # http://stackoverflow.com/questions/11260042/reverse-video-playback-in-opencv
        #cv2.cv.SetCaptureProperty(self._videoCap, cv2.cv.CV_CAP_PROP_POS_FRAMES, 5)
 
        self.paused = False
 
    @QtCore.pyqtSlot()
    def _queryFrame(self):
        #curframe = cv2.cv.GetCaptureProperty(self._videoCap, cv2.cv.CV_CAP_PROP_POS_FRAMES)
        #cv2.cv.SetCaptureProperty(self._videoCap, cv2.cv.CV_CAP_PROP_POS_FRAMES, curframe+10)
        frame = cv2.cv.QueryFrame(self._videoCap)
        if isinstance(frame, cv2.cv.iplimage):
            self.newFrame.emit(frame)
 
    @property
    def paused(self):
        return not self._timer.isActive()
 
    @paused.setter
    def paused(self, p):
        if p:
            self._timer.stop()
        else:
            self._timer.start()
 
    @property
    def frameSize(self):
        #w = self._videoCap.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)
        #h = self._videoCap.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)
        w = cv2.cv.GetCaptureProperty(self._videoCap, \
            cv2.cv.CV_CAP_PROP_FRAME_WIDTH)
        h = cv2.cv.GetCaptureProperty(self._videoCap, \
            cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)
        return int(w), int(h)
 
    @property
    def fps(self):
        #fps = self._videoCap.get(cv2.cv.CV_CAP_PROP_FPS)
        fps = int(cv2.cv.GetCaptureProperty(self._videoCap, cv2.cv.CV_CAP_PROP_FPS))
        if not fps > 0:
            fps = self._DEFAULT_FPS
        return fps


class VideoWidget(QtGui.QWidget):
 
    newFrame = QtCore.pyqtSignal(cv2.cv.iplimage)
 
    def __init__(self, videosource, parent=None, height=None):
        super(VideoWidget, self).__init__(parent)
        self.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
 
        self._frame = None
 
        self._videoSource = videosource
        self._videoSource.newFrame.connect(self._onNewFrame)
 
        w, h = self._videoSource.frameSize
        self.aspectratio = w/h
        if height and isinstance(height, int):
            self.imageheight = height
            self.imagewidth  = height*self.aspectratio
        else:
            self.imageheight = h
            self.imagewidth = w
        ##self.parent().close()
        self.setMinimumSize(100*self.aspectratio, 100)
        self.setContentsMargins(0,0,0,0)
        #self.setMinimumHeight(100)
        #self.resize(self.imagewidth, self.imageheight)  # widget won't resize, maybe needs a layout
        #self.setMaximumSize(w, h)
 
    @QtCore.pyqtSlot(cv2.cv.iplimage)
    def _onNewFrame(self, frame):
        self._frame = cv2.cv.CloneImage(frame)
        self.newFrame.emit(self._frame)
        self.update()
 
    def changeEvent(self, e):
        if e.type() == QtCore.QEvent.EnabledChange:
            if self.isEnabled():
                self._videoSource.newFrame.connect(self._onNewFrame)
            else:
                self._videoSource.newFrame.disconnect(self._onNewFrame)
 
    def paintEvent(self, e):
        if self._frame is None:
            return
        painter = QtGui.QPainter(self)
        qtimage = OpenCVQImage(self._frame)
        w = self.width()
        h = self.height()
        if w/h > self.aspectratio:
            w = h*self.aspectratio
        else:
            h = w/self.aspectratio
        # qtimage.width()
        # qtimage.height()
        qtimage2 = qtimage.scaled(w, h, QtCore.Qt.KeepAspectRatio)  # QtCore.Qt.KeepAspectRatio
        painter.drawImage(QtCore.QPoint(0, 0), qtimage2)

    #def heightForWidth(self, width):   # may need a layout for this to work?
    #    return width/self.aspectratio


class MultiVideoWidget(QtGui.QWidget):
    """ A class for rendering video coming from OpenCV """

    def __init__(self, parent=None, videofiles=None, height=None):
        super(MultiVideoWidget, self).__init__()
        self._videofiles = []
        self._videoSources = []
        self._videoWidgets = []
        self.height = height
        if videofiles:
            if isinstance(videofiles, (list, tuple)):
                self._videofiles.extend(videofiles)
            elif isinstance(videofiles, str):
                self._videofiles.append(videofiles)
            else:
                raise AttributeError("Error MultiVideoWidget: incorrect type for attribute videofiles")
        
        layout = QtGui.QHBoxLayout()
        for ii, vid in enumerate(self._videofiles):
            self._videoSources.append( VideoSource(vidfile=vid) )
            vidwid = VideoWidget(self._videoSources[ii], parent=self, height=self.height)
            self._videoWidgets.append( vidwid )
            layout.addWidget( self._videoWidgets[ii] )
        self.setLayout(layout)
        # VideoWidget won't resize, so need to do it here
        self.resize(self.height*self._videoWidgets[0].aspectratio*len(self._videoWidgets), self.height)

             



if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)

    #widget = MultiVideoWidget()
    #widget.setWindowTitle('multi video widget Test')
    #widget.show()


    if sys.platform.startswith('linux'):
        viddir = "/home/develop/Projects/ComputerVision/openCV/data"
        vidfiles = ["201302210403221@Port.mpg", 
        "201302210403221@Centre.mpg", 
        "201302210403221@Stbd.mpg"]
    else:
        #pass
        viddir = "C:/Users/Stephen/Documents/2013_survey/GEP_KP52_freespan/VisualworksReports/Projects/9821/DATA_201401060852110"
        vidfiles = ["VIDEO_201401060852110@Stbd.mpg", 
        "VIDEO_201401060852110@Centre.mpg", 
        "VIDEO_201401060852110@Port.mpg"]

    videofilelist = []
    for vfile in vidfiles:
        videofilelist.append( os.path.join(viddir, vfile) )

 
    """videofile = os.path.join(viddir, vidfiles[0])
    camSource1 = VideoSource(vidfile=videofile)
    cameraWidget1 = VideoWidget(camSource1)
    cameraWidget1.show()

    videofile = os.path.join(viddir, vidfiles[1])
    camSource2 = VideoSource(vidfile=videofile)
    cameraWidget2 = VideoWidget(camSource2)
    cameraWidget2.show()"""
    
    multividwid = MultiVideoWidget(videofiles=videofilelist, height=300)
    multividwid.show()

    sys.exit(app.exec_())
