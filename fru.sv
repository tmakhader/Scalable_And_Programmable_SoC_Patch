module fru #(
    parameter  M                  =    6,              // Maximum # of triggers (parallel SMU units) 
    parameter  F                  =    12              // Maximum # of FSM state machine bits under control
    parameter  C                  =    5,              // Maximum # of Clk signals under control
    parameter  S                  =    20,             // Maximum # of Non-FSM signal bits under control

    localparam CONTROL_WIDTH      =    (2*F) + C + S
) (
    // clk and reset signals
    input                        clk,
    input                        rst,

    // Controllable signal set
    input   [CONTROL_WIDTH-1:0]  q_in,                 // Controllable signal set input (In the order) -
                                                       // {FSM_STATE_INPUTS, FSM_STATE_OUTPUTS, CLKS, NON_FSM_SIGNALS}
    output  [CONTROL_WIDTH-1:0]  q_out,                // Controllable signal set output (In the order) -
                                                       // {FSM_STATE_INPUTS, FSM_STATE_OUTPUTS, CLKS, NON_FSM_SIGNALS}
    input  logic                 BitStreamSerialIn,    // Bit-Stream input
    input  logic                 BitStreamValid,       // Bit-stream valid
    input  logic                 cfg_clk               // cfg_clk
);
    localparam CFG_WIDTH           = CONTROL_WIDTH + (2*F) + S; // Size of cfg_reg

    localparam PART_FSM_IN_BEGIN    = REG_FSM_IN_END + F - 1;
    localparam PART_FSM_IN_END      = REG_FSM_OUT_BEGIN + 1;
    localparam PART_FSM_OUT_BEGIN   = REG_FSM_OUT_END + F - 1;
    localparam PART_FSM_OUT_END     = REG_CLK_BEGIN + 1;
    localparam PART_CLK_BEGIN       = REG_CLK_END + C - 1;
    localparam PART_CLK_END         = REG_SIGNAL_BEGIN + 1;
    localparam PART_SIGNAL_BEGIN    = REG_SIGNAL_END   + S - 1;
    localparam PART_SIGNAL_END      = 0 

    // CfgRegFru constitite the constants for signal filters and PLA cfg_registers
    // The signal ordering is {cfg_const_fsm_in,    --> Constants for FSM_IN signal filters
    //                         cfg_const_fsm_out,   --> Constants for FSM_OUT signal filters
    //                         cfg_const_signals    --> Constants for controllable signals' filters }

    logic [CFG_WIDTH-1:0]     CfgRegFru, CfgRegFruEncrypted;

    generate
            // Signal Filters for FSM_IN
        for (g_fsm = PART_FSM_IN_BEGIN; g_fsm < PART_FSM_IN_END; g_fsm++) begin
            fru_signal_filter_unit (
                .q_in           ( q_in[g_fsm] ),
                .BypassEn       (),
                .q_out          ( q_out[g_fsm])
            )
        end
    endgenerate


endmodule