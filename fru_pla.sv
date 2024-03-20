// To reduce the hardware impact of the exponential # of select signals, we create a light-weight
// segmented PLA logic that create multiple instances of smaller PLAs. This restricts the max
// # of trigger signals that can be used at a time to generate a FRU select signal. 
//
// Let us assume that a select signal requires SEGMENT_SIZE # of triggers to make a control 
// decision. The segment PLA would be multiple copies of a SEGMENT_SIZE X 1 regular PLA
// To choose the inputs to segments we would have a INPUT_SIZE X SEGMENT_SIZE MUX that is 
// driven by a cfg_reg- RegMux. Depending on the size of FruSelect we would have OUTPUT_SIZE 
// copies of the logic. For optimal timing and resource overhead

module fru_pla #(
    parameter INPUT_SIZE     = 2,
    parameter OUTPUT_SIZE    = 4,
    parameter SEGMENT_SIZE   = 2
) (
    input  [INPUT_SIZE-1:0]                           Trigger,              // Trigger signal 
    input  [OUTPUT_SIZE-1:0][$clog2(INPUT_SIZE)-1:0]  RegMux,               // cfg_reg for configuring signal selection
    input  [OUTPUT_SIZE-1:0][2**SEGMENT_SIZE-1:0]     RegMintermORSelect,   // cfg_reg for selecting Minterms perform OR operation
    output [OUTPUT_SIZE-1:0]  FruSelect                                     // FRU select signal
)

    genvar g_pla;
    generate
        // Instantiate OUTPUT_SIZE # of SEGMENT_SIZE X 1 segmented PLU units
        always_comb begin
            for (g_pla = 0; g_pla < OUTPUT_SIZE; g_pla++) begin
                fru_pla_unit #(
                    .INPUT_SIZE           (INPUT_SIZE),
                    .SEGMENT_SIZE         (SEGMENT_SIZE)
                ) fru_pla_unit_inst (
                    .Inp                  (Trigger),
                    .RegMux               (RegMux[g_pla]),
                    .RegMintermORSelect   (RegMintermORSelect[g_pla]),
                    .out                  (FruSelect[g_pla])
                );
            end
        end
    endgenerate
endmodule