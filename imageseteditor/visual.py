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

import mixedtab

import qtwidgets
import elements
import undo

import ui.imageseteditor.dockwidget

class ImagesetEditorDockWidget(QDockWidget):
    """Provides list of images, property editing of currently selected image and create/delete
    """
    
    def __init__(self, parent):
        super(ImagesetEditorDockWidget, self).__init__()
        
        self.parent = parent
        
        self.ui = ui.imageseteditor.dockwidget.Ui_DockWidget()
        self.ui.setupUi(self)
        
        self.name = self.findChild(QLineEdit, "name")
        self.name.textEdited.connect(self.slot_nameEdited)
        self.image = self.findChild(qtwidgets.FileLineEdit, "image")
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
        self.list.itemSelectionChanged.connect(self.slot_itemSelectionChanged)
        self.list.itemChanged.connect(self.slot_itemChanged)
        
        self.selectionUnderway = False
        self.selectionSynchronisationUnderway = False
        
        self.positionX = self.findChild(QLineEdit, "positionX")
        self.positionX.textChanged.connect(self.slot_positionXChanged)
        self.positionY = self.findChild(QLineEdit, "positionY")
        self.positionY.textChanged.connect(self.slot_positionYChanged)
        self.width = self.findChild(QLineEdit, "width")
        self.width.textChanged.connect(self.slot_widthChanged)
        self.height = self.findChild(QLineEdit, "height")
        self.height.textChanged.connect(self.slot_heightChanged)
        self.offsetX = self.findChild(QLineEdit, "offsetX")
        self.offsetX.textChanged.connect(self.slot_offsetXChanged)
        self.offsetY = self.findChild(QLineEdit, "offsetY")
        self.offsetY.textChanged.connect(self.slot_offsetYChanged)
        
        self.setActiveImageEntry(None)
        
    def setImagesetEntry(self, imagesetEntry):
        self.imagesetEntry = imagesetEntry
        
    def refresh(self):
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
        self.activeImageEntry = imageEntry
        
        self.refreshActiveImageEntry()
    
    def refreshActiveImageEntry(self):
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
        if event.key() == Qt.Key_Delete:
            selection = self.parent.scene.selectedItems()
            
            handled = self.parent.deleteImageEntries(selection)
            
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
        self.parent.scene.clearSelection()
        
        imageEntryNames = self.list.selectedItems()
        for imageEntryName in imageEntryNames:
            imageEntry = imageEntryName.imageEntry
            imageEntry.setSelected(True)
            
        if len(imageEntryNames) == 1:
            imageEntry = imageEntryNames[0].imageEntry
            self.parent.centerOn(imageEntry)
            
        self.selectionUnderway = False
        
    def slot_itemChanged(self, item):
        oldName = item.imageEntry.name
        newName = item.text()
        
        if oldName == newName:
            # most likely caused by RenameCommand doing it's work or is bogus anyways
            return
        
        cmd = undo.RenameCommand(self.parent, oldName, newName)
        self.parent.parent.undoStack.push(cmd)
    
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
        
        cmd = undo.ImagesetRenameCommand(self.parent, oldName, newName)
        self.parent.parent.undoStack.push(cmd)
        
    def slot_imageLoadClicked(self):
        oldImageFile = self.imagesetEntry.imageFile
        newImageFile = self.imagesetEntry.convertToRelativeImageFile(self.image.text())
        
        if oldImageFile == newImageFile:
            return
        
        cmd = undo.ImagesetChangeImageCommand(self.parent, oldImageFile, newImageFile)
        self.parent.parent.undoStack.push(cmd)
        
    def slot_autoScaledChanged(self, newState):
        oldAutoScaled = self.imagesetEntry.autoScaled
        newAutoScaled = self.autoScaled.checkState() == Qt.Checked
        
        if oldAutoScaled == newAutoScaled:
            return
        
        cmd = undo.ImagesetChangeAutoScaledCommand(self.parent, oldAutoScaled, newAutoScaled)
        self.parent.parent.undoStack.push(cmd)
        
    def slot_nativeResolutionEdited(self, newValue):
        oldHorzRes = self.imagesetEntry.nativeHorzRes
        oldVertRes = self.imagesetEntry.nativeVertRes
        newHorzRes = int(self.nativeHorzRes.text())
        newVertRes = int(self.nativeVertRes.text())
        
        if oldHorzRes == newHorzRes and oldVertRes == newVertRes:
            return
        
        cmd = undo.ImagesetChangeNativeResolutionCommand(self.parent, oldHorzRes, oldVertRes, newHorzRes, newVertRes)
        self.parent.parent.undoStack.push(cmd)

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
        
        cmd = undo.PropertyEditCommand(self.parent, self.activeImageEntry.name, propertyName, oldValue, newValue)
        self.parent.parent.undoStack.push(cmd)

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

