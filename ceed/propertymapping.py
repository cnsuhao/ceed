from collections import OrderedDict

from xml.etree import ElementTree

class PropertyMappingEntry(object):
    """Maps a CEGUI::Property (by origin and name) to a CEGUI Type and PropertyEditor
    to allow its viewing and editing.
    
    If target inspector name is \"\" then this mapping means that the property should
    be ignored in the property set inspector listing.
    """

    @classmethod
    def fromElement(cls, element):
        propertyOrigin = element.get("propertyOrigin")
        propertyName = element.get("propertyName")
        typeName = element.get("typeName")
        hidden = element.get("hidden", "False").lower() in ("true", "yes", "1")
        editorName = element.get("editorName")

        editorSettings = dict()
        for settings in element.findall("settings"):
            name = settings.get("name")
            t = OrderedDict()

            for setting in settings.findall("setting"):
                t[setting.get("name")] = setting.get("value")

            editorSettings[name] = t

        return cls(propertyOrigin = propertyOrigin,
                   propertyName = propertyName,
                   typeName = typeName,
                   hidden = hidden,
                   editorName = editorName,
                   editorSettings = editorSettings)

    @classmethod
    def makeKey(cls, propertyOrigin, propertyName):
        return "/".join((propertyOrigin, propertyName)) 

    def __init__(self, propertyOrigin, propertyName,
                 typeName = None, hidden = False,
                 editorName = None, editorSettings = None):

        self.propertyOrigin = propertyOrigin
        self.propertyName = propertyName
        self.typeName = typeName
        self.hidden = hidden
        self.editorName = editorName
        self.editorSettings = editorSettings if editorSettings is not None else dict()

    def getPropertyKey(self):
        return self.makeKey(self.propertyOrigin, self.propertyName) 

    def saveToElement(self):
        element = ElementTree.Element("mapping")

        element.set("propertyOrigin", self.propertyOrigin)
        element.set("propertyName", self.propertyName)
        if self.typeName:
            element.set("typeName", self.typeName)
        if self.hidden:
            element.set("hidden", True)
        if self.editorName:
            element.set("editorName", self.editorName)

        for name, value in self.editorSettings:
            settings = ElementTree.Element("settings")
            settings.set("name", name)
            for sname, svalue in value:
                setting = ElementTree.Element("setting")
                setting.set("name", sname)
                setting.set("value", svalue)
                element.append(setting)
            element.append(settings)

        return element

class PropertyMap(object):

    @classmethod
    def fromElement(cls, element):
        assert(element.get("version") == compat.Manager.instance.EditorNativeType)

        pmap = cls()
        for entryElement in element.findall("mapping"):
            entry = PropertyMappingEntry.fromElement(entryElement)
            pmap.setEntry(entry)
        return pmap

    @classmethod
    def fromXMLString(cls, text):
        element = ElementTree.fromstring(text)
        return cls.fromElement(element)

    @classmethod
    def fromFile(cls, absolutePath):
        text = open(absolutePath, "r").read()
        return cls.fromXMLString(text)

    @classmethod
    def fromFiles(cls, absolutePaths):
        pmap = cls()
        for absolutePath in absolutePaths:
            pmap.update(cls.fromFile(absolutePath))

        return pmap

    def __init__(self):
        self.entries = dict()

    def saveToElement(self):
        element = ElementTree.Element("mappings")
        element.set("version", compat.Manager.instance.EditorNativeType)

        for entry in sorted(self.entries, key = lambda entry: entry.getPropertyKey()):
            eel = entry.saveToElement()
            element.append(eel)

        return element

    def getEntry(self, propertyOrigin, propertyName):
        entry = self.entries.get(PropertyMappingEntry.makeKey(propertyOrigin, propertyName))
        return entry

    def setEntry(self, entry):
        self.entries[entry.getPropertyKey()] = entry

    def update(self, pmap):
        self.entries.update(pmap.entries)

from ceed.compatibility import property_mappings as compat
