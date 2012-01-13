"""Provides a way to build, categorise, visualise and edit a list of properties.

properties -- Built-in properties, representing one simple value.
compositeproperties -- Built-in composite properties based on several simple properties.
editors -- Editors, each supporting a specific set of property types.
ui -- The Qt GUI widget and its supporting classes.
"""

__all__ = ["properties", "compositeproperties", "editors", "ui"]

# Everything below will be removed, I'm just testing it
from properties import Property
from properties import PropertyCategory

from compositeproperties import DictionaryProperty

from editors import PropertyEditorRegistry

from ui import PropertyTreeWidget
from ui import PropertyTreeItemDelegate

from PySide.QtGui import QDockWidget
from PySide.QtGui import QWidget
from PySide.QtGui import QVBoxLayout
from PySide.QtGui import QPushButton

class TestDock(QDockWidget):
    def __init__(self):
        super(TestDock, self).__init__()

        self.setWindowTitle("Test Dock")
        self.setMinimumWidth(400)
        
        self.view = PropertyTreeWidget()
        self.view.setupRegistry(PropertyEditorRegistry(True))
        
        # root widget and layout
        contentsWidget = QWidget()
        contentsLayout = QVBoxLayout()
        contentsWidget.setLayout(contentsLayout)
        margins = contentsLayout.contentsMargins()
        margins.setTop(0)
        contentsLayout.setContentsMargins(margins)

        contentsLayout.addWidget(self.view)
        self.setWidget(contentsWidget)
        
        def test():
            self.props[1].components["X"].setValue(20)
        
        testButton = QPushButton()
        testButton.setText("Test")
        testButton.clicked.connect(test)
        contentsLayout.addWidget(testButton)
        
        self.setup()

    def setup(self):
        from collections import OrderedDict
        # TODO: Write CEGUI widget property creator/loader that
        # creates the properties and destroys them
        
        colourProp = DictionaryProperty(
                                        name = "Colour",
                                        value = OrderedDict([
                                                             ("Red", 160),
                                                             ("Green", 255),
                                                             ("Blue", 160)
                                                             ]),
                                        editorOptions = {"instantApply":False, "numeric": {"min":0, "max":255, "step": 8}}
                                        )
        
        props = [
                Property("stringProperty", "Hello", "Hello", "Default Category", "This is a string property"),
                Property(name = "fourHexChars", value = "0xDEAD", defaultValue="0xBEEF", editorOptions = {
                                                                         "string": {"inputMask":"\\0\\xHHHH;_"}
                                                                         }),
                Property(name = "fourDigits", value = "1234", defaultValue="1337", editorOptions = {
                                                                         "string": {"inputMask":"9999;_"}
                                                                         }),
                DictionaryProperty("dictionary", OrderedDict([
                                                              ("X", 0),
                                                              ("Y", 0),
                                                              ("Width", 50),
                                                              ("Height", 50),
                                                              ("Colour", colourProp)
                                                              ]),
                                   readOnly=False)
                ]
        categories = PropertyCategory.categorisePropertyList(props)
        # test: add the property to another category too!
        categories["Default Category"].properties["dictionary"] = props[1]
        # load
        self.view.load(categories)
        self.props = props
