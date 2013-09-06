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

basedir="/local/borin/perf-regression/"

extra_make_args="-j 64"

import os.path
import cfg_file

# Returns the file name of the regression configuration file. 
def get_regression_info_fn(directory):
	return os.path.join(directory,"regression.cfg")

def get_app_dirname(appcfgd):
	srcbasename = cfg_file.getfld(appcfgd, "srcbasename")
	return os.path.join(basedir,"work","src",srcbasename)

def get_bld_ins_dirname(srccfgd,bldcfgd):
	srcbasename = cfg_file.getfld(srccfgd,"srcbasename")
        srcmodified = cfg_file.getfld(srccfgd,"srcmodified")
        srcver = cfg_file.getfld(srccfgd,"srcver")
        bldbasename = cfg_file.getfld(bldcfgd,"bldbasename")
	basename=srcbasename+"-"+bldbasename+"-v"+str(srcver)
	if srcmodified : basename = basename+"-m"
        blddir = os.path.join(basedir,"work","build",basename)
        insdir = os.path.join(basedir,"results","build",basename)
        return blddir, insdir
