#!/usr/bin/env python33
import sys
import struct
import socket
import binascii
import logging
from datetime import datetime
import ctypes
from user_settings import user_editable_settings
settings = user_editable_settings()

class FEMB_UDP:
    
    #Sends a full 32 bit register to either FPGA
    def write_reg(self, reg, data, board):
        
        regVal = int(reg)
        if (regVal < 0) or (regVal > self.MAX_REG_NUM):
            print ("FEMB_UDP--> Error write_reg: Invalid register number")
            return None
        
        dataVal = int(data)
        if (dataVal < 0) or (dataVal > self.MAX_REG_VAL):
            print ("FEMB_UDP--> Error write_reg: Invalid data value")
            return None
        
        if (board != "wib") and (board != "femb"):
            print ("FEMB_UDP--> Error write_reg: Invalid board value!  Use 'wib' or 'femb'.")
            return None
        
        #Splits the register up, since both halves need to go through socket.htons seperately
        dataValMSB = ((dataVal >> 16) & 0xFFFF)
        dataValLSB = dataVal & 0xFFFF
        
        #Organize packets as described in user manual
        WRITE_MESSAGE = struct.pack('HHHHHHHHH',socket.htons( self.KEY1  ), socket.htons( self.KEY2 ),
                                    socket.htons(regVal),socket.htons(dataValMSB),
                                    socket.htons(dataValLSB),socket.htons( self.FOOTER ), 0x0, 0x0, 0x0  )
        
        #Set up socket for IPv4 and UDP, attach the correct PC IP
        sock_write = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock_write.bind((settings.CHIP_IP[0], 0))
        except:
            print("IP: {}".format(settings.CHIP_IP[0]))
        
        #Send to FPGA at 192.168.121.1, and the correct port for the board we're writing to
        if (board == "femb"):
            sock_write.sendto(WRITE_MESSAGE,(self.UDP_IP[0], self.FEMB_PORT_WREG ))
        elif (board == "wib"):
            sock_write.sendto(WRITE_MESSAGE,(self.UDP_IP[0], self.WIB_PORT_WREG ))
        else:
            print ("FEMB_UDP--> Error write_reg: Invalid board value!  Use 'wib' or 'asic'.")
        #print ("Sent FEMB data from")
        #print (sock_write.getsockname())
        sock_write.close()
        #print ("FEMB_UDP--> Write: reg=%x,value=%x"%(reg,data))
        
    #Read a full register from the FEMB FPGA.  Returns the 32 bits in an integer form
    def read_reg(self, reg, board):
        
        for i in range(10):
            regVal = int(reg)
            if (regVal < 0) or (regVal > self.MAX_REG_NUM):
                    print ("FEMB_UDP--> Error read_reg: Invalid register number")
                    return None
                
            if (board != "wib") and (board != "femb"):
                print ("FEMB_UDP--> Error write_reg: Invalid board value!  Use 'wib' or 'femb'.")
                return None
    
            #Set up listening socket before anything else - IPv4, UDP
            sock_readresp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            #Allows us to quickly access the same socket and ignore the usual OS wait time betweeen accesses
            sock_readresp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            #Prepare to listen at configuration socket and for the correct port for the board we're writing to
            if (board == "femb"):
                sock_readresp.bind((settings.CHIP_IP[0], self.FEMB_PORT_RREGRESP ))
            elif (board == "wib"):
                sock_readresp.bind((settings.CHIP_IP[0], self.WIB_PORT_RREGRESP ))
            else:
                print ("FEMB_UDP--> Error write_reg: Invalid board value!  Use 'wib' or 'asic'.")
    
            sock_readresp.settimeout(.2)
    
            #First send a request to read out this sepecific register at the read request port for the board
            READ_MESSAGE = struct.pack('HHHHHHHHH',socket.htons(self.KEY1), socket.htons(self.KEY2),socket.htons(regVal),0,0,socket.htons(self.FOOTER),0,0,0)
            sock_read = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock_read.setblocking(0)
            sock_read.bind((settings.CHIP_IP[0], 0))
            
            
            if (board == "femb"):
                sock_read.sendto(READ_MESSAGE,(self.UDP_IP[0],self.FEMB_PORT_RREG))
            elif (board == "wib"):
                sock_read.sendto(READ_MESSAGE,(self.UDP_IP[0],self.WIB_PORT_RREG))
            else:
                print ("FEMB_UDP--> Error write_reg: Invalid board value!  Use 'wib' or 'asic'.")
            
            
            #print ("Sent read request from")
            #print (sock_read.getsockname())
            
            sock_read.close()
    
            #try to receive response packet from board, store in hex
            data = []
            try:
                    data = sock_readresp.recv(self.BUFFER_SIZE)
            except socket.timeout:
                if (i > 9):
                    print ("FEMB_UDP--> Error read_reg: No read packet received from board, quitting")
                    if (board == "femb"):
                        print ("Waited for FEMB response on")
                    elif (board == "wib"):
                        print ("Waited for WIB response on")
                    print (sock_readresp.getsockname())
                    sock_readresp.close()
                    return None      
