from tabulate import tabulate
from scripts.adc_info import ADC_INFO

class ADC_ASIC_REG_MAPPING:

####sec_chn_reg only sets a channel register, the other registers remains as before
    def set_adc_chn(self, chip=0, chn=0, d=-1, pcsr=-1, pdsr=-1, slp=-1, tstin=-1, show = "FALSE" ):
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
        if (d != -1):
            d_bit = (((d&0x01)//0x01)<<7)+(((d&0x02)//0x02)<<6)+(((d&0x04)//0x04)<<5)+(((d&0x08)//0x08)<<4)
        else:
            d_bit = (existing_settings & 0xF0)
            
        if (pcsr != -1):
            pcsr_bit = ((pcsr&0x01)<<3)
        else:
            pcsr_bit = (existing_settings & 0x08)
            
        if (pdsr != -1):
            pdsr_bit = ((pdsr&0x01)<<2)
        else:
            pdsr_bit = (existing_settings & 0x04)
            
        if (slp != -1):
            slp_bit = ((slp&0x01)<<1)
        else:
            slp_bit = (existing_settings & 0x02)
            
        if (tstin != -1):
            tstin_bit = ((tstin&0x01)<<0)
        else:
            tstin_bit = (existing_settings & 0x00)
            
            
        chn_reg = d_bit + pcsr_bit + pdsr_bit + slp_bit  + tstin_bit

        or_mask = (chn_reg << bitshift)
        
        self.REGS[tuple_num] = self.REGS[tuple_num] & (and_mask)
        self.REGS[tuple_num] = self.REGS[tuple_num] | (or_mask)

        self.register_printout(show)
        
        self.info.adc_regs_sw = self.REGS


####sec_chip_global only sets a chip global register, the other registers remains as before
    def set_adc_global(self, chip = 0,  clk = -1, frqc = -1, en_gr = -1, f0 = -1, f1 = -1, f2 = -1, f3 = -1,
                        f4 = -1, f5 = -1, slsb = -1, res4 = 0, res3 = 0, res2 = 0, res1 = 0, res0 = 0, show="FALSE"):
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
        
        if (clk != -1):
            clk_bit = ((clk&0x03)<<14)
        else:
            clk_bit = (existing_settings & 0xc000)
            
        if (frqc != -1):
            frqc_bit = ((frqc&0x01)<<13)
        else:
            frqc_bit = (existing_settings & 0x2000)
            
        if (en_gr != -1):
            en_gr_bit = ((en_gr&0x01)<<12)
        else:
            en_gr_bit = (existing_settings & 0x1000)
            
        if (f0 != -1):
            f0_bit = ((f0&0x01)<<11)
        else:
            f0_bit = (existing_settings & 0x0800)
            
        if (f1 != -1):
            f1_bit = ((f1&0x01)<<10)
        else:
            f1_bit = (existing_settings & 0x0400)
            
        if (f2 != -1):
            f2_bit = ((f2&0x01)<<9)
        else:
            f2_bit = (existing_settings & 0x0200)
            
        if (f3 != -1):
            f3_bit = ((f3&0x01)<<8)
        else:
            f3_bit = (existing_settings & 0x0100)
            
        if (f4 != -1):
            f4_bit = ((f4&0x01)<<7)
        else:
            f4_bit = (existing_settings & 0x0080)
            
        if (f5 != -1):
            f5_bit = ((f5&0x01)<<6)
        else:
            f5_bit = (existing_settings & 0x0040)
            
        if (slsb != -1):
            slsb_bit = ((slsb&0x01)<<5)
        else:
            slsb_bit = (existing_settings & 0x0020)
            
        glo_reg = clk_bit + frqc_bit + en_gr_bit + f0_bit + f1_bit + f2_bit + f3_bit + f4_bit + f5_bit + slsb_bit
        

        or_mask = (glo_reg << bitshift)

        self.REGS[tuple_num] = self.REGS[tuple_num] & (and_mask)
        
        self.REGS[tuple_num] = self.REGS[tuple_num] | (or_mask)

        self.register_printout(show)
        
        self.info.adc_regs_sw = self.REGS

####sec_chip sets registers of a whole chip, registers of the other chips remains as before
    def set_adc_chip(self, chip=0,
                 d=-1, pcsr=1, pdsr=1, slp=0, tstin=0,
                 clk = 0, frqc = 0, en_gr = 1, f0 = 0, f1 = 0, 
                 f2 = 0, f3 = 0, f4 = 0, f5 = 0, slsb = 0, show="FALSE"):
        for chn in range(16):
            self.set_adc_chn(chip, chn, d, pcsr, pdsr, slp, tstin )

        self.set_adc_global (chip, clk, frqc, en_gr, f0, f1, f2, f3, f4, f5, slsb)
        self.register_printout(show)

####sec_sbnd_board sets registers of a whole board 
    def set_adc_board(self,  
                 d=-1, pcsr=1, pdsr=1, slp=0, tstin=0,
                 clk = 0, frqc = 0, en_gr = 1, f0 = 0, f1 = 0, 
                 f2 = 0, f3 = 0, f4 = 0, f5 = 0, slsb = 0, show="FALSE"):
        for chip in range(4):
            self.set_adc_chip( chip, d, pcsr, pdsr, slp, tstin,
                 clk, frqc, en_gr, f0, f1, f2, f3, f4, f5, slsb)
        self.register_printout(show)
            
    def register_printout(self,show):
        if ((show == "true") or (show == True)):
            print ("ADC registers are now (from LSB to MSB):\n")
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
	#declare board specific registers
        self.REGS =[0x00000808, 0x00000808, 0x00000808, 0x00000808,
                    0x00000808, 0x00000808, 0x00000808, 0x00000808,
                    0x00001080,
                    0x00000808, 0x00000808, 0x00000808, 0x00000808,
                    0x00000808, 0x00000808, 0x00000808, 0x00000808,
                    0x00001080,
                    0x00000808, 0x00000808, 0x00000808, 0x00000808,
                    0x00000808, 0x00000808, 0x00000808, 0x00000808,
                    0x00001080,
                    0x00000808, 0x00000808, 0x00000808, 0x00000808,
                    0x00000808, 0x00000808, 0x00000808, 0x00000808,
                    0x00001080,
                    ]
        self.info = ADC_INFO()