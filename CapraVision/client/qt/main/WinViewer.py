#! /usr/bin/env python

#    Copyright (C) 2012  Club Capra - capra.etsmtl.ca
#
#    This file is part of CapraVision.
#    
#    CapraVision is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

# from gi.repository import GObject

"""
Description : Windows to "view" a filterchain execution
Authors: Mathieu Benoit (mathben963@gmail.com)
         Junior Gregoire (junior.gregoire@gmail.com)
Date : december 2012
"""

from CapraVision.client.qt.utils import *
from PySide import QtGui
from PySide import QtCore
from CapraVision.server.filters.implementation.bgr2rgb import BGR2RGB
import Image
import time
import threading

class WinViewer(QtCore.QObject):
    """Show the source after being processed by the filter chain.
    The window receives a filter in its constructor.  
    This is the last executed filter on the source.    
    """
    
    newImage = QtCore.Signal(QtGui.QImage)
    
    def __init__(self, controller, execution_name, source_name, filterchain_name, lst_filter_str):  
        super(WinViewer, self).__init__()   
        self.ui = get_ui(self, 'sourcesListStore', 'filterChainListStore')
        
        self.controller = controller
        self.execution_name = execution_name
        self.filterchain_name = filterchain_name
        
        self.size = 1
        self.thread = None
        
        # filterchain.add_filter_observer(self.updateFilters)
        # filterchain.add_image_observer(self.updateImage)        
           
        self.newImage.connect(self.setPixmap)
        self.ui.filterComboBox.currentIndexChanged.connect(self._changeFilter)
        self.ui.sizeComboBox.currentIndexChanged[str].connect(self.setImageScale)
        # self.updateFilters()

        self.lastSecondFps = None
        self.fpsCount = 0
        
        self._updateFilters(lst_filter_str)
        
        self.observer = self.controller.start_filterchain_execution(execution_name, source_name, filterchain_name)
        
        if not self.observer:
            print("Error, we didn't receive observer from filterchain execution.")
        else:
            self.thread = ThreadObserver(self)
            self._changeFilter()
            self.thread.start()
        
    def quit(self):
        if self.thread:
            self.thread.stop()
            self.controller.stop_filterchain_execution(self.execution_name)
        print("WinViewer %s quit." % (self.filterchain_name))
        
    ######################################################################
    ####################### PRIVATE FUNCTION  ############################
    ######################################################################
    def _updateFilters(self, lst_filter_str):
        self.ui.filterComboBox.clear()
        for sFilter in lst_filter_str:
            self.ui.filterComboBox.addItem(sFilter)
    
    def _changeFilter(self):
        if self.thread:
            self.thread.set_filter_name(self.ui.filterComboBox.currentText())
    
    def updateImage(self, image):
        # fps
        iActualTime = time.time()
        if self.lastSecondFps is None:
            # Initiate fps
            self.lastSecondFps = iActualTime
            self.fpsCount = 1
        elif iActualTime - self.lastSecondFps > 1.0:
            self.ui.lbl_fps.setText("%d" % int(self.fpsCount))
            # new set
            self.lastSecondFps = iActualTime
            self.fpsCount = 1
        else:
            self.fpsCount += 1

        self.numpy_to_QImage(image)   
    
    def setPixmap(self, img):
        pix = QtGui.QPixmap.fromImage(img)
        self.ui.imageLabel.setPixmap(pix)
    
    def numpy_to_QImage(self, image):
        bgr2rgb = BGR2RGB()
        imageRGB = bgr2rgb.execute(image)
        img = Image.fromarray(imageRGB)
        buff = StringIO.StringIO()
        img.save(buff, 'ppm')
        data = buff.getvalue()
        buff.close()        
        qimage = QtGui.QImage.fromData(data)
        if self.size <> 1.0:
            shape = image.shape
            qimage = qimage.scaled(shape[1] * self.size, shape[0] * self.size)          
        self.newImage.emit(qimage)
     
    def setImageScale(self, textSize):
        textSize = textSize[:-1]
        self.size = float(textSize) / 100 
            
               
class ThreadObserver(threading.Thread):
    def __init__(self, winViewer):
        threading.Thread.__init__(self)
        self.winViewer = winViewer
        self.isStopped = False
        
    def run(self):
        while not self.isStopped:
            image = self.winViewer.observer.next()
            if image is not None:
                self.winViewer.updateImage(image)
    
    def set_filter_name(self, sFilter):
        self.winViewer.observer.set_filter_name(sFilter)
    
    def stop(self):
        self.isStopped = True
        self.winViewer.observer.stop()
    
    
    
