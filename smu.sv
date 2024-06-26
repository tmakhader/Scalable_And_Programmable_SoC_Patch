module smu # (
    parameter  N                  =    2,             // Maximum # of cycles for observability
    parameter  K                  =    4,             // Maximum # of observable signal bits
    parameter  M                  =    6              // Maximum # of triggers (parallel SMU units)    
    parameter  DECRYPT_KEY        =    32'hDEAD_BEEF, // Decryption key for bit-stream
    parameter  SMU_SEGMENT_SIZE   =    64             // Describes the size of smu_unit. For instance
                                                      // hardware complexity-wise this deploys a 64
                                                      // bit comperator
) (
    // Clk and Rst
    input  logic             clk,                     // clk
    input  logic             rst,                     // rst
    input  logic [K-1:0]     p,                       // K-bit observable input set 
    input  logic             BitStreamSerialIn,       // Bit-Stream input
    input  logic             BitStreamValid,
    input  logic             cfg_clk,
    input  logic             GlobalSmuEn,             // Lets you enable/disable SMU.
                                                      // Note that this doesn't affect bitsream programming/decryption
                                                      // SMU should be enabled after getting BitstreamLoaded handshake

    // M-bit trigger output
    output logic [M-1:0]     trigger,
    output logic             BitstreamLoaded          // Handshake signal to indicate that bitstream has been 
                                                      // successfully programmed and decrypted.
);

    // Generated local params
    localparam SMU_NUM_SEGMENTS   = (K + SMU_SEGMENT_SIZE - 1)/SMU_SEGMENT_SIZE;  // # of segments
    localparam BITS_NUM_SEGMENTS  = $clog2(SMU_NUM_SEGMENTS);
    localparam CFG_SMU_UNIT_SIZE  = ( BITS_NUM_SEGMENTS )                         // RegInpSel
                                    ( 2*SMU_SEGMENT_SIZE ) +                      // RegCmp + RegCmpMask
                                    ( 1 )   +                                     // RegCmpSel
                                    ( $clog2(N) );                                // RegFsmCmp
    localparam REG_SEL_START      = REG_SEL_END        + BITS_NUM_SEGMENTS - 1;
    localparam REG_SEL_END        = REG_CMP_BEGIN      + 1;
    localparam REG_CMP_BEGIN      = REG_CMP_END        + SMU_NUM_SEGMENTS - 1;
    localparam REG_CMP_END        = REG_CMP_MASK_BEGIN + 1;
    localparam REG_CMP_MASK_BEGIN = REG_CMP_MASK_END   + SMU_NUM_SEGMENTS - 1;               
    localparam REG_CMP_MASK_END   = REG_CMP_SEL_BEGIN  + 1;
    localparam REG_FSM_CMP_BEGIN  = REG_FSM_CMP_END    + $clog2(N) - 1;
    localparam REG_FSM_CMP_END    = REG_CMP_SEL_BEGIN  + 1;
    localparam REG_CMP_SEL_BEGIN  = REG_CMP_SEL_END                          
    localparam REG_CMP_SEL_END    = 0


    // Configuration register per state for M X smu_unit 
    // This is muxed based on the SmuState of the corresponding smu_unit
    logic [M-1:0][CFG_SMU_UNIT_SIZE-1:0]            CfgRegSmuPerState;
    logic [M-1:0][$clog2(N)-1:0]                    SmuState;
    logic                                           SmuEn;
    logic                                           DecryptionDone;
    logic                                           SmuCfgDone, SmuCfgDoneUnsynced;

    // Primary configuration register array that is sequentially programmed during boot
    logic [N-1:0][M-1:0][CFG_SMU_UNIT_SIZE-1:0]     CfgRegSmu, CfgRegSmuEncrypted;
    genvar g_smu;


    // Each block here signify a distinct trigger pattern detection logic
    // in same or distinct host logic systems
    generate
        for (g_smu = 0; g_smu < M; g_smu++) begin
            smu_unit # (
                .N                   ( N ),
                .K                   ( K ),
                .SMU_SEGMENT_SIZE    ( SMU_SEGMENT_SIZE )
            
            )smu_unit_inst(
                // Clk, Rst, observable input set, SMU enable signal
                .clk            ( rst ),
                .rst            ( clk ),
                .i              ( p ) , 
                .SmuEn          ( SmuEn ),  // SMU is enabled once the CfgReg is programmed    

                // Configuration Registers -- Function of SmuState and genvar i
                .RegInpSel      ( CfgRegSmuPerState[g_smu][REG_SEL_START:REG_SEL_END] )
                .RegCmpMask     ( CfgRegSmuPerState[g_smu][REG_CMP_MASK_BEGIN:REG_CMP_MASK_END] ),
                .RegCmp         ( CfgRegSmuPerState[g_smu][REG_CMP_BEGIN:REG_CMP_END] ),
                .RegCmpSelect   ( CfgRegSmuPerState[g_smu][REG_CMP_SEL_BEGIN:REG_CMP_SEL_END]),
                .RegFsmCmp      ( CfgRegSmuPerState[g_smu][REG_FSM_CMP_BEGIN:REG_FSM_CMP_END]),
                .SmuState       ( SmuState[g_smu]),

                // Trigger and pattern match state
                .trigger        ( trigger[g_smu]),
                .SmuState       ( SmuState[g_smu] )
            );

            // Multiplexing smu_unit cfg
            assign CfgRegSmuPerState[g_smu] = CfgRegSmu[SmuState][g_smu];
        end
    endgenerate


    // Module to interface a sequential cfg bitstream
    bitstream_deserializer # (
        .CFG_SIZE            ( $bits(CfgRegSmu) )
    ) deserializer_inst (
        .clk                 ( cfg_clk ),
        .rst                 ( rst ),

        .SerialIn            ( BitStreamSerialIn ),
        .StreamValid         ( BitStreamValid ),
        .ParallelOut         ( CfgRegSmuEncrypted ),

        
        .CfgDone             (CfgDoneUnsynced)
    );

    assign 

    // Dual Flop - Sync logic to sync b/w d deserializer and 
    //             the SMU logic. Since, we know that the
    //             deserialized cfg is used only after CfgDone,
    //             syncing CfgDone should ensure appropriate
    //             Clock Domain Crossing (CDC) consistency 

    always_ff @(posedge clk) begin
        SmuCfgDone <= SmuCfgDoneUnsynced;
    end

    assign SmuEn =  GlobalSmuEn  & 
                    SmuCfgDone    &
                    DecryptionDone;
    
    assign BitstreamLoaded = SmuCfgDone &
                             DecryptionDone;

    // Module to decrypt the cfg bitstream
    cfg_decrypt #(
        .CFG_SIZE       ( $bits(CfgRegSmu) ),
        .DECRYPT_KEY    ( DECRYPT_KEY )
    ) smu_cfg_decrypt_smu_inst (
        .EncryptedCfg   ( CfgRegSmuEncrypted ),
        .DecryptedCfg   ( CfgRegSmu ),
        .DecryptionDone ( DecryptionDone ) 
    )
endmodule