import re
import sys
import os

# VM Grammer
ACOMMAND = '(?P<ACOMMAND>add|sub|neg|eq|gt|lt|and|or|not)'

ACCESSTYPE = '(?P<ACCESSTYPE>push|pop)'
SEGMENT = '(?P<SEGMENT>local|argument|this|that|constant|static|temp|pointer)'
VALUE = '(?P<VALUE>[0-9]+)'
MCOMMAND = '(?P<MCOMMAND>' + ACCESSTYPE + SEGMENT + VALUE + ')'

COMMENT = '(?P<COMMENT>//.*$)'

CODE = '^(' + ACOMMAND + '|' + MCOMMAND + ')?' + COMMENT + '?$'
# End of grammer declaration

Parser = re.compile(CODE)
InputFileName = ''
InstructionNumber = 0

def writeLineInFile(outputFile, line):
  with open(outputFile, 'a') as output:
    output.write(line)

def writeCodeInFile(outputFile, line):
  global InstructionNumber

  writeLineInFile(outputFile, line + '\n')
  InstructionNumber += 1

def getSegmentRegister(segment):
  if segment == 'local':
    return 'LCL'
  elif segment == 'argument':
    return 'ARG'
  elif segment == 'this':
    return 'THIS'
  elif segment == 'that':
    return 'THAT'
  else:
    exit(1)
# end getSegmentRegister(...)

def compilePushInputAddress(matchDictionary, outputFile):
  segment = matchDictionary['SEGMENT']
  value = int(matchDictionary['VALUE'])

  if segment == 'constant':
    writeCodeInFile(outputFile, f"@{value}")
    writeCodeInFile(outputFile, "D=A")
    return
  elif segment == 'static':
    writeCodeInFile(outputFile, f"@{InputFileName}.{value}")
  elif segment == 'temp':
    writeCodeInFile(outputFile, f"@{5+value}")
  elif segment == 'pointer':
    writeCodeInFile(outputFile, f"@{'THIS' if value == 0 else 'THAT'}")
  else:
    segmentRegister = getSegmentRegister(segment)
    writeCodeInFile(outputFile, f"@{segmentRegister}")
    writeCodeInFile(outputFile, "D=M")
    writeCodeInFile(outputFile, f"@{value}")
    writeCodeInFile(outputFile, "D=D+A")
    writeCodeInFile(outputFile, "A=D")

  writeCodeInFile(outputFile, "D=M")
# end compilePushInputAddress(...)

def compilePushCommand(matchDictionary, outputFile):
  # Calculate segment memory address and load the value in that address into D
  compilePushInputAddress(matchDictionary, outputFile)
  # Push D onto stack
  writeCodeInFile(outputFile, "@SP")
  writeCodeInFile(outputFile, "A=M")
  writeCodeInFile(outputFile, "M=D")
  # Increment stack pointer
  writeCodeInFile(outputFile, "@SP")
  writeCodeInFile(outputFile, "M=M+1")
# end compilePushCommand(...)

def compilePopInputAddress(matchDictionary, outputFile):
  segment = matchDictionary['SEGMENT']
  value = int(matchDictionary['VALUE'])

  if segment == 'constant':
    # No pop command for 'constant' segment
    exit(1)
  elif segment == 'static' or segment == 'push' or segment == 'pointer' or segment == 'temp':
    # These segments don't require address calculation
    return

  segmentRegister = getSegmentRegister(segment)
  writeCodeInFile(outputFile, f"@{segmentRegister}")
  writeCodeInFile(outputFile, "D=M")
  writeCodeInFile(outputFile, f"@{value}")
  writeCodeInFile(outputFile, "D=D+A")
  writeCodeInFile(outputFile, "@R13")
  writeCodeInFile(outputFile, "M=D")
# def compilePopInputAddress(...)

def decrementSP():
  writeCodeInFile(outputFile, "@SP")
  writeCodeInFile(outputFile, "M=M-1")
  writeCodeInFile(outputFile, "A=M")
  writeCodeInFile(outputFile, "D=M")
# end decrementSP(...)

