module And (
    input wire  [1:0] in_1, // #pragma observe 0:0 control signal 1:0
    input wire  [1:0] in_2, 
    output wire [1:0] out  
);

assign out = in_1 & in_2;
endmodule