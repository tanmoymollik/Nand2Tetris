// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Fill.asm

// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed. 
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.

// Put your code here.

// State of the screen is kept in R0
// R0 = -1 means black screen
// R1 = 0 means white screen
@R0
M = 0           // Initially screen is white

(PROMPT)
  @KBD
  D = M         // Load Keyboard
  @KEY_PRESSED
  D; JGT        // if KBD > 0 goto KEY_PRESSED
  // KEY_NOT_PRESSED
  @R0
  D = M
  @PROMPT
  D; JEQ        // if R0 == 0 goto PROMPT
  @R0
  M = 0
  @FLIP_SCREEN
  0; JMP        // Flip the screen state
  

(KEY_PRESSED)
  @R0
  D = M
  @PROMPT
  D; JLT        // if R0 < 0 goto PROMPT
  @R0
  M = -1
  @FLIP_SCREEN
  0; JMP        // Flip the screen state

(FLIP_SCREEN)
  @i
  M = 0         // i = 0

(LOOP)
  // SCREEN has 256 rows and each row takes 32 registers.
  // So the whole screen consists of 8192 registers.
  @i
  D = M
  @8192
  D = D - A     // D = i - 8192
  @PROMPT
  D; JEQ        // if i - 8192 == 0 goto PROMPT

  @i
  D = M 
  @SCREEN
  D = A + D 
  @screen_i
  M = D
  @i
  M = M + 1     // i = i + 1
  
  @R0
  D = M
  @SET_BLACK
  D; JLT        // if R0 < 0 goto SET_BLACK

  // (SET_WHITE)
    @screen_i
    A = M
    M = 0       // SCREEN[i] = 0
    @LOOP
    0; JMP      // goto LOOP

  (SET_BLACK)
    @screen_i
    A = M
    M = -1      // SCREEN[i] = -1
    @LOOP
    0; JMP      // goto LOOP
