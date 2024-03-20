// Implementation of a full-fledged SEGMENT_SIZE X 1 PLA with input selection
// customization. Note that SEGMENT size should be at max limited to 4 for 
// better timing convergence. This should be reasonable if we can limit control
// selection based on 4 distinct observable patterns (triggers) at a time.

module fru_pla_unit #(
    parameter INPUT_SIZE     = 2,
    parameter SEGMENT_SIZE   = 2
) (
    input  [INPUT_SIZE-1:0]                               Inp,
    input  [SEGMENT_SIZE-1:0][$clog2(INPUT_SIZE)-1:0]     RegMux,
    input  [2**SEGMENT_SIZE-1:0]                          RegMintermORSelect,
    output                                                out
);

    logic [SEGMENT_SIZE-1:0]     MuxedInp;
    logic [2**SEGMENT_SIZE-1:0]  Minterms;

    // There are 3 stages in segmented PLA generation - 
    // 1. Signal Selection - Select SEGMENT_SIZE # of signals from INPUT_SIZE based on 
    //                       RegMux
    // 2. Minterm Generation - In this stage we generate all possible minterms using the.
    //                         selected signals. For a PLA of segment size 2, we will have 4 minterms
    // 3. Minterm ORing - At this stage we need to OR multiple minterms based on RegMintermORSelect
    // This logic enables us to generate a select logic based on any logical combination of
    // SEGMENT_SIZE # of trigger signals.

    // Input selector block
    always_comb begin
        for (int g_pla = 0; g_pla < SEGMENT_SIZE; g_pla++) begin
            MuxedInp[g_pla] = Inp[RegMux[g_pla]];
        end
    end

    // Minterm generator block
    always_comb begin 
        for (int g_pla = 0; g_pla < 2**SEGMENT_SIZE; g_pla++) begin 
            Minterms[g_pla] = 1'b1;
            for (int g_pla_in = 0; g_pla_in < SEGMENT_SIZE; g_pla_in++) begin
                if (g_pla & (1<<g_pla_in)) begin
                    Minterms[g_pla] &= MuxedInp[g_pla_in];
                end else begin
                    Minterms[g_pla] &= ~MuxedInp[g_pla_in];
                end
            end
        end
    end

    // Minterm selector block
    always_comb begin
        for (int g_pla = 0; g_pla < 2**SEGMENT_SIZE; g_pla++) begin
            out |= (Minterms[g_pla] & RegMintermORSelect);
        end
    end
endmodule

