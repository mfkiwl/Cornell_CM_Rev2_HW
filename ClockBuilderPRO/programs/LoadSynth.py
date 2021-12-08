#!/usr/bin/env python 

import serial
import time
import io
import argparse
import os
import pdb

dir = os.path.dirname(os.path.abspath(__file__))

#parser = optparse.OptionParser()
parser = argparse.ArgumentParser()
# allow user to specify the required destination synthesizer in upper/lower/mixed case
synth_choices = ["r0a", "r0b", "r1a", "r1b", "r1c"]
parser.add_argument("synth_id", type=str.lower, choices=synth_choices, help='[required] synthesizer to configure {R0A, R0B, R1A, R1B, R1C}')
# the required register list filename has to be an exact match
parser.add_argument("Reg_List", help='[required] Register List .h file from ClockBuilderPRO')
parser.add_argument('--tty', default='ttyUSB0', help='Specify tty device. ttyUL1 for ZYNQ. ttyUSB0 or ttyUSB1 for CPU.')
parser.add_argument('--debug', action="store_true", default=False, help='Print debug statements')
parser.add_argument('--quiet', action="store_true", default=False, help='Do not print out get_command output')
parser.add_argument('--alpha', action="store_true", default=False, help='Enable registers for FF alpha-2 parts')
#o, a = parser.parse_args()

args = parser.parse_args()

# define variables for accessing each synth
if args.synth_id == "r0a" :
    # SI5341 on mux channel 0 (mask = 0x01)
    i2c_port = "2"
    i2c_addr = "0x77"
    i2c_mux_mask = "0x01"
    Def_List = dir+"/../defaults/Si5341-RevD-default-Registers.h"
elif args.synth_id == "r0b" :
    # SI5395 on mux channel 1 (mask = 0x02)
    i2c_port = "2"
    i2c_addr = "0x6b"
    i2c_mux_mask = "0x02"
    Def_List = dir+"/../defaults/Si5395-RevA-default-Registers.h"
elif args.synth_id == "r1a" :
    # SI5395 on mux channel 2 (mask = 0x04)
    i2c_port = "2"
    i2c_addr = "0x6b"
    i2c_mux_mask = "0x04"
    Def_List = dir+"/../defaults/Si5395-RevA-default-Registers.h"
elif args.synth_id == "r1b" :
    # SI5395 on mux channel 3 (mask = 0x08)
    i2c_port = "2"
    i2c_addr = "0x6b"
    i2c_mux_mask = "0x08"
    Def_List = dir+"/../defaults/Si5395-RevA-default-Registers.h"
elif args.synth_id == "r1c" :
    # SI5395 on mux channel 4 (mask = 0x10)
    i2c_port = "2"
    i2c_addr = "0x6b"
    i2c_mux_mask = "0x10"
    Def_List = dir+"/../defaults/Si5395-RevA-default-Registers.h"

serPort = "/dev/"+args.tty

ser = serial.Serial(serPort,baudrate=115200,timeout=1)  # open serial port
print(ser.portstr)         # check which port was really used

def get_command(command):
    lines = []
    # just ensure command has newline 
    command = command.rstrip()
    command = command + '\r\n'
    # show what will be sent to the board    
    print(command)
    ser.write(command.encode()) # write one char from an int
    done = False
    # wait for the MCU to send back a "%" prompt    
    while ( not done ):
        line  = ser.readline().rstrip()
        if ( len(line) and chr(line[0]) == '%' ) :
            done = True
        else :
            lines.append(line.decode())
    return lines

#write to ClockSynthesizer
#When 'noisy' print out returned data of get_command
def write_reg(ListOfRegs,ListOfDefs,Optimize,Noisy):
    HighByte = -1
    Match = False
    for register in ListOfRegs:
        if Optimize :
            # skip sending register contents if it matches the default
            DefIndx = 0
            Found = False
            Match = False            
            while not Found and DefIndx < len(ListOfDefs) :
               if int(register[0][2:6],16) == int(ListOfDefs[DefIndx][0][2:6],16) :
                   # addresses match
                   Found = True
                   if int(register[1][2:4],16) == int(ListOfDefs[DefIndx][1][2:4],16) :
                       # data matches
                       Match = True
               
               if Match :
                    # data matches default
                    break
               elif not Found :
                    # have not found a matching address
                    DefIndx += 1

        if not Match:
            # determine if the register page has changed
            ChangePage = True if int(register[0][2:4],16)!=HighByte else False
            HighByte = int(register[0][2:4],16)
            if ChangePage:
                # write the new page number to address 0x01
                command = "i2cwr "+i2c_port+" "+i2c_addr+" 0x01 1 "+register[0][0:4]+""
                if Noisy:
                    print(get_command(command))
                else:
                    get_command(command)
            # write the register address and value
            command = "i2cwr "+i2c_port+" "+i2c_addr+" 0x"+register[0][4:6]+" 1 "+register[1]+""
            if Noisy:
                print(get_command(command))
            else:
                get_command(command)

    #Set page back to 0 in the end
    if Noisy:
        print(get_command("i2cwr "+i2c_port+" "+i2c_addr+" 0x01 1 0"))
    else:
        get_command("i2cwr "+i2c_port+" "+i2c_addr+" 0x01 1 0")
        
