from PySide.QtCore import *
from PySide.QtGui import *

from recentlyused import *

class RecentlyUsedMenuEntry(RecentlyUsed):
    def __init__(self, qsettings, sectionIdentifier, ):
        RecentlyUsed.__init__(self, qsettings, sectionIdentifier)
        
    def setParentMenu(self, menu, slot):
        self.menu = menu
        self.slot = slot
        self.updateMenu()
    
    def addRecentlyUsed(self, fileName):
        super(RecentlyUsed, self).addRecentlyUsed(fileName)
        self.updateMenu()
        
    def updateMenu(self):
        self.menu.clear()
        files = self.getRecentlyUsed()
                
        for f in files:
            actionRP = QAction(self, visible = False, triggered = self.slot)
            actionRP.setText(f)
            actionRP.setData(f)
            actionRP.setVisible(True)
            self.menu.addAction(actionRP)
                   
    def updateRecentProjectsActions(self):

        for i in range(min(numRecentFiles, len(self.recentProjectsActions))):
            fileName = files[i]
            if (len(fileName) > self.recentProjectsNameTrimLength):
                # + 3 because of the ...
                fileName = "...%s" % (fileName[-self.recentProjectsNameTrimLength + 3:])
        
            text = "&%d %s" % (i + 1, fileName)
            self.recentProjectsActions[i].setText(text)
            self.recentProjectsActions[i].setData(files[i])
            self.recentProjectsActions[i].setVisible(True)

        for j in range(numRecentFiles, self.maxRecentProjects):
            self.recentProjectsActions[j].setVisible(False)