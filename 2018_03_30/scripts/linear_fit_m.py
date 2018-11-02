# -*- coding: utf-8 -*-
"""
File Name: read_mean.py
Author: GSS
Mail: gao.hillhill@gmail.com
Description: 
Created Time: 3/9/2016 7:12:33 PM
Last modified: 10/12/2016 11:16:42 AM
"""

#defaut setting for scientific caculation
#import numpy
#import scipy
#from numpy import *
#import numpy as np
#import scipy as sp
#import pylab as pl
import traceback
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
import math
import copy
from scipy import stats
import sys
import warnings


####################################################################################################################################################
#Takes in the chip and channel for the error messages.  Takes in the y-data and the slope that will turn "DAC steps" into the
#desired unit.  Also takes in a variable that tells it whether to run for electrons (charge injection) or mv (which gives the
#estimated preamplifier voltage output at the time of sampling.  This requires the last parameter, gain.
def linear_fit(chip_id,chn_id, adc_np,vlt_slope): 
    np.set_printoptions(threshold=np.inf)
    units = []

    for i in (range(len(adc_np))):
#        units.append( vlt_slope * ( (i*(1.85E-13))/(1.60217646E-19) ) )
        units.append(vlt_slope * i * 185)
        
        
    valid_min = 3
    
    valid_max  = 11

#Create new x and y variables that are only in the valid range
    
    y = copy.deepcopy(adc_np[valid_min:valid_max])
#    for i in range(len(y)):
#        y[i] = int(y[i])

    x = copy.deepcopy(units[valid_min:valid_max])
#    for i in range(len(x)):
#        x[i] = int(x[i])
#because math.isnan(None) can't be evaluated
#    print (chip_id)
#    print (chn_id)
#    print (adc_np)
    for i in range(len(y)):
#        print (y[i] == None)
#        print (y[i])
#        print (isinstance(y[i], str))
#        print (math.isnan(y[i]))
        try:
            if (y[i] == None):
                y[i] = 0
            elif (isinstance(y[i], str)):
                y[i] = 0
            elif (math.isnan(y[i])):
                adc_np[i] = 0
                
        except TypeError:
            print ("linear_fit_m--> Error with number type")
            print (adc_np)
            print (i)
            print (adc_np[i])
            print (type(adc_np[i]))
            print (adc_np[i] == None)
            print (math.isnan(adc_np[i]))


        

#Do a linear analysis(we only want the slope and y-intercept).  The previous method didn't worth (OSE something...?) so I used
#The stats library

        try:
            slope, constant, r_value, p_value, std_err = stats.linregress(x,y)
        except:
            traceback.print_exc()
            slope = 0
            constant=0
    return slope,constant, adc_np, units
