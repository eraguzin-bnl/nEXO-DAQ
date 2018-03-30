# -*- coding: utf-8 -*-
"""
Created on Fri Jun  2 11:50:17 2017

@author: vlsilab2
"""

import os
import struct
import matplotlib.pyplot as plt
import glob
import re
import sys
#from user_settings import user_editable_settings
#settings = user_editable_settings()



class Data_Analysis:
    
    def Seperate_Packets(self, path):
        
        self.screendisplay = sys.stdout
        sys.stdout = open(path + self.debug_file_name, "a+")

        
        search_path = [path + "*Chip0_Packet*.dat", path + "*Chip1_Packet*.dat", 
                       path + "*Chip2_Packet*.dat", path + "*Chip3_Packet*.dat"]


        new_path = path + "\Separated_Packets\\"
        try: 
            os.makedirs(new_path)
        except OSError:
            if os.path.exists(new_path):
                pass
            
        for the_file in os.listdir(new_path):
            file_path = os.path.join(new_path, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(e)
        
        print ("Separating packets in " + path + " for " + str(settings.chip_num) + " chips assuming that there's " +\
               str(settings.packets_per_file) + " packets to a file.  The new separated packets will be in " + new_path)
        
        numbers = re.compile(r'(\d+)')
        def numericalSort(value):
            parts = numbers.split(value)
            parts[1::2] = map(int, parts[1::2])
            return parts
        
        for i in range(settings.chip_num):
            packet_counter = 0
            relevant_files = sorted(glob.glob(search_path[i]), key=numericalSort)
            for infile in relevant_files:
                fileinfo  = os.stat(infile)
                filelength = fileinfo.st_size
                shorts = filelength/2

                each_packet = int(filelength / settings.packets_per_file)

                ideal_packet_indices = []
                for j in range(settings.packets_per_file):
                    ideal_packet_indices.append(each_packet * j)

                with open(infile, 'rb') as f:
                    raw_data = f.read(filelength)

                    f.close()
                    

                    
                full_data = struct.unpack_from(">%dH"%shorts,raw_data)

                if ((len(full_data)%(2*settings.packets_per_file)) != 0):
                    print ("WARNING: " + infile + " doesn't have a properly divisible file length")
                    
                
                real_packet_indices = []
                for m in re.finditer(self.start_of_packet, raw_data):
                    real_packet_indices.append(m.start())
                    
                    
                if (len(real_packet_indices) != settings.packets_per_file):
                    print ("WARNING: Found {} different chips in {} instead of the expected {}.".format(
                            real_packet_indices, infile, settings.packets_per_file))

                error = 0
                for j in range(len(real_packet_indices)):
                    
                    if ((ideal_packet_indices[j]) != (real_packet_indices[j])):
                        print ("WARNING: The beginning of Packet {} in {} is not where it should be!".format(j,infile))
                        
                        print ("It should be at {} but for some reason it's at {}.".format(hex(ideal_packet_indices[j]),
                                                hex(real_packet_indices[j])))
                        
                        data_fraction_test = []
                        
                        for k in range(len(real_packet_indices)):
                            if (k < (len(real_packet_indices) - 1)):
                                data_fraction_test.append(raw_data[real_packet_indices[k]:real_packet_indices[k+1]])
                            else:
                                data_fraction_test.append(raw_data[real_packet_indices[k]:])
                            
                        test_packet_indices = []
                        error = 1

                if (error == 1):
                    for k in range(len(data_fraction_test)):
                        for m in re.finditer(self.start_of_sample, data_fraction_test[k]):
                            test_packet_indices.append(m.start())
                            
                        print ("{} samples found for packet {} in {}".format(len(test_packet_indices), k, infile))
                        test_packet_indices = []
                            
                
                
                for j in range(len(real_packet_indices)):

                    if (j < (len(real_packet_indices) - 1)):
                        data_fraction = raw_data[real_packet_indices[j]:real_packet_indices[j+1]]
                    else:
                        data_fraction = raw_data[real_packet_indices[j]:]

                    
                    packet_number_bytes = data_fraction[8:12]
                    packet_number_int = struct.unpack_from(">1I",packet_number_bytes)

                    
                    filename = new_path + "Chip{}_Packet{}.dat".format(i,packet_number_int[0])
                    with open(filename,"wb") as f:
                        f.write(data_fraction) 
                        f.close()
                        
                packet_counter += 1
                if (packet_counter%self.notice1_every == 0):
                    sys.stdout.close()
                    sys.stdout = self.screendisplay
                    print ("Chip {}: {}/{} packet bundles separated".format(i, packet_counter, len(relevant_files)))
                    self.screendisplay = sys.stdout
                    sys.stdout = open(path + self.debug_file_name, "a+")
            sys.stdout.close()
            sys.stdout = self.screendisplay
            print ("Chip {} packet bundles fully separated".format(i))
            self.screendisplay = sys.stdout
            sys.stdout = open(path + self.debug_file_name, "a+")
        Data_Analysis.Missing_Packet_Check(self, new_path, 1)
        sys.stdout.close()
        sys.stdout = self.screendisplay
    
        return new_path
    
    def Missing_Packet_Check(self, path, packets_per_file):
        
        search_path = [path + "*Chip0_Packet*.dat", path + "*Chip1_Packet*.dat", 
                       path + "*Chip2_Packet*.dat", path + "*Chip3_Packet*.dat"]
        
        chip_specific_files = [[],[],[],[]]
        
        numbers = re.compile(r'(\d+)')
        def numericalSort(value):
            parts = numbers.split(value)
            parts[1::2] = map(int, parts[1::2])
            return parts
        
        for i in range(settings.chip_num):
            for infile in sorted(glob.glob(search_path[i]), key=numericalSort):
                chip_specific_files[i].append(infile)
            packets = (len(chip_specific_files[i]))
            packet_num_array = []
            count = 0
            for j in range(packets):
                filename = chip_specific_files[i][j]
                with open(filename, 'rb') as f:
                    raw_data = f.read(12)
                    f.close()
                packet_num_array.append(struct.unpack_from(">3I",raw_data)[2])
                count += 1
                if (count%self.notice2_every ==0):
                    sys.stdout.close()
                    sys.stdout = self.screendisplay
                    print ("Chip {}: {}/{} packets collected".format(i, count, packets))
                    self.screendisplay = sys.stdout
                    sys.stdout = open(path + self.debug_file_name, "a+")

            skips = 0
            
            sys.stdout.close()
            sys.stdout = self.screendisplay
            print ("Analyzing Chip {}".format(i))
            self.screendisplay = sys.stdout
            sys.stdout = open(path + self.debug_file_name, "a+")
            
            for k in range(len(packet_num_array) - 1):
                first_number = packet_num_array[k]
                second_number = packet_num_array[k+1]
                if (second_number != first_number + packets_per_file):
                    print ("Chip {} skips from packet {} to packet {}, index {} to {}"
                           .format(i, first_number, second_number, k, k+1))
                    skips += 1
            if (skips == 0):
                print ("No packet skips for Chip {}!".format(i))
            else:
                print ("Chip {} had {} packet skips".format(i, skips))
                
            sys.stdout.close()
            sys.stdout = self.screendisplay
            print ("Chip {} analyzed".format(i))
            self.screendisplay = sys.stdout
            sys.stdout = open(path + self.debug_file_name, "a+")

    def UnpackData(self, path = "default", data = None, return_data = False):
        
        print (data)

        if (path == "default"):
            fileinfo  = os.stat(data)
            filelength = fileinfo.st_size
        else:
            filelength = len(data)
            
        if (path == "default"):
            with open(data, 'rb') as f:
                raw_data = f.read(filelength)
                f.close()
            FACE_check = struct.unpack_from(">%dH"%(self.BPS + 8),raw_data)
        elif (path == "bytes"):
            FACE_check = struct.unpack_from(">%dH"%(self.BPS + 8),data)
            
        elif (path == "data"):
            FACE_check = data[:(self.BPS + 8)]
            
        else:
            print ("UnpackData--> Error: Specify which kind of unpacking you want to do")

        

        if (path == "default"):
            shorts = filelength/2
            full_data = struct.unpack_from(">%dH"%shorts,raw_data)
        elif (path == "bytes"):
            shorts = filelength/2
            full_data = struct.unpack_from(">%dH"%shorts,data)
        else:
            full_data = data

        start_of_packet = (b"\xde\xad\xbe\xef")
        start_of_chip = []
        for m in re.finditer(start_of_packet, raw_data):
            start_of_chip.append(m.start())
            
        print (start_of_chip)
        
        if (len(start_of_chip) > 4):
            print (start_of_chip[4])
            new_raw_data = raw_data[start_of_chip[4]:]
            with open(data,"wb") as f:
                f.write(new_raw_data) 
                f.close()

        
#__INIT__#
    def __init__(self):
        self.BPS = 13 #Bytes per sample.  The one for "0xFACE" and then 12 bytes for 16 channels at 12 bits each.
        self.channels = 16
        self.start_of_packet = (b"\xde\xad\xbe\xef")
        self.start_of_sample = (b"\xfa\xce")
        self.debug_file_name = "\Data_Analysis_Debug.txt"
        self.screendisplay = None
        self.notice1_every = 10000
        self.notice2_every = 50000
        
if __name__ == "__main__":
    for i in range(32):
        print (len(hex(i)))
        j = hex(i)[len(hex(i))-1]
        print (j)
        Data_Analysis().UnpackData(path = "default", 
                 data = "D:\\nEXO\\2017_11_15\\Calibration_warm_flange\\04.7mV_0.5us_200mV\\cali_intdac\\intdac_{}.dat".format(j))
    #Data_Analysis().UnpackData("D:\\nEXO\\2017_06_19\\" + "ped.dat")
    #Data_Analysis().Missing_Packet_Check("D:\\Eric\\Packets\\")
    #Data_Analysis().Seperate_Packets("D:\\Eric\\Packets\\", 4, 4)