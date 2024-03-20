module fru #(
    parameter  M                  =    6,                // Maximum # of triggers (parallel SMU units) 
    parameter  F                  =    12                // Maximum # of FSM state machine bits under control
    parameter  C                  =    5,                // Maximum # of Clk signals under control
    parameter  S                  =    20,               // Maximum # of Non-FSM signal bits under control
    parameter  SEGMENT_SIZE       =    3,

    localparam CONTROL_WIDTH      =    (2*F) + C + S     // Width of controllable signal set
) (
    // clk and reset signals
    input                        clk,
    input                        rst,

    // Controllable signal set
    input   [CONTROL_WIDTH-1:0]  QIn,                        // Controllable signal set input (In the order) -
                                                             // {FSM_STATE_INPUTS, FSM_STATE_OUTPUTS, CLKS, NON_FSM_SIGNALS}
    output  [CONTROL_WIDTH-1:0]  QOut,                       // Controllable signal set output (In the order) -
                                                             // {FSM_STATE_INPUTS, FSM_STATE_OUTPUTS, CLKS, NON_FSM_SIGNALS}
    input  logic                 BitStreamSerialIn,          // Bit-Stream input
    input  logic                 BitStreamValid,             // Bit-stream valid
    input  logic                 cfg_clk                     // cfg_clk
);
    // CfgRegFru constitite the constants for signal filters and PLA cfg_registers
    // The cfg signal ordering is {RegConstFsmIn,            --> Constants for FSM_IN signal filters
    //                             RegConstFsmOut,           --> Constants for FSM_OUT signal filters
    //                             RegConstSignals,          --> Constants for controllable signals' filters 
    //                             RegMux,                   --> Signal selector for Segment PLAs 
    //                             RegMintermORSelect}       --> Minterm selector for Segment PLAs


    localparam CFG_WIDTH            = (2*F) +                // FSM filter constants
                                       S    +                // Signal filter constants
                             (CONTROL_WIDTH*$clog2(M)) +     // PLA cfg_reg for signal selection
                        (CONTROL_WIDTH* (2**SEGMENT_SIZE));  // PLA cfg_reg for minterm selection

    localparam PART_FSM_IN_BEGIN    = REG_FSM_IN_END + F - 1;
    localparam PART_FSM_IN_END      = REG_FSM_OUT_BEGIN + 1;
    localparam PART_FSM_OUT_BEGIN   = REG_FSM_OUT_END + F - 1;
    localparam PART_FSM_OUT_END     = REG_CLK_BEGIN + 1;
    localparam PART_CLK_BEGIN       = REG_CLK_END + C - 1;
    localparam PART_CLK_END         = REG_SIGNAL_BEGIN + 1;
    localparam PART_SIGNAL_BEGIN    = REG_SIGNAL_END   + S - 1;
    localparam PART_SIGNAL_END      = 0 

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