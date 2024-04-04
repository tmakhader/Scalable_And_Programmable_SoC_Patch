

module Sample
(
  input wire A,
  input wire B,
  input wire clk,
  output wire out,
  output wire out2,
  output wire out3,
  input [3:0] control_port_out,
  output [3:0] control_port_in,
  output [1:0] observe_port
);

  reg out3_controlled;
  wire out2_controlled;
  wire out_controlled;
  wire test_wire_controlled;
  wire test_wire;
  assign out_controlled = A & B;
  assign test_wire_controlled = ~out;
  assign out2_controlled = test_wire | B | out3;

  always @(posedge clk) begin
    out3_controlled <= A;
  end

  assign control_port_in[0:0] = out_controlled[0:0];
  assign control_port_in[1:1] = out2_controlled[0:0];
  assign control_port_in[2:2] = out3_controlled[0:0];
  assign control_port_in[3:3] = test_wire_controlled[0:0];
  assign out[0:0] = control_port_out[0:0];
  assign out2[0:0] = control_port_out[1:1];
  assign out3[0:0] = control_port_out[2:2];
  assign test_wire[0:0] = control_port_out[3:3];
  assign observe_port[0:0] = B[0:0];
  assign observe_port[1:1] = out2_controlled[0:0];

endmodule

