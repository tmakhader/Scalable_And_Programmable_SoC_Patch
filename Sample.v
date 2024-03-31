module Sample(input wire A, input wire B, output wire out, output wire out2);
    assign out = A&B; 
    assign out2 = A|B; 
endmodule
