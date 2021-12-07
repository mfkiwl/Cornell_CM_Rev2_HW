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
parser.add_argument("synth_id", type=str.lower, choices=synth_choices, help='[required] synthesizer to ramp {R0A, R0B, R1A, R1B, R1C}')
# allow user to specify the required direction in upper/lower/mixed case
direction_choices = ["up", "down", "both", "cont"]
parser.add_argument("direction", type=str.lower, choices=direction_choices, help='[required] direction to ramp {Up, Down, Both, Cont}')
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
elif args.synth_id == "r0b" :
    # SI5395 on mux channel 1 (mask = 0x02)
    i2c_port = "2"
    i2c_addr = "0x6b"
    i2c_mux_mask = "0x02"
elif args.synth_id == "r1a" :
    # SI5395 on mux channel 2 (mask = 0x04)
    i2c_port = "2"
    i2c_addr = "0x6b"
    i2c_mux_mask = "0x04"
elif args.synth_id == "r1b" :
    # SI5395 on mux channel 3 (mask = 0x08)
    i2c_port = "2"
    i2c_addr = "0x6b"
    i2c_mux_mask = "0x08"
elif args.synth_id == "r1c" :
    # SI5395 on mux channel 4 (mask = 0x10)
    i2c_port = "2"
    i2c_addr = "0x6b"
    i2c_mux_mask = "0x10"

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
def write_control(ChangePage, direction_mask, Noisy):
    # set the register page to page zero
    if ChangePage:
        # write the page number to address 0x01
        command = "i2cwr "+i2c_port+" "+i2c_addr+" 0x01 1 0"
        if Noisy:
            print(get_command(command))
        else:
            get_command(command)

    # write the direction to the INC/DEC register at 0x1d
    command = "i2cwr "+i2c_port+" "+i2c_addr+" 0x1d 1 "+direction_mask+""
    if Noisy:
        print(get_command(command))
    else:
        get_command(command)
    # clear register back to zero
    #command = "i2cwr "+i2c_port+" "+i2c_addr+" 0x1d 1 0"
    #if Noisy:
    #    print(get_command(command))
    #else:
    #    get_command(command)

      
# send 'help' command and print out results to show that the MCU is communicating
print(get_command("help"))

# enable only the route through the I2C mux to the selected synth
#pdb.set_trace()
print(get_command("i2cw "+i2c_port+" 0x70 1 "+i2c_mux_mask+""))
# ping the synth
print(get_command("i2cr "+i2c_port+" "+i2c_addr+"  1"))

#pdb.set_trace()
# open files for increment/decrement information
regfile=open(args.Reg_List, 'r', encoding='iso-8859-1')
InDCO = 0
line = []
ChangePage = 1
 
# read the step size and range settings from the "register" file
while True:
    line = regfile.readline()
    if not line:
        break    
    # set or clear section flags at the start or end of each section
    if (line.find("Mode: FINC/FDEC") > 0):
        print("Starting to read the DCO section")
        InDCO = 1
        continue
    elif (line.find("Estimated Power & Junction Temperature") > 0):
        print("Finished reading the DCO section")
         # bail out here
        break

    # line does not contain a section marker
    else:
        if InDCO :
            # line is from the DCO section
            if line.find("Desired Step Size") > 0 :
                # extract the step size and the units
                words = line.split()
                indx = 0
                while indx < len(words) :
                   if words[indx].find(":") > 0 :
                       # next two words are the step size and the units
                       step_size = words[indx+1]
                       step_units = words[indx+2]
                       break
                   indx += 1
            elif line.find("Range") > 0 :
                # extract the span (range is a python keyword) and the units
                words = line.split()
                indx = 0
                while indx < len(words) :
                   if words[indx].find(":") > 0 :
                       # next two word are the span and the units
                       span = words[indx+1]
                       span_units = words[indx+2]
                       break
                   indx += 1

# send commands off to synthesizer
pdb.set_trace()
# figure out how many steps are needed
if step_units == span_units :
    # both have the same units
    num_steps_scale = 1.0
elif step_units == "ppb" and span_units == "ppm" :
    # multiply by 1000
    num_steps_scale = 1000.0
num_steps = int(num_steps_scale * float(span)/float(step_size))

# set the initial direction. "both" or "cont" will always start with a decrement
direction_mask = "2"
if (args.direction == "up") :
    direction_mask = "1"

while True :
    step = 0
    while step < num_steps :
        step +=1
        write_control(ChangePage, direction_mask, not args.quiet)
        ChangePage = 0
        time.sleep(1)
    # all steps have been sent to the hardware
    if args.direction == "up" :
        break
    elif args.direction == "down" :
        break
    elif args.direction == "both" :
        if direction_mask == "1" :
            # finshed the "up"
            break
        # finished the "down", now do an "up"
        direction_mask = "1"
    else :
        # continuous mode, toggle direction mask
        if direction_mask == "2" :
            direction_mask = "1"
        else :
            direction_mask = "2"

# disable all of the channels in the switch
print(get_command("i2cw 2 0x70 1 0x00"))

# close the tty port:
ser.close()
