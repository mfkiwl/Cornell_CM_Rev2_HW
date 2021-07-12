module top_vu13p (
	
//-----------------------------------------------
  // clocks
  // 200 MHz system clock
  input p_clk_200, n_clk_200,
  
  // A copy of the RefClk#0 used by the 12-channel FireFlys on the left side of the FPGA.
  // This can be the output of either refclk synthesizer R0A or R0B. 
  input p_lf_x12_r0_clk, n_lf_x12_r0_clk,

  // A copy of the RefClk#0 used by the 4-channel FireFlys on the left side of the FPGA.
  // This can be the output of either refclk synthesizer R0A or R0B. 
  input p_lf_x4_r0_clk, n_lf_x4_r0_clk,

  // A copy of the RefClk#0 used by the 12-channel FireFlys on the right side of the FPGA.
  // This can be the output of either refclk synthesizer R0A or R0B. 
  input p_rt_x12_r0_clk, n_rt_x12_r0_clk,

  // A copy of the RefClk#0 used by the 4-channel FireFlys on the right side of the FPGA.
  // This can be the output of either refclk synthesizer R0A or R0B. 
  input p_rt_x4_r0_clk, n_rt_x4_r0_clk,

  // 'input' "fpga_identity" to differentiate FPGA#1 from FPGA#2.
  // The signal will be HI in FPGA#1 and LO in FPGA#2.
  input fpga_identity,
  
  // 'output' "led": 3 bits to light a tri-color LED
  // These use different pins on F1 vs. F2. The pins are unused on the "other" FPGA,
  // so each color for both FPGAs can be driven at the same time
  output led_f1_blue, led_f1_green, led_f1_red,
  output led_f2_blue, led_f2_green, led_f2_red,

  // 'input' "mcu_to_f": 1 bit trom the MCU
  // 'output' "f_to_mcu": 1 bit to the MCU
  // There is no currently defined use for these.
  input mcu_to_f, 
  output reg f_to_mcu,

  // 'output' "c2c_ok": 1 bit to the MCU
  // The FPGA should set this output HI when the chip-2-chip link is working.
  output c2c_ok,

  // If the Zynq on the SM is the TCDS endpoint, then both FPGAs only use port #0 for TCDS
  // signals and the two FPGAs are programmed identically.
  //
  // If FPGA#1 is the TCDS endpoint, then:
  //  1) TCDS signals from the ATCA backplane connect to port#0 on FPGA#1
  //  2) TCDS information is sent from FPGA#1 to FPGA#2 on port #3
  //  3) TCDS information is sent from FPGA#1 to the Zynq on the SM on port #2.
  //
  // RefClk#0 for quad AB comes from REFCLK SYNTHESIZER R1A which can be driven by: 
  //  a) synth oscillator
  //  b) HQ_CLK from the SM
  //     b1) 320 MHz if FPGA#1 is the TCDS endpoint
  //     b2) 40 MHz if the SM is the TCDS endpoint
  //  c) Optional front panel connector for an external LVDS clock
  // quad AB
  input p_lf_r0_ab, n_lf_r0_ab,
  //
  // RefClk#1 comes from REFCLK SYNTHESIZER R1B which can be driven by: 
  //  a) synth oscillator
  //  b) an output from EXTERNAL REFCLK SYNTH R1A
  //  c) the 40 MHz TCDS RECOVERED CLOCK from FPGA #1 
  // RefClk#1 is only connected on FPGA#1, and is only used when FPGA#1 is the TCDS endpoint.
  // quad AB
  input p_lf_r1_ab, n_lf_r1_ab,
  // quad L
  input p_lf_r1_l, n_lf_r1_l,
  //
  // Port #0 is the main TCDS path. Both FPGAs use it when the Zynq on the SM is the
  // TCDS endpoint. Only FPGA#1 uses it when FPGA#1 is the TCDS endpoint.
  // Port #0 receive (schematic name is "con*_tcds_in")
  input p_tcds_in, n_tcds_in,
  // Port #0 transmit (schematic name is "con*_tcds_out")
  output p_tcds_out, n_tcds_out,
  //
  // Port #2 is used to send TCDS signals between FPGA#1 and the Zynq when
  // FPGA#1 is the TCDS endpoint. Port #2 is not used when the Zynq on the SM is the
  // TCDS endpoint. Port #2 is not connected to anything on FPGA#2.
  // quad AB
  input p_tcds_from_zynq_a, n_tcds_from_zynq_a,
  output p_tcds_to_zynq_a, n_tcds_to_zynq_a,
  // quad L
  input p_tcds_from_zynq_b, n_tcds_from_zynq_b,
  output p_tcds_to_zynq_b, n_tcds_to_zynq_b,
  //
  // Port #3 is cross-connected between the two FPGAs. It is only used when FPGA#1
  // is the TCDS endpoint.
  // quad AB
  input p_tcds_cross_recv_a, n_tcds_cross_recv_a,
  output p_tcds_cross_xmit_a, n_tcds_cross_xmit_a,
  // quad L
  input p_tcds_cross_recv_b, n_tcds_cross_recv_b,
  output p_tcds_cross_xmit_b, n_tcds_cross_xmit_b,
  //
  // Recovered 40 MHz TCDS clock output to feed REFCLK SYNTHESIZER R1B.
  // This is only connected on FPGA#1, and is only used when FPGA#1 is the
  // TCDS endpoint. On FPGA#2, these signals are not connected, but are reserved.
  output p_tcds_recov_clk, n_tcds_recov_clk,
  //
  // 40 MHz TCDS clock connected to FPGA logic. This is used in the FPGA for two
  // purposes. The first is to generate high-speed processing clocks by multiplying
  // in an MMCM. The second is to synchronize processing to the 40 MHz LHC bunch crossing.
  input p_tcds40_clk, n_tcds40_clk,

  
  // Spare input signals from the "other" FPGA.
  // These cross-connect to the spare output signals on the other FPGA
  // 'in_spare[2]' is connected to global glock-capable input pins
  input [2:0] p_in_spare, n_in_spare,
  // Spare output signals to the "other" FPGA.
  // These cross-connect to the spare input signals on the other FPGA
  output [2:0] p_out_spare, n_out_spare,
  
  // HDMI-style test connector on the front panel
  // 5 differential and 2 single-ended
  // 'test_conn_0' connects to global clock-capable input pins
  // THE DIRECTIONS ARE SET UP FOR TESTING. CHANGE THEM FOR REAL APPLICATIONS.
  input p_test_conn_0, n_test_conn_0,
  output p_test_conn_1, n_test_conn_1,
  output p_test_conn_2, n_test_conn_2,
  input p_test_conn_3, n_test_conn_3,
  input p_test_conn_4, n_test_conn_4,
  output reg test_conn_5,
  input test_conn_6,
  
  // Spare pins to 1mm x 1mm headers on the bottom of the board
  // They could be used in an emergency as I/Os, or for debugging
  // hdr[1] and hdr[2] are on global clock-capable pins
  input hdr1, hdr2,
  input hdr3, hdr4, hdr5, hdr6,
  output reg hdr7, hdr8, hdr9, hdr10,
  
  // C2C primary (#1) and secondary (#2) links to the Zynq on the SM
  input p_rt_r0_l, n_rt_r0_l,
  input p_mgt_sm_to_f_1, n_mgt_sm_to_f_1,
  output p_mgt_f_to_sm_1, n_mgt_f_to_sm_1,
  input p_mgt_sm_to_f_2, n_mgt_sm_to_f_2,
  output p_mgt_f_to_sm_2, n_mgt_f_to_sm_2,
  
 // Connect FF1, 12 lane, quad AC,AD,AE
  input p_lf_r0_ad, n_lf_r0_ad,
  input [0:11] n_ff1_recv, p_ff1_recv,
  output [0:11] n_ff1_xmit, p_ff1_xmit,

  // Connect FF4, 4 lane, quad AF
  input p_lf_r0_af, n_lf_r0_af,
  input [0:3] n_ff4_recv, p_ff4_recv,
  output [0:3] n_ff4_xmit, p_ff4_xmit,
   
  // Connect FF4, 4 lane, quad U
  input p_lf_r0_u, n_lf_r0_u,
  input [0:3] n_ff6_recv, p_ff6_recv,
  output [0:3] n_ff6_xmit, p_ff6_xmit,

  // I2C pins
  // The "sysmon" port can be accessed before the FPGA is configured.
  // The "generic" port requires a configured FPGA with an I2C module. The information
  // that can be accessed on the generic port is user-defined.
  inout i2c_scl_f_generic, i2c_sda_f_generic,
  inout i2c_scl_f_sysmon, i2c_sda_f_sysmon
);

