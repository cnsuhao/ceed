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

class Settings(declaration.Settings):
    def __init__(self, qsettings):
        super(Settings, self).__init__("Settings")
        
        self.setPersistenceProvider(persistence.QSettingsPersistenceProvider(qsettings))

        import editors.imageset.settings as imageset_settings
        imageset_settings.declare(self)
        
        import editors.layout.settings as layout_settings
        layout_settings.declare(self)
        
        # download all values from the persistence store
        self.download()
        