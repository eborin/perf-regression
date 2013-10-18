#! /usr/bin/env python2.7
#***************************************************************************
#*   Copyright (C) 2013 by Edson Borin                                     *
#*   edson@ic.unicamp.br                                                   *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU General Public License as published by  *
#*   the Free Software Foundation; either version 2 of the License, or     *
#*   (at your option) any later version.                                   *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU General Public License for more details.                          *
#*                                                                         *
#*   You should have received a copy of the GNU General Public License     *
#*   along with this program; if not, write to the                         *
#*   Free Software Foundation, Inc.,                                       *
#*   59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             *
#**************************************************************************/

# Description
# This is a python script to run performance regression tests.
#
# Rationale:
#
# $> run_regression.py  
#
# checkout the most recent code
#
# for each build configuration ()
#   configure and build the tree
#   change into build_tree/regression_script_dir
#   run ./regression_script -r results_dir   // results_dir => directory to store results
#
# ./regression_script script is responsible for running, checking and moving the
# performance results to the results_dir

import regression_cfg
import sys
import getopt
import source_setup
import cfg_file
import system_env
import os.path
import build_setup
import subprocess
import shutil # copy2

# List of build configurations to be constructed by the performance regression
gatzalt_build_cfgs = [ "icc-11.339-O3-PAPI-NUMA", "g++-O3-PAPI-NUMA", "icc-11.339-O3-PAPI-NUMA-new_skylmat" ]

#optimator_build_cfgs = [ "icc-12.1.3-O3-PAPI-NUMA", "g++-O3-PAPI-NUMA", "icc-12.1.3-O3-PAPI-NUMA-new_skylmat" ]
optimator_build_cfgs = [ "icc-12.1.3-O3", "g++-O3", "icc-12.1.3-O3-new_skylmat" ]

macos_build_cfgs = [ "g++47-O3-vec-new_skylmat", "g++47-O3-vec" ]

build_cfgs = optimator_build_cfgs

def usage():
	print "\nUsage: ./run_regression.py [-h]\n"
	print "\nARGUMENTS"
	print "\t-h         : help."
	print "\t-b bld_cfg : customize the list of build configurations."

	print "\nDESCRIPTION"
	print "\tThis is a python script to run performance regression tests."
	print "\tThe script relies on \"source_setup.py\" and \"build_setup.py\" to"
	print "\tretrieve the source code and build the configurations."
	print "\tFor each configuration, the script creates a {RESULTS_DIR}/r{SRCVER} directory"
	print ("\tand calls {BUILD_DIR}/"+regression_cfg.regression_script_dir+"/"+
	       regression_cfg.regression_script+" -r {RESULTS_DIR}/r{SRCVER}/{BUILD_BASENAME}")
        print "\tThe "+regression_cfg.regression_script+" script is responsible for running, checking and moving the"
	print "\tresults to {RESULTS_DIR}/r{SRCVER}/{BUILD_BASENAME}"  

	print "\n\tRESULTS_DIR = Directory that contains all the performance regression results."
	print "\t            = "+regression_cfg.results_dir
	print "\tSRCVER = source code SVN revision."
	print "\tBUILD_BASENAME = unique name that identifies the build configuration."
	print "\tBUILD_DIR = path to the build tree constructed for a given build configuration."

	print "\nLIST OF BUILD CONFIGURATIONS"
	for b in build_cfgs :
		print "\t - ", b
	sys.exit(0)

def verbose(msg):
	print msg

def error(message, status):
	sys.stderr.write('ERROR: '+message+'\n')
        # TODO: Check whether we can recover or not...
        sys.exit(status)

def fatal(message):
	sys.stderr.write('FATAL: '+message+'\n')
        sys.exit(1)

def warning(message):
	sys.stderr.write('WARNING: '+message+'\n')

# Parse arguments
import getopt
appcfg_fn="neopz" # default name
version=0
statusf=0
logf=0
custom_cfgs = [ ]
opts, extra_args = getopt.getopt(sys.argv[1:], 'a:v:b:h')
for f, v in opts:
    if   f == '-h'  : usage()
    elif f == '-a'  : appcfg_fn=v
    elif f == '-b'  : custom_cfgs.append(v)
    elif f == '-v'  : version=v

if len(custom_cfgs) != 0 :
	build_cfgs= custom_cfgs

# Retrieve the source code. (appcfg contains the name of the application config file) 
appcfg=cfg_file.read(os.path.join(regression_cfg.basedir,"cfg","apps",appcfg_fn+".cfg"))
verbose("Retrieving source code")
ss_status, srcri_d = source_setup.retrieve(appcfg,version)
# Check for errors
if ss_status != 0 : 
	fatal("Error when setting up the source_setup.retrieve(...) "+
	      "returned error code "+str(ss_status)+".")

