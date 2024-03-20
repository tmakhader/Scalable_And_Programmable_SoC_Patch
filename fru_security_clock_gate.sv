module fru_security_clock_gate (
    input    clk,
    input    gate_en
    output   gated_clk,
);
    assign gated_clk = clk & gate_en;
     
endmodule