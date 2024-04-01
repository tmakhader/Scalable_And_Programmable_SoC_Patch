module Sample(
    input wire A,  // #pragma observe 0:0
    input wire B, 
    output wire out, 
    output wire out2
);
    assign out = A&B; 
    assign out2 = A|B; 
endmodule
