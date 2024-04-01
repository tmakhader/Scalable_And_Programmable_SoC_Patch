module Sample(
    input wire A,    // #pragma observe 0:0 control fsm 0:0
    input wire B,    // #pragma observe 0:0
    output wire out, // #pragma control fsm 0:0
    output wire out2
);
    wire test_wire; // #pragma control signal 0:0
    assign out = A&B; 
    assign test_wire = ~out;
    assign out2 = test_wire|B; 
endmodule
