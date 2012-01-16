"""Qt property tree widget supporting classes.

PropertyTreeItem -- Base item for all items.
PropertyTreeRow -- Pair of name and value items, manages it's child rows.
PropertyCategoryRow -- Special tree items placed at the root of the tree.
PropertyRow -- Tree row bound to a Property.
PropertyTreeItemDelegate -- Facilitates editing of the rows' values.
PropertyTreeView -- QTreeView with some modifications for better results.
PropertyTreeWidget -- The property tree widget.
"""

from .properties import Property
from .properties import StringWrapperProperty
from .editors import StringWrapperValidator

from PySide.QtGui import QStandardItem
from PySide.QtGui import QApplication
from PySide.QtGui import QPalette
from PySide.QtGui import QColor
from PySide.QtGui import QPen
from PySide.QtGui import QStyleHintReturn
from PySide.QtGui import QTreeView
from PySide.QtGui import QStyledItemDelegate
from PySide.QtGui import QStyle
from PySide.QtGui import QWidget
from PySide.QtGui import QStandardItemModel
from PySide.QtGui import QAbstractItemView
from PySide.QtGui import QVBoxLayout
from PySide.QtGui import QHeaderView

from PySide.QtCore import Qt
from PySide.QtCore import QModelIndex
from PySide.QtCore import QSize

class PropertyTreeItem(QStandardItem):
    """Base item for all items."""

    def __init__(self, propertyTreeRow):
        super(PropertyTreeItem, self).__init__()

        self.setSizeHint(QSize(-1, 24))
        self.propertyTreeRow = propertyTreeRow

        self.finalised = False

    def finalise(self):
        self.propertyTreeRow = None
        self.finalised = True

    def bold(self):
        return self.font().bold()

    def setBold(self, value):
        font = self.font()
        font.setBold(value)
        self.setFont(font)

class PropertyTreeRow(object):
    """Pair of name and value items, manages it's child rows."""
    def __init__(self):
        self.nameItem = PropertyTreeItem(self)
        self.valueItem = PropertyTreeItem(self)
        self.editor = None
        self.finalised = False

        self.createChildRows()

    def finalise(self):
        # TODO: Remove print
        print("Finalising row with nameItem.text() = " + str(self.nameItem.text()))
        if not self.finalised:
            # Finalise children before clearing nameItem or we can't get them
            self.destroyChildRows()

            self.nameItem.finalise(); self.nameItem = None
            self.valueItem.finalise(); self.valueItem = None
            self.finalised = True

    def childRows(self):
        """Get the child rows; self.nameItem must exist and be valid."""
        return [self.nameItem.child(childRowIndex).propertyTreeRow for childRowIndex in range(0, self.nameItem.rowCount())]

    def appendChildRow(self, row):
        self.nameItem.appendRow([row.nameItem, row.valueItem])

    def createChildRows(self):
        """Create and add child rows."""
        pass

    def destroyChildRows(self):
        for row in self.childRows():
            row.finalise()
        self.nameItem.setRowCount(0)

class PropertyCategoryRow(PropertyTreeRow):
    """Special tree items placed at the root of the tree."""

    def __init__(self, propertyCategory):
        # set the category before super init because
        # we need it in createChildRows() which is
        # called by super init.
        self.category = propertyCategory

        super(PropertyCategoryRow, self).__init__()

        self.nameItem.setEditable(False)
        self.nameItem.setText(self.category.name)
        self.nameItem.setBold(True)

        self.valueItem.setEditable(False)

        # Change default colours
        palette = QApplication.palette()
        self.nameItem.setForeground(palette.brush(QPalette.Normal, QPalette.BrightText))
        self.nameItem.setBackground(palette.brush(QPalette.Normal, QPalette.Dark))

    def createChildRows(self):
        for prop in self.category.properties.values():
            row = PropertyRow(prop)
            self.appendChildRow(row)

