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

# TODO:

# 1) Adapt the framework to incorporate the features described by Gomes and
# Borin [1].  We may have one cfg subdirectory for each table and one file for
# each entry in the tables. File names are unique ids.
#
# [1] G. Gomes and E. Borin. A Database for Reproducible Computational
# Research. 13th Symposium on Computing Systems (WSCAD'12). 2012

# Description
# This is a python script to help building applications for performance and
# correctness tests
#
# Rationale:
#
# $> build.py -c bldcfg [-a appcfg] [-v 123] [-l output_log] [-o status]  
#
# calls system_environment.py to verify if the current environment is equivalent to cfg/env/current 
# and return the environment version.
# (STATUS,ENVVER) = env-check.py 
# - STATUS=OK|ERR
# - ENVVER=[cfg/env/current] 
#
# VERIFY(STATUS)
#
# calls source-setup.py to setup the source code (place a copy of the code at SRCDIR).
# (STATUS,SRCDIR,SRCVER,MODIFIED) = source-setup.py [-a appcfg] [-v version] 
# - STATUS=OK|ERR
# - SRCDIR=work/src/appcfg.id
# - SRCVER=current_version
# - MODIFIED=TRUE|FALSE
#
# VERIFY(STATUS)
# SUFFIX="SRCVER-ENVVER
# if [MODIFIED]: SUFFIX="SUFFIX-m"
#
# calls build-setup.py to configure the build (it may use autotools, cmake, etc...)
# (STATUS,BLDDIR,INSDIR,SUFFIX) = build-setup.py -a appcfg -c bldcfg
# - STATUS=OK|ERR
# - BLDDIR=work/build/appcfg.id-bldcfg.id-SUFFIX
# - INSDIR=results/build/appcfg.id-bldcfg.id-SUFFIX
#
# VERIFY(STATUS)
# 
# call build-make.py to make and install tool (it may your favorite make tool)
# (STATUS) = build-make.py -b BLDDIR -i INSDIR
# 
# VERIFY(STATUS)
#
# if(STATUS==OK)
#  move log files (including the CMakeCache.txt) to INSDIR
# else
#  gen report on BLDDIR
#
# The log messages are directed to output_log if -l is provided, and 
# The build status is provided on the status file, if -o is provided. 
#  - It contains information about the build status and can parsed to 
#    check for errors or retrieve the install dir.

# Configuration files:
# cfg/env/current: contains the name of the file that describes the current environment.
# cfg/app/appcfg: information about the application to be built
#  - appcfg.id: application short name (ex: neopz)
# cfg/build/bldcfg: cmake (configure) flags to configure the building
#  - bldcfg.id: cmake|autotools configuration short name (ex: gcc47-O3)

import regression_cfg
import sys
import getopt
import source_setup
import cfg_file
import system_env
import os.path
import build_setup
#import build_make

def usage():
	print "\nUsage: build.py -c bldcfg [-a appcfg] [-v 123] [-l logfile] [-o status]\n"
	print "\nARGUMENTS"
	print "\t-c bldcfg: a build-config file with configuration options."
	print "\t-a appcfg: a application-config file describing the application."
        print "\t-v version: the version of the application source code."
        print "\t-l logfile: the filename to dump the log messages."
        print "\t-o status: the status of the build. It can be parsed to retrieve information."
	print "\nDESCRIPTION"
	print "\tThe build script configure, build and install an application defined "
        print "\tby appcfg using the configuration options defined at bldcfg"
        print "\n\tThe application use the following functions defined at the follinwg files"


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
bldcfg_fn=0
version=0
statusf=0
logf=0
opts, extra_args = getopt.getopt(sys.argv[1:], 'c:a:v:l:o:h')
for f, v in opts:
    if f == '-a'    : appcfg_fn=v
    elif f == '-c'  : bldcfg_fn=v
    elif f == '-v'  : version=v
    elif f == '-o'  : statusfn=v
    elif f == '-l'  : logfn=v
    elif f == '-h': usage()
    
if bldcfg_fn == 0:
    fatal("A build configuration file name (-c bld_cfg) must be provided.")

# Verify if the current environment is valid
envstatus, envid = system_env.check()
if envstatus != True :
    error("Environment information is not up to date", ENVERR)

# Read the application and build configuration files
appcfg=cfg_file.read(os.path.join(regression_cfg.basedir,"cfg","apps",appcfg_fn+".cfg"))
bldcfg=cfg_file.read(os.path.join(regression_cfg.basedir,"cfg","build",bldcfg_fn+".cfg"))

# Retrieve the source code. (appcfg contains the name of the application config file) 
verbose("Retrieving source code")
ss_status, srcri_d = source_setup.retrieve(appcfg,version)

# Check for errors
if ss_status != 0 : 
    fatal("Error when setting up the source_setup.retrieve(...) returned error code "+str(ss_status)+".")

# Configure the build directory
verbose("Configuring build directory")
try:
	bldri_d=build_setup.configure(srcri_d,bldcfg)
except build_setup.ConfigureSetupError, e:
       	fatal("Error when configuring the build directory. "+str(e))

# Make the build directory
verbose("Building the application")
try:
	build_setup.make(bldri_d, True)
except build_setup.MakeSetupError, e:
       	fatal("Error when building the application/library. "+str(e)+"\n"+e.long_msg)

# TODO handle logs
# if(STATUS==OK)
#  move log files (including the CMakeCache.txt) to INSDIR
# else
#  gen report on BLDDIR
#
# The log messages are directed to output_log if -l is provided, and 
# The build status is provided on the status file, if -o is provided. 
#  - It contains information about the build status and can parsed to 
#    check for errors or retrieve the install dir.

