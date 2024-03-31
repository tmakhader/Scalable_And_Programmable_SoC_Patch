from __future__ import absolute_import
from __future__ import print_function
import os
import pyverilog                                           # PyVerilog
from pyverilog.vparser.parser import VerilogCodeParser     # PyVerilog Parser
from pyverilog.vparser.ast import *                        # PyVerilog AST

# Exception class for pragma parsing
class PragmaParsingError(Exception):
    pass


# Class to process filelist and extract pragmas and associated properties
class PragmaExtractor:
    def __init__(self, filelist) -> None:
        self.filelist = filelist

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
                    raise PragmaParsingError("Invalid pragma directive: Insufficient or incorrect arguments for 'control' or 'observe'")
            elif "control" in pragmaArgs:
                try:
                    control_index = pragmaArgs.index("control") + 2
                    control_range = pragmaArgs[control_index].split(':')
                    control_type  = pragmaArgs[pragmaArgs.index("control") + 1]
                    return None, (control_type, int(control_range[0]), int(control_range[1]))
                except (IndexError, ValueError):
                    raise PragmaParsingError("Invalid pragma directive: Insufficient or incorrect arguments for 'control'")
            elif "observe" in pragmaArgs:
                try:
                    observe_index = pragmaArgs.index("observe") + 1
                    observe_range = pragmaArgs[observe_index].split(':')
                    return (int(observe_range[0]), int(observe_range[1])), None
                except (IndexError, ValueError):
                    raise PragmaParsingError("Invalid pragma directive: Insufficient or incorrect arguments for 'observe'")
            else:
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
        return pragmaDict
    
    # Goes through filelist, parses every file in the filelist for pragmas
    def filelistParse(self):
        # Ensure that the filelist exists
        assert os.path.exists(self.filelist), "Filelist %s doesn't exist"%(self.filelist)
        files = [filename.strip() for filename in open(self.filelist, 'r') if filename.strip()]
        return {file: self.fileParser(file) for file in files}


# Class to populate a map {file: {signal:{observe:None/[start, end],
#                                         control:None/[type, start, end]}}}
class VerilogParser:
    def __init__(self, filelist) -> None:
        self.VERSION = pyverilog.__version__
        self.filelist = filelist

    # Source file to AST hash map
    def fileWiseAst(self):
        assert os.path.exists(self.filelist), "Filelist %s doesn't exist"%(self.filelist)
        files = [filename.strip() for filename in open(self.filelist, 'r') if filename.strip()]
        print (files)
        assert all(os.path.exists(file) for file in files), "Not all files in the filelist are valid"
        fileToAst = {file: VerilogCodeParser([file]).parse() for file in files}
        return fileToAst
    
    
    # For a given file (ast and pragmaHashMap computed), find the
    # signal associated with each pragma and segregate the signals 
    # into signalToControl and signalToObserve maps.
    # signalToObserve - {<SIGNAL>:(START_INDEX, END_INDEX)}
    # signalToControl - {<SIGNAL>:(CONTROL_TYPE, START_INDEX, END_INDEX)}
    def traverseAst(self, ast, pragma):
        ModuleDefs = ast.description.definitons
        signalToControl = {}
        signalToObserve = {}

        # Traverse through each Module defintions
        for definition in ModuleDefs:
            for item in definition.children:
                itemHash = {}

                if isinstance(item, Input) or  \
                   isinstance(item, Output) or \
                   isinstance(item, Inout) or  \
                   isinstance(item, Decl):
                    # Check if the line has a pragma
                    if pragma[int(item.lineno)]:
                        # Check if there is an observe and control pragma
                        if pragma[item.lineno][0] and pragma[item.lineno][1]:
                            signalToObserve.update({item.name:(pragma[int(item.lineno)][0][0],   \
                                                               pragma[int(item.lineno)][0][1])})  
                            signalToControl.update({item.name:(pragma[int(item.lineno)][0][0],   \
                                                               pragma[int(item.lineno)][0][0],   \
                                                               pragma[int(item.lineno)][0][1])}) 
                        # Check if there is only an observe pragma
                        elif pragma[item.lineno][0]:
                            signalToObserve.update({item.name:(pragma[int(item.lineno)][0][0],   \
                                                               pragma[int(item.lineno)][0][1])})  
                        
                        # Given pragma is exception protected, this one should be control pragma
                        else:
                            signalToControl.update({item.name:(pragma[int(item.lineno)][0][0],   \
                                                               pragma[int(item.lineno)][0][0],   \
                                                               pragma[int(item.lineno)][0][1])}) 
        return signalToObserve, signalToControl

    # For all files in the file list creates the following hash maps:
    # Observability Map:   {<FILE>:{<SIGNAL>:(START_INDEX, END_INDEX)}} 
    # Controllability Map: {<FILE>:{<SIGNAL>:(CONTROL_TYPE, START_INDEX, END_INDEX)}} 
    def fileToSignalToPragma(self):
        fileToAst    = self.fileWiseAst()
        fileToPragma = PragmaExtractor(self.filelist).filelistParse()
        fileToSignalToControl = {}
        fileToSignalToObserve = {}

        # For all files populates signals and appropriate observe/control properties
        for file in fileToAst:
            signalToObserve, signalToControl = self.traverseAst(fileToAst[file], fileToPragma[file])
            fileToSignalToObserve.update({file:signalToObserve})
            fileToSignalToControl.update({file:signalToControl})



if __name__ == '__main__':
    #extractor = PragmaExtractor("filelist.f")
    #print(extractor.filelistParse())
    parser = VerilogParser("filelist.f")
    astMap = parser.fileWiseAst()
    print (astMap)