// connect 200 MHz to a clock wizard that outputs 200 MHz, 100 MHz, and 50 MHz
clk_wiz_0 clk_wiz_inst (
     .clk_in1_n                       (n_clk_200),
     .clk_in1_p                       (p_clk_200),
     .clk_out1                        (clk_200),
     .clk_out2                        (clk_100),
     .clk_out3                        (clk_50), 
     .locked                          (clk_locked)
);

// add differential clock buffers to all the incoming clocks
wire lf_x12_r0_clk;
IBUFDS lf_x12_r0_clk_buf(.O(lf_x12_r0_clk), .I(p_lf_x12_r0_clk), .IB(n_lf_x12_r0_clk) );
wire lf_x4_r0_clk;
IBUFDS lf_x4_r0_clk_buf(.O(lf_x4_r0_clk), .I(p_lf_x4_r0_clk), .IB(n_lf_x4_r0_clk) );
wire rt_x12_r0_clk;
IBUFDS rt_x12_r0_clk_buf(.O(rt_x12_r0_clk), .I(p_rt_x12_r0_clk), .IB(n_rt_x12_r0_clk) );
wire rt_x4_r0_clk;
IBUFDS rt_x4_r0_clk_buf(.O(rt_x4_r0_clk), .I(p_rt_x4_r0_clk), .IB(n_rt_x4_r0_clk) );
wire tcds40_clk;           // 40 MHz LHC clock
IBUFDS tcds40_clk_buf(.O(tcds40_clk), .I(p_tcds40_clk), .IB(n_tcds40_clk) );

