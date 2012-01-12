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

from PySide.QtCore import Qt
from PySide.QtCore import QModelIndex

class PropertyTreeItem(QStandardItem):

    def __init__(self, propertyTreeRow):
        super(PropertyTreeItem, self).__init__()

        self.propertyTreeRow = propertyTreeRow

    def finalise(self):
        self.propertyTreeRow = None

class PropertyTreeRow(object):

    def __init__(self):
        self.nameItem = PropertyTreeItem(self)
        self.valueItem = PropertyTreeItem(self)
        self.editor = None
        self.finalised = False

    def finalise(self):
        # TODO: Remove print
        print("Finalising row with nameItem.text() = " + str(self.nameItem.text()))
        if not self.finalised:
            # Finalise children before clearing nameItem or we can't get them
            for row in self.childRows():
                row.finalise()
                # Will be removed from the tree automatically

            self.nameItem.finalise(); self.nameItem = None
            self.valueItem.finalise(); self.valueItem = None
            self.finalised = True

    def childRows(self):
        return [self.nameItem.child(childRowIndex).propertyTreeRow for childRowIndex in range(0, self.nameItem.rowCount())]

    def appendChildRow(self, row):
        self.nameItem.appendRow([row.nameItem, row.valueItem])

class PropertyCategoryRow(PropertyTreeRow):

    def __init__(self, propertyCategory):
        super(PropertyCategoryRow, self).__init__()

        self.category = propertyCategory

        self.nameItem.setEditable(False)
        self.nameItem.setText(self.category.name)

        self.valueItem.setEditable(False)

        palette = QApplication.palette()
        self.nameItem.setForeground(palette.brush(QPalette.Normal, QPalette.BrightText))
        self.nameItem.setBackground(palette.brush(QPalette.Normal, QPalette.Dark))

        for prop in self.category.properties.values():
            row = PropertyRow(prop)
            self.appendChildRow(row)

class PropertyRow(PropertyTreeRow):

    def __init__(self, boundProperty):
        super(PropertyRow, self).__init__()

        self.property = boundProperty

        self.nameItem.setEditable(False)
        self.nameItem.setText(self.property.name)

        self.valueItem.setEditable(not self.property.readOnly)
        self.valueItem.setText(self.property.valueToString())

        self.property.valueChanged.add(self.propertyValueChanged)

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

    def propertyValueChanged(self, component, reason):
        self.valueItem.setText(self.property.valueToString())

class PropertyTreeItemDelegate(QStyledItemDelegate):

    def __init__(self, propertyTree, editorRegistry):
        super(PropertyTreeItemDelegate, self).__init__(propertyTree)

        self.registry = editorRegistry

    def getPropertyRow(self, index):
        if index.isValid():
            return self.parent().model.itemFromIndex(index).propertyTreeRow
        return None

    def createEditor(self, parent, option, index):
        row = self.getPropertyRow(index)
        if row is None:
            return

        row.editor = self.registry.createEditor(row.property)
        if row.editor is None:
            return None

        editWidget = row.editor.createEditWidget(parent)

        return editWidget

    def setEditorData(self, editWidget, index):
        row = self.getPropertyRow(index)
        if row is None:
            return

        row.editor.setWidgetValueFromProperty()

    def setModelData(self, editorWidget, model, index):
        row = self.getPropertyRow(index)
        if row is None:
            return

        row.editor.setPropertyValueFromWidget()

class PropertyTreeView(QTreeView):

    def drawRow(self, painter, option, index):
        super(PropertyTreeView, self).drawRow(painter, option, index)

        returnData = QStyleHintReturn()
        gridHint = self.style().styleHint(QStyle.SH_Table_GridLineColor, option, self, returnData)
        gridColor = QColor(gridHint & 0xFFFFFF)
        gridPen = QPen(gridColor)
        colX = self.columnViewportPosition(1) - 1
        drawVertical = not self.isFirstColumnSpanned(index.row(), index.parent())

        painter.save()
        painter.setPen(gridPen)
        painter.drawLine(option.rect.x(), option.rect.bottom(), option.rect.right(), option.rect.bottom())
        if drawVertical:
            painter.drawLine(colX, option.rect.y(), colX, option.rect.bottom())
        painter.restore()

    def currentChanged(self, currentIndex, previousIndex):
        QTreeView.currentChanged(self, currentIndex, previousIndex)
        if currentIndex.isValid() and currentIndex.column() == 0:
            valueIndex = currentIndex.sibling(currentIndex.row(), 1)
            if valueIndex.isValid():
                flags = valueIndex.flags()
                if (flags & Qt.ItemIsSelectable) and (flags & Qt.ItemIsEditable) and (flags & Qt.ItemIsEnabled):
                    self.setCurrentIndex(valueIndex)

# http://www.qtforum.org/post/81956/qtreeview-qstandarditem-and-singals.html#post81956

class PropertyTreeWidget(QWidget):

    def __init__(self, parent = None):
        super(PropertyTreeWidget, self).__init__(parent)

        self.model = QStandardItemModel()
        def rowsAboutToBeRemoved(parentIndex, start, end):
            for i in range(start, end+1):
                mi = self.model.index(i, 0, parentIndex)
                item = self.model.itemFromIndex(mi)
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

    def setupRegistry(self, registry):
        self.registry = registry
        itemDelegate = PropertyTreeItemDelegate(self, self.registry)
        self.view.setItemDelegate(itemDelegate)

    def load(self, categoryList):
        self.view.setUpdatesEnabled(False)
        self.model.clear()
        self.model.setColumnCount(2)
        self.model.setHorizontalHeaderLabels(["Property", "Value"])

        for category in categoryList.values():
            self.appendCategory(category)

        self.view.expandAll()
        self.view.resizeColumnToContents(0)
        self.view.setUpdatesEnabled(True)

    def appendCategory(self, category):
        row = PropertyCategoryRow(category)
        self.model.appendRow([row.nameItem, row.valueItem])
        self.view.setFirstColumnSpanned(self.model.rowCount() - 1, QModelIndex(), True)
