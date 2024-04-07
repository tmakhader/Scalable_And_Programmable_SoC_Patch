module Sample(
    input wire A,    // #pragma observe 0:0 control signal 0:0 
    input wire B,    // #pragma observe 0:0
    input wire clk,
    output wire out, // #pragma control signal 0:0
    output wire out2,// #pragma observe 0:0 control signal 0:0
    output reg  out3 // #pragma control signal 0:0
);
    wire test_wire; // #pragma control signal 0:0
    wire test_wire_2; // #pragma control signal 0:0
    assign out = A&B; 

    Or inst1 (.in(A),
             .out(test_wire));

    Or inst2 (.in(B),
             .out(test_wire_2));

    assign out2 = test_wire|B|out3|test_wire_2; 
    always @(posedge clk) begin
      out3 <= A;
    end
endmodule

module Or(
    input in,
    output out
);
    wire inter; // #pragma observe 0:0 control signal 0:0
    assign inter = ~in; 
    assign out = inter;
endmodule
