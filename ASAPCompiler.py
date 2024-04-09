from typing import List
import ply.lex as lex
import logging                                                       # logger
import pyfiglet                                                      # ASCII formatter (Just for tooling fun :) :))
import re                                                            # Regex

#--------------------------------------------- LOGGER SETUP----------------------------------------#
# Configure logging - Done at file top so that all classes have it accessible
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# Setting up log file
fileHandler = logging.FileHandler('asap_compiler.log', mode='w') 
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fileHandler.setFormatter(formatter)
logging.getLogger().addHandler(fileHandler)
logging.info("Started Automatic, Scalable And Programmable (ASAP) tool for Hardware Patching...\n\n " + pyfiglet.figlet_format("ASAP COMPILER"))
#--------------------------------------------------------------------------------------------------#


# **************************** <SMU PATCH FILE (<name>.asap.smu) GRAMMER> *************************************
# Every observable sequence is enclosed within - {}
# Within an observable sequence, a pattern is enclosed within <>
# There can be multiple patterns in a sequence.
# A pattern can have multiple 'pattern tokens' enclosed within ()
# One can have any number of pattern tokens in a pattern. 
# We have two possible operation between tokens - & and |
# Example sequence - 
# seq s0 {
#  (TOP.A[1:0] == 2'b00)
#  (TOP.inst1.inter[1:0] > 2'b10)
# }
#Given below is the AST for the above sequence. A SequenceList may have multiple sequences
#
#SequenceList(List(Sequences))
#  |
#  +-- Sequence(List(Pattern), name = "s0")
#        |
#        +-- Pattern (Variable, Comparison, Constant)
#        |     |
#        |     +-- Variable (name = TOP.A, msb = 1, lsb = 0)
#        |     +-- Comparison (operator = "==")      
#        |     +-- Const (width = 2, binaryValue = "00")     
#        |     |     
#        |          
#        |
#        +-- Pattern (Variable, Comparison, Constant)
#              |
#              +-- Variable (name = TOP.inst1.inter, msb = 1, lsb = 0)
#              +-- Comparison (operator = ">")
#              +-- Const (width = 2, binaryValue = "10")

#
# Refer the code for detailed analysis of the structures


#  ****  AST Structures for ASAP-SMU Programming Language **** #

# A Const is always a sized binary representation like 3'b010.
# For 3'b010, width = 3, binaryValue = 010
class Const:
    def __init__(self, width:int, binaryValue:str):
        self.width = width
        self.binaryValue = binaryValue

    def __repr__(self):
        return f'{self.width}\'b{self.binaryValue}'

# A variable is always a partselected var like A[1:0]
# It may also have hierarchy in name - e.g. TOP.inst1.sig[1:0]
# In that case, TOP.inst1.sig becomes name, msb = 1, lsb = 0        
class Variable:
    def __init__(self, name:str, msb:int, lsb:int):
        self.name = name
        self.msb  = msb
        self.lsb  = lsb

    def __repr__(self):
        return f'{self.name}[{self.msb}:{self.lsb}]'


# An operation can be >/</==
class Comparison:
    def __init__(self, operator: str):
        self.operator = operator

    def __repr__(self) -> str:
        return f'Comparison({self.operator})'


# A token is always an operation statement with LHS and RHS. e.g. A[1:0] == 2'b00 / A[1:0] > 2'b01 /  A[1:0] < 2'b11 
# Here lhs can be either a Variable/Token. rhs can be either a Const/Token
class Pattern:
    def __init__(self, lhs: Variable, opType: Comparison, rhs: Const):
        self.lhs = lhs
        self.opType = opType
        self.rhs = rhs

    def __repr__(self):
        return f'Pattern({self.lhs} {self.opType} {self.rhs})'



class Sequence:
    def __init__(self, patterns: List['Pattern'], name: str):
        self.patterns = patterns if patterns is not None else []
        self.name = name

    def addPatterns(self, pattern):
        self.patterns.append(pattern)

    def __repr__(self):
        return f'Sequence({self.name} {self.patterns})'
    

class SequenceList:
    def __init__(self, sequences:List['Sequence']):
        self.sequences = sequences if sequences is not None else []

    def addSequences(self, sequence):
        self.sequences.append(sequence)

    def __repr__(self):
        return f'SequenceList({self.sequences})'


class ASAPSmuLexer:
    # Token definitions
    tokens = (
        'SEQUENCE_START',  # '{' Marks the beginning of a sequence
        'SEQUENCE_END',    # '}' Marks the end of a sequence
        'PATTERN_START',   # '(' Marks the start of a pattern
        'PATTERN_END',     # ')' Marks the end of a pattern
        'VARIABLE',        # '<Starts with an small/cap alphabet>, <Followed by alpha numeric chars>, <have multiple '.'s, <Has part select>>'
        'COMPARISON',      # Either of </>/==
        'CONST',           # A binary number with size. e.g. 2'b00, 5'b10101 
    )

    # Token regex patterns
    t_SEQUENCE_START = r'[a-zA-Z_][a-zA-Z_0-9]*\s*{'
    t_SEQUENCE_END   = r'}'
    t_PATTERN_START  = r'\('
    t_PATTERN_END    = r'\)'
    t_VARIABLE       = r'[a-zA-Z_][a-zA-Z_0-9]*(?:\.[a-zA-Z_][a-zA-Z_0-9]*)*\[[0-9]+:[0-9]+\]'
    t_COMPARISON     = r'[><=]=?'
    t_CONST          = r'[0-9]+\'[bB][01]+'

    # Ignored characters
    t_ignore = ' \t\n'

    # Error handling - Raise an exception
    def t_error(self, t):
        raise Exception(f"Unexpected character '{t.value[0]}' at line {t.lineno}, position {t.lexpos}")

    # Build the lexer
    def build(self, **kwargs):
        self.lexer = lex.lex(module=self, **kwargs)

    def __init__(self, **kwargs):
        self.build(**kwargs)


