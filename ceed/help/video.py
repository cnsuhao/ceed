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

from PySide.QtWebKit import QWebView

import declaration
import web

class FlashWebView(QWebView):
    def __init__(self, url):
        super(FlashWebView, self).__init__()
        
        padding = 10
        self.resize(1080 + 2 * padding, 720 + 2 * padding)
        
        html = """
        <html>
            <body>
                <embed type="application/x-shockwave-flash" src="%s" width="1080" height="720"
                       allowscriptaccess="always" allowfullscreen="true" bgcolor="#000000">
                </embed>
            </body>
        </html>
        """ % (url)
        
        self.setHtml(html)

class YoutubeVideoHelpSource(declaration.HelpSource):
    """A help source consisting of a video (it plays a video and allows the user
    to move the window or even close it, it's not modal).
    """
    
    def __init__(self, title, youtubeId):
        self.title = title
        self.youtubeId = youtubeId
        
    def execute(self):
        web.ensureInitialised()
        
        # this essentially makes sure that only one flash view of this help source is displayed at a time
        # if this is executed for the second time the reference to the first viewer is lost, it's decrefed and destroyed
        # FIXME: We should not rely on garbage collection to do logic for us!
        self.viewer = FlashWebView("http://www.youtube.com/v/%s" % (self.youtubeId))
        self.viewer.setWindowTitle(self.title)
        self.viewer.show()
        