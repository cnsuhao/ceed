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
    
    def __init__(self, section, name, defaultValue, label = None, help = "", typeHint = STRING, sortingWeight = 0):
        self.section = section
        
        if label is None:
            label = name
        
        self.name = name
        self.label = label
        self.help = help
        self.defaultValue = defaultValue
        self._value = defaultValue
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
        self.hasChanges = True

    def upload(self):
        self.getPersistenceProvider().upload(self, self._value)
    
    def download(self):
        self._value = self.getPersistenceProvider().download(self)
        self.hasChanges = False

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
            
        return None
        
    def addEntry(self, **kwargs):
        if self.getSection("") is None:
            section = self.addSection("")
            section.sortingWeight = -1
            
        section = self.getSection("")
        return section.addEntry(**kwargs)
        
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
    def __init__(self, name):
        self.categories = []
        self.name = name
        
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
