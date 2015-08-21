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

####note I got the some of these settings from wb_command -file-information:
# wb_command -file-information fsaverage.Yeo2011_7Networks_N1000.32k_fs_LR.dlabel.nii
# ...
# Map   Map Name
#   1   fsaverage_Yeo2011_7Networks_N1000
#
# Label table for ALL maps
#        KEY   NAME                                 RED   GREEN    BLUE   ALPHA
#          0   ???                                1.000   1.000   1.000   0.000
#          1   L_FreeSurfer_Defined_Medial_Wall   0.004   0.004   0.004   1.000
#          2   L_7Networks_1                      0.471   0.071   0.525   1.000
#          3   L_7Networks_2                      0.275   0.510   0.706   1.000
#          4   L_7Networks_3                      0.000   0.463   0.055   1.000
#          5   L_7Networks_4                      0.769   0.227   0.980   1.000
#          6   L_7Networks_5                      0.863   0.973   0.643   1.000
#          7   L_7Networks_6                      0.902   0.580   0.133   1.000
#          8   L_7Networks_7                      0.804   0.243   0.306   1.000
#          9   R_FreeSurfer_Defined_Medial_Wall   0.004   0.004   0.004   1.000
#         10   R_7Networks_1                      0.471   0.071   0.525   1.000
#         11   R_7Networks_2                      0.275   0.510   0.706   1.000
#         12   R_7Networks_3                      0.000   0.463   0.055   1.000
#         13   R_7Networks_4                      0.769   0.227   0.980   1.000
#         14   R_7Networks_5                      0.863   0.973   0.643   1.000
#         15   R_7Networks_6                      0.902   0.580   0.133   1.000
#         16   R_7Networks_7                      0.804   0.243   0.306   1.000


## define name of dlabel map
dlabelmap = 'fsaverage.Yeo2011_7Networks_N1000.32k_fs_LR.dlabel.nii'
mapname = 'fsaverage_Yeo2011_7Networks_N1000'

surface_R = 'fsaverage.R.midthickness.32k_fs_LR.surf.gii'
surface_L = 'fsaverage.L.midthickness.32k_fs_LR.surf.gii'

## define interger map names for L and R hemisphere networks
networks={}
networksL = range(2,9)                                          #the keys for the left cortex networks on dlabel map
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
