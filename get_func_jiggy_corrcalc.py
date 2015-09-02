#!/usr/bin/env python
"""
This looks for most correlated seeds within brain networks

Usage:
  get_func_jiggy.py [options] <input.dtseries.nii> <ROItemplate.dscalar.nii> <result.csv>

Arguments:
    <input.dtseries.nii>        Paths to directory containing .mnc images to align and mean
    <ROItemplate.dscalar.nii>   Path to template for the ROIs of network regions
    <result.csv>                Name (with full path to the csv of the found nodes)

Options:
  -v,--verbose             Verbose logging
  --debug                  Debug logging in Erin's very verbose style
  -n,--dry-run             Dry run
  -h,--help                Print help

DETAILS
Requires python enviroment with numpy and nibabel:
module load use.own datman/edickie

Requires HCP pipeline environment
module load FSL/5.0.7 freesurfer/5.3.0 connectome-workbench/1.1.1 hcp-pipelines/3.7.0

ROI template example:
ROItemplate='/projects/edickie/code/templates/fsaverage.Yeo2011_7Networksfrom17.32k_fs_LR.ROI.dscalar.nii'
fROItemplate='/projects/edickie/code/templates/fsaverage.Yeo2011_7Networksfrom17.32k_fs_LR.ROI_dscalarfake.nii'

inputfile example:
inputfile= '/projects/edickie/analysis/restcifti/SN110/MNINonLinear/Results/RSN/RSN_Atlas.dtseries.nii'
Work in progress
"""
from docopt import docopt
import numpy as np
import nibabel as nib
import os
import subprocess
import pandas as pd

arguments       = docopt(__doc__)
inputfile       = arguments['<input.dtseries.nii>']
ROItemplate     = arguments['<ROItemplate.dscalar.nii>']
resultsfile     = arguments['<result.csv>']
VERBOSE         = arguments['--verbose']
DEBUG           = arguments['--debug']
DRYRUN          = arguments['--dry-run']

###
### Erin's little function for running things in the shell
def docmd(cmdlist):
    "sends a command (inputed as a list) to the shell"
    if DEBUG: print ' '.join(cmdlist)
    if not DRYRUN: subprocess.call(cmdlist)

## use wm_commad to get the cross correlation - if not done
# sub_dconn = inputfile.replace('.dtseries.nii','Z.dconn.nii')
# if os.path.exists(sub_dconn)==False:
#     '''
#     if the dconn file does not exists - make  it with wb_command
#     # wb_command -cifti-correlation -fisher-z <cifti-in> <cifti-out>
#     '''
#     docmd(['wb_command', '-cifti-correlation', '-fisher-z', inputfile, sub_dconn])

## read in the dconn file
# img1 = nib.load(sub_dconn)
# sub_corrmat = img1.get_data()
# fc_df = pd.DataFrame(sub_corrmat[0,0,0,0,:,:])

## read in the dtseries file
img1 = nib.load(inputfile)
inputdata = img1.get_data()
input_df = pd.DataFrame(inputdata[0,0,0,0,:,:])

## also read in template
img2 = nib.load(ROItemplate)
ROInet = img2.get_data()
roi_df = pd.DataFrame(ROInet[0,0,0,0,:,:],index=range(1,ROInet.shape[4]+1))

##may need to export the mapping to get the ROItemplate and the dtseries files to match up..

cols = ['Network','ROI','cifti-index']
result = pd.DataFrame(columns = cols)
thisrow = 1
for network in roi_df.index.values.tolist():
    ### subset matrix to contain rows of only this Network
    network_idx = roi_df.loc[network,roi_df.loc[network,:]>0].index
    ### get a list of ROIs to within the network
    roi_list = roi_df.loc[network,network_idx].unique()
    for roi in roi_list:
        '''
        for each roi find its best vertex and add to table
        '''
        ### get the subarray that contains the ROI
        roi_idx = roi_df.loc[network,roi_df.loc[network,:]==roi].index
        ### calculate the maximal correlation at every vertex with this ROI
        max_indexes = []
        for other_roi in roi_list[roi_list != roi]:
            ## for combination of ROI and other_roi get the indices of the other roi that is most correlated with it
            oroi_idx = roi_df.loc[network,roi_df.loc[network,:]==other_roi].index

            roi_oroi_mat = fc_df.loc[roi_idx,oroi_idx]
            row_maxes = roi_oroi_mat.max(1)
            max_idx = int(row_maxes.loc[row_maxes==row_maxes.max()].index[0])
            max_indexes.append(max_idx)
        ### top picks are those ROIs are those vertices from each other ROI in the network with the highest correlation with it
        toppicks = fc_df.loc[roi_idx,max_indexes]
        ### caculate the median correlation from these top picks
        toppicks_median = toppicks.median(1)
        ### take the highest
        toppick = toppicks_median[toppicks_median==toppicks_median.max()].index[0]
        ### add a row to the result dataframe and fill in the cols
        result = result.append(pd.DataFrame(columns = cols, index = [thisrow]))
        result.Network[thisrow] = network
        result.ROI[thisrow] = int(roi)
        result['cifti-index'][thisrow] = toppick
        thisrow = thisrow + 1


## write the checklist out to a file
result.to_csv(resultsfile, sep=',', columns = cols, index = False)
