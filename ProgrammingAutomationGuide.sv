/************************* SMU/FRU Programming Automation Guide **********************************
Relevant Parameters of Patch Package
<---SMU---->
N                  --> Maximum # of cycles for observability
K                  --> Maximum # of observable signal bits
M                  --> Maximum # of triggers (parallel SMU units)   
SMU_SEGMENT_SIZE   --> Maximum # of signal bits required for generating a trigger 
<---FRU---->
F                  --> Maximum # of FSM state machine bits under control
C                  --> Maximum # of Clk signals under control
S                  --> Maximum # of Non-FSM signal bits under control
FRU_SEGMENT_SIZE   --> Maximum # of triggers required for a single control decision 

Relevant interface I/O
<---SMU---->
p             --> Observable signal set (K bits)
Qin           --> Controllable input (2F + C + S)
Qout          --> Controlled output (2F + C + S)

The above parameters needd to be fixed. 
For SMU, every single sequential signal patterns that are observed becomes a trigger
Lets say the multi-bit signals under observation are {A, B, C, D, E, F}

Given M = lets say, 6, we can observe upto 6 patters in any combination of the signals
We can specify a sample of pattern as follows
{
    (A[3:4] == const1)
    (B[1:2] > const2 | B[1:2] < const2)
    (C[0] == const3 & D[1] == const4 ) 
}

Note that the second pattern in the sequence uses a logical operation.
If there is a pattern with a logical operation, it will be treated as 
two distinct triggers unless three conditions are satisfied
 -- They use the same comparison operation
 -- Observable input bits included in the same segment of SMU 
 -- Operation is an AND operation

 Multiple logical operations are permitted in a pattern. The operations
 within a sequence that follow the above rules are first merged, and the 
 rest are seperated into distinct triggers
 For instance, The sequence above has a binary operation in two of the
 patterns in sequence. Assuming C, D falls within the same segment,
 they are merged into a single operation.

{
    (A[3:4] == const1)
    (B[1:2] > const2 & B[1:2] < const2)
    ({C[0],D[1]} == const4' ) 
}

Now the unseperable operations are seperated into distinct triggers as
follows:

{
    (A[3:4] == const1)
    (B[1:2] > const2 )
    ({C[0],D[1]} == const4' ) 
} --> t0

{
    (A[3:4] == const1)
    (B[1:2] < const2)
    ({C[0],D[1]} == const4' ) 
} --> t1



These triggers feeds in to the FRU-PLA to generate a logic 
sel = t0 | t1

Now responses are always single line (as the FRU logic is
combinational). Any sequential requirements must be mapped to
a sequence pattern that can be interpreted by an SMU.

If there are multiple monitoring patterns, they always get 
seperated into seperate triggers. 

Automation guide.
For each pattern in the sequence, operations within "()" will be
first delimited. The compiler should initally be aware of signal
to segment mapping. Following this operating merging takes place. 

**************************************************************************************************/