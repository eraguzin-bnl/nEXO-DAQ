#!/usr/bin/env python33

import sys 
import time
from scripts.femb_udp_cmdline import FEMB_UDP
from scripts.adc_asic_reg_mapping import ADC_ASIC_REG_MAPPING
from scripts.fe_asic_reg_mapping import FE_ASIC_REG_MAPPING
from user_settings import user_editable_settings
from scripts.Data_Analysis import Data_Analysis
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import os
from scripts.Data_Analysis import Data_Analysis
settings = user_editable_settings()

class FEMB_CONFIG:

    def resetFEMBBoard(self):
        print ("FEMB_CONFIG--> Reset FEMB (3 seconds)")
        sys.stdout.flush()
        #Reset FEMB system
        self.femb.write_reg ( self.REG_RESET, 1, "femb")
        time.sleep(1.)

        #Reset FEMB registers
        self.femb.write_reg ( self.REG_RESET, 2, "femb")
        time.sleep(1.)
        
        #Reset ADC ASICs
        self.femb.write_reg ( self.REG_ASIC_RESET, 1, "femb")
        time.sleep(0.5)
        
        #Reset FE ASICs
        self.femb.write_reg ( self.REG_ASIC_RESET, 2, "femb")
        time.sleep(0.5)
        
        print ("FEMB_CONFIG--> Reset FEMB is DONE")
        
    def resetWIBBoard(self):
        print ("FEMB_CONFIG--> Reset WIB (5 seconds)")
        sys.stdout.flush()
        #Global reset to WIB board.  Yes, it actually takes 3-4 seconds to accept packets again.
        self.femb.write_reg( self.WIB_RESET, 1, "wib")
        time.sleep(5)
        
        print ("FEMB_CONFIG--> Reset WIB is DONE")

    def initBoard(self):
        print ("FEMB_CONFIG--> Initialize FEMB")
        #set up default registers
#        #As long as you try to write something, the network interface will map it
#        self.femb.init_ports(hostIP = "192.168.121.51", destIP = "192.168.121.1", dummy_port = 1)
#        self.femb.init_ports(hostIP = "192.168.121.60", destIP = "192.168.121.2", dummy_port = 2)
#        self.femb.init_ports(hostIP = "192.168.121.70", destIP = "192.168.121.3", dummy_port = 3)
#        self.femb.init_ports(hostIP = "192.168.121.80", destIP = "192.168.121.4", dummy_port = 4)
        
        #Reset ADC ASICs
