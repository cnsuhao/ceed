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

from PySide.QtGui import *
from PySide.QtCore import *
from PySide.QtOpenGL import QGLWidget

import fnmatch

from ceed.editors import mixed
from ceed import qtwidgets
from ceed import resizable

import elements
import undo

import ceed.ui.editors.imageset.dockwidget

class ImageEntryItemDelegate(QItemDelegate):
    """The only reason for this is to track when we are editing.
    
    We need this to discard key events when editor is open.
    TODO: Isn't there a better way to do this?
    """
    
    def __init__(self):
        super(ImageEntryItemDelegate, self).__init__()
        self.editing = False
        
    def setEditorData(self, editor, index):
        self.editing = True

        super(ImageEntryItemDelegate, self).setEditorData(editor, index)
    
    def setModelData(self, editor, model, index):
        super(ImageEntryItemDelegate, self).setModelData(editor, model, index)
        
        self.editing = False

class ImagesetEditorDockWidget(QDockWidget):
    """Provides list of images, property editing of currently selected image and create/delete
    """
    
    def __init__(self, visual):
        super(ImagesetEditorDockWidget, self).__init__()
        
        self.visual = visual
        
        self.ui = ceed.ui.editors.imageset.dockwidget.Ui_DockWidget()
        self.ui.setupUi(self)
        
        self.name = self.findChild(QLineEdit, "name")
        self.name.textEdited.connect(self.slot_nameEdited)
        self.image = self.findChild(qtwidgets.FileLineEdit, "image")
        # nasty, but at this point tabbedEditor.mainWindow isn't set yet
        project = mainwindow.MainWindow.instance.project
        self.image.startDirectory = lambda: project.getResourceFilePath("", "imagesets") if project is not None else ""
        self.imageLoad = self.findChild(QPushButton, "imageLoad")
        self.imageLoad.clicked.connect(self.slot_imageLoadClicked)
        self.autoScaled = self.findChild(QCheckBox, "autoScaled")
        self.autoScaled.stateChanged.connect(self.slot_autoScaledChanged)
        self.nativeHorzRes = self.findChild(QLineEdit, "nativeHorzRes")
        self.nativeHorzRes.textEdited.connect(self.slot_nativeResolutionEdited)
        self.nativeVertRes = self.findChild(QLineEdit, "nativeVertRes")
        self.nativeVertRes.textEdited.connect(self.slot_nativeResolutionEdited)
        
        self.filterBox = self.findChild(QLineEdit, "filterBox")
        self.filterBox.textChanged.connect(self.filterChanged)
        
        self.list = self.findChild(QListWidget, "list")
        self.list.setItemDelegate(ImageEntryItemDelegate())
        self.list.itemSelectionChanged.connect(self.slot_itemSelectionChanged)
        self.list.itemChanged.connect(self.slot_itemChanged)
        
        self.selectionUnderway = False
        self.selectionSynchronisationUnderway = False
        
        self.positionX = self.findChild(QLineEdit, "positionX")
        self.positionX.setValidator(QIntValidator(0, 9999999, self))
        self.positionX.textChanged.connect(self.slot_positionXChanged)
        self.positionY = self.findChild(QLineEdit, "positionY")
        self.positionY.setValidator(QIntValidator(0, 9999999, self))
        self.positionY.textChanged.connect(self.slot_positionYChanged)
        self.width = self.findChild(QLineEdit, "width")
        self.width.setValidator(QIntValidator(0, 9999999, self))
        self.width.textChanged.connect(self.slot_widthChanged)
        self.height = self.findChild(QLineEdit, "height")
        self.height.setValidator(QIntValidator(0, 9999999, self))
        self.height.textChanged.connect(self.slot_heightChanged)
        self.offsetX = self.findChild(QLineEdit, "offsetX")
        self.offsetX.setValidator(QIntValidator(-9999999, 9999999, self))
        self.offsetX.textChanged.connect(self.slot_offsetXChanged)
        self.offsetY = self.findChild(QLineEdit, "offsetY")
        self.offsetY.setValidator(QIntValidator(-9999999, 9999999, self))
        self.offsetY.textChanged.connect(self.slot_offsetYChanged)
        
        self.setActiveImageEntry(None)
        
    def setImagesetEntry(self, imagesetEntry):
        self.imagesetEntry = imagesetEntry
        
    def refresh(self):
        """Refreshes the whole list
        
        Note: User potentially looses selection when this is called!
        """
        
        # FIXME: This is really really weird!
        #        If I call list.clear() it crashes when undoing image deletes for some reason
        #        I already spent several hours tracking it down and I couldn't find anything
        #
        #        If I remove items one by one via takeItem, everything works :-/
        #self.list.clear()
        
        self.selectionSynchronisationUnderway = True
        
        while self.list.takeItem(0):
            pass
        
        self.selectionSynchronisationUnderway = False

        self.setActiveImageEntry(None)
        
        self.name.setText(self.imagesetEntry.name)
        self.image.setText(self.imagesetEntry.getAbsoluteImageFile())
        self.autoScaled.setChecked(self.imagesetEntry.autoScaled)
        self.nativeHorzRes.setText(str(self.imagesetEntry.nativeHorzRes))
        self.nativeVertRes.setText(str(self.imagesetEntry.nativeVertRes))
        
        for imageEntry in self.imagesetEntry.imageEntries:
            item = QListWidgetItem()
            item.dockWidget = self
            item.setFlags(Qt.ItemIsSelectable |
                          Qt.ItemIsEditable |
                          Qt.ItemIsEnabled)
            
            item.imageEntry = imageEntry
            imageEntry.listItem = item
            # nothing is selected (list was cleared) so we don't need to call
            #  the whole updateDockWidget here
            imageEntry.updateListItem()
            
            self.list.addItem(item)
        
        # explicitly call the filtering again to make sure it's in sync    
        self.filterChanged(self.filterBox.text())

    def setActiveImageEntry(self, imageEntry):
        """Active image entry is the image entry that is selected when there are no
        other image entries selected. It's properties show in the property box.
        
        Note: Imageset editing doesn't allow multi selection property editing because
              IMO it doesn't make much sense.
        """
        
        self.activeImageEntry = imageEntry
        
        self.refreshActiveImageEntry()
    
    def refreshActiveImageEntry(self):
        """Refreshes the properties of active image entry (from image entry to the property box)
        """
        
        if not self.activeImageEntry:
            self.positionX.setText("")
            self.positionX.setEnabled(False)
            self.positionY.setText("")
            self.positionY.setEnabled(False)
            self.width.setText("")
            self.width.setEnabled(False)
            self.height.setText("")
            self.height.setEnabled(False)
            self.offsetX.setText("")
            self.offsetX.setEnabled(False)
            self.offsetY.setText("")
            self.offsetY.setEnabled(False)
            
        else:
            self.positionX.setText(str(self.activeImageEntry.xpos))
            self.positionX.setEnabled(True)
            self.positionY.setText(str(self.activeImageEntry.ypos))
            self.positionY.setEnabled(True)
            self.width.setText(str(self.activeImageEntry.width))
            self.width.setEnabled(True)
            self.height.setText(str(self.activeImageEntry.height))
            self.height.setEnabled(True)
            self.offsetX.setText(str(self.activeImageEntry.xoffset))
            self.offsetX.setEnabled(True)
            self.offsetY.setText(str(self.activeImageEntry.yoffset))
            self.offsetY.setEnabled(True)
            
    def keyReleaseEvent(self, event):
        # if we are editing, we should discard key events
        # (delete means delete character, not delete image entry in this context)
        
        if not self.list.itemDelegate().editing:
            if event.key() == Qt.Key_Delete:
                selection = self.visual.scene().selectedItems()
                
                handled = self.visual.deleteImageEntries(selection)
                
                if handled:
                    return True
        
        return super(ImagesetEditorDockWidget, self).keyReleaseEvent(event)  

    def slot_itemSelectionChanged(self):
        imageEntryNames = self.list.selectedItems()
        if len(imageEntryNames) == 1:
            imageEntry = imageEntryNames[0].imageEntry
            self.setActiveImageEntry(imageEntry)
        else:
            self.setActiveImageEntry(None)
            
        # we are getting synchronised with the visual editing pane, do not interfere
        if self.selectionSynchronisationUnderway:
            return
        
        self.selectionUnderway = True
        self.visual.scene().clearSelection()
        
        imageEntryNames = self.list.selectedItems()
        for imageEntryName in imageEntryNames:
            imageEntry = imageEntryName.imageEntry
            imageEntry.setSelected(True)
            
        if len(imageEntryNames) == 1:
            imageEntry = imageEntryNames[0].imageEntry
            self.visual.centerOn(imageEntry)
            
        self.selectionUnderway = False
        
    def slot_itemChanged(self, item):
        oldName = item.imageEntry.name
        newName = item.text()
        
        if oldName == newName:
            # most likely caused by RenameCommand doing it's work or is bogus anyways
            return
        
        cmd = undo.RenameCommand(self.visual, oldName, newName)
        self.visual.tabbedEditor.undoStack.push(cmd)
    
    def filterChanged(self, filter):
        # we append star at the end by default (makes image filtering much more practical)
        filter = filter + "*"
        
        i = 0
        while i < self.list.count():
            listItem = self.list.item(i)
            match = fnmatch.fnmatch(listItem.text(), filter)
            listItem.setHidden(not match)
            
            i += 1
            
    def slot_nameEdited(self, newValue):
        oldName = self.imagesetEntry.name
        newName = self.name.text()
        
        if oldName == newName:
            return
        
        cmd = undo.ImagesetRenameCommand(self.visual, oldName, newName)
        self.visual.tabbedEditor.undoStack.push(cmd)
        
    def slot_imageLoadClicked(self):
        oldImageFile = self.imagesetEntry.imageFile
        newImageFile = self.imagesetEntry.convertToRelativeImageFile(self.image.text())
        
        if oldImageFile == newImageFile:
            return
        
        cmd = undo.ImagesetChangeImageCommand(self.visual, oldImageFile, newImageFile)
        self.visual.tabbedEditor.undoStack.push(cmd)
        
    def slot_autoScaledChanged(self, newState):
        oldAutoScaled = self.imagesetEntry.autoScaled
        newAutoScaled = self.autoScaled.checkState() == Qt.Checked
        
        if oldAutoScaled == newAutoScaled:
            return
        
        cmd = undo.ImagesetChangeAutoScaledCommand(self.visual, oldAutoScaled, newAutoScaled)
        self.visual.tabbedEditor.undoStack.push(cmd)
        
    def slot_nativeResolutionEdited(self, newValue):
        oldHorzRes = self.imagesetEntry.nativeHorzRes
        oldVertRes = self.imagesetEntry.nativeVertRes
        newHorzRes = int(self.nativeHorzRes.text())
        newVertRes = int(self.nativeVertRes.text())
        
        if oldHorzRes == newHorzRes and oldVertRes == newVertRes:
            return
        
        cmd = undo.ImagesetChangeNativeResolutionCommand(self.visual, oldHorzRes, oldVertRes, newHorzRes, newVertRes)
        self.visual.tabbedEditor.undoStack.push(cmd)

    def metaslot_propertyChanged(self, propertyName, newTextValue):
        if not self.activeImageEntry:
            return
        
        oldValue = getattr(self.activeImageEntry, propertyName)
        newValue = None
        
        try:
            newValue = int(newTextValue)
        except ValueError:
            # if the string is not a valid integer literal, we allow user to edit some more
            return
        
        if oldValue == newValue:
            return
        
        cmd = undo.PropertyEditCommand(self.visual, self.activeImageEntry.name, propertyName, oldValue, newValue)
        self.visual.tabbedEditor.undoStack.push(cmd)

    def slot_positionXChanged(self, text):
        self.metaslot_propertyChanged("xpos", text)

    def slot_positionYChanged(self, text):
        self.metaslot_propertyChanged("ypos", text)
        
    def slot_widthChanged(self, text):
        self.metaslot_propertyChanged("width", text)
        
    def slot_heightChanged(self, text):
        self.metaslot_propertyChanged("height", text)
        
    def slot_offsetXChanged(self, text):
        self.metaslot_propertyChanged("xoffset", text)

    def slot_offsetYChanged(self, text):
        self.metaslot_propertyChanged("yoffset", text)

