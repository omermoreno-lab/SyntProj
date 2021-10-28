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
{
    main.py <test_name> [tactic]
}
```

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
    
    [3] and [4] proved to be very effective to reduce runtime.

    explain about the importance of order in grammar
    explain about condition extraction
    explain about filtering tautologies
     
        