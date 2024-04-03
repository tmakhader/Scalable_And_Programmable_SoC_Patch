from __future__ import absolute_import
from __future__ import print_function
import os
import copy
import logging                                                       # logger
import pyverilog                                                     # PyVerilog
from pyverilog.vparser.parser import VerilogCodeParser               # PyVerilog Parser
from pyverilog.vparser.ast import *                                  # PyVerilog AST
from pyverilog.ast_code_generator.codegen import ASTCodeGenerator    # AST to verilog code generator

#--------------------------------------------- LOGGER SETUP----------------------------------------#
# Configure logging - Done at file top so that all classes have it accessible
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# Setting up log file
fileHandler = logging.FileHandler('verilog_parse.log', mode='w') 
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
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
            if isinstance(astNode, Input)  or  \
               isinstance(astNode, Output) or  \
               isinstance(astNode, Reg)    or  \
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
                self.traverseAst(childNode, lineToPragma, signalToControl, signalToObserve)
        return 

    # For a given file, performs AST traversal on all modules to extract
    # signalToObserve - {<SIGNAL>:(START_INDEX, END_INDEX)}
    # signalToControl - {<SIGNAL>:(CONTROL_TYPE, START_INDEX, END_INDEX)}
    def signalToPragma(self, ast, lineToPragma):
        moduleDefs = ast.description.definitions
        signalToControl = {}
        signalToObserve = {}
        for moduleDef in moduleDefs:
            if isinstance(moduleDef, ModuleDef):
                self.traverseAst(moduleDef, lineToPragma, signalToControl, signalToObserve)
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
            logging.info("Starting AST traversal for file - %s"%(file))
            signalToObserve, signalToControl = self.signalToPragma(fileToAst[file], fileToPragma[file])
            if bool(signalToObserve) | bool(signalToControl):
                logging.info("AST traversal complete: Observable/Controllable signals found in file - %s"%(str(file)))
            else:
                logging.warning("AST traversal complete: No observable or controllable signals found in file - %s"%(str(file)))
            fileToSignalToObserve.update({file:signalToObserve})
            fileToSignalToControl.update({file:signalToControl})
        return fileToSignalToObserve, fileToSignalToControl



