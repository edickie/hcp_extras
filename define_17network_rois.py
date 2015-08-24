#!/usr/bin/env python
"""
This tries to split a cifti map Yeo11 networks into many surface ROIs.

Usage:
  define_network_rois.py [options]

Options:
  -v,--verbose             Verbose logging
  --debug                  Debug logging in Erin's very verbose style
  -n,--dry-run             Dry run

DETAILS
Requires python enviroment with numpy and nibabel:
module load use.own datman/edickie

Requires HCP pipeline environment
module load FSL/5.0.7 freesurfer/5.3.0 connectome-workbench/1.1.1 hcp-pipelines/3.7.0

Work in progress

This should be run inside the directory that contains the map
"""
from docopt import docopt
import os
import subprocess
import numpy as np
import nibabel as nib
import tempfile
import os.path
import shutil

arguments       = docopt(__doc__)
VERBOSE         = arguments['--verbose']
DEBUG           = arguments['--debug']
DRYRUN          = arguments['--dry-run']

###


### Erin's little function for running things in the shell
def docmd(cmdlist):
    "sends a command (inputed as a list) to the shell"
    if DEBUG: print ' '.join(cmdlist)
    if not DRYRUN: subprocess.call(cmdlist)
#
# ####note I got the some of these settings from wb_command -file-information:
# wb_command -file-information fsaverage.Yeo2011_17Networks_N1000.32k_fs_LR.dlabel.nii
# Name:                    fsaverage.Yeo2011_17Networks_N1000.32k_fs_LR.dlabel.nii
# Type:                    Connectivity - Dense Label
# Structure:               CortexLeft CortexRight
# Data Size:               237.65 Kilobytes
# Maps to Surface:         true
# Maps to Volume:          false
# Maps with LabelTable:    true
# Maps with Palette:       false
# Number of Maps:          1
# Number of Rows:          59412
# Number of Columns:       1
# Volume Dim[0]:           0
# Volume Dim[1]:           0
# Volume Dim[2]:           0
# Palette Type:            None
# CIFTI Dim[0]:            1
# CIFTI Dim[1]:            59412
# ALONG_ROW map type:      LABELS
# ALONG_COLUMN map type:   BRAIN_MODELS
#     Has Volume Data:     false
#     CortexLeft:          29696 out of 32492 vertices
#     CortexRight:         29716 out of 32492 vertices
#
# Map   Map Name
#   1   fsaverage_Yeo2011_17Networks_N1000
#
# Label table for ALL maps
#        KEY   NAME                                 RED   GREEN    BLUE   ALPHA
#          0   ???                                1.000   1.000   1.000   0.000
#          1   L_FreeSurfer_Defined_Medial_Wall   0.004   0.004   0.004   1.000
#          2   L_17Networks_1                     0.471   0.071   0.525   1.000
#          3   L_17Networks_2                     1.000   0.000   0.000   1.000
#          4   L_17Networks_3                     0.275   0.510   0.706   1.000
#          5   L_17Networks_4                     0.165   0.800   0.643   1.000
#          6   L_17Networks_5                     0.290   0.608   0.235   1.000
#          7   L_17Networks_6                     0.000   0.463   0.055   1.000
#          8   L_17Networks_7                     0.769   0.227   0.980   1.000
#          9   L_17Networks_8                     1.000   0.596   0.835   1.000
#         10   L_17Networks_9                     0.863   0.973   0.643   1.000
#         11   L_17Networks_10                    0.478   0.529   0.196   1.000
#         12   L_17Networks_11                    0.467   0.549   0.690   1.000
#         13   L_17Networks_12                    0.902   0.580   0.133   1.000
#         14   L_17Networks_13                    0.529   0.196   0.290   1.000
#         15   L_17Networks_14                    0.047   0.188   1.000   1.000
#         16   L_17Networks_15                    0.000   0.000   0.510   1.000
#         17   L_17Networks_16                    1.000   1.000   0.000   1.000
#         18   L_17Networks_17                    0.804   0.243   0.306   1.000
#         19   R_FreeSurfer_Defined_Medial_Wall   0.004   0.004   0.004   1.000
#         20   R_17Networks_1                     0.471   0.071   0.525   1.000
#         21   R_17Networks_2                     1.000   0.000   0.000   1.000
#         22   R_17Networks_3                     0.275   0.510   0.706   1.000
#         23   R_17Networks_4                     0.165   0.800   0.643   1.000
#         24   R_17Networks_5                     0.290   0.608   0.235   1.000
#         25   R_17Networks_6                     0.000   0.463   0.055   1.000
#         26   R_17Networks_7                     0.769   0.227   0.980   1.000
#         27   R_17Networks_8                     1.000   0.596   0.835   1.000
#         28   R_17Networks_9                     0.863   0.973   0.643   1.000
#         29   R_17Networks_10                    0.478   0.529   0.196   1.000
#         30   R_17Networks_11                    0.467   0.549   0.690   1.000
#         31   R_17Networks_12                    0.902   0.580   0.133   1.000
#         32   R_17Networks_13                    0.529   0.196   0.290   1.000
#         33   R_17Networks_14                    0.047   0.188   1.000   1.000
#         34   R_17Networks_15                    0.000   0.000   0.510   1.000
#         35   R_17Networks_16                    1.000   1.000   0.000   1.000
#         36   R_17Networks_17                    0.804   0.243   0.306   1.000

