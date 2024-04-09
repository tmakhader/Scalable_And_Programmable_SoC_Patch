module Sample(
    input wire  [1:0] A,    // #pragma observe 0:0 control signal 1:0 
    input wire  [1:0] B,    // #pragma observe 0:0
    input wire        C,
    input wire        D,
    input wire        clk,
    output wire [1:0] out,  // #pragma control signal 1:0
    output wire [1:0] out2, // #pragma observe 0:0 control signal 1:0
    output reg  [1:0] out3  // #pragma control signal 0:0
);
    wire [1:0] test_wire; 
    wire [1:0] test_wire_2; // #pragma control signal 1:0
    wire [1:0] test_wire_3; // #pragma observe 1:0
    wire [1:0] test_wire_4;
    assign out = A & B; 

    Or inst1 (.in_1(A),
              .in_2(B),
              .out(test_wire));

    Or inst2 (.in_1(test_wire),
              .in_2(test_wire_2),
              .out(test_wire_3));

    And inst3 (.in_1(test_wire),
               .in_2(test_wire_3),
               .out(test_wire_4));

    assign test_wire_2 = test_wire | {C, D};
    assign out2 = test_wire_3 | test_wire_4; 

    always @(posedge clk) begin
      out3 <= test_wire_3;
    end
endmodule

module Or(
    input [1:0] in_1,
    input [1:0] in_2,
    output [1:0] out
);
    wire [1:0]inter;                    // #pragma observe 1:0 
    assign inter = ~in_1; 
    assign out   =  inter | in_2;
endmodule