# Class to generate modified verilog code based on added pragmas
class VerilogGenerator(LogStructuring):
    def __init__(self, filewiseAst, fileToSignalToObserve, fileToSignalToControl, observePort, controlPortIn, controlPortOut) -> None:
        self.filewiseAst = filewiseAst
        self.fileToSignalToObserve = fileToSignalToObserve
        self.fileToSignalToControl = fileToSignalToControl
        self.observePort = observePort
        self.controlPortIn = controlPortIn
        self.controlPortOut = controlPortOut
    
    # Create necessary tap (assignment )logic for observe signals to propagate to SMU
    def createObserveTaps(self, signalToObserve):
        assignmentList = []
        observePortIndexLast = 0
        for signal in signalToObserve:
            signalRangeLhs = signalToObserve[signal][0]
            signalRangeRhs = signalToObserve[signal][1]
            observePortRangeLhs = observePortIndexLast + (signalRangeRhs - signalRangeLhs)
            observePortRangeRhs = observePortIndexLast
            Lhs = Partselect(Identifier(self.observePort),  \
                            IntConst(observePortRangeLhs), \
                            IntConst(observePortRangeRhs))
            Rhs = Partselect(Identifier(signal),  \
                            IntConst(signalRangeLhs), \
                            IntConst(signalRangeRhs))
            assignmentList.append(Assign(Lhs, Rhs))
            observePortIndexLast = observePortRangeLhs + 1
        return assignmentList, observePortIndexLast - 1
    
    def signalCounterPart(self, signal):
        if "controlled" in signal:
            return signal[0:signal.index("_controlled")-1]
        else:
            return signal + "_controlled"


    # Create necessary tap (assignment) logic for control signals to propagate to and from SRU   
    #                                         ________
    # signal 1 ---|      (SRU Input Tap)     |        |     (SRU Output Tap)  | --- signal' 1
    # signal 2 ---|------ controlPortIn- ----|  SRU   |------ControlPortOut---| --- signal' 2
    # ,,,,,,,, ---|                          |________|                       | --- ,,,,,,,,,
    def createControlTaps(self, sruDriverList, sruLoadList):
        assignmentList = []
        controlPortInIndexLast = 0
        controlPortOutIndexLast = 0
        # Input tap assignment - assign <controlPortIn[range]]> = <signal[START:END]>;
        for signalNode in sruDriverList:
            signalRangeLhs = signalNode[1]
            signalRangeRhs = signalNode[2]
            controlPortRangeLhs = controlPortInIndexLast + (signalRangeRhs - signalRangeLhs)
            controlPortRangeRhs = controlPortInIndexLast
            Lhs = Partselect(Identifier(self.controlPortIn), \
                            IntConst(controlPortRangeLhs),   \
                            IntConst(controlPortRangeRhs))
            Rhs = Partselect(Identifier(signalNode[0]),      \
                            IntConst(signalRangeLhs),        \
                            IntConst(signalRangeRhs))
            assignmentList.append(Assign(Lhs, Rhs))
            controlPortInIndexLast = controlPortRangeLhs + 1

        # Output tap assignment - assign <signal'[START:END]> = <controlPortIn[range]]>
        # FIXME (Not implemented) assign <signal'[rest]> = <signal[rest]>
        for signalNode in sruLoadList:
            signalRangeLhs = signalNode[1]
            signalRangeRhs = signalNode[2]
            controlPortRangeLhs = controlPortOutIndexLast + (signalRangeRhs - signalRangeLhs)
            controlPortRangeRhs = controlPortOutIndexLast
            Lhs = Partselect(Identifier(signalNode[0]),  \
                            IntConst(signalRangeLhs),             \
                            IntConst(signalRangeRhs))
            Rhs = Partselect(Identifier(self.controlPortOut),     \
                            IntConst(controlPortRangeLhs),        \
                            IntConst(controlPortRangeRhs))
            assignmentList.append(Assign(Lhs, Rhs))
            controlPortOutIndexLast = controlPortOutIndexLast + 1

        return assignmentList, controlPortInIndexLast - 1, controlPortOutIndexLast - 1
    
    # This method recursively traverses the AST to modify all drivers of a signal
    def traverseAstToModifyLHS(self, astNode, signal):
        # traverse the node if the nod is valid and it is not branching to an RHS assignment
        if astNode is not None and not isinstance(astNode, Rvalue):
            childNodes = astNode.children()
            if isinstance(astNode, Identifier):
                if astNode.name == signal:
                    astNode.name = astNode.name  + "_controlled"
            for child in childNodes:
                self.traverseAstToModifyLHS(child, signal)
        return

    # This method recursively traverses the AST to modify all loads of a signal
    def traverseAstToModifyRHS(self, astNode, signal):
        # traverse the node if the nod is valid and it is not branching to an RHS assignment
        if astNode is not None and not isinstance(astNode, Lvalue):
            childNodes = astNode.children()
            if isinstance(astNode, Identifier):
                if astNode.name == signal:
                    astNode.name = astNode.name  + "_controlled"
            for child in childNodes:
                self.traverseAstToModifyRHS(child, signal)
        return
 
    # Method to modify controlled IO ports
    def ModifyControlledIOPorts(self, moduleDef, signalToControl):
        items = list(moduleDef.items) # Items include Decls, Assigns, Blocks etc
        ports = list(moduleDef.portlist.ports)
        newPorts = []
        sruDriverList = [] # Drivers of SRU input (each would be a tuple (signal, start_index, end_index))
        sruLoadList = []   # Loads for SRU output (each would be a tuple (signal, start_index, end_index))
        for port in ports:
            #                  ________                               _________                                 
            #                 |        |                             |         |                             
            #  Input(A) ------| Wire(A)| ----To SRU --- From SRU --- | Wire(A')| -------- Loads 
            #                 |        |                             |         |                              
            #                 |________|                             |_________|
            #                                                                                                                                                                           
            # If the controlled port is an Input wire A 
            # -- Declare a new wire A_controlled
            # -- Leave the input as is
            # -- Change all loads (RHS) of A to A_controlled 
            if isinstance(port.second, Wire) and isinstance(port.first, Input):
                newPorts.append(port)
                if port.first.name in signalToControl:
                    logging.info("Bits [%s:%s] of Input port %s found as %s controlled"%(signalToControl[port.first.name][1],  \
                                                                                     signalToControl[port.first.name][2],  \
                                                                                     port.first.name,                      \
                                                                                     signalToControl[port.first.name][0]))
                    newWire  = Decl((Wire(name = port.second.name + "_controlled", \
                                          width = port.second.width,               \
                                          signed = port.second.signed,             \
                                          dimensions = port.second.dimensions),))
                    items.insert(0, newWire)
                    self.traverseAstToModifyRHS(moduleDef, port.first.name)
                    sruDriverList.append((port.second.name,                        \
                                          signalToControl[port.second.name][1],    \
                                          signalToControl[port.second.name][2]))
                    sruLoadList.append((port.second.name + "_controlled",
                                        signalToControl[port.second.name][1],      \
                                        signalToControl[port.second.name][2]))
            #                  _________                                     ________
            #                 |         |                                   |        |
            #  Drivers -------| Wire(A')| -------- To SRU ---- From SRU ----| Wire(A)| -- Output
            #                 |         |                                   |        |                    
            #                 |_________|                                   |________|   
            #                                                                   |
            #                                                                   |                                                            
            #                                                            To internal loads
            # If the controlled port is an Output wire
            # -- Declare a new wire A_controlled 
            # -- Leave the output as is
            # -- Change all drivers (LHS) of A to A_controlled
            elif isinstance(port.second, Wire) and isinstance(port.first, Output):
                newPorts.append(port)
                if port.first.name in signalToControl:
                    logging.info("Bits [%s:%s] of Output (wire) port %s found as %s controlled"%(signalToControl[port.first.name][1], \
                                                                                                 signalToControl[port.first.name][2], \
                                                                                                 port.first.name,                     \
                                                                                                 signalToControl[port.first.name][0]))
                    newWire  = Decl((Wire(name = port.second.name + "_controlled", \
                                          width = port.second.width,               \
                                          signed = port.second.signed,             \
                                          dimensions = port.second.dimensions),))
                    items.insert(0, newWire)
                    self.traverseAstToModifyLHS(moduleDef, port.first.name)
                    sruDriverList.append((port.second.name + "_controlled",        \
                                          signalToControl[port.second.name][1],    \
                                          signalToControl[port.second.name][2]))
                    sruLoadList.append((port.second.name,
                                        signalToControl[port.second.name][1],      \
                                        signalToControl[port.second.name][2]))
            #                  ________                                      ________
            #                 |        |                                    |        |
            #  Drivers -------| Reg(A')| -------- To SRU ---- From SRU ---- | Wire(A)| -- Output
            #                 |        |                                    |        |                 
            #                 |________|                                    |________|                           
            #                                                                   |
            #                                                                   |                                                            
            #                                                            To internal loads  
            # If the controlled port is an Output reg
            # -- Declare a new reg A_controlled
            # -- Change the output port type to wire
            # -- Change all drivers of A to A_controlled 
            elif isinstance(port.second, Reg) and isinstance(port.first, Output):
                if port.first.name in signalToControl:
                    logging.info("Bits [%s:%s] of Output (reg) port %s found as %s controlled"%(signalToControl[port.first.name][1], \
                                                                                                signalToControl[port.first.name][2], \
                                                                                                port.first.name,                     \
                                                                                                signalToControl[port.first.name][0]))
                    newReg   = Decl((Reg(name = port.second.name + "_controlled",  \
                                         width = port.second.width,                \
                                         signed = port.second.signed,
                                         dimensions = port.second.dimensions),))
                    items.insert(0, newReg)
                    portWire = Wire(name = port.second.name,                       \
                                    width = port.second.width,                     \
                                    signed = port.second.signed,                   \
                                    dimensions = port.second.dimensions)
                    newOutput = Output(name = port.first.name,                     \
                                       width = port.first.width)
                    newPort   = Ioport(first=newOutput, second=portWire)
                    newPorts.append(newPort) 
                    self.traverseAstToModifyLHS(moduleDef, port.first.name)
                    sruDriverList.append((port.second.name + "_controlled",        \
                                          signalToControl[port.second.name][1],    \
                                          signalToControl[port.second.name][2]))
                    sruLoadList.append((port.second.name,                          \
                                        signalToControl[port.second.name][1],      \
                                        signalToControl[port.second.name][2]))
                else:
                    newPorts.append(port)
            else:
                newPorts.append(port)
        moduleDef.items = tuple(items)
        moduleDef.portlist.ports = tuple(newPorts)
        return sruDriverList, sruLoadList
        

    # Method to modify controlled Reg/Wire declarations
    def ModifyControlledRegAndWires(self, moduleDef, signalToControl):
        items = list(moduleDef.items)
        newItems = []      # item list (to be converted to tuple) for new AST items
        sruDriverList = [] # Drivers of SRU input (each would be a tuple (signal, start_index, end_index))
        sruLoadList = []   # Loads for SRU output (each would be a tuple (signal, start_index, end_index))
        for item in items:
            if isinstance(item, Decl):
                #                 ________                                  ________
                #                |        |                                |        |
                #  Drivers ------| Reg(A')| ----- To SRU ---- From SRU --- | Wire(A)| --- Loads 
                #                |________|                                |________|
                #        
                # if a controlled signal is a reg declaration A  
                # -- Declare a new register - A_controlled
                # -- Convert the the register A to wire
                # -- Change all the drivers of A to A_controlled
                if isinstance(item.list[0], Reg):   # NOTE: item.list is a tuple
                    regDecl = item.list[0]
                    if regDecl.name in signalToControl:
                        logging.info("Bits [%s:%s] of Register %s found as %s controlled"%(signalToControl[regDecl.name][1], \
                                                                                           signalToControl[regDecl.name][2], \
                                                                                           regDecl.name,                     \
                                                                                           signalToControl[regDecl.name][0]))
                        # Making a Declaration node passed with list (tuple) of the new register - A_controlled
                        newReg =  Decl((Reg(name = regDecl.name + "_controlled",   \
                                            width = regDecl.width,                 \
                                            signed = regDecl.signed,               \
                                            dimensions = regDecl.dimensions),))
                        # Making a Declaration node passed with list (tuple) of the register converted to wire
                        newWire = Decl((Wire(name = regDecl.name,                  \
                                            width = regDecl.width,                 \
                                            signed = regDecl.signed,               \
                                            dimensions = regDecl.dimensions),))
                        newItems.append(newWire)
                        newItems.append(newReg)
                        self.traverseAstToModifyLHS(moduleDef, regDecl.name)
                        sruDriverList.append((regDecl.name + "_controlled",        \
                                              signalToControl[regDecl.name][1],
                                              signalToControl[regDecl.name][2]))
                        sruLoadList.append((regDecl.name,
                                            signalToControl[regDecl.name][1],
                                            signalToControl[regDecl.name][2]))
                        

                    else:
                        newItems.append(item)
                #                 _________                                  ________
                #                |         |                                |        |
                #  Drivers ------| Wire(A')| ----- To SRU ---- From SRU --- | Wire(A)| --- Loads 
                #                |_________|                                |________|
                #        
                # if a controlled signal is a wire declaration A  
                # -- Declare a new wire - A_controlled
                # -- leave wire A as is
                # -- Change all drivers of A to A_controlled
                elif isinstance(item.list[0], Wire):
                    wireDecl = item.list[0]
                    if wireDecl.name in signalToControl:
                        logging.info("Bits [%s:%s] of Wire %s found as %s controlled"%(signalToControl[wireDecl.name][1], \
                                                                                       signalToControl[wireDecl.name][2], \
                                                                                       wireDecl.name,                     \
                                                                                       signalToControl[wireDecl.name][0]))
                        # Making a Declaration node passed with list (tuple) of the new wire - A_controlled
                        newWire = Decl((Wire(name = wireDecl.name + "_controlled",  \
                                            width = wireDecl.width,                 \
                                            signed = wireDecl.signed,               \
                                            dimensions = wireDecl.dimensions),))
                        # Existing controlled wire will remain in place 
                        oldWire = Decl((Wire(name = wireDecl.name,                  \
                                            width = wireDecl.width,                 \
                                            signed = wireDecl.signed,               \
                                            dimensions = wireDecl.dimensions),))
                        newItems.append(newWire)
                        newItems.append(oldWire)    
                        self.traverseAstToModifyLHS(moduleDef, wireDecl.name)
                        sruDriverList.append((wireDecl.name + "_controlled",        \
                                              signalToControl[wireDecl.name][1],
                                              signalToControl[wireDecl.name][2]))
                        sruLoadList.append((wireDecl.name,
                                            signalToControl[wireDecl.name][1],      \
                                            signalToControl[wireDecl.name][2]))
                    else:
                        newItems.append(item)
                else:
                    newItems.append(item)
            else:
                newItems.append(item)
        moduleDef.items = tuple(newItems)
        return sruDriverList, sruLoadList


    def addLogicForControl(self, moduleNode, signalToControl):
        sruDriverListIo, sruLoadListIo   = self.ModifyControlledIOPorts(moduleNode, signalToControl)
        sruDriverListDec, sruLoadListDec = self.ModifyControlledRegAndWires(moduleNode, signalToControl)

        assignmentList, controlPortInIndexLast, controlPortOutIndexLast = self.createControlTaps((sruDriverListIo + sruDriverListDec),
                                                                                                 (sruLoadListIo + sruLoadListDec))
        # Adding Control port input and output
        controlPortInWidth  =  Width(msb=IntConst(controlPortInIndexLast), lsb=IntConst(0))
        controlPortOutWidth =  Width(msb=IntConst(controlPortOutIndexLast), lsb=IntConst(0))
        controlPortOutput   = Ioport(Output(self.controlPortIn, width=controlPortInWidth))
        controlPortInput    = Ioport(Input(self.controlPortOut, width=controlPortOutWidth))
        amendedPort = list(moduleNode.portlist.ports)
        amendedPort.extend([controlPortInput, controlPortOutput])
        moduleNode.portlist.ports = tuple(amendedPort)
        items_list = list(moduleNode.items)
        for assignment in assignmentList:
            items_list.insert(0, assignment)
        moduleNode.items = tuple(items_list)


    
    # This method modifies the module AST node to add observe ports and assignments
    def addPumpsForObserveSignals(self, moduleNode, signalToObserve):
        assignmentList, observePortIndexLast = self.createObserveTaps(signalToObserve)
        outputWidth = Width(msb=IntConst(observePortIndexLast), lsb=IntConst(0))
        observePortOutput = Ioport(Output(self.observePort, width=outputWidth))
        amendedPort = list(moduleNode.portlist.ports)
        amendedPort.append(observePortOutput)
        moduleNode.portlist.ports = tuple(amendedPort)
        items_list = list(moduleNode.items)
        for assignment in assignmentList:
            items_list.append(assignment)
        moduleNode.items = tuple(items_list)
    
    # This method does module-wise code insertion in a file
    def fileModifier(self, file, signalToObserve, signalToControl):
        ast = self.filewiseAst[file]
        moduleDefs = ast.description.definitions
        for moduleDef in moduleDefs:
            if isinstance(moduleDef, ModuleDef):
                self.addLogicForControl(moduleDef, signalToControl)
    
    # This method generates new verilog code for a file
    def genModifiedVerilogFile(self, file, signalToObserve, signalToControl):
        codegen = ASTCodeGenerator()
        newFilename = os.path.splitext(file)[0] + "_patch.v"
        logging.info("Inserting patch wiring in file - %s" %(file))
        self.fileModifier(file, signalToObserve, signalToControl)
        verilogCode = codegen.visit(self.filewiseAst[file])
        with open(newFilename, "w") as f:
            f.write(str(verilogCode))
    
    # This method generates new verilog code for each file in the filelist
    def generateVerilog(self):
        logging.info("Starting Patch Logic Insertion.....")
        for file in self.fileToSignalToObserve:
            self.genModifiedVerilogFile(file, self.fileToSignalToObserve[file],   \
                                              self.fileToSignalToControl[file])
        logging.info("Patch logic insertion complete.")


if __name__ == '__main__':
    filelist = "filelist.f"
    logging.info("Verilog signal parsing started for filelist %s"%(filelist))
    parser = VerilogParser(filelist)
    fileToSignalToObserve, fileToSignalToControl = parser.fileToSignalToPragma()
    filewiseAst = parser.fileWiseAst()
    OBSERVE_PORT_NAME = "observe_sig"
    CONTROL_PORT_IN_NAME = "control_port_in"
    CONTROL_PORT_OUT_NAME = "control_port_out"
    verilogGenerator = VerilogGenerator(filewiseAst,              \
                                        fileToSignalToObserve,    \
                                        fileToSignalToControl,    \
                                        OBSERVE_PORT_NAME,        \
                                        CONTROL_PORT_IN_NAME,     \
                                        CONTROL_PORT_OUT_NAME)
    verilogGenerator.generateVerilog()