// add differential output buffer to TCDS recovered clock
wire tcds_recov_clk;
OBUFDS(.I(tcds_recov_clk), .O(p_tcds_recov_clk), .OB(n_tcds_recov_clk)); 
// dummy connection to tcds_recov_clk
assign tcds_recov_clk = tcds40_clk;

// add a free running counter to divide the clock
reg [27:0] divider;
always @(posedge clk_200) begin
  divider[27:0] <= divider[27:0] + 1;
end

assign led_f1_red = divider[27];
assign led_f1_green = divider[26];
assign led_f1_blue = divider[25];
assign led_f2_red = divider[27];
assign led_f2_green = divider[26];
assign led_f2_blue = divider[25];

// create 3 differential buffers for spare inputs 
genvar chan;
wire [2:0] in_spare;
generate
  for (chan=0; chan < 3; chan=chan+1)
    begin: gen_in_spare_buf
      IBUFDS in_spare_buf(.O(in_spare[chan]), .I(p_in_spare[chan]), .IB(n_in_spare[chan]) );
  end
endgenerate

// create 3 differential buffers for spare outputs 
reg [2:0] out_spare;
generate
  for (chan=0; chan < 3; chan=chan+1)
    begin: gen_out_spare_buf
      OBUFDS out_spare_buf(.I(out_spare[chan]), .O(p_out_spare[chan]), .OB(n_out_spare[chan]) );
  end
