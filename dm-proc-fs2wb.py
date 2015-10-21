#!/usr/bin/env python
"""
This will convert the all freesurfer outputs to hcp "space".

Usage:
  dm-proc-fs2wb.py [options] <fssubjectsdir> <hcpdir>

Arguments:
    <fssubjectsdir>      Path to input directory (freesurfer SUBJECTS_DIR)
    <hcpdir>             Path to top hcp directory (outputs)   `

Options:
  --prefix STR			   Tag for filtering subject directories
  -v,--verbose             Verbose logging
  --debug                  Debug logging in Erin's very verbose style
  -n,--dry-run             Dry run
  -h,--help                Print help

DETAILS
Converts freesurfer outputs to a Human Connectome Project outputs in
a rather organized way on all the participants within one project.

This script writes a little script (bin/hcpconvert.sh) within the output directory structure
that gets submitted to the queue for each subject. Subject's ID is passed into the qsub
command as an argument.

"""
from docopt import docopt
import pandas as pd
import datman as dm
import datman.utils
import datman.scanid
import glob
import os.path
import sys
import subprocess
import datetime
import tempfile
import shutil
import filecmp
import difflib

arguments       = docopt(__doc__)
inputpath       = arguments['<fssubjectsdir>']
targetpath      = arguments['<hcpdir>']
prefix          = arguments['--prefix']
VERBOSE         = arguments['--verbose']
DEBUG           = arguments['--debug']
DRYRUN          = arguments['--dry-run']

if DEBUG: print arguments

### Erin's little function for running things in the shell
def docmd(cmdlist):
    "sends a command (inputed as a list) to the shell"
    if DEBUG: print ' '.join(cmdlist)
    if not DRYRUN: subprocess.call(cmdlist)

fs2wb_script = '/home/edickie/code/hcp_extras/FreeSurfer2Workbench.sh'

# need to find the t1 weighted scan and update the checklist
# def doCIVETlinking(colname, archive_tag, civet_ext):
#     """
#     for a particular scan type, will look for new files in the inputdir
#     and link them inside civet_in using the CIVET convenstions
#     Will also update the checklist will what files have been found
#     (or notes is problems occur)
#
#     colname -- the name of the column in the checklist to update ('mnc_t1', 'mnc_t2' or 'mnc_pd')
#     archive_tag -- filename tag that can be used for search (i.e. '_T1_')
#     civet_ext -- end of the link name (following CIVET guide) (i.e. '_t1.mnc')
#     """
#     for i in range(0,len(checklist)):
#     	#if link doesn't exist
#     	target = os.path.join(civet_in, prefix + '_' + checklist['id'][i] + civet_ext)
#     	if os.path.exists(target)==False:
#             mncdir = os.path.join(inputpath,checklist['id'][i])
#     	    #if mnc name not in checklist
#             if pd.isnull(checklist[colname][i]):
#                 mncfiles = []
#                 for fname in os.listdir(mncdir):
#                     if archive_tag in fname:
#                         mncfiles.append(fname)
#                 if DEBUG: print "Found {} {} in {}".format(len(mncfiles),archive_tag,mncdir)
#                 if len(mncfiles) == 1:
#                     checklist[colname][i] = mncfiles[0]
#                 elif len(mncfiles) > 1 & QCedTranfer:
#                     meanmnc = [m for m in mncfiles if "mean" in m]
#                     if len(meanmnc) == 1:
#                         checklist[colname][i] = meanmnc[0]
#                     else:
#                         checklist['notes'][i] = "> 1 {} found".format(archive_tag)
#                 elif len(mncfiles) > 1 & QCedTranfer==False:
#                     checklist['notes'][i] = "> 1 {} found".format(archive_tag)
#                 elif len(mncfiles) < 1:
#                     checklist['notes'][i] = "No {} found.".format(archive_tag)
#             # make the link
#             if pd.isnull(checklist[colname][i])==False:
#                 mncpath = os.path.join(mncdir,checklist[colname][i])
#                 if DEBUG: print("linking {} to {}".format(mncpath, target))
#                 os.symlink(mncpath, target)