class PropertyRow(PropertyTreeRow):
    """Tree row bound to a Property."""

    def __init__(self, boundProperty):
        # set the property before super init because
        # we need it in createChildRows() which is
        # called by super init.
        self.property = boundProperty

        super(PropertyRow, self).__init__()

        self.nameItem.setEditable(False)
        self.nameItem.setText(self.property.name)
        if self.property.helpText:
            self.nameItem.setToolTip(self.property.helpText)

        self.valueItem.setEditable(not self.property.readOnly)
        self.valueItem.setText(self.property.valueToString())

        self.property.valueChanged.add(self.propertyValueChanged)
        self.property.componentsUpdate.add(self.propertyComponentsUpdate)

        self.updateStyle()

    def createChildRows(self):
        components = self.property.getComponents()
        if components:
            for component in components.values():
                row = PropertyRow(component)
                self.appendChildRow(row)

    def finalise(self):
        # TODO: uncomment below to be safe, it's commented to test execution order
        #if self.propertyValueChanged in self.property.valueChanged:
        self.property.valueChanged.remove(self.propertyValueChanged)

        super(PropertyRow, self).finalise()

    def propertyComponentsUpdate(self, senderProperty, updateType):
        # destroy or recreate child rows as necessary
        if updateType == Property.ComponentsUpdateType.BeforeDestroy:
            self.destroyChildRows()
        elif updateType == Property.ComponentsUpdateType.AfterCreate:
            self.createChildRows()

    def propertyValueChanged(self, senderProperty, reason):
        self.valueItem.setText(self.property.valueToString())

        self.updateStyle()

    def updateStyle(self):
        """Update the style of the row,
        i.e. make the name bold if the property value is not the default.
        """
        self.nameItem.setBold(not self.property.hasDefaultValue())

class PropertyTreeItemDelegate(QStyledItemDelegate):
    """Facilitates editing of the rows' values."""

    # Sample delegate
    # http://www.qtforum.org/post/81956/qtreeview-qstandarditem-and-singals.html#post81956

    def __init__(self, propertyTree, editorRegistry):
        super(PropertyTreeItemDelegate, self).__init__(propertyTree)

        self.registry = editorRegistry

    def getPropertyRow(self, index):
        if index.isValid():
            return self.parent().model.itemFromIndex(index).propertyTreeRow
        return None

    def createEditor(self, parent, option, index):
        # get the PropertyRow from the index
        row = self.getPropertyRow(index)
        if row is None:
            return

        # try to create an editor for the property
        row.editor = self.registry.createEditor(row.property)
        if row.editor is None:
            # if no suitable editor was found and the property
            # supports editing it as a string, wrap it and fire
            # up the string editor.
            if row.property.isStringRepresentationEditable():
                wrapperProperty = StringWrapperProperty(row.property)
                wrapperProperty.editorOptions["string"] = { "validator": StringWrapperValidator(row.property) }
                row.editor = self.registry.createEditor(wrapperProperty)
            if row.editor is None:
                return None

        # tell the newly created editor to create its widget
        editWidget = row.editor.createEditWidget(parent)

        return editWidget

    def setEditorData(self, editWidget, index):
        """Set the value of the editor to the property's value."""
        row = self.getPropertyRow(index)
        if row is None:
            return

        row.editor.setWidgetValueFromProperty()

    def setModelData(self, editorWidget, model, index):
        """Set the value of the property to the editor's value."""
        row = self.getPropertyRow(index)
        if row is None:
            return

        row.editor.setPropertyValueFromWidget()

