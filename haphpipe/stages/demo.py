#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import sys
import os
import argparse
import shutil

from haphpipe.utils import helpers
from haphpipe.utils import sysutils
from haphpipe.utils.sysutils import PipelineStepError
from haphpipe.utils.sysutils import MissingRequiredArgument


__author__ = 'Matthew L. Bendall and Keylie M. Gibson'
__copyright__ = "Copyright (C) 2019 Matthew L. Bendall and 2020 Keylie M. Gibson"

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

def stageparser(parser):
    """ Add stage-specific options to argparse parser

    Args:
        parser (argparse.ArgumentParser): ArgumentParser object

    Returns:
        None
    
    """
    group1 = parser.add_argument_group('Input/Output')
    group1.add_argument('--outdir', type=sysutils.new_or_existing_dir,
                        default='./demo',
                        help='Output directory.')
    group1.add_argument('--refonly', action='store_true',
                        help='Does not run entire demo, only pulls the reference files')
    parser.set_defaults(func=demo)


def demo(outdir="./demo", refonly=False):
    """ Get references """
    req_files = ['HIV_B.K03455.HXB2.amplicons.fasta',
                 'HIV_B.K03455.HXB2.fasta',
                 'HIV_B.K03455.HXB2.gtf',
                 ]
    getrefs = any(not os.path.exists(os.path.join(outdir, 'refs', f)) for f in req_files)
    
    if getrefs:
        ref_gz = os.path.join(outdir, 'refs.tar.gz')
        # download ref command
        cmd1 = [
            'curl',
            '-L',
            'https://github.com/gwcbi/haphpipe/blob/master/bin/refs.tar.gz?raw=true',
            '>',
            ref_gz,
        ]
        # unzip refs
        cmd2 = ['tar', '-xzvf', ref_gz, '-C', outdir, ]
        cmd3 = ['rm', ref_gz, ]
        sysutils.command_runner(
            [cmd1, cmd2, cmd3, ], 'refs'
        )
    else:
        print('References found at %s.' % os.path.join(outdir, 'refs'))
    
    if refonly:
        print("Complete: Demo was run with --refonly.")
        return
    
    print("Running demo in %s." % os.path.join(outdir))
    
    # Check for executable
    sysutils.check_dependency("fastq-dump")
    
    # Demo command
    cmd1 = ['haphpipe_demo', outdir, ]
    sysutils.command_runner(
        [cmd1, ], 'demo'
    )


def console():
    """ Entry point

    Returns:
        None

    """
    parser = argparse.ArgumentParser(
        description='Set up demo directory and run demo.',
        formatter_class=sysutils.ArgumentDefaultsHelpFormatterSkipNone,
    )
    stageparser(parser)
    args = parser.parse_args()
    try:
        args.func(**sysutils.args_params(args))
    except MissingRequiredArgument as e:
        parser.print_usage()
        print('error: %s' % e, file=sys.stderr)


if __name__ == '__main__':
    console()
