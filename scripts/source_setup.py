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
import cfg_file
# MacOS => sudo port install py27-pysvn
import pysvn 

def error(message, status):
	sys.stderr.write('ERROR: '+message+'\n')
        sys.exit(status)
def warn(message):
	sys.stderr.write('WARNING: '+message+'\n')

# Retrieves the source code for the given application configuration file. And
# writes a regression information file into the source code.
# Input:
#  appcfg: dictionary with information about the application
#    - requires the following fields at appcfg:
#      * rep_address: the repository http address
#      * srcbasename: the basename of the source directory
#  version: source code version
#    - if version == 0 do not updates the repository. Just retrieve information
#    - if version == -1 updates the repository to the last available revision.
#    - if version > 0 updates the respository to revision to version
#    - in case version > 0 || version == -1, the function returns error in case the 
#      source code contains local modifications.
# Output:
#  errcode: 0 => OK, != 0 => ERROR
#  srcdir:source directory
#  ri_d:regression information dictionary. It contains the following info:
#    - srcdir: source code directory
#    - srcbasename: souce code base name
#    - srcver: source code version
#    - srcmodified: true => local copy has modifications, false => no modifications
#    - cfgfn: => the path of the name that contains the regression information.

def retrieve(appcfg,version):
	errcode=0
	srcver=0
	srcdir = regression_cfg.get_app_dirname(appcfg)
	srcbasename = cfg_file.getfld(appcfg,"srcbasename")
	# Removes the old source regression information
	ri_fn = regression_cfg.get_regression_info_fn(srcdir)
	if os.path.isfile(ri_fn):
		try: os.remove(ri_fn)
		except OSError, e:
			(error('Could not remove regression information file from'+
			       ' source directory: '+ri_fn+'('+e.output+')',2))
	client = pysvn.Client()

	# Prompt for authentication credentials when there are no valid store credentials.
	client.set_interactive( True )
	# Check whether there are local modifications
	if not os.path.isdir(srcdir): 
		# Src dir does not exist. Try to check it out!
		rep_addr = cfg_file.getfld(appcfg,"rep_address")
		# Check out the current version of the repository
		try: 
			if version > 0 : 
				r = pysvn.Revision(pysvn.opt_revision_kind.number, version)
 				rev = client.checkout(rep_addr,srcdir,revision=r)
			else :
				print "Checkout fresh from: "+rep_addr
				rev = client.checkout(rep_addr,srcdir)
		except pysvn.ClientError, e:
			error("Could not checkout source from repository: "+rep_addr+". ERR("+str(e)+")",2)
		srcmodified=False
	else:
		# Source dir exists. Retrieve info from the current copy
		entry   = client.info(srcdir)
		# Check for local changes
		changes = client.status(srcdir)
		srcmodified=False
		localcopychanges=""
		for f in changes: 
			if f.text_status != pysvn.wc_status_kind.normal : 
				srcmodified = True 
				# Store modified files for eventual logging.
				localcopychanges+=('['+str(f.text_status)+']:['+f.path+']\n')
				#print (f.path,f.text_status)
		# Check the version
		if version != 0: 
			# Change the revision. Ensure it is not modified
			if version > 0 : 
				rev=pysvn.Revision(pysvn.opt_revision_kind.number, version)
			else : # Last revision
				rev=pysvn.Revision(pysvn.opt_revision_kind.head)
			if not srcmodified :
				rep_addr = cfg_file.getfld(appcfg,"rep_address")
				# Change to version. 
				try: 
					rev = client.checkout(rep_addr,srcdir,revision=rev)
				except pysvn.ClientError, e:
					error("Could not change the revision to "+str(version)+". ERR("+str(e)+")",2) 
			else :
				errcode=1
				(warn("Cannot change ("+srcdir+") to version "+str(version)+
				      ". There are modifications on the local copy.\n"+localcopychanges))
	# Retrieve the version of the source code
	entry = client.info(srcdir)
	srcver = entry.revision.number
	if entry.revision.kind != pysvn.opt_revision_kind.number:
	       	error("Current source directory ("+srcdir+") does not have a revision number?",3)

	# Setup the regression information dictionary (rid)
	ri_d = {}
	ri_d["srcdir"] = srcdir
	ri_d["srcbasename"] = srcbasename
	ri_d["srcver"] = srcver
	ri_d["srcmodified"] = srcmodified
	ri_d["srcrifn"] = ri_fn
	cfg_file.write(ri_fn,ri_d)
	return errcode, ri_d

# Main -- used for tests. The ideal usage is to import this module and use the
# function retrieve directly.
def usage():
	print "\nUsage: source_setup.py -a appcfg [-v version] [-h]\n"
	print "\nARGUMENTS"
	print "\t-a appcfg: a application-config file describing the application."
	print "\t-v version: SVN repository revision number."
	print "\nDESCRIPTION"
	print "\tSets up the source directory with source code from the repository."
	print "\tif version is provided the source directory should be updated"
	print "\tto reflect the corresponding version number."
	print "\tif version is provided the tool returns error code 2 in case there is a"
	print "\tlocal copy with modifications."
	print "\tif version is not provided, the script must retrieve the version"
	print "\tand the MODIFIED status of the current copy."
	print "\tif version == -1, retrieve the last version."
	print "\nTODO:"
	print "\tHandle errors gracefully."
	sys.exit(1)

if __name__ == "__main__":
	import getopt
	filename=0
	version=0
	opts, extra_args = getopt.getopt(sys.argv[1:], 'a:v:h')
	for f, v in opts:
		if f   == '-a' : filename=v
		elif f == '-v' : version=v
		elif f == '-h' : usage()
	
	if filename == 0:
		error("An input file name must be provided.", 1)
	
	appcfgd = cfg_file.read(filename)
	
	errcode, ri_d =  retrieve(appcfgd,version)
	
	print "ERRCODE : ", errcode
	print "RID     : ", ri_d