## define name of dlabel map
dlabelmap = 'fsaverage.Yeo2011_17Networks_N1000.32k_fs_LR.dlabel.nii'
mapname = 'fsaverage_Yeo2011_17Networks_N1000'

surface_R = 'fsaverage.R.midthickness.32k_fs_LR.surf.gii'
surface_L = 'fsaverage.L.midthickness.32k_fs_LR.surf.gii'

## define interger map names for L and R hemisphere networks
networks={}
networksL = range(2,19)                                          #the keys for the left cortex networks on dlabel map
networksR = range(networksL[0]+networksL[-1],networksL[-1]*2+1)   #the keys for the right cortex networks on dlabel map
networkids = np.array(range(len(networksL))) + 1                        #the numeric ids of the networks -for the output file names

namebase = dlabelmap.replace('.dlabel.nii','')

cluster_maps=[]
for id in networkids:
    ## do the left one
    ## split into 14 separate maps
    #wb_command -cifti-label-to-roi dlabelmap -key <key> <output.dscalar.nii>
    dscalarL = namebase + '.' + str(id) + 'L.dscalar.nii'
    docmd(['wb_command', '-cifti-label-to-roi', dlabelmap, '-key', str(networksL[id-1]), dscalarL])
    ## do the right one
    dscalarR = namebase + '.' + str(id) + 'R.dscalar.nii'
    docmd(['wb_command', '-cifti-label-to-roi', dlabelmap, '-key', str(networksR[id-1]), dscalarR])
    ## merge left and right
    #wb_command -cifti-math '"left || right"' <ciftiLR> -var left <ciftiL> -var right <ciftiR>
    dscalarLR = namebase + '.' + str(id) + 'LR.dscalar.nii'
    docmd(['wb_command', '-cifti-math', '(left || right)', dscalarLR, \
        '-var', 'left', dscalarL, '-var', 'right', dscalarR])
    ## run clusterize on combined
    #wb_command -cifti-find-clusters <ciftiLR> <surface-value-threshold> <surface-minimum-area> <volume-value-threshold> <volume-minimum-size> COLUMN -left-surface <surface> -right-surface <surface> <cifti-out>
    clusterized = namebase + '.' + str(id) + 'LRroi.dscalar.nii'
    docmd(['wb_command', '-cifti-find-clusters', dscalarLR, \
    '0.5','1', '0.5', '1', 'COLUMN', \
    '-left-surface', surface_L, '-right-surface', surface_R, \
    clusterized])
    cluster_maps.append(clusterized)

## merge the final output into one dtseries.nii
#wb_command -cifti-merge <ciftiout> [-cifti <cifti-in>]...
clusters_out = namebase + '.ROI.dscalar.nii'
merge_cmd = ['wb_command', '-cifti-merge', clusters_out]
for map in cluster_maps:
    merge_cmd.append('-cifti')
    merge_cmd.append(map)
docmd(merge_cmd)

## step2 - mapping 17 networks back to 7...combining the maps from 17 networks back to 7 maps
## from my notes...to combined
sevennets = {}
sevennets[1] = [1,2]
sevennets[2] = [3,4]
sevennets[3] = [5,6]
sevennets[4] = [7,8]
sevennets[5] = [9,10]
sevennets[6] = [11,12,13]
sevennets[7] = [14,15,16,17]

