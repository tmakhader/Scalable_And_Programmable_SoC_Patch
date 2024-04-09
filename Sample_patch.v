

module Sample
(
  input wire [1:0] A,
  input wire [1:0] B,
  input wire C,
  input wire D,
  input wire clk,
  output wire [1:0] out,
  output wire [1:0] out2,
  output wire [1:0] out3,
  output [9:0] observe_port,
  output [10:0] control_port_in,
  input [10:0] control_port_out
);

  wire [1:0] control_port_out_inst;
  wire [1:0] control_port_in_inst;
  wire [4:0] observe_port_inst;
  wire [4:0] observe_port_int;
  wire [8:0] control_port_in_int;
  wire [8:0] control_port_out_int;
  reg [1:0] out3_controlled;
  wire [1:0] out2_controlled;
  wire [1:0] out_controlled;
  wire [1:0] A_controlled;
  wire [1:0] test_wire;
  wire [1:0] test_wire_2_controlled;
  wire [1:0] test_wire_2;
  wire [1:0] test_wire_3;
  wire [1:0] test_wire_4;
  assign out_controlled = A_controlled & B;

  Or
  inst1
  (
    .in_1(A_controlled),
    .in_2(B),
    .out(test_wire),
    .observe_port(observe_port_inst[1:0])
  );


  Or
  inst2
  (
    .in_1(test_wire),
    .in_2(test_wire_2_controlled),
    .out(test_wire_3),
    .observe_port(observe_port_inst[3:2])
  );


  And
  inst3
  (
    .in_1(test_wire),
    .in_2(test_wire_3),
    .out(test_wire_4),
    .observe_port(observe_port_inst[4:4]),
    .control_port_in(control_port_in_inst[1:0]),
    .control_port_out(control_port_out_inst[1:0])
  );

  assign test_wire_2_controlled = test_wire | { C, D };
  assign out2_controlled = test_wire_3 | test_wire_4;

  always @(posedge clk) begin
    out3_controlled <= test_wire_3;
  end

  assign control_port_in_int[1:0] = A[1:0];
  assign control_port_in_int[3:2] = out_controlled[1:0];
  assign control_port_in_int[5:4] = out2_controlled[1:0];
  assign control_port_in_int[6:6] = out3_controlled[0:0];
  assign control_port_in_int[8:7] = test_wire_2_controlled[1:0];
  assign A_controlled[1:0] = control_port_out_int[1:0];
  assign out[1:0] = control_port_out_int[3:2];
  assign out2[1:0] = control_port_out_int[5:4];
  assign out3[0:0] = control_port_out_int[6:6];
  assign test_wire_2[1:0] = control_port_out_int[8:7];
  assign observe_port_int[0:0] = A[0:0];
  assign observe_port_int[1:1] = B[0:0];
  assign observe_port_int[2:2] = out2_controlled[0:0];
  assign observe_port_int[4:3] = test_wire_3[1:0];
  assign observe_port = { observe_port_int, observe_port_inst };
  assign control_port_in = { control_port_in_int, control_port_in_inst };
  assign { control_port_out_int, control_port_out_inst } = control_port_out;

endmodule



module Or
(
  input [1:0] in_1,
  input [1:0] in_2,
  output [1:0] out,
  output [1:0] observe_port
);

  wire [1:0] observe_port_int;
  wire [1:0] inter;
  assign inter = ~in_1;
  assign out = inter | in_2;
  assign observe_port_int[1:0] = inter[1:0];
  assign observe_port = observe_port_int;

endmodule