# send 'help' command and print out results to show that the MCU is communicating
print(get_command("help"))

# eventually move the I2C register port setup elsewhere.
# enable ports 6 and 7 on U84 at 0x70
print(get_command("i2cw "+i2c_port+" 0x70 1 0xc0"))
# Ping the registers at 0x20 and 0x21 to make sure they are indeed enabled
print(get_command("i2crr "+i2c_port+" 0x20 0x06 1"))
print(get_command("i2crr "+i2c_port+" 0x21 0x06 1"))
# Setting Control Registers at 0x20 on U88 (TCA9555) to have outputs on P07, P03..P00, P15..P12, and P10 (set '0' for outputs)
print(get_command("i2cwr "+i2c_port+" 0x20 0x06 1 0x70")) # 0b01110000
print(get_command("i2cwr "+i2c_port+" 0x20 0x07 1 0xc2")) # 0b11000010
# Setting U88 outputs on P07 and P10 to '1' to negate active-lo reset signals.
# Also setting P03..P00 to '1' to use synth R0B to drive the R0 RefClks to the FPGA#1
# All others to '0'
print(get_command("i2cwr "+i2c_port+" 0x20 0x02 1 8f")) #0b10001111
print(get_command("i2cwr "+i2c_port+" 0x20 0x03 1 01")) #0b00000001

# enable only the route through the I2C mux to the selected synth
print(get_command("i2cw "+i2c_port+" 0x70 1 "+i2c_mux_mask+""))
# ping the synth
print(get_command("i2cr "+i2c_port+" "+i2c_addr+"  1"))


#pdb.set_trace()
# open files and create/initialize variables
regfile=open(args.Reg_List, 'r', encoding='iso-8859-1')
deffile=open(Def_List, 'r')
PreambleList = []
PostambleList = []
RegisterList = []
DefaultList = []
line = []
InPreamble = 0
InRegisters = 0
InPostamble = 0

#read the default register settings from the "default" file
while True:
    line = deffile.readline()
    if not line:
        break    
    # set or clear section flags at the start or end of the register section
    if (line.find("Start configuration registers") > 0):
        print("Starting to read default register settings")
        InRegisters = 1
        continue
    elif (line.find("End configuration registers") > 0):
        print("Finished reading default register settings")
        InRegisters = 0
        # bail out at the end of the register section
        break

    # line does not contain a section marker
    else:
        if InRegisters :
            # line is from the register sections
            if line.find("/*") < 0 :
                # this is not a comment line that is embedded in a data section
                for words in line.split('"'):
                    # extract the register address and value
                    reg_loc = words.find("0x")
                    reg = words[reg_loc:reg_loc+6]
                    val_loc = words.find("0x",reg_loc + 1)
                    val = words[val_loc:val_loc+4]
                    # append the register address and value to the default list
                    DefaultList.append((reg,val))   
 
# read the desired register settings from the "register" file
while True:
    line = regfile.readline()
    if not line:
        break    
    # set or clear section flags at the start or end of each section
    if (line.find("Start configuration preamble") > 0):
        print("Starting to read the configuration preamble")
        InPreamble = 1
        continue
    elif (line.find("End configuration preamble") > 0):
        print("Finished reading the configuration preamble")
        InPreamble = 0
        continue
    elif (line.find("Start configuration registers") > 0):
        print("Starting to read the configuration data")
        InRegisters = 1
        continue
    elif (line.find("End configuration registers") > 0):
        print("Finished reading the configuration data")
        InRegisters = 0
        continue
    elif (line.find("Start configuration postamble") > 0):
        print("Starting to read the configuration postamble")
        InPostamble = 1
        continue
    elif (line.find("End configuration postamble") > 0):
        print("Finished reading the configuration postamble")
        InPostamble = 0
        # bail out at the end of the postamble
        break

    # line does not contain a section marker
    else:
        if InPreamble or InRegisters or InPostamble :
            # line is from one of the register sections
            if line.find("/*") < 0 :
                # not a comment line that is embedded with a section
                for words in line.split('"'):
                    # not a comment line
                    # extract the register address and value
                    reg_loc = words.find("0x")
                    reg = words[reg_loc:reg_loc+6]
                    val_loc = words.find("0x",reg_loc + 1)
                    val = words[val_loc:val_loc+4]
                    # append the register address and value to the appropriate list
                    if InPreamble:
                        PreambleList.append((reg,val))
                    elif InRegisters:
                        RegisterList.append((reg,val))   
                    elif InPostamble:
                        PostambleList.append((reg,val))

# send the preamble, data, and postamble to the synth
def LoadClock(PreList,RegList,PostList,DefList,Read):
    # for the preamble, send all data    
    Optimize = False
    write_reg(PreList,DefList,Optimize,Read)
    time.sleep(1) #only need 300 msec
    # for the data section, eliminate data that matches the default configuration    
    Optimize = True
    write_reg(RegList,DefList,Optimize,Read)
    time.sleep(1)
    # for the postamble, send all data
    Optimize = False
    write_reg(PostList,DefList,Optimize,Read)

# send data off to synthesizer
LoadClock(PreambleList, RegisterList, PostambleList, DefaultList, not args.quiet)

# disable all of the channels in the switch
print(get_command("i2cw 2 0x70 1 0x00"))

# close the tty port:
ser.close()
