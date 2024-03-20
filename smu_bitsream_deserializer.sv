module smu_bitstream_deserializer #(
    parameter CFG_SIZE = 100            // Number of bits to store
)(
    input  logic SerialIn,              // Single-bit input to stream data
    input  logic StreamValid            // Valid bit indicating input stream is valid
    input  logic clk,                   // Clock input
    input  logic rst,                   // Reset input
    output logic [N-1:0] ParallelOut,   // Output register to store N bits

    output logic CfgDone                // Signal to indicate that bit-stream has been completely loaded.
                                        // For correct programming, CongigDoneOut should always match is 
);

    logic [$clog2(N)-1:0] StreamBitCount;      // Register used to count valid bits in bitstream during cfg
    logic [$clog2(N)-1:0] StreamBitCountNext;  
    logic [N-1:0]         ParallelOutNext;

    // Deserialization logic
    always_comb @(posedge clk) begin
        if (rst) begin
            ParallelOutNext = 0; // Reset the register
        end else begin
            // If stream is valid: Shift the existing data to the left and store the new bit at the LSB
            ParallelOutNext =  StreamValid ? { ParallelOut[N-2:0], SerialIn } : ParallelOut;
        end
    end

    // Logic to count valid input bits during bitstream deserialization
    always_comb  begin
        if (rst) begin
            StreamBitCountNext = 1'b0;
        end
        else  begin
            StreamBitCountNext = StreamValid ? StreamBitCount + $bits(StreamBitCount)'(1'b1) : StreamBitCount;
        end
    end

    // Memory logic for BitStreamCount and ParallelBitstream output
    always_ff (@posedge clk) begin
        StreamBitCount <= StreamBitCountNext;
        ParallelOut    <= ParallelOutNext;
    end

    // CfgDone indicates that bitstream loading is complete
    assign CfgDone = (StreamBitCount == N);

endmodule
