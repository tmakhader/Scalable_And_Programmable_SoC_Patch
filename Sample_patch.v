

module Sample
(
  input wire A,
  input wire B,
  input wire clk,
  output wire out,
  output wire out2,
  output wire out3,
  output [4:0] observe_port,
  output [7:0] control_port_in,
  input [7:0] control_port_out
);

  wire [1:0] control_port_out_inst;
  wire [1:0] control_port_in_inst;
  wire [1:0] observe_port_inst;
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
  inst1
  (
    .in(A_controlled),
    .out(test_wire_controlled),
    .observe_port(observe_port_inst[0:0]),
    .control_port_in(control_port_in_inst[0:0]),
    .control_port_out(control_port_out_inst[0:0])
  );


  Or
  inst2
  (
    .in(B),
    .out(test_wire_2_controlled),
    .observe_port(observe_port_inst[1:1]),
    .control_port_in(control_port_in_inst[1:1]),
    .control_port_out(control_port_out_inst[1:1])
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
  assign observe_port = { observe_port_int, observe_port_inst };
  assign control_port_in = { control_port_in_int, control_port_in_inst };
  assign { control_port_out_int, control_port_out_inst } = control_port_out;

endmodule



module Or
(
  input in,
  output out,
  output [0:0] observe_port,
  output [0:0] control_port_in,
  input [0:0] control_port_out
);

  wire [0:0] observe_port_int;
  wire [0:0] control_port_in_int;
  wire [0:0] control_port_out_int;
  wire inter_controlled;
  wire inter;
  assign inter_controlled = ~in;
  assign out = inter;
  assign control_port_in_int[0:0] = inter_controlled[0:0];
  assign inter[0:0] = control_port_out_int[0:0];
  assign observe_port_int[0:0] = inter_controlled[0:0];
  assign observe_port = observe_port_int;

endmodule

