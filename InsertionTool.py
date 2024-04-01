from __future__ import absolute_import
from __future__ import print_function
import os
import logging                                             # logger
import pyverilog                                           # PyVerilog
from pyverilog.vparser.parser import VerilogCodeParser     # PyVerilog Parser
from pyverilog.vparser.ast import *                        # PyVerilog AST

#--------------------------------------------- LOGGER SETUP----------------------------------------#
# Configure logging - Done at file top so that all classes have it accessible
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# Setting up log file
fileHandler = logging.FileHandler('verilog_parse.log')
formatter   = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fileHandler.setFormatter(formatter)
logging.getLogger().addHandler(fileHandler)
#--------------------------------------------------------------------------------------------------#

# Exception class for pragma parsing
class PragmaParsingError(Exception):
    pass


# Class to create structured log prints of complex objects
class LogStructuring:
    def __init__(self) -> None:
        pass

    def logDictInfo(self, dict):
        mapData = "\n"
        for key in dict:
            mapData += "%s --> %s\n"%(str(key), dict[key])
        return mapData
    
    # Method to create structured log of a list
    def logListInfo(self, list):
        listData = "\n"
        for value in list:
            listData += "%s\n"%(value)    
        return listData


# Class to process filelist and extract pragmas and associated properties
class PragmaExtractor(LogStructuring):
    def __init__(self, filelist) -> None:
        super().__init__()  # LogStructuring constructor
        self.filelist = filelist
        logging.info("Pragma extractor initialized with %s"%(filelist))

    # This method parses the pragma in a line to returns two tuples
    # (start range, end range) for observe and (type, start range, end range) for control
    def pragmaParser(self, line):
        if "#pragma" in line:
            pragmaArgs = line.split("#pragma", 1)[1].strip().split()
            if "control" in pragmaArgs and "observe" in pragmaArgs:
                try:
                    observe_index = pragmaArgs.index("observe") + 1
                    control_index = pragmaArgs.index("control") + 2
                    control_type  = pragmaArgs[pragmaArgs.index("control") + 1]
                    observe_range = pragmaArgs[observe_index].split(':')
                    control_range = pragmaArgs[control_index].split(':')
                    return (int(observe_range[0]), int(observe_range[1])), \
                        (control_type, int(control_range[0]), int(control_range[1]))
                except (IndexError, ValueError):
                    logging.error("Found incorrect arguments for control/observe pragma in line \n%s"%(line))
                    raise PragmaParsingError("Invalid pragma directive: Insufficient or incorrect arguments for 'control' or 'observe'")
            elif "control" in pragmaArgs:
                try:
                    control_index = pragmaArgs.index("control") + 2
                    control_range = pragmaArgs[control_index].split(':')
                    control_type  = pragmaArgs[pragmaArgs.index("control") + 1]
                    return None, (control_type, int(control_range[0]), int(control_range[1]))
                except (IndexError, ValueError):
                    logging.error("Found incorrect arguments for control pragma in line \n%s"%(line))
                    raise PragmaParsingError("Invalid pragma directive: Insufficient or incorrect arguments for 'control'")
            elif "observe" in pragmaArgs:
                try:
                    observe_index = pragmaArgs.index("observe") + 1
                    observe_range = pragmaArgs[observe_index].split(':')
                    return (int(observe_range[0]), int(observe_range[1])), None
                except (IndexError, ValueError):
                    logging.error("Found incorrect arguments for observe pragma in line \n%s"%(line))
                    raise PragmaParsingError("Invalid pragma directive: Insufficient or incorrect arguments for 'observe'")
            else:
                    logging.error("Invalid pragma directive: Neither 'control' nor 'observe' found in \n%s"%(line))
                    raise PragmaParsingError("Invalid pragma directive: Neither 'control' nor 'observe' found")
        else:
            return None, None

    # Parses a file and populates a hash map with line # and observe, control args
    def fileParser(self, file):
        # Ensure that the file exists
        assert os.path.exists(file), "Verilog file %s in filelist doesn't exist"%(file)
        pragmaDict = {}
        with open(file, 'r') as f:
            for line_number, line in enumerate(f, start=1):
                observe, control = self.pragmaParser(line)
                if observe or control:
                    pragmaDict[line_number] = (observe, control)
        logging.info("Pragma distribution in file - %s is %s"%(file, self.logDictInfo(pragmaDict)))
        return pragmaDict
    
    # Goes through filelist, parses every file in the filelist for pragmas
    def filelistParse(self):
        # Ensure that the filelist exists
        assert os.path.exists(self.filelist), "Filelist %s doesn't exist"%(self.filelist)
        files = [filename.strip() for filename in open(self.filelist, 'r')]
        logging.info("Files in filelist %s - %s"%(self.filelist, self.logListInfo(files)))
        return {file: self.fileParser(file) for file in files}