class VisualEditing(QGraphicsView, mixedtab.EditMode):
    def __init__(self, parent):
        mixedtab.EditMode.__init__(self)
        
        self.scene = QGraphicsScene()
        QGraphicsView.__init__(self, self.scene)
        
        # use OpenGL for view redrawing
        # this has slightly better (and consistent) performance when it comes to lots of images
        self.setViewport(QGLWidget());
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate);
        
        self.scene.selectionChanged.connect(self.slot_selectionChanged)
        
        self.parent = parent

        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setBackgroundBrush(QBrush(Qt.lightGray))
        
        self.zoomFactor = 1.0
        self.imagesetEntry = None
        
        self.dockWidget = ImagesetEditorDockWidget(self)
    
        self.setupActions()
        self.setupToolBar()
        self.setupContextMenu()
    
    def setupActions(self):
        self.editOffsetsAction = QAction(QIcon("icons/imageset_editing/edit_offsets.png"), "Show and edit offsets", self)
        self.editOffsetsAction.setCheckable(True)
        self.editOffsetsAction.toggled.connect(self.slot_toggleEditOffsets)
        
        self.cycleOverlappingAction = QAction(QIcon("icons/imageset_editing/cycle_overlapping.png"), "Cycle overlapping images (Q)", self)
        self.cycleOverlappingAction.triggered.connect(self.cycleOverlappingImages)
        
        self.zoomOriginalAction = QAction(QIcon("icons/imageset_editing/zoom_original.png"), "Zoom original", self)
        self.zoomOriginalAction.triggered.connect(self.zoomOriginal)
        
        self.zoomInAction = QAction(QIcon("icons/imageset_editing/zoom_in.png"), "Zoom in (mouse wheel)", self)
        self.zoomInAction.triggered.connect(self.zoomIn)
        
        self.zoomOutAction = QAction(QIcon("icons/imageset_editing/zoom_out.png"), "Zoom out (mouse wheel)", self)
        self.zoomOutAction.triggered.connect(self.zoomOut)
        
        self.createImageAction = QAction(QIcon("icons/imageset_editing/create_image.png"), "Create image", self)
        self.createImageAction.triggered.connect(self.createImageAtCursor)
        
        self.deleteSelectedImagesAction = QAction(QIcon("icons/imageset_editing/delete_image.png"), "Delete selected images", self)
        self.deleteSelectedImagesAction.triggered.connect(self.deleteSelectedImageEntries)
        
    def setupToolBar(self):
        self.toolBar = QToolBar()
        
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
    
    def setupContextMenu(self):    
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
        
    def loadImagesetEntryFromElement(self, element):
        self.scene.clear()
        
        self.imagesetEntry = elements.ImagesetEntry(self)
        self.imagesetEntry.loadFromElement(element)
        
        boundingRect = self.imagesetEntry.boundingRect()
        boundingRect.adjust(-100, -100, 100, 100)
        self.scene.setSceneRect(boundingRect)
        
        self.scene.addItem(self.imagesetEntry)
        
        self.dockWidget.setImagesetEntry(self.imagesetEntry)
        self.dockWidget.refresh()
        
    def performZoom(self):
        transform = QTransform()
        transform.scale(self.zoomFactor, self.zoomFactor)
        self.setTransform(transform)
    
    def zoomOriginal(self):
        self.zoomFactor = 1
        self.performZoom()
    
    def zoomIn(self):
        self.zoomFactor *= 2
        
        if self.zoomFactor > 64:
            self.zoomFactor = 64
        
        self.performZoom()
    
    def zoomOut(self):
        self.zoomFactor /= 2
        
        if self.zoomFactor < 1:
            self.zoomFactor = 1
            
        self.performZoom()
        
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
            self.parent.undoStack.push(cmd)
            
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
                newRects[imageEntry.name] = newRect
                
            cmd = undo.GeometryChangeCommand(self, imageNames, oldPositions, oldRects, newPositions, newRects)
            self.parent.undoStack.push(cmd)
            
            # we handled this
            return True
        
        # we didn't handle this
        return False
        
    def cycleOverlappingImages(self):
        selection = self.scene.selectedItems()
            
        if len(selection) == 1:
            rect = selection[0].boundingRect()
            rect.translate(selection[0].pos())
            
            overlappingItems = self.scene.items(rect)
        
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
        self.parent.undoStack.push(cmd)
    
    def createImageAtCursor(self):
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
            self.parent.undoStack.push(cmd)
            
            return True
        
        else:
            # we didn't handle this
            return False
    
    def deleteSelectedImageEntries(self):
        selection = self.scene.selectedItems()
        
        imageEntries = []
        for item in selection:
            if isinstance(item, elements.ImageEntry):
                imageEntries.append(item)
        
        return self.deleteImageEntries(imageEntries)
    
    def showEvent(self, event):
        super(VisualEditing, self).showEvent(event)
        
        self.dockWidget.setEnabled(True)
        self.toolBar.setEnabled(True)
    
    def hideEvent(self, event):
        self.dockWidget.setEnabled(False)
        self.toolBar.setEnabled(False)
        
        super(VisualEditing, self).hideEvent(event)
    
    def mousePressEvent(self, event): 
        if event.buttons() != Qt.MiddleButton:
            super(VisualEditing, self).mousePressEvent(event) 
            
            if event.buttons() & Qt.LeftButton:
                for selectedItem in self.scene.selectedItems():
                    # selectedItem could be ImageEntry or ImageOffset!                    
                    selectedItem.potentialMove = True
                    selectedItem.oldPosition = None
        else:
            self.lastMousePosition = event.pos()
    
    def mouseReleaseEvent(self, event):
        if event.buttons() != Qt.MiddleButton:
            super(VisualEditing, self).mouseReleaseEvent(event)
            
            imageNames = []
            imageOldPositions = {}
            imageNewPositions = {}
            
            offsetNames = []
            offsetOldPositions = {}
            offsetNewPositions = {}
            
            for selectedItem in self.scene.selectedItems():
                if isinstance(selectedItem, elements.ImageEntry):
                    if selectedItem.oldPosition:
                        imageNames.append(selectedItem.name)
                        imageOldPositions[selectedItem.name] = selectedItem.oldPosition
                        imageNewPositions[selectedItem.name] = selectedItem.pos()
                        
                    selectedItem.potentialMove = False
                    selectedItem.oldPosition = None
                    
                elif isinstance(selectedItem, elements.ImageOffset):
                    if selectedItem.oldPosition:
                        offsetNames.append(selectedItem.parent.name)
                        offsetOldPositions[selectedItem.parent.name] = selectedItem.oldPosition
                        offsetNewPositions[selectedItem.parent.name] = selectedItem.pos()
                        
                    selectedItem.potentialMove = False
                    selectedItem.oldPosition = None
            
            if len(imageNames) > 0:
                cmd = undo.MoveCommand(self, imageNames, imageOldPositions, imageNewPositions)
                self.parent.undoStack.push(cmd)
                
            if len(offsetNames) > 0:
                cmd = undo.OffsetMoveCommand(self, offsetNames, offsetOldPositions, offsetNewPositions)
                self.parent.undoStack.push(cmd)
        else:
            pass
    
    def mouseMoveEvent(self, event): 
        if event.buttons() != Qt.MiddleButton: 
            super(VisualEditing, self).mouseMoveEvent(event)
            
        else:
            horizontal = self.horizontalScrollBar()
            horizontal.setSliderPosition(horizontal.sliderPosition() - (event.pos().x() - self.lastMousePosition.x()))
            vertical = self.verticalScrollBar()
            vertical.setSliderPosition(vertical.sliderPosition() - (event.pos().y() - self.lastMousePosition.y()))
            
        self.lastMousePosition = event.pos() 
    
    def wheelEvent(self, event):
        if event.delta() == 0:
            return
        
        if event.delta() > 0:
            self.zoomIn()
        else:
            self.zoomOut()
            
    def keyReleaseEvent(self, event):
        handled = False
        
        if event.key() in [Qt.Key_A, Qt.Key_D, Qt.Key_W, Qt.Key_S]:
            selection = self.scene.selectedItems()
            
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
        
        selectedItems = self.scene.selectedItems()
        if len(selectedItems) == 1:
            self.dockWidget.list.scrollToItem(selectedItems[0].listItem)
        
    def slot_toggleEditOffsets(self, enabled):
        self.scene.clearSelection()
        
        self.imagesetEntry.showOffsets = enabled
        
    def slot_customContextMenu(self, point):
        self.contextMenu.exec_(self.mapToGlobal(point))
    