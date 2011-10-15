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

# Stefan Stammberger is the original author of this file

from PySide.QtCore import *
from PySide.QtGui import *

class RecentlyUsed(object):
    """This class can be used to store pointers to Items like files and images for later reuse within the application.
    """
    
    def __init__(self, qsettings, sectionIdentifier):
        self.sectionIdentifier = "recentlyUsedIdentifier/" + sectionIdentifier
        self.qsettings = qsettings
        # how many recent items should the editor remember
        self.maxRecentlItems = 5
        # to how many characters should the recent file names be trimmed to
        self.recentlItemsNameTrimLength = 40
        
    def addRecentlyUsed(self, itemName):
        """ Add an item to the list """        
        items = []
        if self.qsettings.contains(self.sectionIdentifier):
            val = unicode(self.qsettings.value(self.sectionIdentifier))
            items = self.stringToStringList(val)
            
        # if something went wrong before, just drop recent projects and start anew,
        # recent projects aren't that important
        if not isinstance(items, list):
            items = []
        
        isInList = False
        for f in items:
            if f == itemName:
                items.remove(f)
                items.insert(0, f)
                isInList = True
                break
        
        #only insert the file if it is not already in list,
        if not isInList:
            items.insert(0, itemName)
        
        self.qsettings.setValue(self.sectionIdentifier, self.stringListToString(items))
        
        # while because items could be in a bad state because of previously thrown exceptions
        # make sure we trim them correctly in all circumstances
        while len(items) > self.maxRecentlItems:
            items.remove(items[self.maxRecentlItems])
            
            
    def getRecentlyUsed(self):
        """ Returns all items as a string list """
        items = []
        if self.qsettings.contains(self.sectionIdentifier):
            val = unicode(self.qsettings.value(self.sectionIdentifier))
            items = self.stringToStringList(val)
            
        return items

    def trimItemName(self, itemName):
        """ trim the itemName to the max. length and return it """ 
        if (len(itemName) > self.recentlItemsNameTrimLength):
            # + 3 because of the ...
            trimedItemName = "...%s" % (itemName[-self.recentlItemsNameTrimLength + 3:])
            return trimedItemName
        else:
            return itemName
        
    def stringListToString(self, list):
        """ converts a list into a string for storage in QSettings """
        temp = ""
        
        first = True
        for s in list:
            t = s.replace( ';', '\\;' )
            if first is True:
                temp = t
                first = False
            else:
                temp = temp + ";" + t
        
        return temp
        
    def stringToStringList(self, instr):
        """ converts a string to a string list """
        workStr = instr
        list = []
        
        if not workStr.find('\\;') > -1:
            return instr.split(";")
        else:
            tempList = []
            pos = workStr.find(';')
            while pos > -1:
                #if we find a string that is escaped split the text and add it to the temporary list
                #the path will be reconstructed when we don't find any escaped semicolons anymore (in else) 
                if workStr[pos-1:pos+1] == "\\;": 
                    tempList.append(workStr[:pos+1].replace("\\;", ";"))
                    workStr = workStr[pos+1:]
                    pos = workStr.find(';')
                    if pos < 0: #end reached, finalize
                        list.append(self.reconstructString(tempList) + workStr)
                        workStr = workStr[pos+1:]
                        tempList = []
                else:
                    #found a unescaped ; so we reconstruct the string before it, it should be a complete item 
                    list.append(self.reconstructString(tempList) + workStr[:pos])
                    workStr = workStr[pos+1:]
                    pos = workStr.find(';')
                    tempList = []
            return list
            
                
    def reconstructString(self, list):
        """ reconstructs the string from a list and return it """
        reconst = ""
        for s in list:
            reconst = reconst + s
        return reconst
                
        
class RecentlyUsedMenuEntry(RecentlyUsed):
    """
    This class can be used to manage a Qt Menu entry to items.
    """
    def __init__(self, qsettings, sectionIdentifier):
        super(RecentlyUsedMenuEntry, self).__init__(qsettings, sectionIdentifier)
        
    def setParentMenu(self, menu, slot):
        """ sets the parent menu and the slot that is called when clicked on an item """
        self.menu = menu
        self.slot = slot
        self.updateMenu()
    
    def addRecentlyUsed(self, itemName):
        """ adds an item to the list """
        super(RecentlyUsedMenuEntry, self).addRecentlyUsed(itemName)
        self.updateMenu()
        
    def updateMenu(self):
        self.menu.clear()
        items = self.getRecentlyUsed()
                
        for f in items:
            actionRP = QAction(self.menu)
            actionRP.setText(self.trimItemName(f))
            actionRP.setData(f)
            actionRP.setVisible(True)
            actionRP.triggered.connect(self.slot)
            self.menu.addAction(actionRP)
                   
        