# Class to populate a map {file: {signal:{observe:None/[start, end],
#                                         control:None/[type, start, end]}}}
class VerilogParser(LogStructuring):
    def __init__(self, filelist) -> None:
        super().__init__()  # LogStructuring constructor
        self.VERSION = pyverilog.__version__
        self.filelist = filelist
        self.pragmaExtractor = PragmaExtractor(self.filelist)
        logging.info("Parser initialized with %s"%(self.filelist))

    # Source file to AST hash map
    def fileWiseAst(self):
        assert os.path.exists(self.filelist), "Filelist %s doesn't exist"%(self.filelist)
        files = [filename.strip() for filename in open(self.filelist, 'r') if filename.strip()]
        print (files)
        assert all(os.path.exists(file) for file in files), "Not all files in the filelist are valid"
        fileToAst = {file: VerilogCodeParser([file]).parse() for file in files}
        if all(value is not None for value in fileToAst.values()):
            logging.info("Filewise AST generated")
        else:
            logging.warning("Invalid ASTs found during fileToAst generation")
        return fileToAst
    
    # Recursive method for AST traversal
    # This method finds Ports/Decl and check if there is a corresponding pragma
    # In effect: For a given file, find the
    # signal associated with each pragma and segregate the signals 
    # into signalToControl and signalToObserve maps.
    # signalToObserve - {<SIGNAL>:(START_INDEX, END_INDEX)}
    # signalToControl - {<SIGNAL>:(CONTROL_TYPE, START_INDEX, END_INDEX)}
    def traverseAst(self, astNode, lineToPragma, signalToControl, signalToObserve):
        if astNode is not None:
            childNodes = astNode.children()
            if isinstance(astNode, Input) or  \
               isinstance(astNode, Output) or \
               isinstance(astNode, Inout) or  \
               isinstance(astNode, Reg) or  \
               isinstance(astNode, Wire): 
                # Check if the line has a pragma
                if astNode.lineno in lineToPragma:
                    # Check if there is an observe and control pragma
                    if lineToPragma[int(astNode.lineno)][0] and lineToPragma[int(astNode.lineno)][1]:
                        signalToObserve.update({astNode.name:(lineToPragma[int(astNode.lineno)][0][0],   \
                                                              lineToPragma[int(astNode.lineno)][0][1])})  
                        signalToControl.update({astNode.name:(lineToPragma[int(astNode.lineno)][1][0],   \
                                                              lineToPragma[int(astNode.lineno)][1][1],   \
                                                              lineToPragma[int(astNode.lineno)][1][2])}) 
                    # Check if there is only an observe pragma
                    elif lineToPragma[int(astNode.lineno)][0]:
                        signalToObserve.update({astNode.name:(lineToPragma[int(astNode.lineno)][0][0],   \
                                                              lineToPragma[int(astNode.lineno)][0][1])})  
                    
                    # Given pragma is exception protected, this one should be control pragma
                    else:
                        signalToControl.update({astNode.name:(lineToPragma[int(astNode.lineno)][1][0],   \
                                                              lineToPragma[int(astNode.lineno)][1][1],   \
                                                              lineToPragma[int(astNode.lineno)][1][2])}) 
            for childNode in childNodes:
                signalToObserveChild, signalToControlChild = self.traverseAst(childNode, lineToPragma, signalToControl, signalToObserve)
                signalToObserve.update(signalToObserveChild)
                signalToControl.update(signalToControlChild)
        return signalToObserve, signalToControl

    # For a given file, performs AST traversal on all modules to extract
    # signalToObserve - {<SIGNAL>:(START_INDEX, END_INDEX)}
    # signalToControl - {<SIGNAL>:(CONTROL_TYPE, START_INDEX, END_INDEX)}
    def signalToPragma(self, ast, lineToPragma):
        moduleDefs = ast.description.definitions
        signalToControl = {}
        signalToObserve = {}
        for moduleDef in moduleDefs:
            signalToObservePerModule, signalToControlPerModule = self.traverseAst(moduleDef, lineToPragma, {}, {})
            signalToControl.update(signalToControlPerModule)
            signalToObserve.update(signalToObservePerModule)
        return signalToObserve, signalToControl



    # For all files in the file list creates the following hash maps:
    # Observability Map:   {<FILE>:{<SIGNAL>:(START_INDEX, END_INDEX)}} 
    # Controllability Map: {<FILE>:{<SIGNAL>:(CONTROL_TYPE, START_INDEX, END_INDEX)}} 
    def fileToSignalToPragma(self):
        fileToAst    = self.fileWiseAst()
        fileToPragma = self.pragmaExtractor.filelistParse()
        fileToSignalToControl = {}
        fileToSignalToObserve = {}

        # For all files populates signals and appropriate observe/control properties
        for file in fileToAst:
            signalToObserve, signalToControl = self.signalToPragma(fileToAst[file], fileToPragma[file])
            if bool(signalToObserve) | bool(signalToControl):
                logging.info("Observable/Controllable signals found in file - %s"%(str(file)))
            else:
                logging.warning("No observable or controllable signals found in file - %s"%(str(file)))
            fileToSignalToObserve.update({file:signalToObserve})
            fileToSignalToControl.update({file:signalToControl})
        return fileToSignalToObserve, fileToSignalToControl



if __name__ == '__main__':
    filelist = "filelist.f"
    logging.info("Verilog signal parsing started for filelist %s"%(filelist))
    parser = VerilogParser(filelist)
    fileToSignalToObserve, fileToSignalToControl = parser.fileToSignalToPragma()
    print (fileToSignalToObserve)
    print (fileToSignalToControl)