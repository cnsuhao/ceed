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

import declaration
import persistence
import interface

class Settings(declaration.Settings):
    instance = None
    
    def __init__(self, qsettings):
        super(Settings, self).__init__(name = "settings",
                                       label = "CEGUI Unified Editor settings",
                                       help = "Provides all persistent settings of CEGUI Unified Editor (CEED), everything is divided into categories (see the tab buttons on the left).")
        
        self.setPersistenceProvider(persistence.QSettingsPersistenceProvider(qsettings))

        import editors.imageset.settings_decl as imageset_settings
        imageset_settings.declare(self)
        
        import editors.layout.settings_decl as layout_settings
        layout_settings.declare(self)
        
        # download all values from the persistence store
        self.download()
        
        assert(Settings.instance is None)
        Settings.instance = self
        
def getEntry(path):
    """This is a convenience method to make settings retrieval easier
    """
    
    assert(Settings.instance is not None)
    return Settings.instance.getEntry(path)
