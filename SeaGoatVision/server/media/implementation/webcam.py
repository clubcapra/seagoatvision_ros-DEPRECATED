#! /usr/bin/env python

#    Copyright (C) 2012  Octets - octets.etsmtl.ca
#
#    This file is part of SeaGoatVision.
#
#    SeaGoatVision is free software: you can redistribute it and/or modify
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

import cv2
from SeaGoatVision.server.media.media_streaming import Media_streaming

class Webcam(Media_streaming):
    """Return images from the webcam."""

    def __init__(self):
        Media_streaming.__init__(self)
        self.writer = None
        self.run = True
        self.camera_number = 0
        self.video = None

    def open(self):
        self.video = cv2.VideoCapture(self.camera_number)
        self.video.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, 320)
        self.video.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 240)
        # call open when video is ready
        Media_streaming.open(self)

    def next(self):
        run, image = self.video.read()
        if run == False:
            raise StopIteration
        if self.writer:
            self.writer.write(image)
        return image

    def close(self):
        Media_streaming.close(self)
        self.video.release()
