from PySide.QtCore import *
from PySide.QtGui import *

from recentlyused import *

class RecentlyUsedMenuEntry(RecentlyUsed):
    def __init__(self, qsettings, sectionIdentifier, ):
        super(RecentlyUsedMenuEntry, self).__init__(qsettings, sectionIdentifier)
        
    def setParentMenu(self, menu, slot):
        self.menu = menu
        self.slot = slot
        self.updateMenu()
    
    def addRecentlyUsed(self, fileName):
        super(RecentlyUsedMenuEntry, self).addRecentlyUsed(fileName)
        self.updateMenu()
        
    def updateMenu(self):
        self.menu.clear()
        files = self.getRecentlyUsed()
                
        for f in files:
            actionRP = QAction(self.menu)
            actionRP.setText(self.trimFileName(f))
            actionRP.setData(f)
            actionRP.setVisible(True)
            actionRP.triggered.connect(self.slot)
            self.menu.addAction(actionRP)
                   