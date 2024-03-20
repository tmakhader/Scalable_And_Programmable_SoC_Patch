// To reduce the hardware impact of the exponential # of select signals, we create a light-weight
// segmented PLA logic that create multiple instances of smaller PLA. This requires a restricted 
// configuration that requires trigger signal vs select signal ordering the design is as follows-

// Let us assume that a select signal requires SEGMENT_SIZE # of triggers to make a control 
// decision. The segment PLA would be a SEGMENT_SIZE X 1 regular PLA

module fru_pla #(
    parameter INPUT_SIZE     = 2,
    parameter OUTPUT_SIZE    = 4
) (
    input  [INPUT_SIZE-1:0]   Trigger,
    output [OUTPUT_SIZE-1:0]  FruSelect
)
    logic [INPUT_SIZE-1:0]    TriggerN;

    // There are 4 stages in PLA - 
    // 1. Signal Buffering/Inverting - In this stage we have buffered/inverted copies of all signals
    // 2. Minterm Generation - In this stage we generate several minterms using signals 
    //                         Two decisions - a. Max # of signals/triggers one would need to combine
    //                                         b. Set of signals from which we need to select
    // 3. Minterm ORing - At this stage we need to OR multiple minterms to generate the select signal
    // 4. Replication of 2, 3 for every select signal
    // In normal scenarios - Generating all possible minters has a complexity - pow(2, N), where N is
    // the set of all signals
   
    genvar g_pla;
    generate

        // Negated Signal generator
        always_comb begin
            for (g_pla = 0; g_pla < INPUT_SIZE; g_pla++) begin
                TriggerN[g_pla] = ~Trigger[g_pla];
            end
        end


    endgenerate