class ASAPSmuParser:
    def __init__(self, asapSmuFile) -> None:
        self.asapSmuFile = asapSmuFile
        self.smuLexer = ASAPSmuLexer()
        with open(asapSmuFile, "r") as file:
            smuCode = file.read() 
            try:
                logging.info("Running lexical analysis on ASAP-SMU patch file - '%s'"%(self.asapSmuFile))
                self.smuLexer.lexer.input(smuCode)
            except Exception as e:
                logging.info(str(e))
                logging.info("Lexical analysis failed.")
                exit(1)
            logging.info("Lexical analysis successyfully completed.")
        self.sequenceList = SequenceList([])
        self.parse()
        logging.info("Generated AST is - \n %s"%(self.sequenceList))

    def extractVariableInfo(self, variable):
        # Define a regular expression pattern to match VAR_NAME, MSB, and LSB
        pattern = r'(?P<name>[a-zA-Z_][a-zA-Z_0-9]*(?:\.[a-zA-Z_][a-zA-Z_0-9]*)*)\[(?P<msb>\d+):(?P<lsb>\d+)\]'
        
        # Match the pattern in the input string
        match = re.match(pattern, variable)
        
        if match:
            # Extract matched groups
            name = match.group('name')
            msb  = int(match.group('msb'))
            lsb  = int(match.group('lsb'))
            
            return name, msb, lsb
        else:
            logging.info("Invalid variable string format - %s" %(variable))
            raise ValueError("Invalid variable string format")

    def extractConstInfo(self, const):
        # Define a regular expression pattern to match WIDTH and BINARY_VALUE
        pattern = r'(?P<width>\d+)\'b(?P<binary_value>[01]+)'
        
        # Match the pattern in the input string
        match = re.match(pattern, const)
        
        if match:
            # Extract matched groups
            width = int(match.group('width'))
            binaryValue = match.group('binary_value')
            
            return width, binaryValue
        else:
            logging.info("Invalid constant string format - %s" %(const))
            raise ValueError("Invalid constant string format")

    def parse(self):
        currentToken = self.smuLexer.lexer.token()
        logging.info("Parsing %s"%(self.asapSmuFile))
        while currentToken:
            try:
                if currentToken.type == "SEQUENCE_START":
                    seqName = currentToken.value.rstrip('{')
                    newSequence = Sequence(patterns = [],     \
                                           name     = seqName)
                    currentToken = self.smuLexer.lexer.token()
                    while currentToken.type != "SEQUENCE_END":
                        try:
                            if currentToken.type == "PATTERN_START":
                                varToken   = self.smuLexer.lexer.token()
                                compToken  = self.smuLexer.lexer.token()
                                constToken = self.smuLexer.lexer.token()
                                # Parsing the variable
                                try:
                                    if varToken.type == "VARIABLE":
                                        varName, msb, lsb  = self.extractVariableInfo(varToken.value)
                                        newVar = Variable(name = varName, \
                                                          msb  = msb,     \
                                                          lsb  = lsb)
                                    else:
                                        raise Exception("Syntax Error - Expected a VARIABLE token. Received token %s" % varToken.type)
                                except Exception as e:
                                    logging.info(str(e))
                                    logging.info("Parsing failed")
                                    exit(1)
                                # Parsing the comparison operation
                                try:
                                    if compToken.type == "COMPARISON":
                                        compType  = compToken.value
                                        newComp = Comparison(operator = compType)
                                    else:
                                        raise Exception("Syntax Error - Expected a COMPARISON token. Received token %s" % compToken.type)
                                except Exception as e:
                                    logging.info(str(e))
                                    logging.info("Parsing failed")
                                    exit(1)
                                # Parsing the Const value
                                try:
                                    if constToken.type == "CONST":
                                        width, binVal  = self.extractConstInfo(constToken.value)
                                        newConst = Const(width       = width, \
                                                         binaryValue = binVal)
                                    else:
                                        raise Exception("Syntax Error - Expected a CONST token. Received token %s" % constToken.type)
                                except Exception as e:
                                    logging.info(str(e))
                                    logging.info("Parsing failed")
                                    exit(1)
                                try:
                                    patternEndToken = self.smuLexer.lexer.token()
                                    if  patternEndToken.type == "PATTERN_END":
                                        newPattern = Pattern(lhs    = newVar,   \
                                                             opType = newComp,  \
                                                             rhs    = newConst)
                                        newSequence.addPatterns(newPattern)
                                    else:
                                        raise Exception("Syntax Error - Pattern should end with ')'. Received token %s" % patternEndToken.type)
                                except Exception as e:
                                    logging.info(str(e))
                                    logging.info("Parsing failed")
                                    exit(1)
                                currentToken = self.smuLexer.lexer.token()
                            else:
                                raise Exception("Syntax Error - Pattern should begin with '(' Received token %s" % currentToken.type)
                        except Exception as e:
                            logging.info(str(e))
                            logging.info("Parsing failed")
                            exit(1)

                    self.sequenceList.addSequences(newSequence)
                    currentToken = self.smuLexer.lexer.token()
                else:
                    raise Exception("Syntax Error - Sequence should start with '{{' Received token %s" % currentToken.type)
            except Exception as e:
                logging.info(str(e))
                logging.info("Parsing failed")
                exit(1)
        logging.info("Parsed %s successfully - AST generated"%(self.asapSmuFile))



if __name__ == '__main__':
    parser = ASAPSmuParser("patch.asap.smu")



