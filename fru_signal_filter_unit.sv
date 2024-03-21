// The Signal Filter Unit is a simple MUX that selects between input signal and a constant
module fru_signal_filter_unit #(
    parameter       FILTER_SIZE = 10
) (
    input  logic [FILTER_SIZE-1:0]    Qin,          // Controllable input signal
    input  logic [FILTER_SIZE-1:0]    BypassEn,     // Select signal
    input  logic [FILTER_SIZE-1:0]    RegConst,     // Constant value

    output logic [FILTER_SIZE-1:0]    Qout          // Filtered output
);

    genvar g_sfu;
    always_comb begin
        for (g_sfu = 0; g_sfu < FILTER_SIZE)
            Qout[g_sfu] = ( BypassEn[g_sfu] & RegConst[g_sfu] ) | 
                            (~BypassEn[g_sfu] & Qin[g_sfu] );
    end
endmodule