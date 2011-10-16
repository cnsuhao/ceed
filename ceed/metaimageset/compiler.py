################################################################################
#   CEED - A unified CEGUI editor
#   Copyright (C) 2011 Martin Preisler <preisler.m@gmail.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
################################################################################

import math
import os.path

from ceed.metaimageset import rectanglepacking
import ceed.compatibility.imageset as imageset_compatibility

from PySide.QtCore import *
from PySide.QtGui import *

class ImageInstance(object):
    def __init__(self, x, y, image):
        self.x = x
        self.y = y
        
        self.image = image

class CompilerInstance(object):
    def __init__(self, metaImageset):
        self.sizeIncrement = 5
        
        self.metaImageset = metaImageset
        
    def estimateMinimalSize(self):
        """Tries to estimate minimal side of the underlying image of the output imageset.
        
        This is used merely as a starting point in the packing process.
        """
        
        area = 0
        
        for input in self.metaImageset.inputs:
            for image in input.getImages():
                area += image.qimage.width() * image.qimage.height()
        
        return math.sqrt(area)
    
    def compile(self):
        def getNextPOT(number):
            """Returns the next power of two that is greater than given number"""

            return int(2 ** math.ceil(math.log(number + 1, 2)))
        
        imageInstances = []
        
        theoreticalMinSize = self.estimateMinimalSize()
        if theoreticalMinSize < 1:
            theoreticalMinSize = 1
        sideSize = getNextPOT(theoreticalMinSize) if self.metaImageset.onlyPOT else theoreticalMinSize

        print("Gathering and rendering all images...")
        images = []
        for input in self.metaImageset.inputs:
            images.extend(input.getImages())
        
        # the image packer performs better if images are inserted by width, thinnest come first
        images = sorted(images, key = lambda image: image.qimage.width())
        
        print("Performing texture side size determination...")
        i = 0
        # This could be way sped up if we used some sort of a "binary search" approach
        while True:
            packer = rectanglepacking.CygonRectanglePacker(sideSize, sideSize)
            try:
                imageInstances = []
                
                for image in images:
                    # TODO: borders to avoid artifacts
                    
                    point = packer.Pack(image.qimage.width(), image.qimage.height())
                    imageInstances.append(ImageInstance(point.x, point.y, image))
                    
                # everything seems to have gone smoothly, lets use this configuration then
                break
            
            except rectanglepacking.OutOfSpaceError:
                sideSize = getNextPOT(sideSize) if self.metaImageset.onlyPOT else sideSize + self.sizeIncrement
                
                i += 1
                if i % 5 == 0:
                    print "%i candidate sizes checked" % (i)

                continue
        
        print("Correct texture side size found after %i iterations" % (i))
        
        print("Rendering the underlying image...")    
        underlyingImage = QImage(sideSize, sideSize, QImage.Format_ARGB32)
        underlyingImage.fill(0)
        
        painter = QPainter()
        painter.begin(underlyingImage)
        
        for imageInstance in imageInstances:
            # TODO: borders
            
            # and then draw the real image on top
            painter.drawImage(QPointF(imageInstance.x, imageInstance.y),
                              imageInstance.image.qimage)
            
        painter.end()
        
        print("Saving underlying image...")
        
        outputSplit = self.metaImageset.output.rsplit(".", 1)
        underlyingImageFileName = "%s.png" % (outputSplit[0])
        underlyingImage.save(os.path.join(self.metaImageset.getOutputDirectory(), underlyingImageFileName))
        
        # CEGUI imageset format is very simple and easy to work with, using serialisation in the editor for this
        # seemed like a wasted effort :-)
        
        nativeData = "<Imageset Name=\"%s\" Imagefile=\"%s\" NativeHorzRes=\"%i\" NativeVertRes=\"%i\" AutoScaled=\"%s\">\n" % (self.metaImageset.name, underlyingImageFileName, self.metaImageset.nativeHorzRes, self.metaImageset.nativeVertRes, "true" if self.metaImageset.autoScaled else "false")
        for imageInstance in imageInstances:
            nativeData += "    <Image Name=\"%s\" XPos=\"%i\" YPos=\"%i\" Width=\"%i\" Height=\"%i\" XOffset=\"%i\" YOffset=\"%i\" />\n" % (imageInstance.image.name, imageInstance.x, imageInstance.y, imageInstance.image.qimage.width(), imageInstance.image.qimage.height(), imageInstance.image.xoffset, imageInstance.image.yoffset)

        nativeData += "</Imageset>\n"
        
        outputData = imageset_compatibility.Manager.instance.transform(imageset_compatibility.Manager.instance.EditorNativeType, self.metaImageset.outputTargetType, nativeData)
        open(os.path.join(self.metaImageset.getOutputDirectory(), self.metaImageset.output), "w").write(outputData)
        
        print("All done and saved!")
        print("")
        
        print("Theoretical minimum texture size: %i x %i" % (theoreticalMinSize, theoreticalMinSize))
        print("Actual texture size: %i x %i" % (sideSize, sideSize))
        print("")
        print("Side size overhead: %f%%" % ((sideSize - theoreticalMinSize) / (theoreticalMinSize) * 100))
        print("Area (squared) overhead: %f%%" % ((sideSize * sideSize - theoreticalMinSize * theoreticalMinSize) / (theoreticalMinSize * theoreticalMinSize) * 100))
        