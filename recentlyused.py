import cPickle

class RecentlyUsed(object):
    def __init__(self, qsettings, sectionIdentifier):
        self.sectionIdentifier = "recentlyUsedIdentifier/" + sectionIdentifier
        self.qsettings = qsettings
        # how many recent files should the editor remember
        self.maxRecentlItems = 5
        # to how many characters should the recent file names be trimmed to
        self.recentlItemsNameTrimLength = 40
        
    def addRecentlyUsed(self, fileName):        
        files = []
        if self.qsettings.contains(self.sectionIdentifier):
            val = str(self.qsettings.value(self.sectionIdentifier))
            temp = cPickle.loads(val)
            files = self.stringToStringList(temp)
            
        # if something went wrong before, just drop recent projects and start anew,
        # recent projects aren't that important
        if not isinstance(files, list):
            files = []
        
        isInList = False
        for f in files:
            if f == fileName:
                files.remove(f)
                files.insert(0, f)
                isInList = True
                break
        
        #only insert the file if it is not already in list,
        if not isInList:
            files.insert(0, fileName)
        
        self.qsettings.setValue(self.sectionIdentifier, cPickle.dumps(self.stringListToString(files)))
        
        # while because files could be in a bad state because of previously thrown exceptions
        # make sure we trim them correctly in all circumstances
        while len(files) > self.maxRecentlItems:
            files.remove(files[self.maxRecentlItems])
            
            
    def getRecentlyUsed(self):
        files = []
        if self.qsettings.contains(self.sectionIdentifier):
            val = str(self.qsettings.value(self.sectionIdentifier))
            temp = cPickle.loads(val)
            files = self.stringToStringList(temp)
            
        return files

    def trimFileName(self, fileName):
        if (len(fileName) > self.recentlItemsNameTrimLength):
            # + 3 because of the ...
            trimedFileName = "...%s" % (fileName[-self.recentlItemsNameTrimLength + 3:])
            return trimedFileName
        else:
            return fileName
        
    def stringListToString(self, list):
        temp = ""
        
        first = True
        for s in list:
            if first is True:
                temp = s
                first = False
            else:
                temp = temp + ";" + s
        
        return temp
        
    def stringToStringList(self, instr):
        return instr.split(";")
        
        
        
        
        