srcbasename = srcri_d["srcbasename"]
srcver = srcri_d["srcver"]
if srcri_d["srcmodified"] == "False" :
	rev_dir_name = "r"+str(srcver)
else :
	rev_dir_name = "r"+str(srcver)+"-m"

log_dir=os.path.join(regression_cfg.results_dir,rev_dir_name)

regression_status = {}

for bldcfg_fn in build_cfgs : 

	# Configure the build directory
	try:
		bldcfg = cfg_file.read(os.path.join(regression_cfg.basedir,"cfg","build",bldcfg_fn+".cfg"))
		bldbasename = cfg_file.getfld(bldcfg,"bldbasename")
	except cfg_file.CFGError, e:
		warning(str(e))
		continue

	regression_status[bldbasename] = {}

	# Creates a results_dir/revision_dir/config_dir"
	regression_status[bldbasename]["bldbasename"] = bldbasename
	regression_status[bldbasename]["srcbasename"] = srcbasename
	regression_status[bldbasename]["srcver"] = srcver
	regression_status[bldbasename]["srcmodified"] = srcri_d["srcmodified"]
	result_dir=os.path.join(regression_cfg.results_dir,rev_dir_name,bldbasename)
	if not os.path.isdir(result_dir) :
		try:    
			os.makedirs(result_dir)
		except os.error, e: 
			warning(str(e))
			regression_status[bldbasename]["status"]="Error"
			regression_status[bldbasename]["err_msg"]="Could not create the result dir. "+str(e)
			continue

	# Copy build configuration file () to results dir.
	# os.path.join(regression_cfg.basedir,"cfg","build",bldcfg_fn+".cfg") => os.path.join(regression_cfg.results_dir,rev_dir_name,basename=".cfg")
	shutil.copy2(os.path.join(regression_cfg.basedir,"cfg","build",bldcfg_fn+".cfg"),
		     os.path.join(regression_cfg.results_dir,rev_dir_name,bldbasename+".cfg"))

	# Configure and make the build configuration
	try:
		verbose("Configuring build directory for: "+bldbasename)
		bldri_d=build_setup.configure(srcri_d,bldcfg,remove_existing_build_dir=True)
	except build_setup.ConfigureSetupError, e:
		warning(str(e))
		regression_status[bldbasename]["status"]="Error"
		regression_status[bldbasename]["build_status"]="Error"
		regression_status[bldbasename]["build_err_msg"]="Configuration error. "+str(e)
		regression_status[bldbasename]["config_status"]="Error"
		regression_status[bldbasename]["make_status"]="Error"
		continue # Next building tree
	regression_status[bldbasename]["config_status"]="Ok"
	try:
		verbose("Making the build directory.")
		build_setup.make(bldri_d)
	except build_setup.MakeSetupError, e:
		warning(str(e))
		regression_status[bldbasename]["status"]="Error"
		regression_status[bldbasename]["build_status"]="Error"
		regression_status[bldbasename]["build_err_msg"]="Make error. "+str(e)
		regression_status[bldbasename]["make_status"]="Error"
		continue # Next building tree
	regression_status[bldbasename]["make_status"]="Ok"

	# The configuration and make where done ok.
	regression_status[bldbasename]["build_status"]="Ok"
	
	# calls build_dir/regression_script_dir/regression_script -r results_dir/revision/config_dir"
	# The regression_script script is responsible for running, checking and moving the"
	# results to result_dir"  
	rundir   = os.path.join(bldri_d["blddir"],regression_cfg.regression_script_dir)
	test_prg = os.path.join(rundir,regression_cfg.regression_script)
	args = [test_prg, "-r", result_dir]
	try:
		verbose("Running the performance regression script")
		# Todo. Redirect stdout and stderr to an output file to keep a log.
		log_fn=os.path.join(log_dir,bldbasename+".run.log")
		logfh = open(log_fn,mode='w+')
		p = subprocess.Popen(args, stdout=logfh, stderr=subprocess.STDOUT, cwd=rundir)
		p.wait()
		if (p.returncode != 0) : 
			regression_status[bldbasename]["status"]="Error"
			regression_status[bldbasename]["run_status"]="Error"
			regression_status[bldbasename]["run_err_msg"]="Regression tool ("+test_prg+") returned code "+str(p.returncode)
			continue
	except OSError, e:
		warning(str(e))
		regression_status[bldbasename]["status"]="Error"
		regression_status[bldbasename]["run_status"]="Error"
		regression_status[bldbasename]["run_err_msg"]=str(e)
		continue # Next building tree

	regression_status[bldbasename]["run_status"]="Ok"
	regression_status[bldbasename]["status"]="Ok"

# Store logs.
verbose("Storing log files")
for b,bres in regression_status.iteritems() :
 	fn=os.path.join(log_dir,b+".info.cfg")
	try:
		cfg_file.write(fn,bres)
	except cfg_file.CFGError, e:
		warning(str(e))
