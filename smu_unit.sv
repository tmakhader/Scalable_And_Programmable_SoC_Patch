module smu_unit # (
    parameter  N                  =    2,   // Maximum # of cycles for observability
    parameter  K                  =    4    // Maximum # of observable signal bits
    parameter  SMU_SEGMENT_SIZE   =    64,
    localparam SMU_NUM_SEGMENTS   =    ((K + SMU_SEGMENT_SIZE - 1)/SMU_SEGMENT_SIZE),
    localparam BITS_NUM_SEGMENTS  =    $clog2(NUM_SEGMENTS)
) (
    // Clock, Reset signals
    input  logic                               clk,
    input  logic                               rst,

    // Observable input set and registers
    input  logic [K-1:0]                  i,                 // Observable signal input
    input  logic [BITS_NUM_SEGMENTS-1:0]  RegInpSel,         // Register to select relevant segment
    input  logic [K-1:0]                  RegCmpMask,        // Comparator Mask Register
    input  logic [K-1:0]                  RegCmp             // Register used for comparison
    input  logic                          RegCmpSelect,      // Register used to select type of comparison
    input  logic [$clog2(N)-1:0]          RegFsmCmp,         // Register used for FSM state comparison 
    input  logic 
    input  logic                          SmuEn              // Signal used to enable SMU -
                                                           // SMU should only be enabled when cfg bitstream is 
                                                           // fully loaded.

    // Trigger signal
    output logic [$clog2(N)-1:0]          SmuState,          // # of patterns matched
    output logic                          trigger            // Output trigger signal
);

    logic [K-1:0]            MaskedCmpInp;
    logic                    CmpEq;   
    logic                    CmpGt;
    logic                    CmpLt;
    logic                    CmpSel;
    logic [$clog2(N)-1:0]    SmuStateNext; 
    logic                    StateMatch;

    logic [SMU_SEGMENT_SIZE-1:0]                       p;
    logic [SMU_NUM_SEGMENTS-1:0][SMU_SEGMENT_SIZE-1:0] SegmentedI;

    // Logic to select relevant segment of observable input set.
    always_comb begin
        SegmentedI = {$bits(SegmentedI)i};
        p          = SegmentedI[RegInpSel];
    end

    // Logic to mask the input for comparison
    assign MaskedCmpInp      = (p & RegCmpMask);

    // Comparator logic
    assign CmpEq = MaskedCmpInp == RegCmp;   // Compare if i == Reg
    assign CmpGt = MaskedCmpInp >  RegCmp;   // Compare if i > Reg
    assign CmpLt = MaskedCmpInp <  RegCmp;   // Compare if i < Reg

    // Cmp Select
    always_comb begin : SelectCompareType
        if (reset) begin
            CmpSel <= 1'b0;
        end else begin
            unique case (RegCmpSelect)
                2'b00,
                1'b11  : CmpSel <= CmpEq;       // Both 00 and 11 selects == op
                2'b01  : CmpSel <= CmpLt;       // 01 selects < op
                2'b10  : CmpSel <= CmpGt;       // 10 selects > op
            endcase
        end
    end

    // Check for pattern  match
    assign StateMatch = ~|(SmuState ^ RegFsmCmp);

    // Check for a multi-cycle pattern match (Given SMU is enabled)
    assign trigger = SmuEn ? (StateMatch & CmpSel) : 1'b0;

    // SMU FSM Datapath - Update FSM when a Cmp match is found and we are not yet at the target pattern match state
    assign SMUNextstate = (CmpSel & ~StateMatch)  ?  (SmuState + ($bits(SmuState))'d1) : '0;

    // SMU FSM FF
    always_ff @(posedge gated_clk) begin
        SmuState <= SmuStateNext;
    end

    // Clock Gating logic - Used to enable/disable SMU
    always_comb begin
        gated_clk = clk & SmuEn;
    end
endmodule