class PropertyTreeView(QTreeView):
    """QTreeView with some modifications for better results."""

    def drawRow(self, painter, option, index):
        """Draws grid lines.
        
        Yep, that's all it does.
        """
        super(PropertyTreeView, self).drawRow(painter, option, index)

        # get color for grid lines from the style
        returnData = QStyleHintReturn()
        gridHint = self.style().styleHint(QStyle.SH_Table_GridLineColor, option, self, returnData)
        gridColor = QColor(gridHint & 0xFFFFFF)
        # setup a pen
        gridPen = QPen(gridColor)
        # x coordinate to draw the vertical line (between the first and the second column)
        colX = self.columnViewportPosition(1) - 1
        # do not draw verticals on spanned rows (i.e. categories)
        drawVertical = not self.isFirstColumnSpanned(index.row(), index.parent())

        # save painter state so we can leave it as it was
        painter.save()
        painter.setPen(gridPen)
        painter.drawLine(option.rect.x(), option.rect.bottom(), option.rect.right(), option.rect.bottom())
        if drawVertical:
            painter.drawLine(colX, option.rect.y(), colX, option.rect.bottom())
        # aaaand restore
        painter.restore()

    def currentChanged(self, currentIndex, previousIndex):
        """Move the focus to the value item, necessary or the
        focus can stay on the name item that's not editable and
        hitting the edit key does nothing.
        """
        # call super
        QTreeView.currentChanged(self, currentIndex, previousIndex)
        # if on column 0 (the name item)
        if currentIndex.isValid() and currentIndex.column() == 0:
            # if it has a sibling (value item), get it
            valueIndex = currentIndex.sibling(currentIndex.row(), 1)
            # if the value item is valid...
            if valueIndex.isValid():
                flags = valueIndex.flags()
                # ... and if it is selectable and not disabled
                if (flags & Qt.ItemIsSelectable) and (flags & Qt.ItemIsEditable) and (flags & Qt.ItemIsEnabled):
                    # blah
                    self.setCurrentIndex(valueIndex)

class PropertyTreeWidget(QWidget):
    """The property tree widget.
    
    Sets up and options necessary.
    Provides easy access methods.
    """

    def __init__(self, parent = None):
        """Initialise the widget instance.
        
        'setupRegistry()' should be called next,
        before any property editing can happen.
        """
        super(PropertyTreeWidget, self).__init__(parent)

        # create model
        self.model = QStandardItemModel()

        # finalise rows that are being removed
        def rowsAboutToBeRemoved(parentIndex, start, end):
            for i in range(start, end+1):
                mi = self.model.index(i, 0, parentIndex)
                item = self.model.itemFromIndex(mi)
                if not item.finalised:
                    row = item.propertyTreeRow
                    row.finalise()
        self.model.rowsAboutToBeRemoved.connect(rowsAboutToBeRemoved)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.view = PropertyTreeView(self)
        self.view.setEditTriggers(QAbstractItemView.EditKeyPressed | QAbstractItemView.SelectedClicked | QAbstractItemView.DoubleClicked)
        self.view.setTabKeyNavigation(True)
        self.view.setAlternatingRowColors(True)
        self.view.setIndentation(20)
        self.view.setRootIsDecorated(False)
        self.view.setItemsExpandable(True)
        self.view.setSortingEnabled(True)
        self.view.setAnimated(False)
        self.view.setExpandsOnDoubleClick(True)
        self.view.setUniformRowHeights(True)
        self.view.setAllColumnsShowFocus(True)
        self.view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.view.setObjectName("view")
        self.view.setModel(self.model)

        layout.addWidget(self.view)

        self.registry = None

        self.clear()

    def setupRegistry(self, registry):
        """Setup the registry and the item delegate."""
        self.registry = registry
        itemDelegate = PropertyTreeItemDelegate(self, self.registry)
        self.view.setItemDelegate(itemDelegate)

    def clear(self):
        """Clear the tree."""
        self.model.clear()
        self.model.setHorizontalHeaderLabels(["Property", "Value"])

    def load(self, categories):
        """Clear tree and load the specified categories into it.
        
        categories -- Dictionary
        """
        
        # prevent flicker
        self.view.setUpdatesEnabled(False)

        # clear and setup
        self.clear()

        # add all categories
        for category in categories.values():
            self.appendCategory(category)

        self.view.expandAll()
        self.view.header().setResizeMode(QHeaderView.Stretch)
        #self.view.resizeColumnToContents(0)
        
        # reset updates
        self.view.setUpdatesEnabled(True)

    def appendCategory(self, category):
        row = PropertyCategoryRow(category)
        self.model.appendRow([row.nameItem, row.valueItem])
        # make the category name span two columns (all)
        self.view.setFirstColumnSpanned(self.model.rowCount() - 1, QModelIndex(), True)
