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

class CFGError(Exception):
	def __init__(self, msg):
		self.msg = msg
	def __str__(self):
		return self.msg

# Handles configuration files
# TODO: Improve the description...
#
# Each line contains an attribute
# The line syntax is: 
#  key : value
# where key may be any string without ":". value may contain any character, even ":"
# If key is a string finished with "_l" it means this attribute is a list. As an example, in:
#  cmake_opt_l : -DCMAKEWHATEVER=2 -DOK
# cmake_opt_l is the attribute key and -DCMAKEWHATEVER=2 -DOK is the
# value. Leading and trailing spaces at the key and the values are removed.

# Read a configuration file into a dictionary
def read(filename):
	# Check configuration file
	if not os.path.isfile(filename): 
		raise CFGError(filename+' is not a valid configuration file.\n')
	d={}
	with open(filename) as f:
		for line in f:
			# Remove leading and trailing white spaces and partition
			key, sep, value = line.partition(':') 
			k = key.strip()
			v = value.strip()
			if k and k[:1] != "#" :
				# Check whether the attribute is a list of a single value
				if k[-2:] != "_l" : 
					d[k] = v # Single Attribute is not a list
				else :
					if k in d : 
						d[k].append(v)
					else : 
					        d[k] = [v]
	return d

	# Retrieve a list of pairs field:value
	#  = []
	# with open(filename) as f:
	# 	for line in f:
	# 		# Remove leading and trailing white spaces and partition
	# 		field, sep, value = line.partition(':') 
	# 		if value:
	# 			l.append((field.strip(),value.strip()))
	# # Return a dictionary
	# return dict(l)

# Writes a configuration dictionary into a file
# Exits if file cannot be written
# TODO: improve error handling
def write(filename,cfgd) :
	try:
		f = open(filename, 'w')
	except IOError:
		raise CFGError('could not open file for writting: '+filename)
	for k, v in cfgd.iteritems() :
		if k[-2:] == "_l" : # List field
			for i in v :
				f.write(k+":"+str(i)+"\n")
		else :
			f.write(k+":"+str(v)+"\n")
	f.close()
	return

# Print a configuration dictionary
def prnt(cfgdct):
	print "------------------------------------"
	for k, v in cfgdct.iteritems() : print k, ":", v
	print "------------------------------------"
	return

# Get one of the fields out of a configuration dictionary
def getfld(d,fld):
	if fld not in d:
		raise CFGError("Configuration file does not contain field \""+fld+"\"")
	return d[fld]

# Functions for stand alone tests
def usage():
	print "\nUsage: cfg_file.py -i input.cfg [-o output.cfg] [-h]\n"
	print "\nARGUMENTS"
	print "\t-i input.cfg: input configuration file."
	print "\t-o output.cfg: output configuration file."
	print "\nDESCRIPTION"
	print "\tReads the contents of the configuration file into a "
	print "\tconfiguration dictionary and prints it on the screen."
	print "\tOptions (-o), it writes configuration dictionary into"
	print "\ta output file."
	sys.exit(1)

def error(message, status):
	sys.stderr.write('ERROR (cfg_file): '+message+'\n')
        sys.exit(status)

# Main - for stand alone tests only
if __name__ == "__main__":
	import getopt
	inputfn=0
	outputfn=0
	opts, extra_args = getopt.getopt(sys.argv[1:], 'i:o:h')
	for f, v in opts:
		if   f == '-i': inputfn=v
		elif f == '-o': outputfn=v
		elif f == '-h': usage()

	if inputfn == 0:
		error("An input file name must be provided.", 1)
	cfgd = read(inputfn)
	prnt(cfgd)
	if outputfn != 0:
		write(outputfn, cfgd)