# ### build a template .sh file that gets submitted to the queue
# def makeCIVETrunsh(filename):
#     """
#     builds a script in the CIVET directory (run.sh)
#     that gets submitted to the queue for each participant
#     """
#     bname = os.path.basename(filename)
#     if bname == runcivetsh:
#         CIVETSTEP = 'runcivet'
#     if bname == runqcsh:
#         CIVETSTEP = 'qc'
#     #open file for writing
#     civetsh = open(filename,'w')
#     civetsh.write('#!/bin/bash\n\n')
#
#     civetsh.write('# SGE Options\n')
#     civetsh.write('#$ -S /bin/bash\n')
#     civetsh.write('#$ -q main.q\n')
#     civetsh.write('#$ -l mem_free=6G,virtual_free=6G\n\n')
#
#     civetsh.write('#source the module system\n')
#     civetsh.write('source /etc/profile.d/modules.sh\n')
#     civetsh.write('source /etc/profile.d/quarantine.sh\n\n')
#
#     civetsh.write('## this script was created by dm-proc-CIVET.py\n\n')
#     ## can add section here that loads chosen CIVET enviroment
#     civetsh.write('##load the CIVET enviroment\n')
#     if CIVET12:
#         civetsh.write('module load CIVET/1.1.12 CIVET-extras/1.0\n\n')
#     else:
#         civetsh.write('module load CIVET/1.1.10+Ubuntu_12.04 CIVET-extras/1.0\n\n')
#
#     ## add a line that will read in the subject id
#     if CIVETSTEP == 'runcivet':
#         civetsh.write('SUBJECT=${1}\n\n')
#
#         #add a line to cd to the CIVET directory
#         civetsh.write('cd '+os.path.normpath(targetpath)+"\n\n")
#
#         ## start building the CIVET command
#         civetsh.write('CIVET_Processing_Pipeline' + \
#             ' -sourcedir input' + \
#             ' -targetdir output' + \
#             ' -prefix ' + prefix + \
#             ' -lobe_atlas -resample-surfaces -spawn -no-VBM' + \
#             ' -thickness tlink 20')
#
#         if MULTISPECTRAL: #if multispectral option is selected - add it to the command
#              civetsh.write(' -multispectral')
#
#         if ONETESLA:
#             civetsh.write(' -N3-distance 200')
#         else: # if not one-tesla (so 3T) using 3T options for N3
#             if CIVET12==False:
#                 civetsh.write(' -3Tesla ')
#             civetsh.write(' -N3-distance 50')
#
#         civetsh.write( ' ${SUBJECT} -run \n\n')
#
#     if CIVETSTEP == 'qc':
#         #add a line to cd to the CIVET directory
#         civetsh.write('cd '+civet_out+"\n")
#         civetsh.write('SUBJECTS=`ls | grep -v QC | grep -v References.txt`\n\n')
#
#         #add a line to cd to the CIVET directory
#         civetsh.write('cd '+os.path.normpath(targetpath)+"\n\n")
#
#         #run the CIVET qc pipeline on all subs who are processed
#         civetsh.write('CIVET_QC_Pipeline -sourcedir ' + civet_in + \
#                     ' -targetdir ' + civet_out + \
#                     ' -prefix ' + prefix +\
#                     ' ${SUBJECTS} \n')
#     #and...don't forget to close the file
#     civetsh.close()

# ### check the template .sh file that gets submitted to the queue to make sure option haven't changed
# def checkrunsh(filename):
#     """
#     write a temporary (run.sh) file and than checks it againts the run.sh file already there
#     This is used to double check that the pipeline is not being called with different options
#     """
#     tempdir = tempfile.mkdtemp()
#     tmprunsh = os.path.join(tempdir,os.path.basename(filename))
#     makeCIVETrunsh(tmprunsh)
#     if filecmp.cmp(filename, tmprunsh):
#         if DEBUG: print("{} already written - using it".format(filename))
#     else:
#         # If the two files differ - then we use difflib package to print differences to screen
#         print('#############################################################\n')
#         print('# Found differences in {} these are marked with (+) '.format(filename))
#         print('#############################################################')
#         with open(filename) as f1, open(tmprunsh) as f2:
#             differ = difflib.Differ()
#             print(''.join(differ.compare(f1.readlines(), f2.readlines())))
#         sys.exit("\nOld {} doesn't match parameters of this run....Exiting".format(filename))
#     shutil.rmtree(tempdir)

######## NOW START the 'main' part of the script ##################
## make the civety directory if it doesn't exist
targetpath = os.path.normpath(targetpath)
logs_dir  = os.path.join(targetpath+'/logs/')
dm.utils.makedirs(civet_logs)

