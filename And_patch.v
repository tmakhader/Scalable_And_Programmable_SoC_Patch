

module And
(
  input wire [1:0] in_1,
  input wire [1:0] in_2,
  output wire [1:0] out,
  output [0:0] observe_port,
  output [1:0] control_port_in,
  input [1:0] control_port_out
);

  wire [0:0] observe_port_int;
  wire [1:0] control_port_in_int;
  wire [1:0] control_port_out_int;
  wire [1:0] in_1_controlled;
  assign out = in_1_controlled & in_2;
  assign control_port_in_int[1:0] = in_1[1:0];
  assign in_1_controlled[1:0] = control_port_out_int[1:0];
  assign observe_port_int[0:0] = in_1[0:0];
  assign observe_port = observe_port_int;

endmodule