#        self.femb.write_reg( self.REG_ASIC_RESET, 1, "femb")
#        time.sleep(1)

        #Set ADC delay
        self.femb.write_reg ( self.REG_LATCHLOC1_4, settings.REG_LATCHLOC1_4_data, "femb")
        self.femb.write_reg ( self.REG_CLKPHASE, settings.REG_CLKPHASE_data, "femb")
        self.femb.write_reg ( 21, settings.read_asic_1_0, "femb")
        self.femb.write_reg ( 22, settings.read_asic_3_2, "femb")
        self.femb.write_reg ( 23, settings.read_asic_neg - 0x80000000, "femb")
        self.femb.write_reg ( 23, settings.read_asic_neg, "femb")

        #Gives default pulse values
        reg_5_value = ((self.REG_TEST_PULSE_FREQ<<16)&0xFFFF0000) + ((self.REG_TEST_PULSE_DLY<<8)&0xFF00) +\
                      ( (self.REG_TEST_PULSE_AMPL)& 0xFF )
                      
        self.femb.write_reg ( self.REG_TEST_PULSE, reg_5_value, "femb")
        
        #No test output to either FPGA or internal pulse (althought this means the external pulse can get through)
        self.femb.write_reg (16, 0x0, "femb")
        
        #No internal test output
        self.femb.write_reg (18, 0x1, "femb")
        
        #Make sure the FEMB is streaming to the WIB
        self.femb.write_reg(9, int('1001',2), "femb")
        
        #Default packet size - DO NOT GO LOWER THAN 0x0300
        frame_size = 0x0300
        
        if (frame_size%13 != 0):
            frame_size = 13 * (frame_size//13)
        
        #Automatic streaming, no trigger for now
        Trigger_mode = 0
        
        reg31_value = ((Trigger_mode<<31) & 0x80000000) + frame_size
        
        self.femb.write_reg(31, reg31_value, "wib")
        
        self.fe_reg.set_fe_board(sts=0, snc=1, sg=3, st=1, smn=0, sbf=1, 
                       slk = 0, stb = 0, s16=0, slkh=0, sdc=0, sdacsw2=0, sdacsw1=0, sdac=0, show="FALSE")
        
        self.adc_reg.set_adc_board(d=0, pcsr=1, pdsr=1, slp=0, tstin=0,
                                                    clk = 0, frqc = 0, en_gr = 1, f0 = 0, f1 = 0, 
                                                    f2 = 0, f3 = 0, f4 = 1, f5 = 0, slsb = 0, show="FALSE")  

        #set default value to FEMB ADCs and FEs
        self.configAdcAsic(output = "first")
        self.configFeAsic()
        
        print ("FEMB_CONFIG--> Initialize FEMB is DONE")

    def configAdcAsic(self, output = "ok", board = "femb"):
        Adcasic_regs = self.adc_reg.REGS
        #ADC ASIC SPI registers
        if (output != "suppress"):
            print ("FEMB_CONFIG--> Config ADC ASIC SPI")
        for k in range(99):
            i = 0
            for regNum in range(self.REG_ADCSPI_BASE,self.REG_ADCSPI_BASE+len(Adcasic_regs),1):
                    self.femb.write_reg( regNum, Adcasic_regs[i], board)
                    i = i + 1
 

            #Write ADC ASIC SPI
            if (output != "suppress"):
                print ("FEMB_CONFIG--> Program ADC ASIC SPI")
            self.femb.write_reg ( self.REG_ASIC_RESET, 1, board)
            time.sleep(0.05)
            self.femb.write_reg ( self.REG_ASIC_SPIPROG, 1, board)
            time.sleep(0.05)
            self.femb.write_reg ( self.REG_ASIC_SPIPROG, 1, board)
            time.sleep(0.05)

            if (output != "suppress"):
                print ("FEMB_CONFIG--> Check ADC ASIC SPI")
            adcasic_rb_regs = []
            for regNum in range(self.REG_ADCSPI_RDBACK_BASE,self.REG_ADCSPI_RDBACK_BASE+len(Adcasic_regs),1):
                val = self.femb.read_reg ( regNum, board) 
                if (val != None):
                    adcasic_rb_regs.append( val & 0x0000FFFF)

            if (adcasic_rb_regs !=Adcasic_regs  ) :
                print ("FEMB_CONFIG--> Something went wrong when programming the ADC SPI.  Let's try again.")
                if ( k == 9 ):
                    print ("FEMB_CONFIG--> Readback Regs")
                    print (adcasic_rb_regs)
                    print ("FEMB_CONFIG--> Desired Regs")
                    print (Adcasic_regs)
                    sys.exit("FEMB_CONFIG--> femb_config_femb : Wrong readback. ADC SPI failed")
                    return
            else: 
                if (output != "suppress"):
                    print ("FEMB_CONFIG--> ADC ASIC SPI is OK")
                if (output != "first"):
                    if (self.sbnd.femb_config.testUnsync(adcNum) == 0):
                        print ("FEMB_CONFIG--> ADC synced after SPI write!")
                        self.adc_reg.info.adc_regs_sent = adcasic_rb_regs
                        break
                    else:
                        print ("FEMB_CONFIG--> ADC not synced after SPI write!")
                else:
                    self.adc_reg.info.adc_regs_sent = adcasic_rb_regs
            break
                


#        self.syncADC([0,1,2,3])
#        self.adc_reg.info.adc_chip_status(2, status = "sent")


    def configFeAsic(self, output = "ok", board = "femb"):
        feasic_regs = self.fe_reg.REGS
        if (output != "suppress"):
            print ("FEMB_CONFIG--> Config FE ASIC SPI")
        for k in range(10):
            i = 0
            for regNum in range(self.REG_FESPI_BASE,self.REG_FESPI_BASE+len(feasic_regs),1):
                self.femb.write_reg( regNum, feasic_regs[i], board)
                i = i + 1
            #Write FE ASIC SPI
            if (output != "suppress"):
                print ("FEMB_CONFIG--> Program FE ASIC SPI")
            self.femb.write_reg( self.REG_ASIC_SPIPROG, 2, board)
            time.sleep(.1)
            self.femb.write_reg( self.REG_ASIC_SPIPROG, 2, board)
            time.sleep(.1)

            if (output != "suppress"):
                print ("FEMB_CONFIG--> Check FE ASIC SPI")
            feasic_rb_regs = []
            for regNum in range(self.REG_FESPI_RDBACK_BASE,self.REG_FESPI_RDBACK_BASE+len(feasic_regs),1):
                val = self.femb.read_reg( regNum, board) 
                time.sleep(.001)
                if (val != None):
                    feasic_rb_regs.append( val & 0x0000FFFF )

            if (feasic_rb_regs !=feasic_regs  ) :
                print ("FEMB_CONFIG--> Something went wrong when programming the FE SPI.  Let's try again.")
                print ("FEMB_CONFIG--> Readback Regs")
                print (feasic_rb_regs)
                print ("FEMB_CONFIG--> Desired Regs")
                print (feasic_regs)
                if ( k == 9 ):
                    print ("FEMB_CONFIG--> Readback Regs")
                    print (feasic_rb_regs)
                    print ("FEMB_CONFIG--> Desired Regs")
                    print (feasic_regs)
                    sys.exit("FEMB_CONFIG--> femb_config_femb : Wrong readback. FE SPI failed")
                    return
            else: 
                if (output != "suppress"):
                    print ("FEMB_CONFIG--> FE ASIC SPI is OK")
#                for fe in feasic_rb_regs:
#                    print (hex(fe))
                self.fe_reg.info.fe_regs_sent = feasic_rb_regs
                break
            
#        self.fe_reg.info.fe_chip_status(2, status = "sent")

    def syncADC(self, chips):
        
        #turn on ADC test mode.  This assumes the chips were written to go into test mode with this method
        print ("FEMB_CONFIG--> Start sync ADC")
        reg3 = self.femb.read_reg(3, board = "femb")
        newReg3 = ( reg3 | 0x80000000 )
        
        #The first two values control the coarse values of the read clock
        #Registers 21-23 control the fine values of the read clock
        #Registers 24-26 control the fine values of the write clock
        self.REG_LATCHLOC1_4_data = self.femb.read_reg( self.REG_LATCHLOC1_4, board = "femb" )
        self.REG_CLKPHASE_data    = self.femb.read_reg( self.REG_CLKPHASE, board = "femb" )
        self.reg21                = self.femb.read_reg( 21, board = "femb" )
        self.reg22                = self.femb.read_reg( 22, board = "femb" )
        self.reg23                = self.femb.read_reg( 23, board = "femb" )
        print ("FEMB_CONFIG--> Latch latency " + str(hex(self.REG_LATCHLOC1_4_data)))
        print ("FEMB_CONFIG--> Clock Phase " + str(hex(self.REG_CLKPHASE_data)))
        print ("FEMB_CONFIG--> Read Control 1 (Reg 21) " + str(hex(self.reg21)))
        print ("FEMB_CONFIG--> Read Control 2 (Reg 22) " + str(hex(self.reg22)))
        print ("FEMB_CONFIG--> Read Control 3 (Reg 23) " + str(hex(self.reg23)))
        
#        file_rec = "C:\\Users\\vlsilab2\\Desktop\\sync_log.txt"
#        screendisplay = sys.stdout
#        sys.stdout = open(file_rec, "w")
        
        for a in chips:
            print ("FEMB_CONFIG--> Test ADC " + str(a))
            unsync = self.testUnsync(a)
            if unsync != 0:
                print ("FEMB_CONFIG--> ADC {} not synced, try to fix".format(a))
                self.fixUnsync(a)
            elif (unsync == 0):
                print ("FEMB_CONFIG--> ADC {} synced!".format(a))
        self.REG_LATCHLOC1_4_data = self.femb.read_reg( self.REG_LATCHLOC1_4, board = "femb" ) 
        self.REG_CLKPHASE_data    = self.femb.read_reg( self.REG_CLKPHASE, board = "femb" )
        self.reg21                = self.femb.read_reg( 21, board = "femb" )
        self.reg22                = self.femb.read_reg( 22, board = "femb" )
        self.reg23                = self.femb.read_reg( 23, board = "femb" )
        
        self.femb.write_reg( 3, newReg3, board = "femb") #31 - enable ADC test pattern
        print ("FEMB_CONFIG--> Final Check!")
        for a in chips:
            print ("FEMB_CONFIG--> Test ADC " + str(a))
            unsync = self.testUnsync_old(a)
            if unsync != 0:
                print ("FEMB_CONFIG--> ADC {} not synced, try to fix".format(a))
                self.fixUnsync(a)
            elif (unsync == 0):
                print ("FEMB_CONFIG--> ADC {} synced!".format(a))
                
#        sys.stdout.close()
#        sys.stdout = screendisplay
        print ("FEMB_CONFIG--> Latch latency " + str(hex(self.REG_LATCHLOC1_4_data)))
        print ("FEMB_CONFIG--> Clock Phase " + str(hex(self.REG_CLKPHASE_data)))
        print ("FEMB_CONFIG--> Read Control 1 (Reg 21) " + str(hex(self.reg21)))
        print ("FEMB_CONFIG--> Read Control 2 (Reg 22) " + str(hex(self.reg22)))
        print ("FEMB_CONFIG--> Read Control 3 (Reg 23) " + str(hex(self.reg23)))
        self.femb.write_reg( 3, (reg3&0x7fffffff), board = "femb" )
        print ("FEMB_CONFIG--> End sync ADC")

    def testUnsync_old(self, chip, output = "ok"):        
        adcNum = int(chip)
        if (adcNum < 0 ) or (adcNum > 3 ):
                print ("FEMB_CONFIG--> femb_config_femb : testLink - invalid asic number")
                return

        #loop through channels, check test pattern against data
        #When I was using the longer cable, I was doing some in depth debugging, so that's where some of the
        #remnants of other stuff comes from
        badSync = 0
        for ch in range(0,16,1):
            for test in range(10):
                data = self.get_data_chipXchnX(chip = chip, chn = ch, packets = 1)
                if (len(data) == 0):
                    print ("FEMB_CONFIG--> Sync response bad.  Exiting...")
                    return 1
                for samp in range(len(data)):
                    if data[samp] != self.ADC_TESTPATTERN[ch]:
                        badSync = 1 
                        if (output != "suppress"):
                            print ("FEMB_CONFIG--> Chip {} chn {} looking for {} but found {} on {}".format(
                                    chip, ch, hex(self.ADC_TESTPATTERN[ch]), hex(data[samp]), samp))

#                        if ((ch != 0)):
#                            data = self.femb.get_data_packets(ip = settings.CHIP_IP[chip], data_type = "int", num = 1, header = False)
#                            for ok in range(20):
#                                print (hex(data[ok]))
                                
#                            self.analyze.UnpackData(path = "data", data = data)
#                        data1 = self.femb.get_data_packets(ip = settings.CHIP_IP[adcNum], 
#                                                               data_type = "int", num = 1, header = False)
#                        print ("Chip {}".format(adcNum))
#                        self.analyze.UnpackData(path = "data", data = data1)
#                    else:
#                        if (((test % 75) == 0) and ((samp % 500) == 0)) :
#                            print (test)
#                            print (samp)
#                            print ("FEMB_CONFIG--> Looking for {} and finding {}!".format(hex(self.ADC_TESTPATTERN[ch]), hex(data[samp])))
                    if badSync == 1:
                            break
                #print("time after checking the sample {}".format(time.time()))
                if badSync == 1:
                    break
            #print("time after checking 100 samples {}".format(time.time()))
            if badSync == 1:
                break
        return badSync
    
    def manualCheck(self,chip):
        data = self.femb.get_data_packets(ip = settings.CHIP_IP[int(chip)], 
            data_type = "int", num = 5, header = False)
        print ("Chip {}".format(chip))
        self.analyze.UnpackData(path = "data", data = data)
        plt.show()
        
        answer = input("Is this ok?")
        if (answer == "y"):
            return 0
        else:
            return 1
    
    def testUnsync(self, chip):
        adcNum = int(chip)
        if (adcNum < 0 ) or (adcNum > 3 ):
            print ("FEMB_CONFIG--> femb_config_femb : testLink - invalid asic number")
            return
        
        badSync = 0
        self.femb.write_reg(31, 1, board = "femb")
        time.sleep(0.1)
        self.femb.write_reg(31, 0, board = "femb")
        
        for test in range(10):
            if (test > 8):
                badSync = 1
                break
            
            time.sleep(0.1)
            conv_error = self.femb.read_reg(32 + (2 * adcNum), board = "femb")
            head_error = self.femb.read_reg(33 + (2 * adcNum), board = "femb")
            
            if ((conv_error != 0) or (head_error != 0)):
                print ("Chip {} had {} conv errors!".format(chip, conv_error))
                print ("Chip {} had {} head errors!".format(chip, head_error))
                self.femb.write_reg(31, 1, board = "femb")
                time.sleep(0.1)
                self.femb.write_reg(31, 0, board = "femb")
            else:
                break
        return badSync

#This is the heart of the debugging I was doing with the long cable, so it gets very verbose
    def fixUnsync(self, adc):
        
#These initial settings choose the min and max of the 3 loops that will happen, and what the step for the fine settings will be
#It'll loop through the coarse read, fine read, and fine write clocks according to these parameters
        if (settings.long_cable == True):
            minimum1 = settings.cold_min1
            maximum1 = settings.cold_max1
            steps1   = settings.cold_step1
            latch_down = 0
            latch_up = 1
        else:
            minimum1 = [-32,-32,-32,-32]
            maximum1 = [32,32,32,32]
            steps1   = [4,4,4,4]
            minimum2 = [0,0,0,0]
            maximum2 = [32,32,32,32]
            steps2   = [36,36,36,36]
            minimum_latch = [0x05,0x05,0x05,0x05]
            maximum_latch = [0x08,0x08,0x08,0x08]
            steps_latch   = [1,1,1,1]
#            latch_down = 1
#            latch_up = 2
        
        adcNum = int(adc)
        if (adcNum < 0 ) or (adcNum > 3 ):
                print ("FEMB_CONFIG--> femb_config_femb : testLink - invalid asic number")
                return
#First it finds the initial settings to reference those
        initLATCH1_4 = self.femb.read_reg( self.REG_LATCHLOC1_4, board = "femb" )

        if (adcNum == 0):
            initPLL_read = self.femb.read_reg( 21, board = "femb" )
            initPLL_write = self.femb.read_reg( 24, board = "femb" )
        elif (adcNum == 1):
            initPLL_read = self.femb.read_reg( 21, board = "femb" )
            initPLL_write = self.femb.read_reg( 24, board = "femb" )
        elif (adcNum == 2):
            initPLL_read = self.femb.read_reg( 22, board = "femb" )
            initPLL_write = self.femb.read_reg( 25, board = "femb" )
        elif (adcNum == 3):
            initPLL_read = self.femb.read_reg( 22, board = "femb" )
            initPLL_write = self.femb.read_reg( 25, board = "femb" )
            
        initPLL_read2 = self.femb.read_reg( 23, board = "femb" )
        initPLL_write2 = self.femb.read_reg( 26, board = "femb" )
        
#Since this register has the settings for all 4 chips, it isolates the value for the chip you want to test
        initSetting = (initLATCH1_4 & (0xFF << (8 * adcNum))) >> (8 * adcNum)
                      
        print ("FEMB_CONFIG--> Initial Read PLL is {}".format(hex(initPLL_read)))
        print ("FEMB_CONFIG--> Initial Latch is {}".format(hex(initLATCH1_4)))
        print ("FEMB_CONFIG--> First testing around the initial setting of {}".format(hex(initSetting)))
        print ("FEMB_CONFIG--> initPLL_read2 is {}".format(hex(initPLL_read2)))
        print ("FEMB_CONFIG--> Initial Write PLL is {}".format(hex(initPLL_write)))
        print ("FEMB_CONFIG--> initPLL_write2 is {}".format(hex(initPLL_write2)))
		
        for shift in range(minimum_latch[adcNum], maximum_latch[adcNum] + 1, steps_latch[adcNum]):
            
#Does bitwise math so that when you increment coarse read clock, you change the right part of that shared register
            shiftMask = (0x3F << 8*adcNum)
            testShift = ( (initLATCH1_4 & ~(shiftMask)) | (shift << 8*adcNum) )
            self.femb.write_reg( self.REG_LATCHLOC1_4, testShift, board = "femb" )
  
#For the fine shifts, for example, the upper half of register 21 is for Chip 1, and the lower half is for Chip 0
#So we need to do bitwise math again.  Also, the register 21 only gives the absolute value of what you want to write
#Register 23 gives the negative sign.  I know it's confusing, it's how the FPGA PLL does it.
            for PLL_read in range(minimum1[adcNum], maximum1[adcNum], steps1[adcNum]):
                absolute = abs(PLL_read)
                if (adcNum == 0):
                    self.femb.write_reg( 21, (initPLL_read & 0xFFFF0000) + absolute, board = "femb" )
                    if (PLL_read > 0):
                        pll2 = initPLL_read2 & 0x000E0000
                    else:
                        pll2 = (initPLL_read2 | 0x00010000) & 0x7FFFFFF
#                    print ("Init PLL is {}, adjusted PLL is {} and adding {} to it gives {}".format(hex(initPLL),
#                       hex(initPLL & 0xFFFF0000), hex(PLL), hex((initPLL & 0xFFFF0000) + PLL)))
                elif (adcNum == 1):
                    self.femb.write_reg( 21, (initPLL_read & 0xFFFF) + (absolute << 16), board = "femb" )
                    if (PLL_read > 0):
                        pll2 = initPLL_read2 & 0x000D0000
                    else:
                        pll2 = (initPLL_read2 | 0x00020000) & 0x7FFFFFF
#                    print ("Init PLL is {}, adjusted PLL is {} and adding {} to it gives {}".format(hex(initPLL),
#                       hex(initPLL & 0xFFFF), hex(PLL << 16), hex((initPLL & 0xFFFF) + (PLL << 16))))
                elif (adcNum == 2):
                    self.femb.write_reg( 22, (initPLL_read & 0xFFFF0000) + absolute, board = "femb" )
                    if (PLL_read > 0):
                        pll2 = initPLL_read2 & 0x000B0000
                    else:
                        pll2 = (initPLL_read2 | 0x00040000) & 0x7FFFFFF
#                    print ("Init PLL is {}, adjusted PLL is {} and adding {} to it gives {}".format(hex(initPLL),
#                       hex(initPLL & 0xFFFF0000), hex(PLL), hex((initPLL & 0xFFFF0000) + PLL)))
                elif (adcNum == 3):
                    self.femb.write_reg( 22, (initPLL_read & 0xFFFF) + (absolute << 16), board = "femb" )
                    if (PLL_read > 0):
                        pll2 = initPLL_read2 & 0x00070000
                    else:
                        pll2 = (initPLL_read2 | 0x00080000) & 0x7FFFFFF
#                    print ("Init PLL is {}, adjusted PLL is {} and adding {} to it gives {}".format(hex(initPLL),
#                       hex(initPLL & 0xFFFF), hex(PLL << 16), hex((initPLL & 0xFFFF) + (PLL << 16))))

                
                self.femb.write_reg ( 23, pll2, "femb")
                self.femb.write_reg ( 23, 0x80000000 + pll2, "femb")
                
#This part is because of weird things the long cable was doing (changing the above settings would sometimes
#cause SPI write failures.)
#                    self.femb.write_reg ( self.REG_ASIC_RESET, 1, "femb")
#                    time.sleep(0.05)
#                    screendisplay = sys.stdout
#                    sys.stdout = None
#                    self.configAdcAsic()
#                    sys.stdout = screendisplay
#                    time.sleep(0.05)
                for PLL_write in range(minimum2[adcNum], maximum2[adcNum], steps2[adcNum]):
                    absolute = abs(PLL_write)
                    if (adcNum == 0):
                        self.femb.write_reg( 24, (initPLL_write & 0xFFFF0000) + absolute, board = "femb" )
                        if (PLL_write > 0):
                            pll2 = initPLL_write2 & 0x000E0000
                        else:
                            pll2 = (initPLL_write2 | 0x00010000) & 0x7FFFFFF
    #                    print ("Init PLL is {}, adjusted PLL is {} and adding {} to it gives {}".format(hex(initPLL),
    #                       hex(initPLL & 0xFFFF0000), hex(PLL), hex((initPLL & 0xFFFF0000) + PLL)))
                    elif (adcNum == 1):
                        self.femb.write_reg( 24, (initPLL_write & 0xFFFF) + (absolute << 16), board = "femb" )
                        if (PLL_write > 0):
                            pll2 = initPLL_write2 & 0x000D0000
                        else:
                            pll2 = (initPLL_write2 | 0x00020000) & 0x7FFFFFF
    #                    print ("Init PLL is {}, adjusted PLL is {} and adding {} to it gives {}".format(hex(initPLL),
    #                       hex(initPLL & 0xFFFF), hex(PLL << 16), hex((initPLL & 0xFFFF) + (PLL << 16))))
                    elif (adcNum == 2):
                        self.femb.write_reg( 25, (initPLL_write & 0xFFFF0000) + absolute, board = "femb" )
                        if (PLL_write > 0):
                            pll2 = initPLL_write2 & 0x000B0000
                        else:
                            pll2 = (initPLL_write2 | 0x00040000) & 0x7FFFFFF
    #                    print ("Init PLL is {}, adjusted PLL is {} and adding {} to it gives {}".format(hex(initPLL),
    #                       hex(initPLL & 0xFFFF0000), hex(PLL), hex((initPLL & 0xFFFF0000) + PLL)))
                    elif (adcNum == 3):
                        self.femb.write_reg( 25, (initPLL_write & 0xFFFF) + (absolute << 16), board = "femb" )
                        if (PLL_write > 0):
                            pll2 = initPLL_write2 & 0x00070000
                        else:
                            pll2 = (initPLL_write2 | 0x00080000) & 0x7FFFFFF
    #                    print ("Init PLL is {}, adjusted PLL is {} and adding {} to it gives {}".format(hex(initPLL),
    #                       hex(initPLL & 0xFFFF), hex(PLL << 16), hex((initPLL & 0xFFFF) + (PLL << 16))))
    
                    
                    self.femb.write_reg ( 26, pll2, "femb")
                    self.femb.write_reg ( 26, 0x80000000 + pll2, "femb")
    
    #Ok, we've finally written everything for the test.  Now I keep track of it to print each one as a sanity check
                    reg21 = self.femb.read_reg( 21, board = "femb" )
                    reg22 = self.femb.read_reg( 22, board = "femb" )
                    reg23 = self.femb.read_reg( 23, board = "femb" )
                    reg24 = self.femb.read_reg( 24, board = "femb" )
                    reg25 = self.femb.read_reg( 25, board = "femb" )
                    reg26 = self.femb.read_reg( 26, board = "femb" )
                    
                    print ("FEMB_CONFIG--> Latch latency " + str(hex(shift)))
                    print ("FEMB_CONFIG--> Read Control 1 (Reg 21) " + str(hex(reg21)))
                    print ("FEMB_CONFIG--> Read Control 2 (Reg 22) " + str(hex(reg22)))
                    print ("FEMB_CONFIG--> Read Control 3 (Reg 23) " + str(hex(reg23)))
                    print ("FEMB_CONFIG--> Write Control 1 (Reg 24) " + str(hex(reg24)))
                    print ("FEMB_CONFIG--> Write Control 2 (Reg 25) " + str(hex(reg25)))
                    print ("FEMB_CONFIG--> Write Control 3 (Reg 26) " + str(hex(reg26)))
#                    self.testUnsync(chip=adc)
                    
                    
#                    data = self.femb.get_data_packets(ip = settings.CHIP_IP[int(adc)], 
#                    data_type = "int", num = 5, header = False)
#                    print ("Chip {}".format(adc))
#                    self.analyze.UnpackData(path = "data", data = data)
#                    plt.show()
                    
                    unsync1 = self.testUnsync(adc)
                    unsync2 = self.testUnsync_old(adc)
                    unsync = unsync1 or unsync2
                    if unsync == 0 :
                        print ("FEMB_CONFIG--> ADC {} synchronized".format(adc))
                        self.REG_LATCHLOC1_4_data = testShift
                        self.reg23 = self.femb.read_reg( 23, board = "femb" )
                        self.reg26 = self.femb.read_reg( 26, board = "femb" )
                        if (adcNum == 0):
                            self.reg21 = self.femb.read_reg( 21, board = "femb" )
                            self.reg24 = self.femb.read_reg( 24, board = "femb" )
                        elif (adcNum == 1):
                            self.reg21 = ((self.femb.read_reg( 21, board = "femb" )) >> 16)
                            self.reg24 = ((self.femb.read_reg( 24, board = "femb" )) >> 16)
                        elif (adcNum == 2):
                            self.reg22 = self.femb.read_reg( 22, board = "femb" )
                            self.reg25 = self.femb.read_reg( 25, board = "femb" )
                        elif (adcNum == 3):
                            self.reg22 = ((self.femb.read_reg( 22, board = "femb" )) >> 16)
                            self.reg25 = ((self.femb.read_reg( 25, board = "femb" )) >> 16)
                        return

        #if program reaches here, sync has failed
        print ("FEMB_CONFIG--> ADC SYNC process failed for ADC # " + str(adc))
        print ("FEMB_CONFIG--> Just going to use default LATCH_LOC of {}".format(
                hex(self.REG_LATCHLOC1_4_data)))
        self.femb.write_reg( self.REG_LATCHLOC1_4, self.REG_LATCHLOC1_4_data, board = "femb" )
        
        if (adcNum == 0):
            self.femb.write_reg( 21, initPLL_read, board = "femb" )
            self.femb.write_reg( 24, initPLL_write, board = "femb" )
        elif (adcNum == 1):
            self.femb.write_reg( 21, initPLL_read, board = "femb" )
            self.femb.write_reg( 24, initPLL_write, board = "femb" )
        elif (adcNum == 2):
            self.femb.write_reg( 22, initPLL_read, board = "femb" )
            self.femb.write_reg( 25, initPLL_write, board = "femb" )
        elif (adcNum == 3):
            self.femb.write_reg( 22, initPLL_read, board = "femb" )
            self.femb.write_reg( 25, initPLL_write, board = "femb" )
            
        self.femb.write_reg( 23, initPLL_read2, board = "femb" )
        self.femb.write_reg( 26, initPLL_write2, board = "femb" )
        
    def optimize_offset(self, path, gain):
        #assume there's no pulses, just a regular baseline.  This finds out how to shift the ADC to find a baseline
        #That's away from stuck bits.  It cycles through, one upping the offset.  First it checks if the current
        #one gives an acceptable baseline.  If not, it writes the new offset in the register directory
        #Then if any were wrong in the whole loop, it writes the new values and looks again
        maximum = 5
        for offset in range(1,maximum,1):
            self.offset = offset - 1
            print ("Checking Offset {}".format(offset -1))
            bit = True
            for chip in range(settings.chip_num):
                self.chip = chip
#                self.adc_reg.info.adc_chip_status(chip, status = "sent")
#                data = self.femb.get_data_packets(ip = settings.CHIP_IP[chip], 
#                                                               data_type = "int", num = 25, header = False)
#                print ("Chip {}, cycle {}".format(chip, offset-1))
#                self.analyze.UnpackData(path = "data", data = data)
#                print ("Chip {}, cycle {}".format(chip, offset-1))
                for chn in range (16):
                    self.chn = chn
                    channel_data = self.get_data_chipXchnX(chip = chip, chn = chn, packets = 25)
                    np_data = np.array(channel_data)
                    datamean = np.mean(np_data)
                    std = np.std(np_data)
                    modulus = datamean % 64
                    mode = (stats.mstats.mode(np_data)[0][0] % 64)
#                    print("Chip {}, Chn{}, Mean is {}, Mod is {} and St Dev is {}".format(chip, chn, datamean, modulus, std))
                    
                    if (modulus < 3 or modulus > 62 or mode < 5 or mode > 60):
#                        print ("Too close to a stuck bit!")
                        print ("Chip {} Channel {} looks suspicious!".format(chip, chn))
                        bit = False
                        self.adc_reg.set_adc_chn(chip=chip, chn=chn, d=offset)
                        self.print_histogram(np_data = np_data, 
                                             path = path, 
                                             comment = "Mean of {} is too close to stuck bit multiple of 64 - {}".format(datamean, (datamean//64)*64),
                                             color = 'red',
                                             gain = gain
                                             )
                        
#                    if (std < 1.5 or std > 90):
##                        print ("Looks a little clumped or spread!")
#                        print ("Chip {} Channel {} looks suspicious!".format(chip, chn))
#                        bit = False
#                        self.adc_reg.set_adc_chn(chip=chip, chn=chn, d=offset)
#                        self.print_histogram(np_data = np_data, path = path, 
#                                             comment = "Standard deviation is {} bits!".format(std),
#                                             color = 'red', gain = gain)
                        
                    total_num = len(np_data)
                    low_range = datamean - (3*std)
                    high_range = datamean + (3*std)
                    num_within = 0
                    
                    for i in range(total_num):
                        if (np_data[i] > low_range) and (np_data[i] < high_range):
                            num_within += 1
                            
                    percentage = (float(num_within)/float(total_num))
                    
                    if (percentage < 0.970):
#                        print ("Doesn't look Gaussian!")
                        print ("Chip {} Channel {} looks suspicious!".format(chip, chn))
                        bit = False
                        self.adc_reg.set_adc_chn(chip=chip, chn=chn, d=offset)
                        self.print_histogram(np_data = np_data, path = path, 
                                             comment = "Only {}% of samples fall within 3 sigma!".format(percentage * 100),
                                             color = 'red', gain = gain)
                        
            if (bit == True):
                break
                        
            self.configAdcAsic(output = "suppress")
            
        for chip in range(settings.chip_num):
            self.chip = chip
            for chn in range (16):
                self.chn = chn
                channel_data = self.get_data_chipXchnX(chip = chip, chn = chn, packets = 25)
                np_data = np.array(channel_data)
                self.print_histogram(np_data = np_data, path = path, 
                                         comment = "Everything passes the test!", color = 'green', gain = gain)
            
    def print_histogram(self, np_data, path, comment, color, gain):
        folder = path + "Chip{}\\".format(self.chip)
        plot_path = folder + "Ch_" + str(self.chn) + "Off_" + str(self.offset)
        if (os.path.exists(folder) != True):
            try: 
                os.makedirs(folder)
            except OSError:
                if os.path.exists(folder):
                    raise
        
        std_np = []
        mean_np = []
    
    #Positioning for histogram text
        av_text = (.8,-.14)
        mode_text = (.8,-.19)
        std_text = (-.10,-.24)
        samples_text = (-.10,-.14)
        samples_within_text = (-.10,-.19)
        st_text = (.8,-.24)
        stuck_text = (.2,-.24)
        enc_text = (.2,-.19)
        datamean = np.mean(np_data)
        mean_np.append (datamean)
        std = np.std(np_data)
        std_np.append (std)
        mode = stats.mstats.mode(np_data)
        if (gain == 0):
            enc = std / 0.0025
        elif (gain == 1):
            enc = std / 0.008
        elif (gain == 2):
            enc = std / 0.0045
        elif (gain == 3):
            enc = std / 0.014
        total_num = len(np_data)
        
        low_range = datamean - (3*std)
        high_range = datamean + (3*std)

        num_within = 0

#As part of stuck bit check, finds the amount of samples within 3 sigma

        for i in range(total_num):
            if (np_data[i] > low_range) and (np_data[i] < high_range):
                num_within += 1
         
        maximum=max(np_data)
        minimum=min(np_data)

        bins = maximum - minimum
        if (bins < 1):
            bins = 1
        if (bins >100):
            bins = 100

        fig = plt.figure(figsize=(12,8))
        ax = fig.add_subplot(111)  
        ax.hist(np_data,bins=bins)
        ax.set_xlabel("ADC Counts")
        ax.set_ylabel("Occurences")
        ax.set_title("ADC Count Distribution for Chip "+str(self.chip+1)+", Channel "+str(self.chn) + ", Offset "+str(self.offset))
# Shrink current axis's height by 10% on the bottom
        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * 0.1,
        box.width, box.height * 0.9])
#Self explanatory, it takes the statistics found above and plots them in the designated place.  'axes fraction' lets you give the coordinates
#in terms of the axes, where 0 is one extreme and 1 is the other.  Without that, the coordinates would be in data format, which is harder to use

        ax.annotate("Average = "+str(round(datamean,2)), xy=av_text,  xycoords='axes fraction',
        xytext=av_text, textcoords='axes fraction',
        horizontalalignment='left', verticalalignment='left',
        )

        ax.annotate("Mode = "+str(int(mode[0][0])), xy=mode_text,  xycoords='axes fraction',
        xytext=mode_text, textcoords='axes fraction',
        horizontalalignment='left', verticalalignment='left',
        )

        ax.annotate("Standard deviation = "+str(round(std,2)), xy=std_text,  xycoords='axes fraction',
        xytext=std_text, textcoords='axes fraction',
        horizontalalignment='left', verticalalignment='left',
        )

        ax.annotate("Total samples = "+str(total_num), xy=samples_text,  xycoords='axes fraction',
        xytext=samples_text, textcoords='axes fraction',
        horizontalalignment='left', verticalalignment='left',
        )

        ax.annotate("Total samples in 3 sigma = "+str(num_within), xy=samples_within_text,  xycoords='axes fraction',
        xytext=samples_within_text, textcoords='axes fraction',
        horizontalalignment='left', verticalalignment='left',
        )

        ax.annotate("S/T Ratio = "+str(round(float(num_within)/float(total_num),6)), xy=st_text,  xycoords='axes fraction',
        xytext=st_text, textcoords='axes fraction',
        horizontalalignment='left', verticalalignment='left',
        )

        plt.annotate(comment, xy=stuck_text,  xycoords='axes fraction',
        xytext=stuck_text, textcoords='axes fraction',
        horizontalalignment='left', verticalalignment='left', color=color,
        )
        
        plt.annotate("Estimated ENC is {}".format(enc), xy=enc_text,  xycoords='axes fraction',
        xytext=enc_text, textcoords='axes fraction',
        horizontalalignment='left', verticalalignment='left', color='red',
        )
        
#        plt.show()
        fig.savefig (plot_path+".jpg")
        fig.clf()
        plt.close()
#        gc.collect()


    def get_data_chipXchnX(self, chip, chn, packets = 1):
        
        if (chip < 0 ) or (chip > settings.chip_num ):
            print ("FEMB CONFIG -> Error in get_data_chipXchnX: Chip must be between 0 and {}".format(self.chip_num))
            return
            
        if (chn < 0 ) or (chn > 15 ):
            print ("FEMB CONFIG -> Error in get_data_chipXchnX: Channel must be between 0 and 15")
            return
        k = 0
        done = False
        for i in range(10):
            
            data = self.femb.get_data_packets(ip = settings.CHIP_IP[chip], data_type = "int", num = packets, header = False)
            #Another remnant of the testing for the long cable.  This whole section should never be entered with
            #The short cable should never get into this, but I'll leave it in case
            try:
                if (k > 0):
                    print ("FEMB CONFIG --> Now doing another test")
                    print (hex(data[0]))
                    print (data[0] == 0xFACE)
                    print (data[0] != 0xFACE)
                if (data[0] != 0xFACE):
                    for j in range (13):
                        if (data[j] == 0xFACE):
                            data = data[j:]
                            done = True
                            break
                            
                    if (k > 8):
                        print ("FEMB CONFIG --> Error in get_data_chipXchnX: Packet format error")
                        print (hex(data[0]))
                        print (data)
                        return None
                    elif (done == True):
                        #print ("FEMB CONFIG --> BREAK!")
                        break
                    else:
                        print ("FEMB CONFIG --> Error in get_data_chipXchnX: Packet format error, trying again...")
                        print ("k = {}".format(k))
                        print (data[0:13])
                        print (hex(data[0]))
                        print (data[0] == 0xFACE)
                        k += 1
                else:
                    break
            except IndexError:
                print ("FEMB CONFIG --> Something was wrong with the incoming data")
                print (data)

        test_length = len(data)
        
#        if ((test_length % self.BPS) != 0):
#            print ("FEMB CONFIG -> Error in get_data_chipXchnX: Irregular packet size")
#            print (data)
#            return None
        
        full_samples = test_length // self.BPS
        chn_data = []
        
        #The incoming data shows all channels.  This will seperate it into the one channel requested
        
        for i in range (full_samples):
            if (chn == 7):
                chn_data.append(data[(self.BPS*i)+1] & 0x0FFF)
            if (chn == 6):
                chn_data.append(((data[(self.BPS*i)+2] & 0x00FF) << 4) + ((data[(self.BPS*i)+1] & 0xF000) >> 12))
            if (chn == 5):
                chn_data.append(((data[(self.BPS*i)+3] & 0x000F) << 8) + ((data[(self.BPS*i)+2] & 0xFF00) >> 8))
            if (chn == 4):
                chn_data.append(((data[(self.BPS*i)+3] & 0xFFF0) >> 4))
            if (chn == 3):
                chn_data.append(data[(self.BPS*i)+4] & 0x0FFF)
            if (chn == 2):
                chn_data.append(((data[(self.BPS*i)+5] & 0x00FF) << 4) + ((data[(self.BPS*i)+4] & 0xF000) >> 12))
            if (chn == 1):
                chn_data.append(((data[(self.BPS*i)+6] & 0x000F) << 8) + ((data[(self.BPS*i)+5] & 0xFF00) >> 8))
            if (chn == 0):
                chn_data.append(((data[(self.BPS*i)+6] & 0xFFF0) >> 4))
            if (chn == 15):
                chn_data.append(data[(self.BPS*i)+7] & 0x0FFF)
            if (chn == 14):
                chn_data.append(((data[(self.BPS*i)+8] & 0x00FF) << 4) + ((data[(self.BPS*i)+7] & 0xF000) >> 12))
            if (chn == 13):
                chn_data.append(((data[(self.BPS*i)+9] & 0x000F) << 8) + ((data[(self.BPS*i)+8] & 0xFF00) >> 8))
            if (chn == 12):
                chn_data.append(((data[(self.BPS*i)+9] & 0xFFF0) >> 4))
            if (chn == 11):
                chn_data.append(data[(self.BPS*i)+10] & 0x0FFF)
            if (chn == 10):
                chn_data.append(((data[(self.BPS*i)+11] & 0x00FF) << 4) + ((data[(self.BPS*i)+10] & 0xF000) >> 12))
            if (chn == 9):
                chn_data.append(((data[(self.BPS*i)+12] & 0x000F) << 8) + ((data[(self.BPS*i)+11] & 0xFF00) >> 8))
            if (chn == 8):
                chn_data.append(((data[(self.BPS*i)+12] & 0xFFF0) >> 4))
            
        return chn_data
    
    
        

    #__INIT__#
    def __init__(self):
        #declare board specific registers
        self.REG_RESET = 0
        self.REG_ASIC_RESET = 1
        self.REG_ASIC_SPIPROG = 2
        self.REG_SEL_ASIC = 7 
        self.REG_SEL_CH = 7
        self.REG_FESPI_BASE = 0x250
        self.REG_ADCSPI_BASE = 0x200
        self.REG_FESPI_RDBACK_BASE = 0x278
        self.REG_ADCSPI_RDBACK_BASE =0x228 
        self.REG_HS = 17
        self.REG_LATCHLOC1_4 = 4
        self.REG_CLKPHASE = 6
        self.REG_TEST_PULSE = 5
        self.REG_TEST_PULSE_FREQ = 500
        self.REG_TEST_PULSE_DLY = 80
        self.REG_TEST_PULSE_AMPL = 0 % 32
        self.REG_EN_CALI = 16
        self.ADC_TESTPATTERN = [0x12, 0x345, 0x678, 0xf1f, 0xad, 0xc01, 0x234, 0x567, 0x89d, 0xeca, 0xff0, 0x123, 0x456, 0x789, 0xabc, 0xdef]

        #initialize FEMB UDP object
        self.femb = FEMB_UDP()
        self.adc_reg = ADC_ASIC_REG_MAPPING()
        self.fe_reg = FE_ASIC_REG_MAPPING() 
        
        self.WIB_RESET = 1
        self.analyze = Data_Analysis()
        self.BPS = 13 #Bytes per sample
        
        self.analyze = Data_Analysis()
        