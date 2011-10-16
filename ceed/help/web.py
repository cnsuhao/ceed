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

from PySide.QtCore import QUrl
from PySide.QtWebKit import QWebView, QWebSettings

from ceed.help import declaration

initialised = False

def ensureInitialised():
    global initialised
    
    if not initialised:
        # FIXME: Is this needed?
        #QNetworkProxyFactory::setUseSystemConfiguration (true);
        
        # this definitely is needed
        QWebSettings.globalSettings().setAttribute(QWebSettings.PluginsEnabled, True)
        QWebSettings.globalSettings().setAttribute(QWebSettings.AutoLoadImages, True)
        
        initialised = True

class WebHelpSource(declaration.HelpSource):
    """A help source consisting of a video (it plays a video and allows the user
    to move the window or even close it, it's not modal).
    """
    
    def __init__(self, title, url):
        self.title = title
        self.url = url
        
    def execute(self):
        ensureInitialised()
        
        # this essentially makes sure that only one view of this help source is displayed at a time
        # if this is executed for the second time the reference to the first viewer is lost, it's decrefed and destroyed
        # FIXME: We should not rely on garbage collection to do logic for us!
        self.viewer = QWebView()
        self.viewer.load(QUrl(self.url))
        self.viewer.setWindowTitle(self.title)
        self.viewer.resize(1080, 720)
        self.viewer.show()
        