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

import ui.mainwindow

import os

import commands
import project
import cegui
import filesystembrowser
import propertyinspector

import tab

# the various editor imports
import bitmapeditor
import texteditor
import imageseteditor
import layouteditor

import about

class MainWindow(QMainWindow):
    """The central window of the application"""
    
    # TODO: This class has grown too much, I think it has too many responsibilities
    #       and refactoring will be needed in the future.
    
    def __init__(self, app):
        super(MainWindow, self).__init__()
        
        self.app = app
        self.settings = QSettings("CEGUI", "CEED")

        # how many recent files should the editor remember
        self.maxRecentProjects = 5
        # to how many characters should the recent file names be trimmed to
        self.recentProjectsNameTrimLength = 40
        # recent files actions
        self.recentProjectsActions = []

        self.editorFactories = [
            bitmapeditor.BitmapTabbedEditorFactory(),
            texteditor.TextTabbedEditorFactory(),
            imageseteditor.ImagesetTabbedEditorFactory(),
            layouteditor.LayoutTabbedEditorFactory()
        ]
        
        self.activeEditor = None
        self.project = None
        
        self.ui = ui.mainwindow.Ui_MainWindow()
        self.ui.setupUi(self)
        
        # we start CEGUI early and we always start it
        self.ceguiContainerWidget = cegui.ContainerWidget(self)
        
        self.tabs = self.centralWidget().findChild(QTabWidget, "tabs")
        self.tabs.currentChanged.connect(self.slot_currentTabChanged)
        #self.tabs.currentChanged.connect(self.slot_currentTabChanged)
        self.tabs.tabCloseRequested.connect(self.slot_tabCloseRequested)
        
        self.tabEditors = []
        
        self.projectManager = project.ProjectManager()
        self.addDockWidget(Qt.RightDockWidgetArea, self.projectManager)
        
        self.fileSystemBrowser = filesystembrowser.FileSystemBrowser()
        self.fileSystemBrowser.setVisible(False)
        self.addDockWidget(Qt.RightDockWidgetArea, self.fileSystemBrowser)
        
        self.undoViewer = commands.UndoViewer()
        self.undoViewer.setVisible(False)
        self.addDockWidget(Qt.RightDockWidgetArea, self.undoViewer)
        
        self.menuPanels = self.findChild(QMenu, "menuPanels")
        self.menuPanels.addAction(self.projectManager.toggleViewAction())
        self.menuPanels.addAction(self.fileSystemBrowser.toggleViewAction())
        self.menuPanels.addAction(self.undoViewer.toggleViewAction())
        
        self.connectActions()
        self.connectSignals()
        
        propertyinspector.PropertyInspectorManager.loadMappings("data/StockMappings.xml")
        
        self.restoreSettings()     
    
    def connectActions(self):
        self.newFileAction = self.findChild(QAction, "actionNewFile")
        self.newFileAction.triggered.connect(self.slot_newFileDialog)
        
        self.openFileAction = self.findChild(QAction, "actionOpenFile")
        self.openFileAction.triggered.connect(self.slot_openFileDialog)
        
        self.saveAction = self.findChild(QAction, "actionSave")
        self.saveAction.triggered.connect(self.slot_save)
        self.saveAction.setEnabled(False)
        self.saveAllAction = self.findChild(QAction, "actionSaveAll")
        self.saveAllAction.triggered.connect(self.slot_saveAll)
        self.saveAllAction.setEnabled(False)
        self.closeAction = self.findChild(QAction, "actionClose")
        self.closeAction.setEnabled(False)
        
        self.undoAction = self.findChild(QAction, "actionUndo")
        self.undoAction.triggered.connect(self.slot_undo)
        self.undoAction.setEnabled(False)
        self.redoAction = self.findChild(QAction, "actionRedo")
        self.redoAction.triggered.connect(self.slot_redo)
        self.redoAction.setEnabled(False)
        
        self.newProjectAction = self.findChild(QAction, "actionNewProject")
        self.newProjectAction.triggered.connect(self.slot_newProject)
        
        self.saveProjectAction = self.findChild(QAction, "actionSaveProject")
        self.saveProjectAction.triggered.connect(self.slot_saveProject)
        # when this starts up, no project is opened, hence you can't save the "no project"
        self.saveProjectAction.setEnabled(False)
        
        self.openProjectAction = self.findChild(QAction, "actionOpenProject")
        self.openProjectAction.triggered.connect(self.slot_openProject)
        
        self.closeProjectAction = self.findChild(QAction, "actionCloseProject")
        self.closeProjectAction.triggered.connect(self.slot_closeProject)
        # when this starts up, no project is opened, hence you can't close the current project
        self.closeProjectAction.setEnabled(False)
        
        self.projectSettingsAction = self.findChild(QAction, "actionProjectSettings")
        self.projectSettingsAction.triggered.connect(self.slot_projectSettings)
        # when this starts up, no project is opened, hence you can't view/edit settings of the current project
        self.projectSettingsAction.setEnabled(False)

        self.recentProjectsMenu = self.findChild(QMenu, "menuRecentProjects")
        
        for i in range(self.maxRecentProjects):
            action = QAction(self, visible = False, triggered = self.slot_openRecentProject)
            self.recentProjectsActions.append(action)
            self.recentProjectsMenu.addAction(action)

        self.licenseAction = self.findChild(QAction, "actionLicense")
        self.licenseAction.triggered.connect(self.slot_license)
        
        self.quitAction = self.findChild(QAction, "actionQuit")
        self.quitAction.triggered.connect(self.slot_quit)
        
    def connectSignals(self):
        self.projectManager.fileOpenRequested.connect(self.slot_openFile)
        self.fileSystemBrowser.fileOpenRequested.connect(self.slot_openFile)

    def openProject(self, path, fromRecentProject=False):
        assert(not self.project)
        
        self.project = project.Project()
        self.project.load(path)
        self.projectManager.setProject(self.project)
        self.fileSystemBrowser.setDirectory(self.project.getAbsolutePathOf(""))
        # sync up the cegui instance
        self.ceguiContainerWidget.syncToProject(self.project)
        
        # project has been opened
        # enable the project management tree
        #self.projectFiles.setEnabled(True)        
        if not fromRecentProject:
            self.updateRecentProjects(path)
            
        # and enable respective actions
        self.saveProjectAction.setEnabled(True)
        self.closeProjectAction.setEnabled(True)
        self.projectSettingsAction.setEnabled(True)
        

    def closeProject(self):
        self.projectManager.setProject(None)
        self.project.unload()
        self.project = None
        
        # no project is opened anymore
        #self.projectFiles.setEnabled(False)
        
        self.saveProjectAction.setEnabled(False)
        self.closeProjectAction.setEnabled(False)
        self.projectSettingsAction.setEnabled(False)
        
    def saveProject(self):
        self.project.save()
    
    def saveProjectAs(self, newPath):
        self.project.save(newPath)
        
    def createEditorForFile(self, absolutePath):
        ret = None
                
        filePath = os.path.relpath(absolutePath, self.project.baseDirectory) if self.project else "<No project opened>"        
        
        if not os.path.exists(absolutePath):
            ret = tab.MessageTabbedEditor(absolutePath,
                   "Couldn't find '%s' (project relative path: '%s'), please check that that your project's "
                   "base directory is set up correctly and that you hadn't deleted "
                   "the file from your HDD. Consider removing the file from the project." % (absolutePath, filePath))
        else: 
            for factory in self.editorFactories:
                if factory.canEditFile(absolutePath):
                    ret = factory.create(absolutePath)
                    break
            
            # at this point if ret is None, no registered tabbed editor factory wanted
            # to accept the file, so we create MessageTabbedEditor that will simply
            # tell the user that given file can't be edited
            #
            # IMO this is a reasonable compromise and plays well with the rest of 
            # the editor without introducing exceptions, etc...
            if not ret:
                ret = tab.MessageTabbedEditor(absolutePath,
                       "No included tabbed editor was able to accept '%s' (project relative path: '%s'), please "
                       "check that it's a file CEED supports and that it has the correct extension "
                       "(CEED enforces proper extensions)" % (absolutePath, filePath))
        
        if not self.project and ret.requiresProject:
            ret = tab.MessageTabbedEditor(absolutePath,
                       "Opening this file requires you to have a project opened!")
        
        ret.initialise(self)
        self.tabEditors.append(ret)
        
        return ret    

    def openEditorTab(self, absolutePath):
        absolutePath = os.path.normpath(absolutePath)
        
        for tabEditor in self.tabEditors:            
            if tabEditor.filePath == absolutePath:
                tabEditor.makeCurrent()
                return
                
        editor = self.createEditorForFile(absolutePath)
        editor.makeCurrent()
        
    def closeEditorTab(self, editor):
        editor.finalise()
        self.tabEditors.remove(editor)
    
    def saveSettings(self):
        #self.settings.setValue("geometry", self.saveGeometry())
        #self.settings.setValue("state", self.saveState())
        pass
        
    def restoreSettings(self):
        #if self.settings.contains("geometry"):
        #    self.restoreGeometry(self.settings.value("geometry"))
        #if self.settings.contains("state"):
        #    self.restoreState(self.settings.value("state"))
        if self.settings.contains("recentProjects"):
            self.updateRecentProjectsActions();
        
    def quit(self):
        self.saveSettings()
        
        if self.project:
            # if the slot returned False, user pressed Cancel
            if not self.slot_closeProject():
                return False
        
        lastTab = None
        while len(self.tabEditors) > 0:
            currentTab = self.tabs.widget(0)
            if currentTab == lastTab:
                # user pressed cancel on one of the tab editor 'save without changes' dialog,
                # cancel the whole quit operation!
                return False
            lastTab = currentTab
            
            self.slot_tabCloseRequested(0)
            
        self.app.exit(0)
        
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
            
            self.openProject(newProject.projectFilePath)
    
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
                return True
            
            elif result == QMessageBox.Cancel:
                return False
            
        self.closeProject()
        return True
        
    def slot_projectSettings(self):
        dialog = project.ProjectSettingsDialog(self.project)
        
        if dialog.exec_() == QDialog.Accepted:
            dialog.apply(self.project)
            self.ceguiContainerWidget.syncToProject(self.project)
    
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
        
        wdt = self.tabs.widget(index)
        
        if self.activeEditor:
            self.activeEditor.deactivate()

        # enable saving by default
        self.saveAction.setEnabled(True)

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
            self.saveAllAction.setEnabled(True)
            self.closeAction.setEnabled(True)
            
            wdt.tabbedEditor.activate()
        else:
            # None is selected right now, lets disable Save and Close actions
            self.saveAction.setEnabled(False)
            self.saveAllAction.setEnabled(False)
            self.closeAction.setEnabled(False)
            
        self.tabs.setUpdatesEnabled(True)
    
    def slot_tabCloseRequested(self, index):
        wdt = self.tabs.widget(index)
        editor = wdt.tabbedEditor
        
        if not editor.hasChanges():
            # we can close immediately
            self.closeEditorTab(editor)
            
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
                
            elif result == QMessageBox.Discard:
                # changes will be discarded
                # note: we don't have to call editor.discardChanges here
                
                self.closeEditorTab(editor)
            
            # don't do anything if user selected 'Cancel'

    def slot_save(self):
        if self.activeEditor:
            self.activeEditor.save()
    
    def slot_saveAll(self):
        for editor in self.tabEditors:
            editor.save()
        
    def slot_undo(self):
        if self.activeEditor:
            self.activeEditor.undo()
            
    def slot_redo(self):
        if self.activeEditor:
            self.activeEditor.redo()
            
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
            
    def updateRecentProjects(self,  fileName):
        self.curFile = fileName
        
        files = []
        if self.settings.contains("recentProjects"):
            files = self.settings.value("recentProjects")
        
        files.insert(0, fileName)
        
        self.settings.setValue("recentProjects", files)
        
        if len(files) > self.maxRecentProjects:
            files.removeAt(self.maxRecentProjects)

        self.updateRecentProjectsActions()
            
    def updateRecentProjectsActions(self):
        files = self.settings.value("recentProjects")

        numRecentFiles = len(files)

        for i in range(numRecentFiles):
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
        
    def slot_openRecentProject(self):
        action = self.sender()
        if action:
            if self.project:
                # give user a chance to save changes if needed
                if not self.slot_closeProject():
                    return
            
            self.openProject(action.data(), True)
