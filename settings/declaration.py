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

class Entry(object):
    STRING = "string"
    
    value = property(fset = lambda entry, value: entry._setValue(value),
                     fget = lambda entry: entry._value)
    editedValue = property(fset = lambda entry, value: entry._setEditedValue(value),
                           fget = lambda entry: entry._editedValue)
    
    
    def __init__(self, section, name, defaultValue, label = None, help = "", typeHint = STRING, sortingWeight = 0):
        self.section = section
        
        if label is None:
            label = name
        
        self.name = name
        self.label = label
        self.help = help
        self.defaultValue = defaultValue
        self._value = defaultValue
        self._editedValue = defaultValue
        self.hasChanges = False
        self.typeHint = typeHint
        
        self.sortingWeight = sortingWeight
        
    def getPath(self):
        """Retrieves a unique path in the qsettings tree, this can be used by persistence providers for example
        """
        
        return "%s/%s" % (self.section.getPath(), self.name)

    def getPersistenceProvider(self):
        return self.section.getPersistenceProvider()

    def _setValue(self, value):
        self._value = value
        self._editedValue = value
        self.upload()

    def _setEditedValue(self, value):
        self._editedValue = value
        self.hasChanges = True

    def upload(self):
        self.getPersistenceProvider().upload(self, self._value)
        self.hasChanges = False
    
    def download(self):
        persistedValue = self.getPersistenceProvider().download(self)
        if persistedValue is not None:
            self._value = persistedValue
            
        self.editedValue = self._value
        self.hasChanges = False
        
    def applyChanges(self):
        self.value = self._editedValue

class Section(object):
    def __init__(self, category, name, label = None, sortingWeight = 0):
        self.category = category
        
        if label is None:
            label = name
        
        self.name = name
        self.label = label
        self.sortingWeight = sortingWeight
        
        self.entries = []
        
    def getPath(self):
        """Retrieves a unique path in the qsettings tree, this can be used by persistence providers for example
        """
        
        return "%s/%s" % (self.category.getPath(), self.name)
        
    def getPersistenceProvider(self):
        return self.category.getPersistenceProvider()
        
    def addEntry(self, **kwargs):
        entry = Entry(section = self, **kwargs)
        self.entries.append(entry)
        
        return entry
        
    def getEntry(self, name):
        for entry in self.entries:
            if entry.name == name:
                return entry
            
        raise RuntimeError("Entry of name '" + name + "' not found inside section '" + self.name + "' (path: '" + self.getPath() + "').")
        
    def upload(self):
        for entry in self.entries:
            entry.upload()
    
    def download(self):
        for entry in self.entries:
            entry.download()
        
    def sort(self):
        # FIXME: This is obviously not the fastest approach
        self.entries = sorted(self.entries, key = lambda entry: entry.name)
        self.entries = sorted(self.entries, key = lambda entry: entry.sortingWeight)
        
class Category(object):
    def __init__(self, settings, name, label = None, sortingWeight = 0):
        self.qsettings = settings
        
        if label is None:
            label = name
        
        self.name = name
        self.label = label
        self.sortingWeight = sortingWeight
        
        self.sections = []
        
    def getPath(self):
        """Retrieves a unique path in the qsettings tree, this can be used by persistence providers for example
        """
        
        return "%s/%s" % (self.qsettings.getPath(), self.name)
        
    def getPersistenceProvider(self):
        return self.qsettings.getPersistenceProvider()
                
    def addSection(self, **kwargs):
        section = Section(category = self, **kwargs)
        self.sections.append(section)
        
        return section
        
    def getSection(self, name):
        for section in self.sections:
            if section.name == name:
                return section
            
        raise RuntimeError("Section '" + name + "' not found in category '" + self.name + "' of this settings")
        
    def addEntry(self, **kwargs):
        if self.getSection("") is None:
            section = self.addSection("")
            section.sortingWeight = -1
            
        section = self.getSection("")
        return section.addEntry(**kwargs)
        
    def getEntry(self, path):
        # FIXME: Needs better error handling
        splitted = path.split("/", 1)
        assert(len(splitted) == 2)
        
        section = self.getSection(splitted[0])
        return section.getEntry(splitted[1])
        
    def upload(self):
        for section in self.sections:
            section.upload()
    
    def download(self):
        for section in self.sections:
            section.download()
        
    def sort(self, recursive = True):
        # FIXME: This is obviously not the fastest approach
        self.sections = sorted(self.sections, key = lambda section: section.name)
        self.sections = sorted(self.sections, key = lambda section: section.sortingWeight)
        
        if recursive:
            for section in self.sections:
                section.sort()
    
class Settings(object):
    def __init__(self, name, label = None, help = ""):
        if label is None:
            label = name
        
        self.name = name
        self.label = label
        self.help = help

        self.categories = []        
        self.persistenceProvider = None
    
    def getPath(self):
        return self.name

    def setPersistenceProvider(self, persistenceProvider):
        self.persistenceProvider = persistenceProvider    
    
    def getPersistenceProvider(self):
        assert(self.persistenceProvider is not None)
        
        return self.persistenceProvider

    def addCategory(self, **kwargs):
        category = Category(settings = self, **kwargs)
        self.categories.append(category)
                
        return category
    
    def getCategory(self, name):
        for category in self.categories:
            if category.name == name:
                return category
        
        raise RuntimeError("Category '" + name + "' not found in this settings")
    
    def getEntry(self, path):
        # FIXME: Needs better error handling
        splitted = path.split("/", 1)
        assert(len(splitted) == 2)
        
        category = self.getCategory(splitted[0])
        return category.getEntry(splitted[1])
    
    def upload(self):
        for category in self.categories:
            category.upload()
    
    def download(self):
        for category in self.categories:
            category.download()
    
    def sort(self, recursive = True):
        # FIXME: This is obviously not the fastest approach
        self.categories = sorted(self.categories, key = lambda category: category.name)
        self.categories = sorted(self.categories, key = lambda category: category.sortingWeight)
        
        if recursive:
            for category in self.categories:
                category.sort()