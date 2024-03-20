module smu_cfg_decrypt # (
    parameter CFG_SIZE      = 100,
    parameter DECRYPT_KEY   = 32'hDEAD_BEEF 
) (
    input  [CFG_SIZE-1: 0]     EncryptedCfg,
    output [CFG_SIZE-1: 0]     DecryptedCfg,
);
    assign DecryptedCfg = EncryptedCfg ^ {$bits(DECRYPT_KEY){DECRYPT_KEY}}

endmodule