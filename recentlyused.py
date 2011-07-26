import re

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
            val = unicode(self.qsettings.value(self.sectionIdentifier))
            files = self.stringToStringList(val)
            
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
        
        self.qsettings.setValue(self.sectionIdentifier, self.stringListToString(files))
        
        # while because files could be in a bad state because of previously thrown exceptions
        # make sure we trim them correctly in all circumstances
        while len(files) > self.maxRecentlItems:
            files.remove(files[self.maxRecentlItems])
            
            
    def getRecentlyUsed(self):
        files = []
        if self.qsettings.contains(self.sectionIdentifier):
            val = unicode(self.qsettings.value(self.sectionIdentifier))
            files = self.stringToStringList(val)
            
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
            t = s.replace( ';', '\\;' )
            if first is True:
                temp = t
                first = False
            else:
                temp = temp + ";" + t
        
        return temp
        
    def stringToStringList(self, instr):
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
        reconst = ""
        for s in list:
            reconst = reconst + s
        return reconst
                
        
        
        