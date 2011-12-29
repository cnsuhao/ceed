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

from PySide.QtCore import *
from PySide.QtGui import *
from recentlyused import RecentlyUsedMenuEntry

import ceed.ui.mainwindow

import os

from ceed import settings
from ceed import action

from ceed import commands
from ceed import project
from ceed import cegui
from ceed import filesystembrowser
import ceed.cegui.container as cegui_container
from ceed import editors

from ceed import help
from ceed import about

class MainWindow(QMainWindow):
    """The central window of the application.

    This is a singleton class, it is assured to only be constructed once during runtime.
    """

    # singleton pattern implementation
    # (usage: mainwindow.MainWindow.instance.doSomething() where mainwindow is the module)
    instance = None

    # TODO: This class has grown too much, I think it has too many responsibilities
    #       and refactoring will be needed in the future.

    def __init__(self, app):
        # make sure multiple instantiation won't happen
        assert(MainWindow.instance is None)
        MainWindow.instance = self

        super(MainWindow, self).__init__()

        self.app = app

        # we have to construct ActionManager before settings interface (as it alters the settings declaration)!
        self.actionManager = action.ActionManager(self, self.app.settings)

        self.settingsInterface = settings.interface.QtSettingsInterface(self.app.settings)

        self.recentlyUsedProjects = RecentlyUsedMenuEntry(self.app.qsettings, "Projects")

        import ceed.editors.animation_list as animation_list_editor
        import ceed.editors.bitmap as bitmap_editor
        import ceed.editors.imageset as imageset_editor
        import ceed.editors.layout as layout_editor
        import ceed.editors.property_mappings as property_mappings_editor
        import ceed.editors.text as text_editor

        self.editorFactories = [
            animation_list_editor.AnimationListTabbedEditorFactory(),
            bitmap_editor.BitmapTabbedEditorFactory(),
            imageset_editor.ImagesetTabbedEditorFactory(),
            layout_editor.LayoutTabbedEditorFactory(),
            property_mappings_editor.PropertyMappingsTabbedEditorFactory(),
            text_editor.TextTabbedEditorFactory()
        ]

        self.activeEditor = None
        self.project = None

        self.ui = ceed.ui.mainwindow.Ui_MainWindow()
        self.ui.setupUi(self)
        
        # for now we can't use unified title and toolbar, it doesn't have toolbar "ellipsis"
        # and that makes the main window jump around when switching tabs
        self.setUnifiedTitleAndToolBarOnMac(False)

        # we start CEGUI early and we always start it
        self.ceguiInstance = cegui.Instance()
        self.ceguiContainerWidget = cegui_container.ContainerWidget(self.ceguiInstance)

        self.tabs = self.centralWidget().findChild(QTabWidget, "tabs")
        self.tabs.currentChanged.connect(self.slot_currentTabChanged)
        self.tabs.tabCloseRequested.connect(self.slot_tabCloseRequested)
        # TODO: this is potentially nasty since the tabBar method is protected
        # we need this to implement the context menu when you right click on the tab bar
        self.tabBar = self.tabs.tabBar()
        self.tabBar.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabBar.customContextMenuRequested.connect(self.slot_tabBarCustomContextMenuRequested)

        # stores all active tab editors
        self.tabEditors = []

        self.projectManager = project.ProjectManager()
        self.addDockWidget(Qt.RightDockWidgetArea, self.projectManager)

        self.fileSystemBrowser = filesystembrowser.FileSystemBrowser()
        self.fileSystemBrowser.setVisible(False)
        self.addDockWidget(Qt.RightDockWidgetArea, self.fileSystemBrowser)

        self.undoViewer = commands.UndoViewer()
        self.undoViewer.setVisible(False)
        self.addDockWidget(Qt.RightDockWidgetArea, self.undoViewer)

        # this menu contains checkable "actions" that hide and show the panels
        # even though you can achieve the same thing by right clicking empty space in
        # mainwindow I believe having this has a benefit, it is much easier to find this way
        self.menuPanels = self.findChild(QMenu, "menuPanels")
        self.menuPanels.addAction(self.projectManager.toggleViewAction())
        self.menuPanels.addAction(self.fileSystemBrowser.toggleViewAction())
        self.menuPanels.addAction(self.undoViewer.toggleViewAction())

        self.setupActions()

        self.restoreSettings()

    def setupActions(self):
        # usage of a connection group in mainwindow may be unnecessary,
        # we never use disconnectAll and/or connectAll, it is just used as a convenient
        # way to group connections
        self.connectionGroup = action.ConnectionGroup(self.actionManager)

        self.globalToolbar = self.findChild(QToolBar, "globalToolbar")

        self.fileMenu = self.findChild(QMenu, "menuFile")
        self.editMenu = self.findChild(QMenu, "menuEdit")

        self.newFileAction = self.actionManager.getAction("all_editors/new_file")
        self.fileMenu.addAction(self.newFileAction)
        self.globalToolbar.addAction(self.newFileAction)
        self.connectionGroup.add(self.newFileAction, receiver = self.slot_newFileDialog)

        self.openFileAction = self.actionManager.getAction("all_editors/open_file")
        self.fileMenu.addAction(self.openFileAction)
        self.globalToolbar.addAction(self.openFileAction)
        self.connectionGroup.add(self.openFileAction, receiver = self.slot_openFileDialog)

        self.saveAction = self.actionManager.getAction("all_editors/save_file")
        self.saveAction.setEnabled(False)
        self.fileMenu.addAction(self.saveAction)
        self.globalToolbar.addAction(self.saveAction)
        self.connectionGroup.add(self.saveAction, receiver = self.slot_save)
        
        self.saveAsAction = self.actionManager.getAction("all_editors/save_file_as")
        self.saveAsAction.setEnabled(False)
        self.fileMenu.addAction(self.saveAsAction)
        self.globalToolbar.addAction(self.saveAsAction)
        self.connectionGroup.add(self.saveAsAction, receiver = self.slot_saveAs)

        self.saveAllAction = self.actionManager.getAction("all_editors/save_all")
        self.fileMenu.addAction(self.saveAllAction)
        self.globalToolbar.addAction(self.saveAllAction)
        self.connectionGroup.add(self.saveAllAction, receiver = self.slot_saveAll)

        self.fileMenu.addSeparator()

        # tab bar context menu (but also added to the file menu so it's easy to discover)
        self.closeTabAction = self.actionManager.getAction("all_editors/close_current_tab")
        self.closeTabAction.setEnabled(False)
        self.fileMenu.addAction(self.closeTabAction)
        self.connectionGroup.add(self.closeTabAction, receiver = self.slot_closeTab)

        self.closeOtherTabsAction = self.actionManager.getAction("all_editors/close_other_tabs")
        self.closeOtherTabsAction.setEnabled(False)
        self.fileMenu.addAction(self.closeOtherTabsAction)
        self.connectionGroup.add(self.closeOtherTabsAction, receiver = self.slot_closeOtherTabs)

        self.closeAllTabsAction = self.actionManager.getAction("all_editors/close_all_tabs")
        self.fileMenu.addAction(self.closeAllTabsAction)
        self.connectionGroup.add(self.closeAllTabsAction, receiver = self.slot_closeAllTabs)
        # end of tab bar context menu

        self.fileMenu.addSeparator()
        self.globalToolbar.addSeparator()

        self.undoAction = self.actionManager.getAction("all_editors/undo")
        self.undoAction.setEnabled(False)
        self.editMenu.addAction(self.undoAction)
        self.globalToolbar.addAction(self.undoAction)
        self.connectionGroup.add(self.undoAction, receiver = self.slot_undo)

        self.redoAction = self.actionManager.getAction("all_editors/redo")
        self.redoAction.setEnabled(False)
        self.editMenu.addAction(self.redoAction)
        self.globalToolbar.addAction(self.redoAction)
        self.connectionGroup.add(self.redoAction, receiver = self.slot_redo)

        self.editMenu.addSeparator()
        self.globalToolbar.addSeparator()

        self.cutAction = self.actionManager.getAction("all_editors/cut")
        self.editMenu.addAction(self.cutAction)
        self.globalToolbar.addAction(self.cutAction)
        self.connectionGroup.add(self.cutAction, receiver = self.slot_cut)

        self.copyAction = self.actionManager.getAction("all_editors/copy")
        self.editMenu.addAction(self.copyAction)
        self.globalToolbar.addAction(self.copyAction)
        self.connectionGroup.add(self.copyAction, receiver = self.slot_copy)

        self.pasteAction = self.actionManager.getAction("all_editors/paste")
        self.editMenu.addAction(self.pasteAction)
        self.globalToolbar.addAction(self.pasteAction)
        self.connectionGroup.add(self.pasteAction, receiver = self.slot_paste)

        self.editMenu.addSeparator()
        self.globalToolbar.addSeparator()

        self.projectSettingsAction = self.actionManager.getAction("project_management/project_settings")
        # when this starts up, no project is opened, hence you can't view/edit settings of the current project
        self.projectSettingsAction.setEnabled(False)
        self.editMenu.addAction(self.projectSettingsAction)
        self.globalToolbar.addAction(self.projectSettingsAction)
        self.connectionGroup.add(self.projectSettingsAction, receiver = self.slot_projectSettings)
        
        self.projectReloadResourcesAction = self.actionManager.getAction("project_management/reload_resources")
        # when this starts up, no project is opened, hence you can't reload resources of the current project
        self.projectReloadResourcesAction.setEnabled(False)
        self.editMenu.addAction(self.projectReloadResourcesAction)
        self.globalToolbar.addAction(self.projectReloadResourcesAction)
        self.connectionGroup.add(self.projectReloadResourcesAction, receiver = self.slot_projectReloadResources)

        self.editMenu.addAction(self.actionManager.getAction("general/application_settings"))
        self.connectionGroup.add("general/application_settings", receiver = lambda: self.settingsInterface.show())

        self.fileMenu.addAction(self.actionManager.getAction("project_management/new_project"))
        self.connectionGroup.add("project_management/new_project", receiver = self.slot_newProject)

        self.fileMenu.addAction(self.actionManager.getAction("project_management/open_project"))
        self.connectionGroup.add("project_management/open_project", receiver = self.slot_openProject)

        self.saveProjectAction = self.actionManager.getAction("project_management/save_project")
        # when this starts up, no project is opened, hence you can't save the "no project"
        self.saveProjectAction.setEnabled(False)
        self.fileMenu.addAction(self.saveProjectAction)
        self.globalToolbar.addAction(self.saveProjectAction)
        self.connectionGroup.add(self.saveProjectAction, receiver = self.slot_saveProject)

        self.closeProjectAction = self.actionManager.getAction("project_management/close_project")
        self.fileMenu.addAction(self.closeProjectAction)
        self.connectionGroup.add(self.closeProjectAction, receiver = self.slot_closeProject)
        # when this starts up, no project is opened, hence you can't close the current project
        self.closeProjectAction.setEnabled(False)

        self.fileMenu.addSeparator()

        self.recentProjectsMenu = self.findChild(QMenu, "menuRecentProjects")
        self.recentlyUsedProjects.setParentMenu(self.recentProjectsMenu, self.slot_openRecentProject)

        self.aboutAction = self.findChild(QAction, "actionAbout")
        self.aboutAction.triggered.connect(self.slot_about)

        self.licenseAction = self.findChild(QAction, "actionLicense")
        self.licenseAction.triggered.connect(self.slot_license)

        self.qtAction = self.findChild(QAction, "actionQt")
        self.qtAction.triggered.connect(QApplication.aboutQt)

        self.connectionGroup.add("general/quit", receiver = self.slot_quit)
        self.fileMenu.addAction(self.actionManager.getAction("general/quit"))

        self.connectionGroup.connectAll()

        self.projectManager.fileOpenRequested.connect(self.slot_openFile)
        self.fileSystemBrowser.fileOpenRequested.connect(self.slot_openFile)

    def syncProjectToCEGUIInstance(self, indicateErrorsWithDialogs = True):
        """Synchronises current project to the CEGUI instance.
        
        indicateErrorsWithDialogs - if True a dialog is opened in case of errors
        
        Returns True if the procedure was successful
        """

        try:
            self.ceguiInstance.syncToProject(self.project, self)
            
            return True

        except Exception as e:
            if indicateErrorsWithDialogs:
                QMessageBox.warning(self, "Failed to synchronise embedded CEGUI to your project",
"""An attempt was made to load resources related to the project being opened, for some reason the loading didn't succeed so all resources were destroyed! The most likely reason is that the resource directories are wrong, this can be very easily remedied in the project settings.

This means that editing capabilities of CEED will be limited to editing of files that don't require a project opened (for example: imagesets).

Details of this error: %s""" % (e))
            
            return False

    def performProjectDirectoriesSanityCheck(self, indicateErrorsWithDialogs = True):
        try:
            self.project.checkAllDirectories()
            
            return True
        
        except IOError as e:
            if indicateErrorsWithDialogs:
                QMessageBox.warning(self, "At least one of project's resource directories is invalid",
"""Project's resource directory paths didn't pass the sanity check, please check projects settings.

Details of this error: %s""" % (e))
        
            return False
        
    def openProject(self, path, openSettings = False):
        """Opens the project file given in 'path'. Assumes no project is opened at the point this is called.
        The slot_openProject method will test if a project is opened and close it accordingly (with a dialog
        being shown if there are changes to it)
        
        Errors aren't indicated by exceptions or return values, dialogs are shown in case of errors.
        
        path - Absolute path of the project file
        openSettings - if True, the settings dialog is opened instead of just loading the resources,
                       this is desirable when creating a new project
        """
        
        assert(self.project is None)
        
        # reset project manager to a clean state just in case
        self.projectManager.setProject(None)

        self.project = project.Project()
        try:
            self.project.load(path)
        except IOError:
            QMessageBox.critical(self, "Error when opening project", "It seems project at path '%s' doesn't exist or you don't have rights to open it." % (path))

            self.project = None
            return
        
        self.performProjectDirectoriesSanityCheck()
        
        # view the newly opened project in the project manager
        self.projectManager.setProject(self.project)
        # and set the filesystem browser path to the base folder of the project
        # TODO: Maybe this could be configurable?
        projectBaseDirectory = self.project.getAbsolutePathOf("")
        if os.path.isdir(projectBaseDirectory):
            self.fileSystemBrowser.setDirectory(projectBaseDirectory)
        
        self.recentlyUsedProjects.addRecentlyUsed(str(self.project.projectFilePath))

        # and enable respective actions
        self.saveProjectAction.setEnabled(True)
        self.closeProjectAction.setEnabled(True)
        self.projectSettingsAction.setEnabled(True)
        self.projectReloadResourcesAction.setEnabled(True)

        if openSettings:
            self.slot_projectSettings()
            
        else:
            self.syncProjectToCEGUIInstance()

    def closeProject(self):
        """Closes currently opened project. Assumes one is opened at the point this is called.
        """
        
        assert(self.project is not None)
        
        # since we are effectively unloading the project and potentially nuking resources of it
        # we should definitely unload all tabs that rely on it to prevent segfaults and other
        # nasty phenomena
        if not self.closeAllTabsRequiringProject():
            return
        
        self.projectManager.setProject(None)
        # TODO: Do we really want to call this there? This was already called when the project was being opened.
        #       It doesn't do anything harmful but maybe is unnecessary.
        self.recentlyUsedProjects.addRecentlyUsed(str(self.project.projectFilePath))
        # clean resources that were potentially used with this project
        self.ceguiInstance.cleanCEGUIResources()
        
        self.project.unload()
        self.project = None

        # as the project was closed be will disable actions related to it
        self.saveProjectAction.setEnabled(False)
        self.closeProjectAction.setEnabled(False)
        self.projectReloadResourcesAction.setEnabled(False)

    def saveProject(self):
        """Saves currently opened project to the file it was opened from (or the last file it was saved to).
        """
        
        assert(self.project is not None)
        
        self.project.save()

    def saveProjectAs(self, newPath):
        """Saves currently opened project to a custom path. For best reliability, use absolute file path as newPath
        """
        
        self.project.save(newPath)
        # set the project's file path to newPath so that if you press save next time it will save to the new path
        # (This is what is expected from applications in general I think)
        self.project.projectFilePath = newPath

    def createEditorForFile(self, absolutePath):
        """Creates a new editor for file at given absolutePath. This always creates a new editor,
        it is not advised to use this method directly, use openEditorTab instead.
        """
        
        ret = None

        projectRelativePath = os.path.relpath(absolutePath, self.project.baseDirectory) if self.project else "<No project opened>"

        if not os.path.exists(absolutePath):
            ret = editors.MessageTabbedEditor(absolutePath,
                   "Couldn't find '%s' (project relative path: '%s'), please check that that your project's "
                   "base directory is set up correctly and that you hadn't deleted "
                   "the file from your HDD. Consider removing the file from the project." % (absolutePath, projectRelativePath))
        else:
            possibleFactories = []

            for factory in self.editorFactories:
                if factory.canEditFile(absolutePath):
                    possibleFactories.append(factory)

            # at this point if possibleFactories is [], no registered tabbed editor factory wanted
            # to accept the file, so we create MessageTabbedEditor that will simply
            # tell the user that given file can't be edited
            #
            # IMO this is a reasonable compromise and plays well with the rest of
            # the editor without introducing exceptions, etc...
            if len(possibleFactories) == 0:
                ret = editors.MessageTabbedEditor(absolutePath,
                       "No included tabbed editor was able to accept '%s' (project relative path: '%s'), please "
                       "check that it's a file CEED supports and that it has the correct extension "
                       "(CEED enforces proper extensions)" % (absolutePath, projectRelativePath))

            else:
                # one or more factories wants to accept the file
                factory = None

                if len(possibleFactories) == 1:
                    # it's decided, just one factory wants to accept the file
                    factory = possibleFactories[0]

                else:
                    assert(len(possibleFactories) > 1)

                    # more than 1 factory wants to accept the file, offer a dialog and let user choose
                    dialog = editors.MultiplePossibleFactoriesDialog(possibleFactories)
                    result = dialog.exec_()

                    if result == QDialog.Accepted:
                        selection = dialog.factoryChoice.selectedItems()

                        if len(selection) == 1:
                            factory = selection[0].data(Qt.UserRole)

                if factory is None:
                    ret = editors.MessageTabbedEditor(absolutePath,
                       "You failed to choose an editor to open '%s' with (project relative path: '%s')." % (absolutePath, projectRelativePath))

                else:
                    ret = factory.create(absolutePath)

        if self.project is None and ret.requiresProject:
            # the old editor will be destroyed automatically by python GC
            ret = editors.MessageTabbedEditor(absolutePath,
                       "Opening this file requires you to have a project opened!")

        try:
            ret.initialise(self)

        except Exception:
            # it may have been partly constructed at this point
            try:
                ret.finalise()

            except:
                # catch all exception the finalisation raises (we can't deal with them anyways)
                pass

            raise

        self.tabEditors.append(ret)
        return ret

    def openEditorTab(self, absolutePath):
        """Opens editor tab. Creates new editor if such file wasn't opened yet and if it was opened,
        it just makes the tab current.
        """

        absolutePath = os.path.normpath(absolutePath)

        for tabEditor in self.tabEditors:
            if tabEditor.filePath == absolutePath:
                tabEditor.makeCurrent()
                return

        editor = self.createEditorForFile(absolutePath)
        editor.makeCurrent()

    def closeEditorTab(self, editor):
        """Closes given editor tab.

        note: Make sure you pass proper existing editor!
        """

        assert(editor in self.tabEditors)
        
        editor.finalise()
        self.tabEditors.remove(editor)

    def saveSettings(self):
        """Saves geometry and state of this window to QSettings.
        
        FIXME: This is not currently used for reasons I am not sure of!
        """
        
        #self.qsettings.setValue("geometry", self.saveGeometry())
        #self.qsettings.setValue("state", self.saveState())
        pass

    def restoreSettings(self):
        """Restores geometry and state of this window from QSettings.
        
        FIXME: This is not currently used for reasons I am not sure of!
        """
        
        #if self.qsettings.contains("geometry"):
        #    self.restoreGeometry(self.qsettings.value("geometry"))
        #if self.qsettings.contains("state"):
        #    self.restoreState(self.qsettings.value("state"))
        return

    def quit(self):
        """Safely quits the editor, prompting user to save changes to files and the project."""

        self.saveSettings()

        if self.project is not None:
            # if the slot returned False, user pressed Cancel
            if not self.slot_closeProject():
                # in case user pressed cancel the entire quitting processed has to be terminated
                return False

        # we remember last tab we closed to check whether user pressed Cancel in any of the dialogs
        lastTab = None
        while len(self.tabEditors) > 0:
            currentTab = self.tabs.widget(0)
            if currentTab == lastTab:
                # user pressed cancel on one of the tab editor 'save without changes' dialog,
                # cancel the whole quit operation!
                return False
            lastTab = currentTab

            self.slot_tabCloseRequested(0)

        self.app.quit()

    def closeAllTabsRequiringProject(self):
        """Attempts to close all tabs that require a project opened.
        
        This is usually done when project settings are altered and CEGUI instance has to be reloaded
        or when project is being closed and we can no longer rely on resource availability.
        """
        
        i = 0
        while i < self.tabs.count():
            tabbedEditor = self.tabs.widget(i).tabbedEditor
            
            if tabbedEditor.requiresProject:
                if not self.slot_tabCloseRequested(i):
                    # if the method returns False user pressed Cancel so in that case
                    # we cancel the entire operation
                    return False
                
                continue
            
            i += 1
            
        return True      
        
    def slot_newProject(self):
        if self.project:
            # another project is already opened!
            result = QMessageBox.question(self,
                                          "Another project already opened!",
                                          "Before creating a new project, you must close the one currently opened. "
                                          "Do you want to close currently opened project? (all unsaved changes will be lost!)",
                                          QMessageBox.Yes | QMessageBox.Cancel,
                                          QMessageBox.Cancel)

            if result == QMessageBox.Yes:
                self.closeProject()
            else:
                # User selected cancel, NOOP
                return

        newProjectDialog = project.NewProjectDialog()
        result = newProjectDialog.exec_()

        if result == QDialog.Accepted:
            newProject = newProjectDialog.createProject()
            newProject.save()

            # since this is a new project we do want to open project settings immediately
            self.openProject(path = newProject.projectFilePath, openSettings = True)
            # save the project with the settings that were potentially set in the project settings dialog
            self.saveProject()

    def slot_openProject(self):
        if self.project:
            # another project is already opened!
            result = QMessageBox.question(self,
                                          "Another project already opened!",
                                          "Before opening a project, you must close the one currently opened. "
                                          "Do you want to close currently opened project? (all unsaved changes will be lost!)",
                                          QMessageBox.Yes | QMessageBox.Cancel,
                                          QMessageBox.Cancel)

            if result == QMessageBox.Yes:
                self.closeProject()
            else:
                # User selected cancel, NOOP
                return

        file, filter = QFileDialog.getOpenFileName(self,
                                           "Open existing project file",
                                           "",
                                           "Project files (*.project)")

        if file != "":
            # user actually selected something ;-)

            self.openProject(file)

    def slot_saveProject(self):
        self.saveProject()

    def slot_closeProject(self):
        assert(self.project)

        if self.project.hasChanges():
            result = QMessageBox.question(self,
                                          "Project file has changes!",
                                          "There are unsaved changes in the project file "
                                          "Do you want to save them? "
                                          "(Pressing Discard will discard the changes!)",
                                          QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                                          QMessageBox.Save)

            if result == QMessageBox.Save:
                self.saveProject()

            elif result == QMessageBox.Cancel:
                return False

        self.closeProject()
        return True

    def slot_projectSettings(self):
        # since we are effectively unloading the project and potentially nuking resources of it
        # we should definitely unload all tabs that rely on it to prevent segfaults and other
        # nasty phenomena
        if not self.closeAllTabsRequiringProject():
            QMessageBox.information(self,
                                    "Project dependent tabs still open!",
                                    "You can't alter project's settings while having tabs that "
                                    "depend on the project and its resources opened!")
            return
        
        dialog = project.ProjectSettingsDialog(self.project)

        if dialog.exec_() == QDialog.Accepted:
            dialog.apply(self.project)
            self.performProjectDirectoriesSanityCheck()
            self.syncProjectToCEGUIInstance()
            
    def slot_projectReloadResources(self):
        # since we are effectively unloading the project and potentially nuking resources of it
        # we should definitely unload all tabs that rely on it to prevent segfaults and other
        # nasty phenomena
        if not self.closeAllTabsRequiringProject():
            QMessageBox.information(self,
                                    "Project dependent tabs still open!",
                                    "You can't reload project's resources while having tabs that "
                                    "depend on the project and its resources opened!")
            return
        
        self.performProjectDirectoriesSanityCheck()
        self.syncProjectToCEGUIInstance()
        
    def slot_newFileDialog(self):
        dir = ""
        if self.project:
            dir = self.project.getAbsolutePathOf("")

        file, filter = QFileDialog.getSaveFileName(self, "New File", dir)

        if file:
            f = open(file, "w")
            f.close()

            self.openEditorTab(file)

    def slot_openFile(self, absolutePath):
        self.openEditorTab(absolutePath)

    def slot_openFileDialog(self):
        dir = ""
        if self.project:
            dir = self.project.getAbsolutePathOf("")

        file, filter = QFileDialog.getOpenFileName(self, "Open File", dir)

        if file:
            self.openEditorTab(file)

    def slot_currentTabChanged(self, index):
        # to fight flicker
        self.tabs.setUpdatesEnabled(False)

        # FIXME: workaround for PySide 1.0.6, I suspect this is a bug in PySide! http://bugs.pyside.org/show_bug.cgi?id=988
        if index is None:
            index = -1
            
        elif isinstance(index, QWidget):
            for i in range(0, self.tabs.count()):
                if index is self.tabs.widget(i):
                    index = i
                    break
                   
            assert(not isinstance(index, QWidget)) 
        # END OF FIXME

        wdt = self.tabs.widget(index)

        if self.activeEditor:
            self.activeEditor.deactivate()

        # it's the tabbed editor's responsibility to handle these,
        # we disable them by default
        self.undoAction.setEnabled(False)
        self.redoAction.setEnabled(False)
        # also reset their texts in case the tabbed editor messed with them
        self.undoAction.setText("Undo")
        self.redoAction.setText("Redo")
        # set undo stack to None as we have no idea whether the previous tab editor
        # set it to something else
        self.undoViewer.setUndoStack(None)

        # we also clear the status bar
        self.statusBar().clearMessage()

        if wdt:
            self.saveAction.setEnabled(True)
            self.saveAsAction.setEnabled(True)

            self.closeTabAction.setEnabled(True)
            self.closeOtherTabsAction.setEnabled(True)

            wdt.tabbedEditor.activate()
        else:
            # None is selected right now, lets disable Save and Close actions
            self.saveAction.setEnabled(False)
            self.saveAsAction.setEnabled(False)

            self.closeTabAction.setEnabled(False)
            self.closeOtherTabsAction.setEnabled(False)

        self.tabs.setUpdatesEnabled(True)

    def slot_tabCloseRequested(self, index):
        wdt = self.tabs.widget(index)
        editor = wdt.tabbedEditor

        if not editor.hasChanges():
            # we can close immediately
            self.closeEditorTab(editor)
            return True

        else:
            # we have changes, lets ask the user whether we should dump them or save them
            result = QMessageBox.question(self,
                                          "Unsaved changes!",
                                          "There are unsaved changes in '%s'. "
                                          "Do you want to save them? "
                                          "(Pressing Discard will discard the changes!)" % (editor.filePath),
                                          QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                                          QMessageBox.Save)

            if result == QMessageBox.Save:
                # lets save changes and then kill the editor (This is the default action)
                editor.save()
                self.closeEditorTab(editor)
                return True

            elif result == QMessageBox.Discard:
                # changes will be discarded
                # note: we don't have to call editor.discardChanges here

                self.closeEditorTab(editor)
                return True

            # don't do anything if user selected 'Cancel'
            return False

    def slot_closeTab(self):
        # a simple delegate
        self.slot_tabCloseRequested(self.tabs.currentIndex())

    def slot_closeOtherTabs(self):
        current = self.tabs.currentWidget()

        i = 0
        while i < self.tabs.count():
            if self.tabs.widget(i) == current:
                # we skip the current widget
                i += 1
            else:
                if not self.slot_tabCloseRequested(i):
                    # user selected Cancel, we skip this widget
                    i += 1

    def slot_closeAllTabs(self):
        i = 0
        while i < self.tabs.count():
            if not self.slot_tabCloseRequested(i):
                # user selected Cancel, we skip this widget
                i += 1

    def slot_tabBarCustomContextMenuRequested(self, point):
        atIndex = self.tabBar.tabAt(point)
        self.tabs.setCurrentIndex(atIndex)

        menu = QMenu(self)
        menu.addAction(self.closeTabAction)
        menu.addSeparator()
        menu.addAction(self.closeOtherTabsAction)
        menu.addAction(self.closeAllTabsAction)

        if atIndex != -1:
            tab = self.tabs.widget(atIndex)
            menu.addSeparator()
            dataTypeAction = QAction("Data type: %s" % (tab.getDesiredSavingDataType()), self)
            dataTypeAction.setToolTip("Displays which data type this file will be saved to (the desired saving data type).")
            menu.addAction(dataTypeAction)

        menu.exec_(self.tabBar.mapToGlobal(point))

    def slot_save(self):
        if self.activeEditor:
            self.activeEditor.save()

    def slot_saveAs(self):
        if self.activeEditor:
            filePath, filter = QFileDialog.getSaveFileName(self, "Save as", os.path.dirname(self.activeEditor.filePath))
            if filePath: # make sure user hasn't cancelled the dialog
                self.activeEditor.saveAs(filePath)

    def slot_saveAll(self):
        """Saves all opened tabbed editors and opened project (if any)
        """
        
        if self.project is not None:
            self.project.save()
        
        for editor in self.tabEditors:
            editor.save()

    def slot_undo(self):
        if self.activeEditor:
            self.activeEditor.undo()

    def slot_redo(self):
        if self.activeEditor:
            self.activeEditor.redo()

    def slot_cut(self):
        if self.activeEditor:
            self.activeEditor.performCut()

    def slot_copy(self):
        if self.activeEditor:
            self.activeEditor.performCopy()

    def slot_paste(self):
        if self.activeEditor:
            self.activeEditor.performPaste()

    def slot_about(self):
        dialog = about.AboutDialog()
        dialog.exec_()

    def slot_license(self):
        dialog = about.LicenseDialog()
        dialog.exec_()

    def slot_quit(self):
        return self.quit()

    def closeEvent(self, event):
        handled = self.slot_quit()

        if not handled:
            event.ignore()

        else:
            event.accept()

    def slot_openRecentProject(self):
        temp = str(self.sender().data())
        if self.sender():
            if self.project:
                # give user a chance to save changes if needed
                if not self.slot_closeProject():
                    return

            self.openProject(temp)
