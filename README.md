# Software Synthesis Project- Loop Invariants Generation
This is the work of Omer Moreno and Dvir Biton.
We used various synthesis and verification techniques, 
and mainly used Z3 as a solver for those conjectures.
The conjectures are built from a grammar
given by the user. and are tested over the program
while randomly generating the program state. 

## Required Files
When starting the synthesizer,
the following files must be provided:
- Grammar file- a file which descirbes the grammar of the
generated invariants.
- Configuration file- a file which describes the type of each
variable in the program. This is needed because inference might
be impossible from the program itself.
- program file- a python file of the program to produce the invariants to.

## Supported Grammars
