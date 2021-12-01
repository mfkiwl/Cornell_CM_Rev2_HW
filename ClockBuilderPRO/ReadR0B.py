#!/usr/bin/env python 

import serial
import time
import io
import optparse
import os
import pdb

dir = os.path.dirname(os.path.abspath(__file__))

parser = optparse.OptionParser()
parser.add_option('--RegisterList', dest="Reg_List", default=dir+'Si5495-RevA-R0Bv0001-Registers.h',help='Base path of Register List.')
parser.add_option('--tty', dest="tty_device", default='ttyUSB0', help='Specify tty device. ttyUL1 for ZYNQ. ttyUSB0 or ttyUSB1 for CPU.')
parser.add_option('--debug', action="store_true", dest="Debug", default=False,help='Print debug statementss')
parser.add_option('--quiet', action="store_true", dest="Quiet", default=False,help='Do not print out get_command output')
parser.add_option('--alpha', action="store_true", dest="Alpha", default=False,help='Enable registers for FF alpha-2 parts')
o, a = parser.parse_args()

serPort = "/dev/"+o.tty_device

ser = serial.Serial(serPort,baudrate=115200,timeout=1)  # open serial port
print(ser.portstr)         # check which port was really used

def get_command(command):
    lines = []
    # just ensure command has newline 
    command = command.rstrip()
    command = command + '\r\n'
    print(command)
    ser.write(command.encode()) # write one char from an int
    done = False
    while ( not done ):
        line  = ser.readline().rstrip()
        if ( len(line) and chr(line[0]) == '%' ) :
            done = True
        else :
            lines.append(line.decode())
    return lines

#write to ClockSynthesizer at 0x6b
#When Read print out output of get_command
def write_reg(ListOfRegs,Read):
    HighByte = -1
    for register in ListOfRegs:
        # determine if the register page has changed
        ChangePage = True if int(register[0][2:4],16)!=HighByte else False
        HighByte = int(register[0][2:4],16)
        if ChangePage:
            # write the new page number to address 0x01
            command = "i2cwr 2 0x6b 0x01 1 "+register[0][0:4]+""
            if Read:
                print(get_command(command))
            else:
                get_command(command)
        # write the register value
        command = "i2cwr 2 0x6b 0x"+register[0][4:6]+" 1 "+register[1]+""
        if Read:
            print(get_command(command))
        else:
            get_command(command)
    #Set page back to 0 in the end
    if Read:
        print(get_command("i2cwr 2 0x6b 0x01 1 0"))
    else:
        get_command("i2cwr 2 0x6b 0x01 1 0")
        
#read from ClockSynthesizer at 0x6b
#When Read print out output of get_command
def read_reg(ListOfRegs,Read):
    HighByte = -1
    for register in ListOfRegs:
        # determine if the register page has changed
        ChangePage = True if int(register[0][2:4],16)!=HighByte else False
        HighByte = int(register[0][2:4],16)
        if ChangePage:
            # write the new page number to address 0x01
            command = "i2cwr 2 0x6b 0x01 1 "+register[0][0:4]+""
            if Read:
                print(get_command(command))
            else:
                get_command(command)
        # read the register value
        command = "i2crr 2 0x6b 0x"+register[0][4:6]+" 1 "
        if Read:
            pdb.set_trace()
            print(get_command(command))
        else:
            get_command(command)
    #Set page back to 0 in the end
    if Read:
        print(get_command("i2cwr 2 0x6b 0x01 1 0"))
    else:
        get_command("i2cwr 2 0x6b 0x01 1 0")

print(get_command("help"))
#enable ports 6 and 7 on U84 at 0x70
print(get_command("i2cw 2 0x70 1 0xc0"))
#Ping the registers at 0x20 and 0x21 to make sure they are indeed enabled
print(get_command("i2crr 2 0x20 0x06 1"))
print(get_command("i2crr 2 0x21 0x06 1"))
#Setting Control Registers at 0x20 on U88 (TCA9555) to have outputs on P07, P03..P00, P15..P12, and P10 (set '0' for outputs)
print(get_command("i2cwr 2 0x20 0x06 1 0x70")) # 0b01110000
print(get_command("i2cwr 2 0x20 0x07 1 0xc2")) # 0b11000010
#Setting U88 outputs on P07 and P10 to '1' to negate active-lo reset signals. All others to '0'
print(get_command("i2cwr 2 0x20 0x02 1 80")) #0b10000000
print(get_command("i2cwr 2 0x20 0x03 1 01")) #0b00000001

# disable I2C routes to register chips, enable route to synth
print(get_command("i2cw 2 0x70 1 0x02"))
# ping the synth
print(get_command("i2cr 2 0x6b 1"))


regfile=open(o.Reg_List, 'r')
PreambleList = []
PostambleList = []
RegisterList =[]
line = []
InPreamble = 0
InRegisters = 0
InPostamble = 0

while True:
    line = regfile.readline()
    if not line:
        break    
    # set or clear section flags at the start or end of each section
    if (line.find("Start configuration preamble") > 0):
        print(line)
        InPreamble = 1
        continue
    elif (line.find("End configuration preamble") > 0):
        print(line)
        InPreamble = 0
        continue
    elif (line.find("Start configuration registers") > 0):
        print(line)
        InRegisters = 1
        continue
    elif (line.find("End configuration registers") > 0):
        print(line)
        InRegisters = 0
        continue
    elif (line.find("Start configuration postamble") > 0):
        print(line)
        InPostamble = 1
        continue
    elif (line.find("End configuration postamble") > 0):
        print(line)
        InPostamble = 0
        # bail out at the end of the postamble
        break

    # line does not contain a section marker
    else:
        if InPreamble or InRegisters or InPostamble :
            # line is from one of the register sections
            for words in line.split('"'):
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
 
def LoadClock(PreList,RegList,PostList,Read):
    write_reg(PreList,Read)
    time.sleep(1) #only need 300 msec
    read_reg(RegList,Read)
    time.sleep(1)
    write_reg(PostList,Read)

# send data off to synthesizer
LoadClock(PreambleList, RegisterList, PostambleList, not o.Quiet)

# disable all of the channels in the switch
print(get_command("i2cw 2 0x70 1 0x00"))

#if ser.is_open:
ser.close()
