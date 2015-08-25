#!/usr/bin/env python
"""
This looks for most correlated seeds within brain networks

Usage:
  get_func_jiggy.py [options] <input.dtseries.nii> <ROItemplate.dscalar.nii>

Arguments:
    <input.dtseries.nii>        Paths to directory containing .mnc images to align and mean
    <ROItemplate.dscalar.nii>  Path to template for the ROIs of network regions
Options:
  -v,--verbose             Verbose logging
  --debug                  Debug logging in Erin's very verbose style
  -n,--dry-run             Dry run

DETAILS
Requires python enviroment with numpy and nibabel:
module load use.own datman/edickie

Requires HCP pipeline environment
module load FSL/5.0.7 freesurfer/5.3.0 connectome-workbench/1.1.1 hcp-pipelines/3.7.0

ROI template example:
/projects/edickie/code/templates/fsaverage.Yeo2011_7Networksfrom17.32k_fs_LR.ROI.dscalar.nii

inputfile example:
/projects/edickie/analysis/restcifti/SN110/MNINonLinear/Results/RSN/RSN_Atlas.dtseries.nii
Work in progress
"""
from docopt import docopt
import numpy as np
import nibabel as nib
import os
import subprocess

arguments       = docopt(__doc__)
inputfile       = arguments['<input.dtseries.nii>']
ROItemplate     = arguments['<ROItemplate.dscalar.nii>']
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
sub_dconn = inputfile.replace('.dtseries.nii','Z.dconn.nii')
if os.path.exists(sub_dconn)==False:
    '''
    if the dconn file does not exists - make  it with wb_command
    # wb_command -cifti-correlation -fisher-z <cifti-in> <cifti-out>
    '''
    docmd(['wb_command', '-cifti-correlation', '-fisher-z', inputfile, sub_dconn])

## read in the dconn file
img1 = nib.load(sub_dconn)
sub_corrmat = img1.get_data(img1)
sub_corrmat.shape()

## also read in template
img2 = nib.load(ROItemplate)
ROInet = img2.get_data(img2)
ROInet.shape()

##take submatrix by network name

## take median of max correlation values within each ROI within each network
