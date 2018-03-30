from tabulate import tabulate
from scripts.fe_info import FE_INFO

class FE_ASIC_REG_MAPPING:
    
    def set_fe_chn(self, chip=0, chn=0, sts=-1, snc=-1, sg=-1, st=-1, smn=-1, sbf=-1, show = "FALSE"):
        
        
        #Check to make sure multiple monitors don't open together
        if (smn == 1):
            bottom_range = (3-chip)*9
            which_tuple = (9*(3-chip)) + 7 + ((chn//-2) + (chn % 2))

            for i in range(bottom_range,bottom_range+8,1):
                
                #Or else you wouldn't be able to change anything about a channel that already has the monitor open
                if (i == which_tuple):
                    if (chn % 2 == 0):
                        if ((self.REGS[i] & 0x00000002) > 0):
                             print ("ERROR: Do not try to open multiple monitors at the same time!")
                             print ("\n")
                             return
                    else:
                        if ((self.REGS[i] & 0x00000200) > 0):
                            print ("ERROR: Do not try to open multiple monitors at the same time!")
                            print ("\n")
                            return
                else:
                    #Check each tuple in the chip to see if the two channels' SMN bits are already high
                    if ((self.REGS[i] & 0x00000202) > 0):
                        print ("ERROR: Do not try to open multiple monitors at the same time!")
                        print ("\n")
                        return
                        
        #If a monitor is to be opened, check to make sure that SDACSW1 isn't already open
            global_index = ((4-chip)*9) -1
            if ((self.REGS[global_index] & 0x00000200) > 0):
                print ("ERROR: Do not open a monitor when the SDACSW1 switch is closed!")
                print ("\n")
                return
        
        #If you imagine all 36 tuples in self.REG lined up, these first few lines find which tuple and spot the given channel's settings are.
        # [0xFACEFACE] this is the tuple for chip 7, channel 14, channel 15, then chip 3, channel 14, channel 15 in order, 2 hex values each channel
        # [0xFACEFACE] this is the tuple for chip 7, channel 12, channel 13, then chip 3, channel 12, channel 13 in order, 2 hex values each channel
        # [0xFACEFACE] this is the tuple for chip 7, channel 10, channel 11, then chip 3, channel 10, channel 11 in order, 2 hex values each channel
        # etc
        #These lines find which two hex letters are for the given chip and channel
        
        spot = (18*(chip%4) + (chn + 2))

        tuple_num = 35 - (spot // 2)
        
        if (spot%2 == 0):

            if (chip < 4):
                bitshift = 8
                and_mask = 0xFFFF00FF
            else:
                bitshift = 24
                and_mask = 0x00FFFFFF
        else:

            if (chip < 4):
                bitshift = 0
                and_mask = 0xFFFFFF00
            else:
                bitshift = 16
                and_mask = 0xFF00FFFF
                
        #now we have bitmasks assigned for each position, so we can easily isolate the two hex letters we want
        
        find_mask = (0xFF << bitshift)
        existing_settings = ((self.REGS[tuple_num] & find_mask) >> bitshift)
        
        #now existing_settings is simply the two hex letters that already exist for this channel before anything has been done
        
        #if the bit is not being changed, we can just keep the existing settings
        if (sts != -1):
            sts_bit = ((sts&0x01)<<7)
        else:
            sts_bit = (existing_settings & 0x80)
            
        if (snc != -1):
            snc_bit = ((snc&0x01)<<6)
        else:
            snc_bit = (existing_settings & 0x40)
            
        if (sg != -1):
            sg_bit = ((sg&0x03)<<4)
        else:
            sg_bit = (existing_settings & 0x30)
            
        if (st != -1):
            st_bit = ((st&0x03)<<2)
        else:
            st_bit = (existing_settings & 0x0c)
            
        if (smn != -1):
            smn_bit = ((smn&0x01)<<1)
        else:
            smn_bit = (existing_settings & 0x02)
            
        if (sbf != -1):
            sbf_bit = ((sbf&0x01)<<0)
        else:
            sbf_bit = (existing_settings & 0x01)
            
        chn_reg = sts_bit + snc_bit + sg_bit + st_bit  + smn_bit + sbf_bit

        or_mask = (chn_reg << bitshift)

        self.REGS[tuple_num] = self.REGS[tuple_num] & (and_mask)
        
        self.REGS[tuple_num] = self.REGS[tuple_num] | (or_mask)

        self.register_printout(show)
        
        self.info.fe_regs_sw = self.REGS

####sec_chip_global only sets a chip global register, the other registers remains as before
    def set_fe_global(self, chip = 0, slk = -1, stb = -1, s16=-1, slkh=-1, sdc=-1, sdacsw2=-1, sdacsw1=-1, sdac=-1, show="FALSE"):
                  
                #Check to make sure multiple monitors don't open together
        if (sdacsw1 == 1):
            bottom_range = (3-chip)*9

            for i in range(bottom_range,bottom_range+8,1):

                #Check each tuple in the chip to see if the two channels' SMN bits are already high
                if ((self.REGS[i] & 0x00000202) > 0):
                    print ("ERROR: Do not close the SDACSW1 switch when monitors are open!")
                    print ("\n")
                    return

        tuple_num = (9*(4 - (chip % 4))) -1
        
        if (chip < 4):
            bitshift = 0
            and_mask = 0xFFFF0000
        else:
            bitshift = 16
            and_mask = 0x0000FFFF
                
        #now we have bitmasks assigned for each position, so we can easily isolate the two hex letters we want
        
        find_mask = (0xFFFF << bitshift)
        existing_settings = ((self.REGS[tuple_num] & find_mask) >> bitshift)
        
        if (sdac != -1):
            sdac_bit = (((sdac&0x01)//0x01)<<15)+(((sdac&0x02)//0x02)<<14)+\
                       (((sdac&0x04)//0x04)<<13)+(((sdac&0x08)//0x08)<<12)+\
                       (((sdac&0x10)//0x10)<<11)+(((sdac&0x20)//0x20)<<10)
        else:
            sdac_bit = (existing_settings & 0xfc00)
            
        if (sdacsw1 != -1):
            sdacsw1_bit = (((sdacsw1&0x01))<<9)
        else:
            sdacsw1_bit = (existing_settings & 0x0200)
            
        if (sdacsw2 != -1):
            sdacsw2_bit = (((sdacsw2&0x01))<<8)
        else:
            sdacsw2_bit = (existing_settings & 0x0100)
            
        if (sdc != -1):
            sdc_bit = (((sdc&0x01))<<5)
        else:
            sdc_bit = (existing_settings & 0x0020)
            
        if (slkh != -1):
            slkh_bit = ((slkh&0x01)<<4)
        else:
            slkh_bit = (existing_settings & 0x0010)
            
        if (s16 != -1):
            s16_bit = ((s16&0x01)<<3)
        else:
            s16_bit = (existing_settings & 0x0008)
            
        if (stb != -1):
            stb_bit = ((stb&0x03)<<1)
        else:
            stb_bit = (existing_settings & 0x0006)
            
        if (slk != -1):
            slk_bit = ((slk&0x01)<<0)
        else:
            slk_bit = (existing_settings & 0x0001)
            
        glo_reg = sdac_bit + sdacsw1_bit + sdacsw2_bit + sdc_bit + slkh_bit + s16_bit + stb_bit + slk_bit
        

        or_mask = (glo_reg << bitshift)

        self.REGS[tuple_num] = self.REGS[tuple_num] & (and_mask)
        
        self.REGS[tuple_num] = self.REGS[tuple_num] | (or_mask)

        self.register_printout(show)
        
        self.info.fe_regs_sw = self.REGS

####sec_chip sets registers of a whole chip, registers of the other chips remains as before
    def set_fe_chip(self, chip=0,
                 sts=0, snc=0, sg=0, st=0, smn=0, sbf=0,
                 slk=0, stb=0, s16=0, slkh=0, sdc=0, sdacsw2=0, sdacsw1=0, sdac=0, show="FALSE"):
        for chn in range(16):
            self.set_fe_chn(chip, chn, sts, snc, sg, st, smn, sbf)     

        self.set_fe_global (chip, slk, stb, s16, slkh, sdc, sdacsw2, sdacsw1, sdac)
        self.register_printout(show)

####sec_sbnd_board sets registers of a whole board 
    def set_fe_board(self, sts=0, snc=0, sg=0, st=0, smn=0, sbf=1, 
                       slk = 0, stb = 0, s16=0, slkh=0, sdc=0, sdacsw2=0, sdacsw1=0, sdac=0, show="FALSE"):
        for chip in range(4):
            self.set_fe_chip( chip, sts, snc, sg, st, smn, sbf, slk, stb, s16, slkh, sdc, sdacsw2, sdacsw1, sdac)
        self.register_printout(show)
            
    def register_printout(self,show):
        if ((show == "true") or (show == True)):
            print ("Front end registers are now (from LSB to MSB):")
            headers = ["Chip/Chn", "0", "1", "2", "3", ]
            registers=[["0", "0", "1", "2", "3",],
                       ["1", "0", "1", "2", "3",],
                       ["2", "0", "1", "2", "3",],
                       ["3", "0", "1", "2", "3",],
                       ["4", "0", "1", "2", "3",],
                       ["5", "0", "1", "2", "3",],
                       ["6", "0", "1", "2", "3",],
                       ["7", "0", "1", "2", "3",],
                       ["8", "0", "1", "2", "3",],
                       ["9", "0", "1", "2", "3",],
                       ["10", "0", "1", "2", "3",],
                       ["11", "0", "1", "2", "3",],
                       ["12", "0", "1", "2", "3",],
                       ["13", "0", "1", "2", "3",],
                       ["14", "0", "1", "2", "3",],
                       ["15", "0", "1", "2", "3",],
                       ["GLOBAL", "0", "1", "2", "3",],]
            

            reg_num = len(self.REGS)
            chip_opposite = 0
            for i in range(0,reg_num,1):
                if (i % 9 == 8):
                    chip_opposite = (i // 8)
                    registers[16][5-chip_opposite] = str(hex(self.REGS[i] & 0x0000FFFF).rstrip("L"))
                else:
                    lower_chn = -2 * (i-(chip_opposite*9)-7)
                    registers[lower_chn][4-chip_opposite] = str(hex((self.REGS[i] & 0x0000FF00)>>8).rstrip("L"))
                    registers[lower_chn + 1][4-chip_opposite] = str(hex(self.REGS[i] & 0x000000FF).rstrip("L"))
                
            print ("\n")
            print (tabulate(registers,headers,tablefmt="fancy_grid"))
            print ("\n")
        
    #__INIT__#
    def __init__(self):
	#declare board specific registers, only SNC is high by default
         self.REGS =[0x00008080, 0x00008080, 0x00008080, 0x00008080,
                     0x00008080, 0x00008080, 0x00008080, 0x00008080,
                     0x00000000,
                     0x00008080, 0x00008080, 0x00008080, 0x00008080,
                     0x00008080, 0x00008080, 0x00008080, 0x00008080,
                     0x00000000,
                     0x00008080, 0x00008080, 0x00008080, 0x00008080,
                     0x00008080, 0x00008080, 0x00008080, 0x00008080,
                     0x00000000,
                     0x00008080, 0x00008080, 0x00008080, 0x00008080,
                     0x00008080, 0x00008080, 0x00008080, 0x00008080,
                     0x00000000,
                     ]
         self.info = FE_INFO()