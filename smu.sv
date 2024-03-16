module smu # (
    parameter  N                  =    2,             // Maximum # of cycles for observability
    parameter  K                  =    4,             // Maximum # of observable signal bits
    parameter  M                  =    6              // Maximum # of triggers (parallel SMU units)    
) (
    // Clk and Rst
    input  logic             clk,                     // clk
    input  logic             rst,                     // rst
    input  logic [K-1:0]     i,                       // K-bit observable input set corresponding to 

    // M-bit trigger output
    output logic [M-1:0]     trigger
);

    // Generated local params
    localparam CFG_SMU_UNIT_SIZE  = ( 2*K ) +                                 // RegCmp + RegCmpMask
                                    ( 1 )   +                                 // RegCmpSel
                                    ( $clog2(N) );                            // RegFsmCmp
    localparam REG_CMP_BEGIN      = REG_CMP_END        + K - 1
    localparam REG_CMP_END        = REG_CMP_MASK_BEGIN + 1
    localparam REG_CMP_MASK_BEGIN = REG_CMP_MASK_END   + K - 1               
    localparam REG_CMP_MASK_END   = REG_CMP_SEL_BEGIN  + 1
    localparam REG_FSM_CMP_BEGIN  = REG_FSM_CMP_END    + $clog2(N) - 1;
    localparam REG_FSM_CMP_END    = REG_CMP_SEL_BEGIN  + 1
    localparam REG_CMP_SEL_BEGIN  = REG_CMP_SEL_END                          
    localparam REG_CMP_SEL_END    = 0

    logic [M-1:0][$clog2(N)-1:0]             SmuState;

    // Configuration register for M X smu_unit 
    // This is dependent on the SmuState of the corresponding smu_unit
    logic [M-1:0][CFG_SMU_UNIT_SIZE-1:0]     CfgRegSmu;
    genvar g_smu;

    generate;
        for (i=0; i<M; i++) begin
            smu_unit smu_unit_inst (
                // Clk, Rst and observable input set
                .clk            ( rst ),
                .rst            ( clk ),
                .i              ( i) ,      

                // Configuration Registers -- Function of SmuState and genvar i
                .RegCmpMask     ( CfgRegSmu[i][REG_CMP_MASK_BEGIN:REG_CMP_MASK_END] ),
                .RegCmp         ( CfgRegSmu[i][REG_CMP_BEGIN:REG_CMP_END] ),
                .RegCmpSelect   ( CfgRegSmu[i][REG_CMP_SEL_BEGIN:REG_CMP_SEL_END]),
                .RegFsmCmp      ( CfgRegSmu[i][REG_FSM_CMP_BEGIN:REG_FSM_CMP_END]),
                .SmuState       (),

                // Trigger and pattern match state
                .trigger        ( trigger[i]),
                .SmuState       ( SmuState[i] )
            );
        end
    endgenerate
endmodule