#                else:
#                    print ("FEMB_UDP--> Didn't get a readback response, trying again...")
                
            #print ("Waited for FEMB response on")
            #print (sock_readresp.getsockname())
            sock_readresp.close()
            
            if (data != []):
                break
        
        #Goes from binary data to hexidecimal (because we know this is host order bits)
        dataHex = []
        try:
            dataHex = binascii.hexlify(data)
            #If reading, say register 0x290, you may get back
            #0290FFFFCCCC0291FFFFDDDD00000000000000
            #The first 4 bits are the register you requested, the next 8 bits are the value
            #By default, the current firmware also sends back the next register (0291 in this case) also
            #There's an option to continuously read out successive registers, but it would need a larger buffer
            
            #Looks for those first 4 bits to make sure you read the register you're looking for
            if int(dataHex[0:4],16) != regVal :
                print ("FEMB_UDP--> Error read_reg: Invalid response packet")
                return None
                
            #Return the data part of the response in integer form (it's just easier)
            dataHexVal = int(dataHex[4:12],16)
            #print ("FEMB_UDP--> Read: reg=%x,value=%x"%(reg,dataHexVal))
            return dataHexVal
        except TypeError:
            print (data)
        


    #Read and return a given amount of unpacked data "packets"
    #If you're going to save it write to disk, request it as "bin"
    #If you're going to use it in Python for something else, request the int or hex
    def get_data_packets(self, ip, data_type, num=1, header = False):
        numVal = int(num)
        if (numVal < 0) or (numVal > self.MAX_NUM_PACKETS):
                print ("FEMB_UDP--> Error: Invalid number of data packets requested")
                return None
            
        if ((data_type != "int") and (data_type != "hex") and (data_type != "bin")):
            print ("FEMB_UDP--> Error: Request packets as data_type = 'int', 'hex', or 'bin'")
            return None

        #set up IPv4, UDP listening socket at requested IP
        sock_data = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock_data.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock_data.bind((ip,self.PORT_HSDATA))
        sock_data.settimeout(10)

        #Read a certain amount of packets
        rawdataPackets = bytearray()
        for packet in range(0,numVal,1):
            data = []
            try:
                    data = sock_data.recv(self.BUFFER_SIZE)
            except socket.timeout:
                    print ("FEMB_UDP--> Error get_data_packets: No data packet received from board, quitting")
                    print ("FEMB_UDP--> Socket was {}".format(sock_data))
                    return []
            except OSError:
                print ("FEMB_UDP--> Error accessing socket: No data packet received from board, quitting")
                print ("FEMB_UDP--> Socket was {}".format(sock_data))
                sock_data.close()
                return []
            if (data != None):
                #If the user wants the header, keep those 16 bits in, or else don't
                if (header != True):
                    rawdataPackets += data[16:]
                else:
                    rawdataPackets += data

        #print (sock_data.getsockname())
        sock_data.close()
        
        #If the user wanted straight up bytes, then return the bytearray
        if (data_type == "bin"):
            return rawdataPackets

        
        buffer = (len(rawdataPackets))/2
        #Unpacking into shorts in increments of 2 bytes
        formatted_data = struct.unpack_from(">%dH"%buffer,rawdataPackets)

        #If the user wants to display the data as a hex
        if (data_type == "hex"):
            hex_tuple = []
            for i in range(len(formatted_data)):
                hex_tuple.append(hex(formatted_data[i]))
            return hex_tuple
            
            
        return formatted_data
    
    #Send a dummy packet from the PC to an FPGA port in order to initiate an ARP request and map the FPGA port
    def init_ports(self, hostIP = '', destIP = '', dummy_port = 0):
        
        #An incorrect version of the packet is fine, the communication wont go through, it just triggeres ARP
        WRITE_MESSAGE = struct.pack('HHH',socket.htons( self.KEY1  ), socket.htons( self.FOOTER  ), 0x0  )
        
        #Set up the port for IPv4 and UDP
        sock_write = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        sock_write.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        #Send from the appropriate socket to the requested IP (maybe add something to tell you if you did it wrong?)
        try:
            sock_write.bind((hostIP,dummy_port))
            sock_write.sendto(WRITE_MESSAGE,(destIP, self.FEMB_PORT_WREG ))
    
            sock_write.close()
        except:
            print("Host IP: {}\nDummy Port: {}\nDest IP:{}\nWREG: {}".format(hostIP, dummy_port, destIP, self.FEMB_PORT_WREG))
        
    #This function will start the C dll that simulataneously reads 4 sockets for a given time or number of packets. Takes:
    #The amount of total packets to read (0 means go until Python externally tells it to stop)
    #The amount of chips to use (in case certain chips or ethernet connections are down)
    #Packets to concatenate per file.  Should be at least two, or else the PC can't write 1000 3kB files per second.  Even 500 6 kB files is doable
    #Buffer size of the FIFO.  Should be 10-50 or so
    #The port that the FPGA will be writing to
    #All 4 FPGA IP addresses that will be read
    #Directory to save the data/debug files to
    #The inter-thread queue so that this thread can pass back the handler to the DLL so the main thread can stop it
    def get_packets_from_c(self,
                           num_of_packets,
                           num_of_chips,
                           packets_per_file,
                           buffer_size,
                           udp_port,
                           PC_IP1,
                           PC_IP2,
                           PC_IP3,
                           PC_IP4,
                           directory,
                           queue):
        
        #Load the DLL and hand itback to the main thread
        mydll = ctypes.cdll.LoadLibrary(settings.DLL_LOCATION)
        queue.put(mydll)

        #Python strings need to be converted first to bytes and then to Ctype strings
        PC_IP1_in = ctypes.create_string_buffer(PC_IP1.encode())
        PC_IP2_in = ctypes.create_string_buffer(PC_IP2.encode())
        PC_IP3_in = ctypes.create_string_buffer(PC_IP3.encode())
        PC_IP4_in = ctypes.create_string_buffer(PC_IP4.encode())
        debug_directory = ctypes.create_string_buffer(directory.encode())
        
        #Name of the main function in the DLL
        testFunction = mydll.socket_read_main
        print("Debug information will print in " + repr(debug_directory.value))
        
        #Calls the DLL and passes all these arguments
        result = testFunction(num_of_packets,
                              num_of_chips,
                              packets_per_file,
                              buffer_size,
                              udp_port,
                              PC_IP1_in,
                              PC_IP2_in,
                              PC_IP3_in,
                              PC_IP4_in,
                              debug_directory
                              )
        if (result == 0):
            print ("CmdLine--> Listening thread exited successfully")
        else:
            print ("CmdLine--> Listening thread exited with an error")
        
        #The DLL has to be released from memory in a convoluted way becaues it's for 64-bit systems
        libHandle = mydll._handle
        del mydll
        ctypes.windll.kernel32.FreeLibrary.argtypes = [ctypes.wintypes.HMODULE]
        ctypes.windll.kernel32.FreeLibrary(libHandle)
        print ("CmdLine--> Done")
        


    #__INIT__#
    def __init__(self):
        #IP addresses of the FPGA board
        self.UDP_IP = ["192.168.121.1", "192.168.121.2", "192.168.121.3", "192.168.121.4"]


        #Standard keys to include in data transmission
        self.KEY1 = 0xDEAD
        self.KEY2 = 0xBEEF
        self.FOOTER = 0xFFFF
        
        #The relevant ports for reading and writing to each board
        self.WIB_PORT_WREG = 32000
        self.WIB_PORT_RREG = 32001
        self.WIB_PORT_RREGRESP = 32002
        
        self.FEMB_PORT_WREG = 32016
        self.FEMB_PORT_RREG = 32017
        self.FEMB_PORT_RREGRESP = 32018
        
        self.PORT_HSDATA = 32003
        
        #Just some limits to check against
        self.MAX_REG_NUM = 667
        self.MAX_REG_VAL = 0xFFFFFFFF
        self.MAX_NUM_PACKETS = 1000
        self.BUFFER_SIZE = 9014