## writes a standard CIVET running script for this project (if it doesn't exist)
## the script requires a $SUBJECT variable - that gets sent if by qsub (-v option)
# runcivetsh = 'runcivet.sh'
# runqcsh    = 'runqc.sh'
# for runfilename in [runcivetsh,runqcsh]:
#     runsh = os.path.join(civet_bin,runfilename)
#     if os.path.isfile(runsh):
#         ## create temporary run file and test it against the original
#         checkrunsh(runsh)
#     else:
#         ## if it doesn't exist, write it now
#         makeCIVETrunsh(runsh)

####set checklist dataframe structure here
#because even if we do not create it - it will be needed for newsubs_df (line 80)
cols = ["id", "date_converted", "qc_rator", "qc_rating", "notes"]

# if the checklist exists - open it, if not - create the dataframe
checklistfile = os.path.normpath(targetpath+'/CIVETchecklist.csv')
if os.path.isfile(checklistfile):
	checklist = pd.read_csv(checklistfile, sep=',', dtype=str, comment='#')
else:
	checklist = pd.DataFrame(columns = cols)


## find those subjects in input who have not been processed yet and append to checklist
subjects = filter(os.path.isdir, glob.glob(os.path.join(inputpath, '*')))
for i, subj in enumerate(subjects):
    subjects[i] = os.path.basename(subj)
subids_fs = [ v for v in subids_fs if "PHA" not in v ] ## remove the phantoms from the list
if prefix != None:
    subids_fs = [ v for v in subids_fs if prefix in v ] ## remove the phantoms from the list
newsubs = list(set(subids_fs) - set(checklist.id))
newsubs_df = pd.DataFrame(columns = cols, index = range(len(checklist),len(checklist)+len(newsubs)))
newsubs_df.id = newsubs
checklist = checklist.append(newsubs_df)

# # do linking for the T1
# doCIVETlinking("mnc_t1",T1_TAG , '_t1.mnc')

# #link more files if multimodal
# if MULTISPECTRAL:
#     doCIVETlinking("mnc_t2", T2_TAG, '_t2.mnc')
#     doCIVETlinking("mnc_pd", PD_TAG, '_pd.mnc')

## now checkoutputs to see if any of them have been run
#if yes update spreadsheet
#if no submits that subject to the queue
jobnames = []
for i in range(0,len(checklist)):
    subid = checklist['id'][i]
    freesurferdone = os.path.join(inputpath,subid,'scripts', subid, 'recon-all.done')
    # checks that all the input files are there
    CIVETready = os.path.exists(freesurferdone)
    # if all input files are there - check if an output exists
    if CIVETready:
        thicknessdir = os.path.join(civet_out,subid,'thickness')
        # if no output exists than run civet
        if os.path.exists(thicknessdir)== False:
            os.chdir(civet_bin)
            jobname = 'fs2wb_' + subid
            docmd(['qsub','-o', logs_dir, \
                     '-N', jobname,  \
                     fs2wb_script,
                     '--FSpath=' + inputpath,
                     '--HCPpath=' + targetpath,
                     '--subject=' + subid])
            jobnames.append(jobname)
            checklist['date_converted'][i] = datetime.date.today()
        # # if failed logs exist - update the CIVETchecklist
        # else :
        #     civetlogs = os.path.join(civet_out,subid,'logs')
        #     faillogs = glob.glob(civetlogs + '/*.failed')
        #     if DEBUG: print "Found {} fails for {}: {}".format(len(faillogs),subid,faillogs)
        #     if len(faillogs) > 0:
        #         checklist['notes'][i] = "CIVET failed :("

# ##subit a qc pipeline job (kinda silly as a job, but it needs to be dependant, and have right enviroment)
# ### if more that 30 subjects have been submitted to the queue,
# ### use only the last 30 submitted as -hold_jid arguments
# if len(jobnames) > 30 : jobnames = jobnames[-30:]
# ## if any subjects have been submitted,
# ## submit a final job that will qc the resutls after they are finished
# if len(jobnames) > 0:
#     #if any subjects have been submitted - submit an extract consolidation job to run at the end
#     os.chdir(civet_bin)
#     docmd(['qsub','-o', civet_logs, \
#         '-N', 'civet_qc',  \
#         '-hold_jid', ','.join(jobnames), \
#         runqcsh ])

## write the checklist out to a file
checklist.to_csv(checklistfile, sep=',', columns = cols, index = False)
