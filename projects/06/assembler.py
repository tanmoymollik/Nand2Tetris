import re
import sys

DEST_TABLE = {
        None    : '000',
        'M'     : '001',
        'D'     : '010',
        'MD'    : '011',
        'A'     : '100',
        'AM'    : '101',
        'AD'    : '110',
        'AMD'   : '111',
}

COMP_TABLE = {
        '0'     : '0101010',
        '1'     : '0111111',
        '-1'    : '0111010',
        'D'     : '0001100',
        'A'     : '0110000',
        'M'     : '1110000',
        '!D'    : '0001101',
        '!A'    : '0110001',
        '!M'    : '1110001',
        '-D'    : '0001111',
        '-A'    : '0110011',
        '-M'    : '1110011',
        'D+1'   : '0011111',
        'A+1'   : '0110111',
        'M+1'   : '1110111',
        'D-1'   : '0001110',
        'A-1'   : '0110010',
        'M-1'   : '1110010',
        'D+A'   : '0000010',
        'D+M'   : '1000010',
        'D-A'   : '0010011',
        'D-M'   : '1010011',
        'A-D'   : '0000111',
        'M-D'   : '1000111',
        'D&A'   : '0000000',
        'D&M'   : '1000000',
        'D|A'   : '0010101',
        'D|M'   : '1010101'
}

JUMP_TABLE = {
        None    : '000',
        'JGT'   : '001',
        'JEQ'   : '010',
        'JGE'   : '011',
        'JLT'   : '100',
        'JNE'   : '101',
        'JLE'   : '110',
        'JMP'   : '111',
}

REGISTER_TABLE = {
        'R0'    : 0,
        'R1'    : 1,
        'R2'    : 2,
        'R3'    : 3,
        'R4'    : 4,
        'R5'    : 5,
        'R6'    : 6,
        'R7'    : 7,
        'R8'    : 8,
        'R9'    : 9,
        'R10'   : 10,
        'R11'   : 11,
        'R12'   : 12,
        'R13'   : 13,
        'R14'   : 14,
        'R15'   : 15,
        'SP'    : 0,
        'LCL'   : 1,
        'ARG'   : 2,
        'THIS'  : 3,
        'THAT'  : 4,
        'KBD'   : 24576,
        'SCREEN': 16384
}

# Hack assembly language grammer
def processCOMPTable():
  comp = ' '.join(COMP_TABLE.keys())
  comp = comp.replace('+', '\+')
  comp = comp.replace('|', '\|')
  comp = comp.replace(' ', '|')
  return comp

CHARACTER = '[a-zA-Z_$.:]'
CHARACTER_OR_DIGIT = '[0-9a-zA-Z_$.:]'
NUMBER = '(?P<NUMBER>[0-9]+)'
IDENTIFIER = CHARACTER + CHARACTER_OR_DIGIT + '*'

AINSTRUCTION = '@' + '(?P<AINSTRUCTION>' + NUMBER + '|(?P<IDENTIFIER>' + IDENTIFIER + '))'

DEST = '(?P<DEST>(' + '|'.join(list(DEST_TABLE.keys())[1:]) + ')(?==))'
COMP = '(?P<COMP>' + processCOMPTable() + ')'
JUMP = '(;(?P<JUMP>' + '|'.join(list(JUMP_TABLE.keys())[1:]) + '))'
CINSTRUCTION = '(?P<CINSTRUCTION>' + DEST + '?=?' + COMP + JUMP + '?)'

INSTRUCTION = '(?P<INSTRUCTION>' + AINSTRUCTION + '|' + CINSTRUCTION + ')'

LABEL = '\((?P<LABEL>' + IDENTIFIER + ')\)'
COMMENT = '(?P<COMMENT>//.*$)'

CODE = '^(' + INSTRUCTION + '|' + LABEL + ')?' + COMMENT + '?$'
# End of grammer declaration

parser = re.compile(CODE)
NEXT_VARIABLE_ADDRESS = 16

def getLabelTable(inputFileName):
  labelTable = {}
  instructionNumber = 0
  with open(inputFileName) as inputFile:
    for line in inputFile:
      match = parser.match(line.replace(' ', ''))
      if match:
        if match.group('LABEL'):
          addLabel(labelTable, match.group('LABEL'), instructionNumber)
        elif match.group('INSTRUCTION'):
          instructionNumber += 1
  
  return labelTable

def addLabel(labelTable, label, instructionNumber):
  if label not in labelTable:
    labelTable[label] = instructionNumber

def getAssemblyCode(labelTable, variableTable, matchDictionary):
  if matchDictionary['AINSTRUCTION']:
    value = int(matchDictionary['NUMBER']) if matchDictionary['NUMBER'] else translateIdentifier(labelTable, variableTable, matchDictionary['IDENTIFIER'])
    return '0' + f'{value:015b}'
  elif matchDictionary['CINSTRUCTION']:
    dest = DEST_TABLE[matchDictionary['DEST']]
    comp = COMP_TABLE[matchDictionary['COMP']]
    jump = JUMP_TABLE[matchDictionary['JUMP']]
    return '111' + comp + dest + jump

# Translates the identifier into memory address.
# Adds to the variableTable if this is the first occurance
def translateIdentifier(labelTable, variableTable, identifier):
  global NEXT_VARIABLE_ADDRESS

  if identifier in labelTable:
    return labelTable[identifier]
  elif identifier in REGISTER_TABLE:
    return REGISTER_TABLE[identifier]
  elif identifier in variableTable:
    return variableTable[identifier]

  variableTable[identifier] = NEXT_VARIABLE_ADDRESS
  NEXT_VARIABLE_ADDRESS += 1
  return variableTable[identifier]

if __name__ == "__main__":
  labelTable = getLabelTable(sys.argv[1])
  variableTable = {}

  with open(sys.argv[1]) as inputFile, open(sys.argv[2], 'w') as outputFile:
    for line in inputFile:
      match = parser.match(line.replace(' ', ''))
      if match and match.group('INSTRUCTION'):
        code = getAssemblyCode(labelTable, variableTable, match.groupdict())
        outputFile.write(code + '\n')
