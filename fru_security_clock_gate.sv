module fru_security_clock_gate (
    input    clk,
    input    gate_en,
    input    FruEn,
    output   gated_clk,
);
    assign gated_clk = clk & (~FruEn | (gate_en & FruEn));

endmodule