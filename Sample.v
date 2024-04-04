module Sample(
    input wire A,    
    input wire B,    // #pragma observe 0:0
    input wire clk,
    output wire out, // #pragma control signal 0:0
    output wire out2,// #pragma observe 0:0 control signal 0:0
    output reg  out3 // #pragma control signal 0:0
);
    wire test_wire; // #pragma control signal 0:0
    assign out = A&B; 
    assign test_wire = ~out;
    assign out2 = test_wire|B|out3; 
    always @(posedge clk) begin
      out3 <= A;
    end
    
endmodule
