##############################################################################
#   CEED - Unified CEGUI asset editor
#
#   Copyright (C) 2011-2014   Martin Preisler <martin@preisler.me>
#                             and contributing authors (see AUTHORS file)
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
##############################################################################

from PySide import QtCore
from PySide import QtGui
import cPickle

from ceed import settings

from ceed.editors.looknfeel import widgethelpers

from hierarchy_tree_item import LookNFeelHierarchyItem

class LookNFeelHierarchyTreeModel(QtGui.QStandardItemModel):
    def __init__(self, dockWidget):
        super(LookNFeelHierarchyTreeModel, self).__init__()

        self.dockWidget = dockWidget
        """ :type : LookNFeelHierarchyDockWidget """
        self.setItemPrototype(LookNFeelHierarchyItem(None))

        self.widgetLookObject = None

        self.limitDisplayTo = None
        """ A string defining a name of a StateImagery. This StateImagery, and everything referenced within it, will be the only one
        to be displayed in the hierarchy. The value None means there won't be any limitation and everything will be displayed. """

    def updateTree(self, widgetLookObject, limitDisplayTo):
        """
        Sets the WidgetLookFeel object based on which this widget should create the hierarchy.
        Rebuilds the hierarchy tree based on a WidgetFeelLook object.
        :param widgetLookObject: PyCEGUI.WidgetLookFeel
        :param limitDisplayTo: str
        :return:
        """

        self.limitDisplayTo = limitDisplayTo
        self.widgetLookObject = widgetLookObject

        # Clear any existing hierarchy
        self.clear()

        if self.widgetLookObject is None:
            return

        self.createAndAddItem(self.widgetLookObject)
        if self.limitDisplayTo is None:
            self.appendAllWidgetLookFeelChildren(self.widgetLookObject)
        else:
            self.appendOnlyWidgetLookFeelElementsReferencedInStateImagery(self.widgetLookObject)

    def appendAllWidgetLookFeelChildren(self, widgetLookObject):
        """
        Iterates over all contained elements of the WidgetLookFeel. Creates the contained elements as
        new items and appends them to this tree view's root item
        :param widgetLookObject: PyCEGUI.WidgetLookFeel
        :return:
        """

        namedAreaIter = widgetLookObject.getNamedAreaIterator()
        while not namedAreaIter.isAtEnd():
            currentNamedArea = namedAreaIter.getCurrentValue()
            self.createAndAddItem(currentNamedArea)
            namedAreaIter.next()

        imageryIter = widgetLookObject.getImageryIterator()
        while not imageryIter.isAtEnd():
            currentImagerySection = imageryIter.getCurrentValue()
            self.createAndAddItem(currentImagerySection)
            imageryIter.next()

        stateIter = widgetLookObject.getStateIterator()
        while not stateIter.isAtEnd():
            currentStateImagery = stateIter.getCurrentValue()
            self.createAndAddItem(currentStateImagery)
            stateIter.next()

        childWidgetIter = widgetLookObject.getWidgetComponentIterator()
        while not childWidgetIter.isAtEnd():
            currentChildWidget = childWidgetIter.getCurrentValue()
            self.createAndAddItem(currentChildWidget)
            childWidgetIter.next()

    def appendOnlyWidgetLookFeelElementsReferencedInStateImagery(self, widgetLookObject):
        """
        Iterates over all contained elements of the WidgetLookFeel. It will add only those elements
        which are referenced by the StateImagery that was selected to be viewed. Additionally, it will add
        the elements referenced from within the StateImagery, which are part of the WidgetLookFeel

        :param widgetLookObject: PyCEGUI.WidgetLookFeel
        :return:
        """
        displayedStateImageryName = self.limitDisplayTo
        displayedStateImagery = None

        # Iterate through all StateImageries to see if we find the StateImagery
        # we want to exclusively display in the hierarchy
        stateIter = widgetLookObject.getStateIterator()
        while not stateIter.isAtEnd():
            currentStateImagery = stateIter.getCurrentValue()

            if displayedStateImageryName == currentStateImagery.getName():
                displayedStateImagery = currentStateImagery
                break
            stateIter.next()

        # If no StateImagery was found we don't add a hierarchy
        if displayedStateImagery is None:
            return

        referencedImagerySections = []
        # We iterate over all layers and all SectionSpecification in the layers, looking for all
        # ImagerySections that are referenced from there and are "owned" by this WidgetLookFeel
        # (They could also be inside another WLF definition, in which case we won't display them)
        # All such ImagerySections will be added to a list
        layerIter = displayedStateImagery.getLayerIterator()
        while not layerIter.isAtEnd():
            layer = layerIter.getCurrentValue()
            sectionIter = layer.getSectionIterator()

            while not sectionIter.isAtEnd():
                currentSectionSpecification = sectionIter.getCurrentValue()
                ownerWidgetFeel = currentSectionSpecification.getOwnerWidgetLookFeel()
                if ownerWidgetFeel == self.widgetLookObject.getName():
                    referencedImagerySections.append(currentSectionSpecification.getSectionName())

                sectionIter.next()
            layerIter.next()

        #We make each ImagerySection unique using a set
        imagerySectionNamesSet = set(referencedImagerySections)
        for imagerySectionName in imagerySectionNamesSet:
            imagerySection = widgetLookObject.getImagerySection(imagerySectionName)
            self.createAndAddItem(imagerySection)

        # At last we end the StateImagery itself to the root
        self.createAndAddItem(displayedStateImagery)

    def createAndAddItem(self, widgetLookElement):
        """
        Creates an item based on the supplied object and appends it to the rootItem of this tree model
        :param widgetLookElement:
        :return:
        """
        if widgetLookElement is None:
            raise Exception("Invalid parameter supplied to LookNFeelHierarchyTreeModel.createAndAddItem")
        rootItem = self.invisibleRootItem()

        newItem = LookNFeelHierarchyItem(widgetLookElement)
        rootItem.appendRow(newItem)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        return super(LookNFeelHierarchyTreeModel, self).data(index, role)

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        return super(LookNFeelHierarchyTreeModel, self).setData(index, value, role)

    def flags(self, index):
        return super(LookNFeelHierarchyTreeModel, self).flags(index)

    def shouldManipulatorBeSkipped(self, manipulator):
        return \
           manipulator.widget.isAutoWindow() and \
           settings.getEntry("looknfeel/visual/hide_deadend_autowidgets").value and \
           not manipulator.hasNonAutoWidgetDescendants()

    def constructSubtree(self, manipulator):
        ret = LookNFeelHierarchyItem(manipulator)

        manipulatorChildren = []

        for item in manipulator.childItems():
            if isinstance(item, widgethelpers.Manipulator):
                manipulatorChildren.append(item)

        manipulatorChildren = sorted(manipulatorChildren, key = lambda item: item.getWidgetPath())

        for item in manipulatorChildren:
            if self.shouldManipulatorBeSkipped(item):
                # skip this branch as per settings
                continue

            childSubtree = self.constructSubtree(item)
            ret.appendRow(childSubtree)

        return ret

    def synchroniseSubtree(self, hierarchyItem, manipulator, recursive = True):
        """Attempts to synchronise subtree with given widget manipulator.
        If such a thing isn't possible it returns False.

        recursive - If True the synchronisation will recurse, trying to
                    unify child widget hierarchy items with child manipulators.
                    (This is generally what you want to do)
        """

        if hierarchyItem is None or manipulator is None:
            # no manipulator = no hierarchy item, we definitely can't synchronise
            return False

        if hierarchyItem.manipulator is not manipulator:
            # this widget hierarchy item itself will need to be recreated
            return False

        hierarchyItem.refreshPathData(False)

        if recursive:
            manipulatorsToRecreate = manipulator.getChildManipulators()

            i = 0
            # we knowingly do NOT use range in here, the rowCount might change
            # while we are processing!
            while i < hierarchyItem.rowCount():
                childHierarchyItem = hierarchyItem.child(i)

                if childHierarchyItem.manipulator in manipulatorsToRecreate and \
                   self.synchroniseSubtree(childHierarchyItem, childHierarchyItem.manipulator, True):
                    manipulatorsToRecreate.remove(childHierarchyItem.manipulator)
                    i += 1

                else:
                    hierarchyItem.removeRow(i)

            for childManipulator in manipulatorsToRecreate:
                if self.shouldManipulatorBeSkipped(childManipulator):
                    # skip this branch as per settings
                    continue

                hierarchyItem.appendRow(self.constructSubtree(childManipulator))

        return True

    def mimeData(self, indexes):
        # if the selection contains children of something that is also selected, we don't include that
        # (it doesn't make sense to move it anyways, it will be moved with its parent)

        def isChild(parent, potentialChild):
            i = 0
            # DFS, Qt doesn't have helper methods for this it seems to me :-/
            while i < parent.rowCount():
                child = parent.child(i)

                if child is potentialChild:
                    return True

                if isChild(child, potentialChild):
                    return True

                i += 1

            return False

        topItems = []

        for index in indexes:
            item = self.itemFromIndex(index)
            hasParent = False

            for parentIndex in indexes:
                if parentIndex is index:
                    continue

                potentialParent = self.itemFromIndex(parentIndex)

                if isChild(item, potentialParent):
                    hasParent = True
                    break

            if not hasParent:
                topItems.append(item)

        data = []
        for item in topItems:
            data.append(item.data(QtCore.Qt.UserRole))

        ret = QtCore.QMimeData()
        ret.setData("application/x-ceed-widget-paths", cPickle.dumps(data))

        return ret

    def mimeTypes(self):
        return ["application/x-ceed-widget-paths", "application/x-ceed-widget-type"]

    def dropMimeData(self, data, action, row, column, parent):
        return False