endgenerate

// loop the spare in to the spare out
always @(posedge clk_200) begin
  out_spare[2:0] <= in_spare[2:0];
end

// create differential buffers to loop the test_conn signals
wire test_conn_clk;
IBUFDS test_conn_clk_buf(.O(test_conn_clk), .I(p_test_conn_0), .IB(n_test_conn_0) );
wire test_conn_3, test_conn_4;
IBUFDS test_conn_4_buf(.O(test_conn_4), .I(p_test_conn_4), .IB(n_test_conn_4));
IBUFDS test_conn_3_buf(.O(test_conn_3), .I(p_test_conn_3), .IB(n_test_conn_3));
reg test_conn_out_2, test_conn_out_1;
OBUFDS test_conn_out_2_buf(.I(test_conn_out_2), .O(p_test_conn_2), .OB(n_test_conn_2));
OBUFDS test_conn_out_1_buf(.I(test_conn_out_1), .O(p_test_conn_1), .OB(n_test_conn_1));

// loop test_conn 'in' to 'out' using 'clk'
always @(posedge test_conn_clk) begin
  test_conn_out_2 <= test_conn_4;
  test_conn_out_1 <= test_conn_3;
  test_conn_5 <= test_conn_6;
end

// create differential buffers to loop the 'hdr' signals
wire hdr_clk;
IBUFDS hdr_clk_buf(.O(hdr_clk), .I(hdr1), .IB(hdr2) );

// loop hdr 'in' to 'out' using 'clk'
always @(posedge hdr_clk) begin
  hdr7 <= hdr3;
  hdr8 <= hdr4;
  hdr9 <= hdr5;
  hdr10 <= hdr6;
end

// create tri-state buffers for generic I2C scl and sda
wire i2c_scl_generic_out, i2c_scl_generic_tri, i2c_scl_generic_in; 
IOBUF generic_scl(.I(i2c_scl_generic_out),.T(i2c_scl_generic_tri), .O(i2c_scl_generic_in), .IO(i2c_scl_f_generic));
wire i2c_sda_generic_out, i2c_sda_generic_tri, i2c_sda_generic_in; 
IOBUF generic_sda(.I(i2c_sda_generic_out),.T(i2c_sda_generic_tri), .O(i2c_sda_generic_in), .IO(i2c_sda_f_generic));

wire i2c_scl_sysmon_out, i2c_scl_sysmon_tri, i2c_scl_sysmon_in; 
IOBUF sysmon_scl(.I(i2c_scl_sysmon_out),.T(i2c_scl_sysmon_tri), .O(i2c_scl_sysmon_in), .IO(i2c_scl_f_sysmon));
wire i2c_sda_sysmon_out, i2c_sda_sysmon_tri, i2c_sda_sysmon_in; 
IOBUF sysmon_sda(.I(i2c_sda_sysmon_out),.T(i2c_sda_sysmon_tri), .O(i2c_sda_sysmon_in), .IO(i2c_sda_f_sysmon));

// create dummy logic to use remaining inputs and outputs 
always @(posedge clk_200) begin
  f_to_mcu <= mcu_to_f & fpga_identity;
end

// Connect the c2c block
top_block_wrapper top_block_wrapper1 (
   .c2c_refclk_n(n_rt_r0_l),
   .c2c_refclk_p(p_rt_r0_l),
   .c2c_rxn(n_mgt_sm_to_f_1),
   .c2c_rxp(p_mgt_sm_to_f_1),
   .c2c_txn(n_mgt_f_to_sm_1),
   .c2c_txp(p_mgt_f_to_sm_1),
   .c2c2_rxn(n_mgt_sm_to_f_2),
   .c2c2_rxp(p_mgt_sm_to_f_2),
   .c2c2_txn(n_mgt_f_to_sm_2),
   .c2c2_txp(p_mgt_f_to_sm_2),
   .clk_100(clk_100),
   .c2c_ok(c2c_ok),
   .scl_i(i2c_scl_generic_in),
   .scl_o(i2c_scl_generic_out),
   .scl_t(i2c_scl_generic_tri),
   .sda_i(i2c_sda_generic_in),
   .sda_o(i2c_sda_generic_out),
   .sda_t(i2c_sda_generic_tri)
);

