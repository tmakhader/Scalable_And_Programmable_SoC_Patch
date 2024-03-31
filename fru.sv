// AR: FRU_UNIT segmentation

module fru #(
    parameter  M                  =    6,                // Maximum # of triggers (parallel SMU units) 
    parameter  F                  =    12                // Maximum # of FSM state machine bits under control
    parameter  C                  =    5,                // Maximum # of Clk signals under control
    parameter  S                  =    20,               // Maximum # of Non-FSM signal bits under control
    parameter  SEGMENT_SIZE       =    3,
    parameter  DECRYPT_KEY        =    32'hDEAD_BEEF,    // Decryption key for bit-stream

    localparam CONTROL_WIDTH      =    (2*F) + C + S     // Width of controllable signal set
) (
    // clk and reset signals
    input                        clk,
    input  logic                 cfg_clk,                    // cfg_clk
    input                        rst,
    input  logic                 BitStreamSerialIn,          // Bit-Stream input
    input  logic                 BitStreamValid,             // Bit-stream valid
    input  logic                 GlobalFruEn                 // Lets you enable/disable FRU
    // Controllable signal set
    input  logic [CONTROL_WIDTH-1:0]  Qin,                   // Controllable signal set input (In the order) -
                                                             // {FSM_STATE_INPUTS, FSM_STATE_OUTPUTS, CLKS, NON_FSM_SIGNALS}

    output logic [CONTROL_WIDTH-1:0]  QOut,                  // Controllable signal set output (In the order) -
                                                             // {FSM_STATE_INPUTS, FSM_STATE_OUTPUTS, CLKS, NON_FSM_SIGNALS}

    output logic                      BitstreamLoaded        // Handshake signal to indicate that bitstream has been 
                                                             // successfully programmed and decrypted.
);
    // CfgRegFru constitite the constants for signal filters and PLA cfg_registers
    // The signal ordering is:    {RegMux                    --> Signal selector for Segment PLAs 
    //                             RegMintermORSelect,       --> Minterm selector for Segment PLAs
    //                             RegConstFsmIn,            --> Constants for FSM_IN signal filters
    //                             RegConstFsmOut,           --> Constants for FSM_OUT signal filters
    //                             RegConstSignals}          --> Constants for controllable signals' filters 

    localparam REG_SIG_SEL_BEGIN    = REG_SIG_SEL_END + (CONTROL_WIDTH*$clog2(M)) - 1;                // (CONTROL_WIDTH*$clog2(M)) Bits
    localparam REG_SIG_SEL_END      = REG_MINTERM_BEGIN + 1; 
    localparam REG_MINTERM_BEGIN    = REG_MINTERM_END + (CONTROL_WIDTH*(2**SEGMENT_SIZE)) - 1;        // (CONTROL_WIDTH*(2**SEGMENT_SIZE)) Bits
    localparam REG_MINTERM_END      = REG_FSM_IN_BEGIN; 
    localparam REG_FSM_IN_BEGIN     = REG_FSM_IN_END + F - 1;                                         // F Bits
    localparam REG_FSM_IN_END       = REG_FSM_OUT_BEGIN + 1;
    localparam REG_FSM_OUT_BEGIN    = REG_FSM_OUT_END + F - 1;                                        // F Bits
    localparam REG_FSM_OUT_END      = REG_SIGNAL_BEGIN + 1;
    localparam REG_SIGNAL_BEGIN     = REG_SIGNAL_END   + S - 1;                                       // S Bits
    localparam REG_SIGNAL_END       = 0 

    localparam CFG_WIDTH            = (2*F) +                // FSM filter constants
                                       S    +                // Signal filter constants
                             (CONTROL_WIDTH*$clog2(M)) +     // PLA cfg_reg for signal selection
                        (CONTROL_WIDTH* (2**SEGMENT_SIZE));  // PLA cfg_reg for minterm selection

    // Qin/Qout constitute the controllable input/output set
    // The signal ordering is:   {FsmIn,                     --> Signal input bits to FSM state memory
    //                            FsmOut,                    --> Signal output bits from FSM state memory
    //                            NonFsmSignals,             --> Non-FSM signals under control horizon
    //                            ClkSignals}                --> Clk signals under control horizon

    localparam PART_CLK_BEGIN       = PART_CLK_END + C - 1;                                            // C Bits
    localparam PART_CLK_END         = PART_FSM_IN_BEGIN + 1;
    localparam PART_FSM_IN_BEGIN    = PART_FSM_IN_END + F - 1;                                         // F Bits
    localparam PART_FSM_IN_END      = PART_FSM_OUT_BEGIN + 1;
    localparam PART_FSM_OUT_BEGIN   = PART_FSM_OUT_END + F - 1;                                        // F Bits
    localparam PART_FSM_OUT_END     = PART_SIGNAL_BEGIN + 1;
    localparam PART_SIGNAL_BEGIN    = PART_SIGNAL_END   + S - 1;                                       // S Bits
    localparam PART_SIGNAL_END      = 0 

    logic [CFG_WIDTH-1:0]       CfgRegFru, CfgRegFruEncrypted;
    logic [CONTROL_WIDTH-1:0]   FruSelect;
    logic                       FruEn;

    // Segmented PLA instantiation
    fru_pla #(
        .INPUT_SIZE                 ( M ),
        .OUTPUT_SIZE                ( CONTROL_WIDTH ),
        .SEGMENT_SIZE               ( SEGMENT_SIZE )
    ) fru_pla_inst (
        .Qin                        (  Qin ),
        .RegMux                     ( CfgRegFru[PART_SIG_SEL_BEGIN:PART_SIG_SEL_END]),
        .RegMintermORSelect         ( CfgRegFru[PART_MINTERM_BEGIN:PART_MINTERM_END]),
        .FruSelect                  ( FruSelect )
    );

    // Signal filter instantiation for {FSM_IN, FSM_OUT, NON_FSM_SIGNALS}
    fru_signal_filter_unit #(
        .FILTER_SIZE   (2*F + S)
    ) fru_signal_filter_unit_inst (
        .Qin                        ( Qin[PART_FSM_IN_BEGIN:PART_SIGNAL_END] ),
        .BypassEn                   ( FruSelect[PART_FSM_IN_BEGIN:PART_SIGNAL_END] ),
        .RegConst                   ( CfgRegFru[REG_FSM_IN_BEGIN:REG_SIGNAL_END] ),
        .FruEn                      ( FruEn ),
        .Qout                       ( Qout[PART_FSM_IN_BEGIN:PART_SIGNAL_END] )
    );

    genvar g_fru;

    // Security clock gating logic instantiation
    generate
        for (g_fru = 0; g_fru < (PART_CLK_BEGIN-PART_CLK_END); g_fru++) begin
            fru_security_clock_gate fru_security_clock_gate_inst (
                .clk                ( clk ),
                .gate_en            ( CfgRegFru[g_fru + REG_CLK_END] ),
                .FruEn              ( FruEn )
                .gated_clk          ( Qout[g_fru + PART_CLK_END] )
            );
        end
    endgenerate

    // Bitstream deserializer
    bitstream_deserializer #(
        .CFG_SIZE           (CFG_WIDTH)
    ) fru_bitstream_deserializer_inst (
        .SerialIn           ( SerialIn ),
        .StreamValid        ( StreamValid ),
        .clk                ( clk_cfg ),
        .rst                ( rst ),
        .ParallelOut        ( CfgRegFruEncrypted ),
        .CfgDone            ( FruCfgDoneUnsynced )
    );

    assign FruEn  = GlobalFruEn   & 
                    FruCfgDone    &
                    DecryptionDone;

    assign BitstreamLoaded = FruCfgDone &
                             DecryptionDone;

    // Dual Flop - Sync logic to sync b/w d deserializer and 
    //             the SMU logic. Since, we know that the
    //             deserialized cfg is used only after CfgDone,
    //             syncing CfgDone should ensure appropriate
    //             Clock Domain Crossing (CDC) consistency 

    always_ff @(posedge clk) begin
        FruCfgDone <= FruCfgDoneUnsynced;
    end

    // Bitstream decryption
    cfg_decrypt #(
        .CFG_SIZE          ( CFG_WIDTH ),
        .DECRYPT_KEY       ( DECRYPT_KEY )
    ) fru_cfg_decrypt_inst (
        .EncryptedCfg      ( CfgRegFruEncrypted ),
        .DecryptedCfg      ( CfgRegFru ),
        .DecryptionDone    ( DecryptionDone )
    )
endmodule