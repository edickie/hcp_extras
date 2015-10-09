#!/usr/bin/env python
"""
This maps results (generated in R from csv of aparc outputs) back onto the surface as a dscalar

Usage:
  map_aparc_results_to_surface.py [options] <results-csv> <resultcolname> <out-dscalar-nii>

Arguments:
  <results-csv>            A csv of the resutls from aprac (with header) ROIs. The ROI names shoud be the first column.
  <resultcolname>          The name (in the header) of the result to map to the surface.
  <out-dscalar-nii>        The name for the output file (should end in .dscalar.nii)

Options:
  -v,--verbose             Verbose logging
  --debug                  Debug logging in Erin's very verbose style
  -n,--dry-run             Dry run

DETAILS
Requires python enviroment with numpy and nibabel:
module load use.own datman/edickie

Requires HCP pipeline environment
module load connectome-workbench/1.1.1

Work in progress

This should be run inside the directory that contains the map
"""
from docopt import docopt
import numpy as np
import nibabel as nib
import os
import tempfile
import shutil
import subprocess
import pandas as pd

arguments       = docopt(__doc__)
resultcsv       = arguments['<results-csv>']
resultcolname   = arguments['<resultcolname>']
outdscalar      = arguments['<out-dscalar-nii>']
VERBOSE         = arguments['--verbose']
DEBUG           = arguments['--debug']
DRYRUN          = arguments['--dry-run']

###


### Erin's little function for running things in the shell
def docmd(cmdlist):
    "sends a command (inputed as a list) to the shell"
    if DEBUG: print ' '.join(cmdlist)
    if not DRYRUN: subprocess.call(cmdlist)

## make a tmpdir
tempdir = tempfile.mkdtemp()
####note I got the lut by taking the end of:
# wb_command -file-information wb_command -file-information fsaverage.aparc.164k_fs_LR.dlabel.nii
# resultcsv = '/projects/edickie/code/spins-1yr-analysis/freesurfer/ttestres_thickness_raw.csv'
# resultcolname = 'cohen.D'
# outdscalar = 'thinknessresults.dscalar.nii'
## define name of dlabel map
templatefolder = '/projects/edickie/code/templates/Yeo_JNeurophysiol11/hcp/fsaverage/MNINonLinear/fsaverage_LR32k'
dlabelmap = 'fsaverage.aparc.32k_fs_LR.dlabel.nii'
#dlabelmapnii = 'fsaverage.aparc.32k_fs_LR.dlabel.fake.nii'
dscalar_example = 'fsaverage.thickness.32k_fs_LR.dscalar.nii'
#dlabelROImap = 'fsaverage.aparc.32k_fs_LR.ROI.dscalar.nii'
mapname = 'fsaverage_aparc'
lookup_table = '/projects/edickie/code/hcp_extras/fsaverage.aparc.lut.txt'
os.chdir(templatefolder)

fakeniitemplate = os.path.join(tempdir, 'tmptemplate.nii')
fakeniiresutls = os.path.join(tempdir, 'tmpresults.nii')

docmd(['wb_command', '-cifti-convert', '-to-nifti', dlabelmap, fakeniitemplate])
# img1 = nib.load(dlabelROImap)
# dlabelsscalar = img1.get_data()
#
# img2 = nib.load(dlabelmap)
# dlabels = img2.get_data()

img = nib.load(fakeniitemplate)
dlabelsnii = img.get_data()

# roi_labels = pd.DataFrame(dlabels[0,0,0,0,:,:])

results = pd.read_csv(resultcsv, sep=',', dtype=str, comment='#')
lookup = pd.read_table(lookup_table, sep='\s+', dtype=str, comment='#')

for i in range(0,len(lookup)):
    dlabelindex = lookup.KEY[i]
    dlabelname = lookup.NAME[i]
    for j in range(0,len(results)):
        thisroi = results.iloc[j,0]
        thisresult = results[resultcolname][j]
        if dlabelname in thisroi:
            dlabelsnii[dlabelsnii==float(dlabelindex)] = thisresult

nib.save(img, fakeniiresutls)

docmd(['wb_command', '-cifti-convert', '-from-nifti',
    fakeniiresutls,
    dscalar_example,
    outdscalar])

## remove the tmpdir
shutil.rmtree(tempdir)
