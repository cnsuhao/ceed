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

from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtOpenGL import *

from OpenGL.GL import *

import os.path
import time
import math

import PyCEGUI
import PyCEGUIOpenGLRenderer

#class CEGUIQtLogger(PyCEGUI.Logger):
#    """Redirects CEGUI log info to CEGUIWidgetInfo"""
#
#    # This is a separate class from CEGUIWidgetInfo because PySide and PyCEGUI
#    # don't like mixing base classes at all
#    
#    def __init__(self, widgetInfo):
#        super(CEGUIQtLogger, self).__init__()
#        
#        self.widgetInfo = widgetInfo
#        
#    def logEvent(self, message, level):
#        self.widgetInfo.logEvent(message, level)
#        
#    def setLogFilename(self, name, append):
#        pass

class GLContextProvider(object):
    """Interface that provides a method to make OpenGL context
    suitable for CEGUI the current context.
    """
    
    def makeGLContextCurrent(self):
        """Activates the OpenGL context held by this provider"""
        
        raise NotImplementedError("All classes inheriting GLContextProvider must override GLContextProvider.makeGLContextCurrent")

class Instance(object):
    """Encapsulates a running CEGUI instance.
    
    Right now CEGUI can only be instantiated once because it's full of singletons.
    This might change in the future though...
    """
    
    def __init__(self, contextProvider = None):
        self.contextProvider = contextProvider
        
        self.initialised = False
        
    def setGLContextProvider(self, contextProvider):
        """CEGUI instance might need an OpenGL context provider to make sure the right context is active
        (to load textures, render, ...)
        
        see GLContextProvider
        """
        
        self.contextProvider = contextProvider
        
    def makeGLContextCurrent(self):
        """Activate the right OpenGL context.
        
        This is usually called internally and you don't need to worry about it, it generally needs to be called
        before any rendering is done, textures are loaded, etc...
        """
        
        self.contextProvider.makeGLContextCurrent()
        
    def ensureIsInitialised(self):
        """Ensures this CEGUI instance is properly initialised, if it's not it initialises it right away.
        """
        
        if not self.initialised:
            self.makeGLContextCurrent()
            
            PyCEGUIOpenGLRenderer.OpenGLRenderer.bootstrapSystem(PyCEGUIOpenGLRenderer.OpenGLRenderer.TTT_NONE)
            self.initialised = True

            self.setDefaultResourceGroups()
            
    def setResourceGroupDirectory(self, resourceGroup, absoluteDirPath):
        """Sets given resourceGroup to look into given absoluteDirPath
        """
        
        self.ensureIsInitialised()
        
        rp = PyCEGUI.System.getSingleton().getResourceProvider()
 
        rp.setResourceGroupDirectory(resourceGroup, absoluteDirPath)
    
    def setDefaultResourceGroups(self):
        """Puts the resource groups to a reasonable default value.
        
        ./datafiles followed by the respective folder, same as CEGUI stock datafiles
        """
        
        self.ensureIsInitialised()
        
        # reasonable default directories
        defaultBaseDirectory = os.path.join(os.path.curdir, "datafiles")
        
        self.setResourceGroupDirectory("imagesets",
                                       os.path.join(defaultBaseDirectory, "imagesets"))
        self.setResourceGroupDirectory("fonts",
                                       os.path.join(defaultBaseDirectory, "fonts"))
        self.setResourceGroupDirectory("schemes",
                                       os.path.join(defaultBaseDirectory, "schemes"))
        self.setResourceGroupDirectory("looknfeels",
                                       os.path.join(defaultBaseDirectory, "looknfeel"))
        self.setResourceGroupDirectory("layouts",
                                       os.path.join(defaultBaseDirectory, "layouts"))
        
        # all this will never be set to anything else again
        PyCEGUI.ImageManager.setImagesetDefaultResourceGroup("imagesets")
        PyCEGUI.Font.setDefaultResourceGroup("fonts")
        PyCEGUI.Scheme.setDefaultResourceGroup("schemes")
        PyCEGUI.WidgetLookManager.setDefaultResourceGroup("looknfeels")
        PyCEGUI.WindowManager.setDefaultResourceGroup("layouts")
        
        parser = PyCEGUI.System.getSingleton().getXMLParser()
        if parser.isPropertyPresent("SchemaDefaultResourceGroup"):
            parser.setProperty("SchemaDefaultResourceGroup", "schemas")
        
    def syncToProject(self, project):
        """Synchronises the instance with given project, respecting it's paths and resources
        """
        
        progress = QProgressDialog()
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowTitle("Synchronising embedded CEGUI with the project")
        progress.setCancelButton(None)
        progress.resize(400, 100)
        progress.show()
        
        self.ensureIsInitialised()
        self.makeGLContextCurrent()
        
        schemeFiles = []
        absoluteSchemesPath = project.getAbsolutePathOf(project.schemesPath)
        if os.path.exists(absoluteSchemesPath):
            for file in os.listdir(absoluteSchemesPath):
                if file.endswith(".scheme"):
                    schemeFiles.append(file)
        else:
            # TODO: warning perhaps?
            #       with a dialog to let user immediately remedy the situation before loading continues
            pass

        progress.setMinimum(0)
        progress.setMaximum(3 + len(schemeFiles))
        
        progress.setLabelText("Purging all resources...")
        progress.setValue(0)
        
        # destroy all previous resources (if any)
        PyCEGUI.WindowManager.getSingleton().destroyAllWindows()
        PyCEGUI.FontManager.getSingleton().destroyAll()
        PyCEGUI.ImageManager.getSingleton().destroyAll()
        PyCEGUI.SchemeManager.getSingleton().destroyAll()
        PyCEGUI.WidgetLookManager.getSingleton().eraseAllWidgetLooks()
        
        progress.setLabelText("Setting resource paths...")
        progress.setValue(1)
        
        self.setResourceGroupDirectory("imagesets", project.getAbsolutePathOf(project.imagesetsPath))
        self.setResourceGroupDirectory("fonts", project.getAbsolutePathOf(project.fontsPath))
        self.setResourceGroupDirectory("schemes", project.getAbsolutePathOf(project.schemesPath))
        self.setResourceGroupDirectory("looknfeels", project.getAbsolutePathOf(project.looknfeelsPath))
        self.setResourceGroupDirectory("layouts", project.getAbsolutePathOf(project.layoutsPath))
        
        progress.setLabelText("Recreating all schemes...")
        progress.setValue(2)
        
        # we will load resources manually to be able to use the compatibility layer machinery
        PyCEGUI.SchemeManager.getSingleton().setAutoLoadResources(False)
        
        for schemeFile in schemeFiles:
            progress.setValue(progress.value() + 1)
            progress.setLabelText("Recreating all schemes... (%s)" % (schemeFile))
            
            scheme = PyCEGUI.SchemeManager.getSingleton().createFromFile(schemeFile, "schemes")
            
            # NOTE: This is very CEGUI implementation specific unfortunately!
            #       
            #       However I am not really sure how to do this any better.
            
            scheme.loadXMLImagesets()
            scheme.loadImageFileImagesets()
            scheme.loadFonts()
            scheme.loadLookNFeels()
            scheme.loadWindowRendererFactories()
            scheme.loadWindowFactories()
            scheme.loadFactoryAliases()
            scheme.loadFalagardMappings()
            
        # put SchemeManager into the default state again
        PyCEGUI.SchemeManager.getSingleton().setAutoLoadResources(True)
        
        progress.reset()
        
    def getAvailableSkins(self):
        """Retrieves skins (as strings representing their names) that are available
        from the set of schemes that were loaded.
        
        see syncToProject
        """
        
        skins = []

        i = PyCEGUI.WindowFactoryManager.getSingleton().getFalagardMappingIterator()

        while not i.isAtEnd():
            current_skin = i.getCurrentValue().d_windowType.split('/')[0]
            if current_skin not in skins:
                skins.append(current_skin)

            i.next()

        skins.sort()

        return skins
    
    def getAvailableFonts(self):
        """Retrieves fonts (as strings representing their names) that are available
        from the set of schemes that were loaded.
        
        see syncToProject
        """
        
        fonts = []
        font_iter = PyCEGUI.FontManager.getSingleton().getIterator()
        while not font_iter.isAtEnd():
            fonts.append(font_iter.getCurrentValue().getName())
            font_iter.next()

        fonts.sort()

        return fonts
    
    def getAvailableWidgetsBySkin(self):
        """Retrieves all mappings (string names) of all widgets that can be created
        
        see syncToProject
        """
        
        ret = {}
        ret["__no_skin__"] = ["DefaultWindow", "DragDropContainer",
                             "VerticalLayoutContainer", "HorizontalLayoutContainer",
                             "GridLayoutContainer"]

        i = PyCEGUI.WindowFactoryManager.getSingleton().getFalagardMappingIterator()
        while not i.isAtEnd():
            #base = i.getCurrentValue().d_baseType
            mapped_type = i.getCurrentValue().d_windowType.split('/', 1)
            assert(len(mapped_type) == 2)
            
            look = mapped_type[0]
            widget = mapped_type[1]

            # insert empty list for the look if it's a new look
            if not look in ret:
                ret[look] = []

            # append widget name to the list for it's look
            ret[look].append(widget)

            i.next()

        # sort the lists
        for look in ret:
            ret[look].sort()

        return ret
        
    def getWidgetPreviewImage(self, widgetType, previewWidth = 128, previewHeight = 64):
        """Renders and retrieves a widget preview image (as QImage).
        
        This is useful for various widget selection lists as a preview.
        """
        
        self.ensureIsInitialised()
        self.makeGLContextCurrent()

        system = PyCEGUI.System.getSingleton()

        renderer = system.getRenderer()
        
        renderTarget = PyCEGUIOpenGLRenderer.OpenGLViewportTarget(renderer)
        renderTarget.setArea(PyCEGUI.Rectf(0, 0, previewWidth, previewHeight))
        renderingSurface = PyCEGUI.RenderingSurface(renderTarget)
        
        widgetInstance = PyCEGUI.WindowManager.getSingleton().createWindow(widgetType, "preview")
        widgetInstance.setRenderingSurface(renderingSurface)
        # set it's size and position so that it shows up
        widgetInstance.setPosition(PyCEGUI.UVector2(PyCEGUI.UDim(0, 0), PyCEGUI.UDim(0, 0)))
        widgetInstance.setSize(PyCEGUI.USize(PyCEGUI.UDim(0, previewWidth), PyCEGUI.UDim(0, previewHeight)))
        # fake update to ensure everything is set
        widgetInstance.update(1)
        
        temporaryFBO = QGLFramebufferObject(previewWidth, previewHeight, GL_TEXTURE_2D)
        temporaryFBO.bind()
        
        renderingSurface.invalidate()

        renderer.beginRendering()
        
        try:
            widgetInstance.render()
        
        finally:
            # no matter what happens we have to clean after ourselves!
            renderer.endRendering()
            temporaryFBO.release()
            PyCEGUI.WindowManager.getSingleton().destroyWindow(widgetInstance)
        
        return temporaryFBO.toImage()
    
# make it visible to the outside
import container
import qtgraphics
import widgethelpers
