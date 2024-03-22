module cfg_decrypt # (
    parameter CFG_SIZE      = 100,
    parameter DECRYPT_KEY   = 32'hDEAD_BEEF 
) (
    input  [CFG_SIZE-1: 0]     EncryptedCfg,
    output [CFG_SIZE-1: 0]     DecryptedCfg,
    output                     DecryptionDone
);
    assign DecryptedCfg   = EncryptedCfg ^ {$bits(DECRYPT_KEY){DECRYPT_KEY}}
    assign DecryptionDone = 1'b1;

endmodule