numROIS = [0,2,2,2,2,2,6,6,8,2,2,3,7,7,2,4,9,4] ## taken from table below
# note added 0 to list above to indexing would work
 #  1     0.000     2.000   0.098        0.392        6.495        0.000         0   fsaverage_Yeo2011_17Networks_N1000
 #  2     0.000     2.000   0.085        0.366        5.667        0.000         0   fsaverage_Yeo2011_17Networks_N1000
 #  3     0.000     2.000   0.148        0.476        9.835        0.000         0   fsaverage_Yeo2011_17Networks_N1000
 #  4     0.000     2.000   0.123        0.436        8.236        0.000         0   fsaverage_Yeo2011_17Networks_N1000
 #  5     0.000     2.000   0.088        0.375        5.810        0.000         0   fsaverage_Yeo2011_17Networks_N1000
 #  6     0.000     6.000   0.135        0.643        5.386        0.000         0   fsaverage_Yeo2011_17Networks_N1000
 #  7     0.000     6.000   0.251        1.011        7.574        0.000         0   fsaverage_Yeo2011_17Networks_N1000
 #  8     0.000     8.000   0.246        1.184        5.053        0.000         0   fsaverage_Yeo2011_17Networks_N1000
 #  9     0.000     2.000   0.061        0.315        3.981        0.000         0   fsaverage_Yeo2011_17Networks_N1000
 # 10     0.000     2.000   0.050        0.284        3.376        0.000         0   fsaverage_Yeo2011_17Networks_N1000
 # 11     0.000     3.000   0.042        0.319        2.059        0.000         0   fsaverage_Yeo2011_17Networks_N1000
 # 12     0.000     7.000   0.204        0.945        5.327        0.000         0   fsaverage_Yeo2011_17Networks_N1000
 # 13     0.000     7.000   0.203        1.034        4.435        0.000         0   fsaverage_Yeo2011_17Networks_N1000
 # 14     0.000     2.000   0.052        0.294        3.395        0.000         0   fsaverage_Yeo2011_17Networks_N1000
 # 15     0.000     4.000   0.050        0.388        1.963        0.000         0   fsaverage_Yeo2011_17Networks_N1000
 # 16     0.000     9.000   0.346        1.368        8.010        0.000         0   fsaverage_Yeo2011_17Networks_N1000
 # 17     0.000     8.000   0.230        1.018        6.780        0.000         0   fsaverage_Yeo2011_17Networks_N1000

### add function to combine the ROIs (just add them..)

#mkdir a tmpdir for the
tmpdir = tempfile.mkdtemp()
outnamebase = 'fsaverage.Yeo2011_7Networksfrom17.32k_fs_LR'
maps = []
for network in sevennets.keys():
    numROI = numROIS[sevennets[network][0]]
    input1 = namebase + '.' + str(sevennets[network][0]) + 'LRroi.dscalar.nii'
    output = outnamebase + '.' + str(network) + 'LRroi.dscalar.nii'
    maps.append(output)
    for subnet in sevennets[network][1:]:
        input2 = namebase + '.' + str(subnet) + 'LRroi.dscalar.nii'
        tmpfile = os.path.join(tmpdir,'tmp'+str(subnet)+ 'LRroi.dscalar.nii')
        docmd(['wb_command', '-cifti-math', '(y+'+ str(numROI) + ')*(y > 0)',
                 tmpfile, '-var', 'y', input2])
        #wb_command -cifti-math '"left || right"' <ciftiLR> -var left <ciftiL> -var right <ciftiR>
        docmd(['wb_command', '-cifti-math', '(x + y)',
            output, '-var', 'x', input1, '-var', 'y', tmpfile])
        numROI = numROI + numROIS[subnet]
        input1 = output


clusters_out = outnamebase + '.ROI.dscalar.nii'
merge_cmd = ['wb_command', '-cifti-merge', clusters_out]
for thismap in maps:
    merge_cmd.append('-cifti')
    merge_cmd.append(thismap)
docmd(merge_cmd)

#get rid of the tmpdir
shutil.rmtree(tmpdir)
