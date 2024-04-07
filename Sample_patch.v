

module Sample
(
  input wire A,
  input wire B,
  input wire clk,
  output wire out,
  output wire out2,
  output wire out3,
  output [2:0] observe_port,
  output [5:0] control_port_in,
  input [5:0] control_port_out
);

  wire [2:0] observe_port_int;
  wire [5:0] control_port_in_int;
  wire [5:0] control_port_out_int;
  reg out3_controlled;
  wire out2_controlled;
  wire out_controlled;
  wire A_controlled;
  wire test_wire_controlled;
  wire test_wire;
  wire test_wire_2_controlled;
  wire test_wire_2;
  assign out_controlled = A_controlled & B;

  Or
  inst
  (
    .in(A_controlled),
    .out(test_wire_controlled)
  );


  Or
  inst
  (
    .in(B),
    .out(test_wire_2_controlled)
  );

  assign out2_controlled = test_wire | B | out3 | test_wire_2;

  always @(posedge clk) begin
    out3_controlled <= A_controlled;
  end

  assign control_port_in_int[0:0] = A[0:0];
  assign control_port_in_int[1:1] = out_controlled[0:0];
  assign control_port_in_int[2:2] = out2_controlled[0:0];
  assign control_port_in_int[3:3] = out3_controlled[0:0];
  assign control_port_in_int[4:4] = test_wire_controlled[0:0];
  assign control_port_in_int[5:5] = test_wire_2_controlled[0:0];
  assign A_controlled[0:0] = control_port_out_int[0:0];
  assign out[0:0] = control_port_out_int[1:1];
  assign out2[0:0] = control_port_out_int[2:2];
  assign out3[0:0] = control_port_out_int[3:3];
  assign test_wire[0:0] = control_port_out_int[4:4];
  assign test_wire_2[0:0] = control_port_out_int[5:5];
  assign observe_port_int[0:0] = A[0:0];
  assign observe_port_int[1:1] = B[0:0];
  assign observe_port_int[2:2] = out2_controlled[0:0];

endmodule



module Or
(
  input in,
  output out
);

  assign out = ~in;

endmodule