def compilePopOutput(matchDictionary, outputFile):
  segment = matchDictionary['SEGMENT']
  value = int(matchDictionary['VALUE'])

  if segment == 'constant':
    exit(1)
  elif segment == 'static':
    writeCodeInFile(outputFile, f"@{InputFileName}.{value}")
  elif segment == 'temp':
    writeCodeInFile(outputFile, f"@{5+value}")
  elif segment == 'pointer':
    writeCodeInFile(outputFile, f"@{'THIS' if value == 0 else 'THAT'}")
  else:
    writeCodeInFile(outputFile, "@R13")
    writeCodeInFile(outputFile, "A=M")

  writeCodeInFile(outputFile, "M=D")
# def compilePopOutput(...)

def compilePopCommand(matchDictionary, outputFile):
  # Calculate segment memory address and save it in R13
  compilePopInputAddress(matchDictionary, outputFile)
  # Load topmost number from stack into D and decrement SP
  decrementSP()
  # Save D into memory address
  compilePopOutput(matchDictionary, outputFile)
#end compilePopCommand(...)

def compileMCommand(matchDictionary, outputFile):
  if matchDictionary['ACCESSTYPE'] == 'push':
    compilePushCommand(matchDictionary, outputFile)
  elif matchDictionary['ACCESSTYPE'] == 'pop':
    compilePopCommand(matchDictionary, outputFile)
# end compileMCommand(...)

def getOperationFor(aCommand):
  if aCommand == 'neg' or aCommand == 'not':
    exit(1)

  if aCommand == 'add':
    return 'D=D+M'
  elif aCommand == 'or':
    return 'D=D|M'
  elif aCommand == 'and':
    return 'D=D&M'
  else:
    return 'D=D-M'
# end getOperationFor(...)

def compileACommand(aCommand, outputFile):
  if aCommand != 'neg' and aCommand != 'not':
    # Load topmost number from stack into D and decrement SP
    decrementSP()
    # Save D in R13, load the next number from stack into D
    writeCodeInFile(outputFile, "@R13")
    writeCodeInFile(outputFile, "M=D")
    writeCodeInFile(outputFile, "@SP")
    writeCodeInFile(outputFile, "A=M-1")
    writeCodeInFile(outputFile, "D=M")
    # Get value from R13 and do specified operation
    writeCodeInFile(outputFile, "@R13")
    writeCodeInFile(outputFile, getOperationFor(aCommand))

  if aCommand == 'eq' or aCommand == 'lt' or aCommand == 'gt':
    global InstructionNumber

    # Set D to True if condition satisfies, False otherwise
    writeCodeInFile(outputFile, f"@{InstructionNumber + 5}")
    writeCodeInFile(outputFile, "D;J" + aCommand.upper())
    writeCodeInFile(outputFile, "D=0")  # False
    writeCodeInFile(outputFile, f"@{InstructionNumber + 3}")
    writeCodeInFile(outputFile, "0;JMP")  # False
    writeCodeInFile(outputFile, "D=-1") # True

  writeCodeInFile(outputFile, "@SP")
  writeCodeInFile(outputFile, "A=M-1")

  if aCommand == 'neg':
    writeCodeInFile(outputFile, "M=-M")
  elif aCommand == 'not':
    writeCodeInFile(outputFile, "M=!M")
  else:
    writeCodeInFile(outputFile, "M=D")
# end compileACommand(...)

if __name__ == "__main__":
  InputFileName = os.path.basename(sys.argv[1])
  InputFileName = os.path.splitext(InputFileName)[0]
  outputFile = sys.argv[1].rsplit('.', 1)[0] + ".asm"
  with open(outputFile, 'w') as output:
    output.write("// Created by triploblastic\n")

  with open(sys.argv[1]) as inputFile:
    for line in inputFile:
      if line == '\n':
        continue
      match = Parser.match(line.replace(' ', ''))
      if match and not match.group('COMMENT'):
        writeLineInFile(outputFile, "// " + line)
        if match.group('MCOMMAND'):
          compileMCommand(match.groupdict(), outputFile)
        elif match.group('ACOMMAND'):
          compileACommand(match.group('ACOMMAND'), outputFile)
