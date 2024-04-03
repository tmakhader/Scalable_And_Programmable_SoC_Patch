

module Sample
(
  input wire A,
  input wire B,
  input wire clk,
  output wire out,
  output wire out2,
  output wire out3,
  input [3:0] control_port_out,
  output [3:0] control_port_in
);

  assign test_wire[0:0] = control_port_out[3:3];
  assign out3[0:0] = control_port_out[2:2];
  assign out[0:0] = control_port_out[1:1];
  assign A_controlled[0:0] = control_port_out[0:0];
  assign control_port_in[3:3] = test_wire_controlled[0:0];
  assign control_port_in[2:2] = out3_controlled[0:0];
  assign control_port_in[1:1] = out_controlled[0:0];
  assign control_port_in[0:0] = A[0:0];
  reg out3_controlled;
  wire out_controlled;
  wire A_controlled;
  wire test_wire_controlled;
  wire test_wire;
  assign out_controlled = A_controlled & B;
  assign test_wire_controlled = ~out;
  assign out2 = test_wire | B;

  always @(posedge clk) begin
    out3_controlled <= A_controlled;
  end


endmodule