// add a ffx4 block to use 1 quad (quad AF = FF4)
BD_FFx4 FFx4_AF (
  .init_clk(clk_50),
  .refclk_n(n_lf_r0_af),
  .refclk_p(p_lf_r0_af),
  .rx_n({n_ff4_recv[0],n_ff4_recv[1],n_ff4_recv[2],n_ff4_recv[3]}),
  .rx_p({p_ff4_recv[0],p_ff4_recv[1],p_ff4_recv[2],p_ff4_recv[3]}),
  .tx_n({n_ff4_xmit[0],n_ff4_xmit[1],n_ff4_xmit[2],n_ff4_xmit[3]}),
  .tx_p({p_ff4_xmit[0],p_ff4_xmit[1],p_ff4_xmit[2],p_ff4_xmit[3]})
);

//// add a ffx4 block to use 1 quad (quad U = FF6)
//FFx4_U FFx4_U (
//  .init_clk(clk_200),
//  .refclk_n(n_lf_r0_u),
//  .refclk_p(p_lf_r0_u),
//  .rx_n({n_ff6_recv[0],n_ff6_recv[1],n_ff6_recv[2],n_ff6_recv[3]}),
//  .rx_p({p_ff6_recv[0],p_ff6_recv[1],p_ff6_recv[2],p_ff6_recv[3]}),
//  .tx_n({n_ff6_xmit[0],n_ff6_xmit[1],n_ff6_xmit[2],n_ff6_xmit[3]}),
//  .tx_p({p_ff6_xmit[0],p_ff6_xmit[1],p_ff6_xmit[2],p_ff6_xmit[3]})
//);

// add a ffx12 block to use 3 quads (quad AC,AD,AE = FF1)
BD_FFx12 FFx12_AD (
  .init_clk(clk_50),
  .refclk_n(n_lf_r0_ad),
  .refclk_p(p_lf_r0_ad),
  .rx_n({n_ff1_recv[11],n_ff1_recv[10],n_ff1_recv[9],n_ff1_recv[8],n_ff1_recv[7],n_ff1_recv[6],n_ff1_recv[5],n_ff1_recv[4],n_ff1_recv[3],n_ff1_recv[2],n_ff1_recv[1],n_ff1_recv[0]}),
  .rx_p({p_ff1_recv[11],p_ff1_recv[10],p_ff1_recv[9],p_ff1_recv[8],p_ff1_recv[7],p_ff1_recv[6],p_ff1_recv[5],p_ff1_recv[4],p_ff1_recv[3],p_ff1_recv[2],p_ff1_recv[1],p_ff1_recv[0]}),
  .tx_n({n_ff1_xmit[11],n_ff1_xmit[10],n_ff1_xmit[9],n_ff1_xmit[8],n_ff1_xmit[7],n_ff1_xmit[6],n_ff1_xmit[5],n_ff1_xmit[4],n_ff1_xmit[3],n_ff1_xmit[2],n_ff1_xmit[1],n_ff1_xmit[0]}),
  .tx_p({p_ff1_xmit[11],p_ff1_xmit[10],p_ff1_xmit[9],p_ff1_xmit[8],p_ff1_xmit[7],p_ff1_xmit[6],p_ff1_xmit[5],p_ff1_xmit[4],p_ff1_xmit[3],p_ff1_xmit[2],p_ff1_xmit[1],p_ff1_xmit[0]})
);

endmodule
