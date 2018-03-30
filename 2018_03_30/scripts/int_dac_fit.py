# -*- coding: utf-8 -*-
"""
File Name: read_mean.py
Author: GSS
Mail: gao.hillhill@gmail.com
Description: 
Created Time: 3/9/2016 7:12:33 PM
Last modified: 9/8/2016 5:30:46 PM
"""

#defaut setting for scientific caculation
#import numpy
#import scipy
#from numpy import *
#import numpy as np
#import scipy as sp
#import pylab as pl

import openpyxl as px
import numpy as np
import statsmodels.api as sm
#import matplotlib.pyplot as plt

def int_dac_fit(env=0):
    a = []
    for i in range(65):
        a.append(i-1)
    dacbins = np.array(a)


    if ( env == 0 ): #RT
        amp = np.array( [0.01975,0.01983,0.02760,0.04568,0.06431,0.08245,0.10085,0.11904,
						0.13785,0.15660,0.17518,0.19370,0.21237,0.23150,0.24983,0.26810,
						0.28682,0.30541,0.32363,0.34195,0.36034,0.37939,0.39779,0.41622,
						0.43439,0.45262,0.47090,0.48962,0.50804,0.52642,0.54515,0.56423,
						0.58286,0.60096,0.61976,0.63800,0.65639,0.67502,0.69358,0.71216,
						0.73053,0.74855,0.76708,0.78539,0.80385,0.82212,0.84049,0.85873,
						0.87708,0.89574,0.91402,0.93286,0.95086,0.96883,0.98723,1.00600,
						1.02430,1.04260,1.06080,1.07960,1.09770,1.11680,1.13510,1.15370
                        ] )
    else: #LN2
        amp = np.array( [0.01047,0.01047,0.02385,0.04144,0.05955,0.07659,0.09475,0.11262,
						0.13126,0.14975,0.16835,0.18660,0.20440,0.22380,0.24138,0.25883,
						0.27744,0.29570,0.31347,0.33114,0.34935,0.36795,0.38607,0.40375,
						0.42161,0.43913,0.45717,0.47592,0.49395,0.51176,0.53037,0.54947,
						0.56784,0.58536,0.60405,0.62183,0.63980,0.65841,0.67677,0.69524,
						0.71296,0.73030,0.74857,0.76643,0.78436,0.80211,0.82000,0.83742,
						0.85564,0.87414,0.89119,0.91091,0.92838,0.94621,0.96419,0.98238,
						1.00000,1.01800,1.03560,1.05440,1.07230,1.09170,1.10960,1.12820
                        ] )
   


    cresults = sm.OLS(amp[3:65],sm.add_constant(dacbins[3:65])).fit()
    cslope = cresults.params[1]
    cconstant = cresults.params[0]
#    if ( env == 0 ):
#        with open ("./rt_dac_fit.txt","w") as f:
#            a = str(cresults.summary())
#            f.write(a)        
#    else:
#        with open ("./ln2_dac_fit.txt","w") as f:
#            a = str(cresults.summary())
#            f.write(a)        

    return cslope

#int_dac_fit(1)