class VisualEditing(resizable.GraphicsView, mixed.EditMode):
    """This is the "Visual" tab for imageset editing
    """
    
    def __init__(self, tabbedEditor):
        resizable.GraphicsView.__init__(self)
        mixed.EditMode.__init__(self)
        
        self.wheelZoomEnabled = True
        self.middleButtonDragScrollEnabled = True
        
        self.lastMousePosition = None
        
        scene = QGraphicsScene()
        self.setScene(scene)
        
        self.setFocusPolicy(Qt.ClickFocus)
        self.setFrameStyle(QFrame.NoFrame)
        
        if settings.getEntry("imageset/visual/partial_updates").value:
            # the commented lines are possible optimisation, I found out that they don't really
            # speed it up in a noticeable way so I commented them out
            
            #self.setOptimizationFlag(QGraphicsView.DontSavePainterState, True)
            #self.setOptimizationFlag(QGraphicsView.DontAdjustForAntialiasing, True)
            #self.setCacheMode(QGraphicsView.CacheBackground)
            self.setViewportUpdateMode(QGraphicsView.MinimalViewportUpdate)
            #self.setRenderHint(QPainter.Antialiasing, False)
            #self.setRenderHint(QPainter.TextAntialiasing, False)
            #self.setRenderHint(QPainter.SmoothPixmapTransform, False)
            
        else:
            # use OpenGL for view redrawing
            # depending on the platform and hardware this may be faster or slower
            self.setViewport(QGLWidget())
            self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        
        self.scene().selectionChanged.connect(self.slot_selectionChanged)
        
        self.tabbedEditor = tabbedEditor

        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setBackgroundBrush(QBrush(Qt.lightGray))
        
        self.imagesetEntry = None
        
        self.dockWidget = ImagesetEditorDockWidget(self)
    
        self.setupActions()
    
    def setupActions(self):
        self.connectionGroup = action.ConnectionGroup(action.ActionManager.instance)
        
        self.editOffsetsAction = action.getAction("imageset/edit_offsets")
        self.connectionGroup.add(self.editOffsetsAction, receiver = self.slot_toggleEditOffsets, signalName = "toggled")
        
        self.cycleOverlappingAction = action.getAction("imageset/cycle_overlapping")
        self.connectionGroup.add(self.cycleOverlappingAction, receiver = self.cycleOverlappingImages)
        
        self.zoomOriginalAction = action.getAction("imageset/zoom_original")
        self.connectionGroup.add(self.zoomOriginalAction, receiver = self.zoomOriginal)
        self.zoomInAction = action.getAction("imageset/zoom_in")
        self.connectionGroup.add(self.zoomInAction, receiver = self.zoomIn)
        self.zoomOutAction = action.getAction("imageset/zoom_out")
        self.connectionGroup.add(self.zoomOutAction, receiver = self.zoomOut)
        
        self.createImageAction = action.getAction("imageset/create_image")
        self.connectionGroup.add(self.createImageAction, receiver = self.createImageAtCursor)
        
        self.deleteSelectedImagesAction = action.getAction("imageset/delete_image")
        self.connectionGroup.add(self.deleteSelectedImagesAction, receiver = self.deleteSelectedImageEntries)
        
        self.toolBar = QToolBar()
        self.toolBar.setIconSize(QSize(32, 32))
        
        self.toolBar.addAction(self.editOffsetsAction)
        self.toolBar.addSeparator() # ---------------------------
        self.toolBar.addAction(self.cycleOverlappingAction)
        self.toolBar.addSeparator() # ---------------------------
        self.toolBar.addAction(self.zoomOriginalAction)
        self.toolBar.addAction(self.zoomInAction)
        self.toolBar.addAction(self.zoomOutAction)
        self.toolBar.addSeparator() # ---------------------------
        self.toolBar.addAction(self.createImageAction)
        self.toolBar.addAction(self.deleteSelectedImagesAction)
 
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        
        self.contextMenu = QMenu(self)
        self.customContextMenuRequested.connect(self.slot_customContextMenu)
        
        self.contextMenu.addAction(self.editOffsetsAction)
        self.contextMenu.addSeparator() # ----------------------
        self.contextMenu.addAction(self.cycleOverlappingAction)
        self.contextMenu.addSeparator() # ----------------------
        self.contextMenu.addAction(self.zoomOriginalAction)
        self.contextMenu.addAction(self.zoomInAction)
        self.contextMenu.addAction(self.zoomOutAction)
        self.contextMenu.addSeparator()
        self.contextMenu.addAction(self.createImageAction)
        self.contextMenu.addAction(self.deleteSelectedImagesAction)
        
    def initialise(self, rootElement):
        self.loadImagesetEntryFromElement(rootElement)
        
    def refreshSceneRect(self):
        boundingRect = self.imagesetEntry.boundingRect()
        
        # the reason to make the bounding rect 100px bigger on all the sides is to make
        # middle button drag scrolling easier (you can put the image where you want without
        # running out of scene
        
        boundingRect.adjust(-100, -100, 100, 100)
        self.scene().setSceneRect(boundingRect)
        
    def loadImagesetEntryFromElement(self, element):
        self.scene().clear()
        
        self.imagesetEntry = elements.ImagesetEntry(self)
        self.imagesetEntry.loadFromElement(element)
        self.scene().addItem(self.imagesetEntry)

        self.refreshSceneRect()
        
        self.dockWidget.setImagesetEntry(self.imagesetEntry)
        self.dockWidget.refresh()
        
    def moveImageEntries(self, imageEntries, delta):
        if delta.manhattanLength() > 0 and len(imageEntries) > 0:
            imageNames = []
            oldPositions = {}
            newPositions = {}
            
            for imageEntry in imageEntries:
                imageNames.append(imageEntry.name)
                oldPositions[imageEntry.name] = imageEntry.pos()
                newPositions[imageEntry.name] = imageEntry.pos() + delta
                
            cmd = undo.MoveCommand(self, imageNames, oldPositions, newPositions)
            self.tabbedEditor.undoStack.push(cmd)
            
            # we handled this
            return True
        
        # we didn't handle this
        return False
    
    def resizeImageEntries(self, imageEntries, topLeftDelta, bottomRightDelta):
        if (topLeftDelta.manhattanLength() > 0 or bottomRightDelta.manhattanLength() > 0) and len(imageEntries) > 0:
            imageNames = []
            oldPositions = {}
            oldRects = {}
            newPositions = {}
            newRects = {}
            
            for imageEntry in imageEntries:

                imageNames.append(imageEntry.name)
                oldPositions[imageEntry.name] = imageEntry.pos()
                newPositions[imageEntry.name] = imageEntry.pos() - topLeftDelta
                oldRects[imageEntry.name] = imageEntry.rect()
                
                newRect = imageEntry.rect()
                newRect.setBottomRight(newRect.bottomRight() - topLeftDelta + bottomRightDelta)

                if newRect.width() < 1:
                    newRect.setWidth(1)
                if newRect.height() < 1:
                    newRect.setHeight(1)
                
                newRects[imageEntry.name] = newRect
                
            cmd = undo.GeometryChangeCommand(self, imageNames, oldPositions, oldRects, newPositions, newRects)
            self.tabbedEditor.undoStack.push(cmd)
            
            # we handled this
            return True
        
        # we didn't handle this
        return False
        
    def cycleOverlappingImages(self):
        selection = self.scene().selectedItems()
            
        if len(selection) == 1:
            rect = selection[0].boundingRect()
            rect.translate(selection[0].pos())
            
            overlappingItems = self.scene().items(rect)
        
            # first we stack everything before our current selection
            successor = None
            for item in overlappingItems:
                if item == selection[0] or item.parentItem() != selection[0].parentItem():
                    continue
                
                if not successor and isinstance(item, elements.ImageEntry):
                    successor = item
                    
            if successor:
                for item in overlappingItems:
                    if item == successor or item.parentItem() != successor.parentItem():
                        continue
                    
                    successor.stackBefore(item)
                
                # we deselect current
                selection[0].setSelected(False)
                selection[0].hoverLeaveEvent(None)
                # and select what was at the bottom (thus getting this to the top)    
                successor.setSelected(True)
                successor.hoverEnterEvent(None)
        
            # we handled this        
            return True
        
        # we didn't handle this
        return False
    
    def createImage(self, centrePositionX, centrePositionY):
        """Centre position is the position of the centre of the newly created image,
        the newly created image will then 'encapsulate' the centrepoint
        """
        
        # find a unique image name
        name = "NewImage"
        index = 1
        
        while True:
            found = False
            for imageEntry in self.imagesetEntry.imageEntries:
                if imageEntry.name == name:
                    found = True
                    break
                
            if found:
                name = "NewImage_%i" % (index)
                index += 1
            else:
                break
        
        halfSize = 25
        
        xpos = centrePositionX - halfSize
        ypos = centrePositionY - halfSize
        width = 2 * halfSize
        height = 2 * halfSize
        xoffset = 0
        yoffset = 0

        cmd = undo.CreateCommand(self, name, xpos, ypos, width, height, xoffset, yoffset)
        self.tabbedEditor.undoStack.push(cmd)
    
    def createImageAtCursor(self):
        assert(self.lastMousePosition is not None)
        sceneCoordinates = self.mapToScene(self.lastMousePosition)
        
        self.createImage(int(sceneCoordinates.x()), int(sceneCoordinates.y()))
    
    def deleteImageEntries(self, imageEntries):        
        if len(imageEntries) > 0:
            oldNames = []
            
            oldPositions = {}
            oldRects = {}
            oldOffsets = {}
            
            for imageEntry in imageEntries:
                oldNames.append(imageEntry.name)
                
                oldPositions[imageEntry.name] = imageEntry.pos()
                oldRects[imageEntry.name] = imageEntry.rect()
                oldOffsets[imageEntry.name] = imageEntry.offset.pos()
            
            cmd = undo.DeleteCommand(self, oldNames, oldPositions, oldRects, oldOffsets)
            self.tabbedEditor.undoStack.push(cmd)
            
            return True
        
        else:
            # we didn't handle this
            return False
    
    def deleteSelectedImageEntries(self):
        selection = self.scene().selectedItems()
        
        imageEntries = []
        for item in selection:
            if isinstance(item, elements.ImageEntry):
                imageEntries.append(item)
        
        return self.deleteImageEntries(imageEntries)
    
    def showEvent(self, event):        
        self.dockWidget.setEnabled(True)
        self.toolBar.setEnabled(True)
        
        # connect all our actions
        self.connectionGroup.connectAll()
        # call this every time the visual editing is shown to sync all entries up
        self.slot_toggleEditOffsets(self.editOffsetsAction.isChecked())
        
        super(VisualEditing, self).showEvent(event)
    
    def hideEvent(self, event):
        # disconnected all our actions
        self.connectionGroup.disconnectAll()
        
        self.dockWidget.setEnabled(False)
        self.toolBar.setEnabled(False)
        
        super(VisualEditing, self).hideEvent(event)
    
    def mousePressEvent(self, event): 
        super(VisualEditing, self).mousePressEvent(event) 
        
        if event.buttons() & Qt.LeftButton:
            for selectedItem in self.scene().selectedItems():
                # selectedItem could be ImageEntry or ImageOffset!                    
                selectedItem.potentialMove = True
                selectedItem.oldPosition = None
    
    def mouseReleaseEvent(self, event):
        """When mouse is released, we have to check what items were moved and resized.
        
        AFAIK Qt doesn't give us any move finished notification so I do this manually
        """
        
        super(VisualEditing, self).mouseReleaseEvent(event)
        
        # moving
        moveImageNames = []
        moveImageOldPositions = {}
        moveImageNewPositions = {}
        
        moveOffsetNames = []
        moveOffsetOldPositions = {}
        moveOffsetNewPositions = {}
        
        # resizing            
        resizeImageNames = []
        resizeImageOldPositions = {}
        resizeImageOldRects = {}
        resizeImageNewPositions = {}
        resizeImageNewRects = {}
        
        # we have to "expand" the items, adding parents of resizing handles
        # instead of the handles themselves
        expandedSelectedItems = []
        for selectedItem in self.scene().selectedItems():
            if isinstance(selectedItem, elements.ImageEntry):
                expandedSelectedItems.append(selectedItem)
            elif isinstance(selectedItem, elements.ImageOffset):
                expandedSelectedItems.append(selectedItem)
            elif isinstance(selectedItem, resizable.ResizingHandle):
                expandedSelectedItems.append(selectedItem.parentItem())
        
        for selectedItem in expandedSelectedItems:
            if isinstance(selectedItem, elements.ImageEntry):
                if selectedItem.oldPosition:
                    if selectedItem.mouseOver:
                        # show the label again if mouse is over because moving finished
                        selectedItem.label.setVisible(True)
                        
                    # only include that if the position really changed
                    if selectedItem.oldPosition != selectedItem.pos():
                        moveImageNames.append(selectedItem.name)
                        moveImageOldPositions[selectedItem.name] = selectedItem.oldPosition
                        moveImageNewPositions[selectedItem.name] = selectedItem.pos()
                    
                if selectedItem.resized:
                    # only include that if the position or rect really changed
                    if selectedItem.resizeOldPos != selectedItem.pos() or selectedItem.resizeOldRect != selectedItem.rect():
                        resizeImageNames.append(selectedItem.name)
                        resizeImageOldPositions[selectedItem.name] = selectedItem.resizeOldPos
                        resizeImageOldRects[selectedItem.name] = selectedItem.resizeOldRect
                        resizeImageNewPositions[selectedItem.name] = selectedItem.pos()
                        resizeImageNewRects[selectedItem.name] = selectedItem.rect()
                    
                selectedItem.potentialMove = False
                selectedItem.oldPosition = None
                selectedItem.resized = False
                
            elif isinstance(selectedItem, elements.ImageOffset):
                if selectedItem.oldPosition:
                    # only include that if the position really changed
                    if selectedItem.oldPosition != selectedItem.pos():
                        moveOffsetNames.append(selectedItem.imageEntry.name)
                        moveOffsetOldPositions[selectedItem.imageEntry.name] = selectedItem.oldPosition
                        moveOffsetNewPositions[selectedItem.imageEntry.name] = selectedItem.pos()
                    
                selectedItem.potentialMove = False
                selectedItem.oldPosition = None
        
        # NOTE: It should never happen that more than 2 of these sets are populated
        #       User moves images XOR moves offsets XOR resizes images
        #
        #       I don't do elif for robustness though, who knows what can happen ;-)
        
        if len(moveImageNames) > 0:
            cmd = undo.MoveCommand(self, moveImageNames, moveImageOldPositions, moveImageNewPositions)
            self.tabbedEditor.undoStack.push(cmd)
            
        if len(moveOffsetNames) > 0:
            cmd = undo.OffsetMoveCommand(self, moveOffsetNames, moveOffsetOldPositions, moveOffsetNewPositions)
            self.tabbedEditor.undoStack.push(cmd)
            
        if len(resizeImageNames) > 0:
            cmd = undo.GeometryChangeCommand(self, resizeImageNames, resizeImageOldPositions, resizeImageOldRects, resizeImageNewPositions, resizeImageNewRects)
            self.tabbedEditor.undoStack.push(cmd)
            
    def mouseMoveEvent(self, event):
        self.lastMousePosition = event.pos()
        
        super(VisualEditing, self).mouseMoveEvent(event)
        
    def keyReleaseEvent(self, event):
        # TODO: offset keyboard handling
        
        handled = False
        
        if event.key() in [Qt.Key_A, Qt.Key_D, Qt.Key_W, Qt.Key_S]:
            selection = []
            
            for item in self.scene().selectedItems():
                if item in selection:
                    continue
                
                if isinstance(item, elements.ImageEntry):
                    selection.append(item)
                    
                elif isinstance(item, resizable.ResizingHandle):
                    parent = item.parentItem()
                    if not parent in selection:
                        selection.append(parent)
            
            if len(selection) > 0:
                delta = QPointF()
                
                if event.key() == Qt.Key_A:
                    delta += QPointF(-1, 0)
                elif event.key() == Qt.Key_D:
                    delta += QPointF(1, 0)
                elif event.key() == Qt.Key_W:
                    delta += QPointF(0, -1)
                elif event.key() == Qt.Key_S:
                    delta += QPointF(0, 1)
                
                if event.modifiers() & Qt.ControlModifier:
                    delta *= 10
                
                if event.modifiers() & Qt.ShiftModifier:
                    handled = self.resizeImageEntries(selection, QPointF(0, 0), delta)
                else:
                    handled = self.moveImageEntries(selection, delta)
                
        elif event.key() == Qt.Key_Q:
            handled = self.cycleOverlappingImages()
        
        elif event.key() == Qt.Key_Delete:
            handled = self.deleteSelectedImageEntries()           
            
        if not handled:
            super(VisualEditing, self).keyReleaseEvent(event)
            
        else:
            event.accept()
            
    def slot_selectionChanged(self):
        # if dockWidget is changing the selection, back off
        if self.dockWidget.selectionUnderway:
            return
        
        selectedItems = self.scene().selectedItems()
        if len(selectedItems) == 1:
            if isinstance(selectedItems[0], elements.ImageEntry):
                self.dockWidget.list.scrollToItem(selectedItems[0].listItem)
        
    def slot_toggleEditOffsets(self, enabled):
        self.scene().clearSelection()
        
        if self.imagesetEntry is not None:
            self.imagesetEntry.showOffsets = enabled
        
    def slot_customContextMenu(self, point):
        self.contextMenu.exec_(self.mapToGlobal(point))
    
from ceed import action
from ceed import settings
from ceed import mainwindow