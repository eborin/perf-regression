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
import regression_cfg
import sys
import os.path
import shutil
import cfg_file
import subprocess as sp

class BuildSetupError(Exception):
	def __init__(self, msg):
		self.msg = msg
	def __str__(self):
		return self.msg

def warn(message):
	sys.stderr.write('WARNING (build_setup): '+message+'\n')

# TODO: Describe the function!!!
def configure(srcri_d,bldcfg,remove_existing_build_dir=False):
	# Check src directories
	srcdir=cfg_file.getfld(srcri_d,"srcdir")
	if not os.path.isdir(srcdir) : 
		raise BuildSetupError("source directory ("+srcdir+") is not a valid directory.")

	# Get build and install directory names
	blddir, insdir = regression_cfg.get_bld_ins_dirname(srcri_d,bldcfg)
	
	# Remove existing build tree?
	if os.path.isdir(blddir) :
		if remove_existing_build_dir :
			def rmtreeError(function, path, execinfo):
				raise OSError('Cannot delete file/dir: ' + path + '. ' + execinfo)
			try:    
				shutil.rmtree(blddir,ignore_errors=False,onerror=rmtreeError)
			except OSError, e: 
				raise BuildSetupError("Could not remove the blddir ("+blddir+"). "+str(e))

	# Create the build directory
	if not os.path.isdir(blddir) :
		try:    
			os.makedirs(blddir)
		except: 
			raise BuildSetupError("Could not create blddir ("+blddir+").")

	# Removes the old build regression information
	ri_fn = regression_cfg.get_regression_info_fn(blddir)
	if os.path.isfile(ri_fn):
		try: 
			os.remove(ri_fn)
		except OSError, e:
			raise BuildSetupError('Could not remove regression information file from'+
					      ' source directory: '+ri_fn+'('+e.output+')',2)

	# Retrieve the cmake arguments from the build configuration.
	cm_args_l = cfg_file.getfld(bldcfg,"cm_args_l")
	build_options='-DCMAKE_INSTALL_PREFIX:PATH='+insdir
	for i in cm_args_l : 
		build_options=build_options+' '+i

	# Change into bld dir and configure
	cmd = 'cd '+blddir+' && '+'cmake '+build_options+' '+srcdir
	logf = open(os.path.join(blddir,"cmake.log"), 'w')
	logf.write('CMD:'+cmd)
	try :
		log = sp.check_output(cmd, shell=True, stderr=sp.STDOUT)
		logf.write('LOG:\n'+log)
		logf.close()
		status=0
	except sp.CalledProcessError, e:
		msg='Error when trying to configure the build using cmake: '+e.output
		logf.write('WARNING:\n'+msg)
		warn(msg)
		logf.close()
		status=1

	# Setup the regression information dictionary (rid)
	ri_d = srcri_d
	ri_d["blddir"] = blddir
	ri_d["insdir"] = insdir
	ri_d["bldrifn"] = ri_fn
	cfg_file.write(ri_fn,ri_d)

	return ri_d

def make(bldri_d,install=False):
	blddir=cfg_file.getfld(bldri_d,"blddir")
	cmd = 'cd '+blddir+' && '+'make '+regression_cfg.extra_make_args
	if install : cmd=cmd+' && make install'
	logf = open(os.path.join(blddir,"make.log"), 'w')
	logf.write('CMD:'+cmd)
	try :
		log = sp.check_output(cmd, shell=True, stderr=sp.STDOUT)
		logf.write('LOG:\n'+log)
		logf.close()
		status = 0
	except sp.CalledProcessError, e:
		msg='"Error when trying to make the build using make: '+e.output
		logf.write('WARNING:\n'+msg)
		warn(msg)
		logf.close()
		status = 1
	# Update the build regression info
	ri_fn = cfg_file.getfld(bldri_d,"bldrifn")
	bldri_d["bld-last-make-status"]=status
	cfg_file.write(ri_fn,bldri_d)
	if status != 0 :
		raise BuildSetupError(msg)

# Main -- used for tests. The ideal usage is to import this module and use the
# function retrieve directly.
def usage():
	print "\nUsage: build_setup.py -s srcdir -b bldcfg_fn [-m] [-h]\n"
	print "\nARGUMENTS"
	print "\t-s srcdir     : souce code directory."
	print "\t-b bldcfg_fn  : build configuration file name."
	print "\t-m            : execute make."
	print "\t-h            : help ."
	print "\nDESCRIPTION"
	print "\tTODO....."
	print "\nTODO:"
	print "\tHandle errors gracefully."
	sys.exit(1)

def error(message,exit_code):
	sys.stderr.write('ERROR: '+message+'\n')
	sys.exit(exit_code)

if __name__ == "__main__":
	import getopt
	srcdir=0
	srcbasename=0
	srcver=0
	makeTree=False
	srcmodified=False
	bldcfg_fn=0
	opts, extra_args = getopt.getopt(sys.argv[1:], 's:b:hm')
	for f, v in opts:
		if f   == '-s': srcdir=v
		elif f == '-b': bldcfg_fn=v
		elif f == '-h': usage()
		elif f == '-m': makeTree=True
	
	if bldcfg_fn == 0:
		error("An input build configuration file must be provided (-b).", 1)
	
	bldcfgd = cfg_file.read(bldcfg_fn)

	srcri_fn = os.path.join(srcdir,"regression.cfg")

	srcri = cfg_file.read(srcri_fn)
	
	try:
		rid = configure(srcri,bldcfgd)
		if makeTree : make(rid)
	except BuildSetupError, e:
		error(str(e),1)
	
	print "RID    : ", rid
