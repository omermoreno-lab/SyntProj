# Software Synthesis Project- Loop Invariants Generation
This is the work of Omer Moreno and Dvir Biton.
We used various synthesis and verification techniques, 
and mainly used Z3 as a solver for those conjectures.
The conjectures are built from a grammar
given by the user. and are tested over the program
while randomly generating the program state. 

## Running test files
In order to run a test, run the following commmand
``` 
main.py <test_name> [tactic]
```
Currently valid tests are [harder_check, arith_check, int_list_check]
## Input Format
In order to make a test, one must supply five files:
| file name | Description |
| ----------- | ----------- |
| env.json | file describing the type of every variable in the grammar |
| grammar.txt | file describing the grammar from which the synth will generate the invriants |
| properties.json | file containing a list of all properties one would like to prove
| records.json | file containing recorded states of the program (can be generated using the synthesizer)
| test.py | the python file with the program

## Something Extra
We have done quite a few additions:
1. Optimizations in the Bottom Up algorithm: When we first implemented the bottom up enumeration
    algorithm in a naive way- it was extremely slow! When seeing that, we have thought of 
    a few ways to change the algorithm to work quickly:
    1. Token driven bottom up: This is a simple idea- instead of trying to merge all programs, 
        try to merge all programs of the same token.
        When doing this we also consider options that we have already tried to merge and failed,
        and we are not trying to merge them again.
    2. Grammar graph analysis: We have analyzed the grammar graph to achieve a few things:
        - Determining generation order: We used DFS to determine the desired generation
            order. This also handles loops in the graph, as can be seen using the grammar in "harder_check"
            test.
        - Generating examples of only expandable tokens: Let's look at a given grammar:
        ```
        VAR ::= INT | ID
        ID ::= x | y
        INT ::= 1, 2
        ```
        Notice that even though VAR, ID and INT are not ground tokens, they are not expandable.
        Meaning, trying to run grow and merge on them will give nothing. Using the analysis
        we are not taking these token into consideration. This is also true for production
        rules (we only try to expand those which are expandable)
        - Iteration based grow function instead of recursion based: Python is quicker
            and more memory efficient using list comprehension than recursion.
        - Custom number of grow iterations: Lets one expand a single token more than the rest
            of the graph. A reason to do this is when one token requires more expansion than
            the others. Graph Analysis allows one to know which other tokens (which the desired token
            is dependent on) also need to be expanded more. This is a currently not implemented feature.
            An example for this is when dealing with unbounded numbers. We can only generate numbers
            of a certain size given the examples beforehand. If we want to not limit this by grammar
            (for example, adding 1, 2, 3 and 4 to the previous numbers) then we can instead
            allow the user to define the depth of addition to the number without changing the grammar.
            An optimization to this is least-expensive generation, which takes the subgraph in which
            the expanded token is the root and contains only the nodes achievable by this node
            and not over its level, and finding the expression with the least expandable tokens
            (in the overall expansion, not only single level) and then expanding this rule only when
            using the "special iterations".
    3. Merge during grow: In the original algorithm, the grow and merge stages are different.
        We changed this to merge the token examples once finished growing the token. This means
        that given tokens T1 and T2, if T1 is dependent on T2, and we call grow on the graph.
        T1's new examples will be generated using T2's already merged new examples.
    4. Encoding-based merging: We know that a program generated from S (the root of the grammar tree)
        is necessarily a boolean (as this should be the invariant candidates). We used this 
        to allow the merge function to compare integer encodings of the evaluation of the programs
        rather than comparing the evaluations themselves. This reduces the number of 
        equality checks from O(states) to O(log(states)), and also avoids slow python functions.
        This was later changed by the guidance of Eytan to hash all results.
    
    [3] and [4] proved to be very effective to reduce runtime.

2. condition extraction:
   We have extracted the condition from the while loop, and added it to the
   invariants generated by the synthesizer using the or operator. This should
   allow the synthesizer to produce more correct invariants.
3. and operator between formulas:
   Our synth takes all formulas that passed the positive test cases and
   tries all possible combinations of them. They are then tested to make
   sure they passed the tests and if so, are treated as new invariants.
4. tautologies filtering:
   Given a tautology, the synthesizer will filter the result if it 
   is a tautology.
5. counter example synthesis: given a formula f and a safety property p,
   if f does not imply p then we add the counter example to the example file.

## Where have we failed (for now)
1. Due to the way __grow_merge works, we merge the formulas when growing
them. This means only one formula is being verified each iteration
of the algorithm, even though we synthesize other valid candidates.
This is more infuriating that we also don't stop the synthesis
when finding this single example, meaning that we let the computer 
do all the work while still not reaping the resutls.
The ways to fix this problem:
    - return invariant candidates before merge- will result
        in more work for the solver, but should work
    - multiple programs for the same evaluation result- will allow
        to not get stuck if we chose a "bad" program during merge.
        To not generate more programs than before, we can use 
        randomization to choose between the sub-programs during the
        program generation
2. Supporing weakest precondition analysis: Due to the conversion
    from the python expressions to z3 equivalent, which is not 
    necessarily possible



        