#!/usr/bin/env python
"""
This looks for most correlated seeds within brain networks

Usage:
  get_func_jiggy.py [options] <input.dtseries.nii>

Arguments:
    <input.dtseries.nii>   Paths to directory containing .mnc images to align and mean

Options:
  -v,--verbose             Verbose logging
  --debug                  Debug logging in Erin's very verbose style
  -n,--dry-run             Dry run

DETAILS
Requires python enviroment with numpy and nibabel:
module load use.own datman/edickie

Requires HCP pipeline environment

Work in progress
"""
import numpy as np
import nibabel as nib

arguments       = docopt(__doc__)
inputfile           = arguments['<input.dtseries.nii>']
VERBOSE         = arguments['--verbose']
DEBUG           = arguments['--debug']
DRYRUN          = arguments['--dry-run']

###
img = nib.load(inputfile)
data = img.get_data()

## also read in template

## read in coordinates

##do cross correlation

##take submatrix by network name

## take median of max correlation values within each ROI within each network
