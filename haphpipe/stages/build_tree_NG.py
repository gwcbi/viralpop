# -*- coding: utf-8 -*-

from __future__ import print_function
import sys
import os
import argparse
import shutil

from haphpipe.utils import sysutils
from haphpipe.utils.sysutils import MissingRequiredArgument

__author__ = "Uzma Rentia and Margaret C. Steiner"
__copyright__ = "Copyright (C) 2020 Uzma Rentia and Margaret C. Steiner"

def stageparser(parser):
    group1 = parser.add_argument_group('Input/Output')
    group1.add_argument('--seqs', type=sysutils.existing_file,
                        help='Input alignment in FASTA or PHYLIP format')
    group1.add_argument('--in_type',type=str,help="File format: FASTA or PHYLIP (Default is FASTA)")
    group1.add_argument('--output_name', type=str,
                        help='Run name for trees')
    group1.add_argument('--outdir', type=sysutils.existing_dir, default='.',
                        help='Output directory')

    group2 = parser.add_argument_group('RAxML-NG Options')
    group2.add_argument('--model',type=str,help="Substitution model OR path to partition file")
    group2.add_argument('--all', action='store_true', help="Run bootstrap search and find best ML tree")
    group2.add_argument('--branch_length', type=str,
                        help="Branch length estimation mode: linked, scaled, unlinked (partitioned analysis only)")
    group2.add_argument('--consense', type=str, help='Consensus tree building options: STRICT, MR, or MRE')
    group2.add_argument('--rand_tree', type=int,
                        help="Start from a random topology")
    group2.add_argument('--pars_tree', type=int,
                        help="Start from a tree generated by the parsimony-based randomized stepwise addition algorithm")
    group2.add_argument('--user_tree', type=sysutils.existing_file,
                        help="Load a custom starting tree from the NEWICK file")
    group2.add_argument('--search', action='store_true',
                        help="Find best scoring ML tree (default)")
    group2.add_argument('--search_1random', action='store_true',
                        help="Find best scoring ML tree with 1 random tree")
    group2.add_argument('--constraint_tree', type=sysutils.existing_file,
                        help="Specify a constraint tree to e.g. enforce monophyly of certain groups")
    group2.add_argument('--outgroup', type=str,
                        help="Outgroup(s) for tree")
    group2.add_argument('--bsconverge', action='store_true',
                        help="A posteriori bootstrap convergence test")
    group2.add_argument('--bs_msa', action='store_true',
                        help="Generate bootstrap replicate alignments")
    group2.add_argument('--bs_trees',type=str,help="Number of bootstrap trees OR autoMRE")
    group2.add_argument('--bs_tree_cutoff', type=float,
                        help="Change the bootstopping cutoff value to make the test more or less stringent")
    group2.add_argument('--bs_metric', type=str,
                        help="Options: tbe or fbp,tbe")
    group2.add_argument('--bootstrap', action='store_true',
                        help="Run non-parametric bootstrap analysis")
    group2.add_argument('--check', action='store_true',
                        help="Check alignment file and remove any columns consisting entirely of gaps")
    group2.add_argument('--log', type=str,
                        help="Options for output verbosity: ERROR, WARNING, RESULT, INFO, PROGRESS, VERBOSE, or DEBUG")
    group2.add_argument('--loglh', action='store_true',
                        help="Compute log-likelihood of a given tree without any optimization")
    group2.add_argument('--terrace', action='store_true',
                        help="Check whether a tree lies on a phylogenetic terrace")

    group3 = parser.add_argument_group('Settings')
    group3.add_argument('--version', action='store_true',
                        help="Check RAxML-NG version ONLY")
    group2.add_argument('--seed', type=int,
                        help="Seed for random numbers (default: 12345)")
    group2.add_argument('--redo', action='store_true',
                        help="Run even if there are existing files with the same name (use with caution!)")
    group3.add_argument('--keep_tmp', action='store_true',
                        help='Keep temporary directory')
    group3.add_argument('--quiet', action='store_true',
                        help='''Do not write output to console
                                (silence stdout and stderr)''')
    group3.add_argument('--logfile', type=argparse.FileType('a'),
                        help='Append console output to this file')
    group3.add_argument('--ncpu', type=int, default=1, help='Number of CPU to use') ### changed threads to ncpu
    group3.add_argument('--debug', action='store_true',
                        help='Print commands but do not run')

    parser.set_defaults(func=build_tree_NG)

def check_name_compatibility(input,outname,in_type):
    if in_type == 'FASTA':
        symbol_list = [' ',';',',',':','(',')',"'"]
    elif in_type == 'PHYLIP':
        symbol_list = [';', ',', ':', '(', ')', "'"]
    with open(input,'r') as file, open(outname,'w') as file_new:
        in_file = file.read()
        for sym in symbol_list:
            if sym in in_file:
                in_file = in_file.replace(sym,"_")
        file_new.write(in_file)

def build_tree_NG(seqs=None, in_type='FASTA', output_name='hp_tree', outdir='.',
                     treedir='hp_tree', model='GTR', bs_trees=None,
                     outgroup=None,branch_length=None, consense=None,rand_tree=None, pars_tree=None,
                     user_tree=None, search=None, search_1random=None, all=None,
                     constraint_tree=None,bsconverge=None, bs_msa=None,
                     bs_tree_cutoff=None,bs_metric=None, bootstrap=None, check=None,
                     log=None, loglh=None, redo=None,
                     terrace=None, seed=12345,version=None, quiet=False,
                     logfile=None, debug=False, ncpu=1,
                     keep_tmp=False):

    sysutils.check_dependency('raxml-ng')

    if version is True:
        cmd2 = ['raxml-ng', '-v']
        sysutils.command_runner([cmd2], 'build_tree_NG', quiet, logfile, debug)
        return

    if seqs is None:
        msg = 'No alignment provided.'
        raise sysutils.PipelineStepError(msg)

    # Set Output Directory
    output_dir = os.path.join(outdir, treedir)
    cmd0 = ['mkdir -p %s' % output_dir]
    sysutils.command_runner([cmd0], 'build_tree_NG', quiet, logfile, debug)

    # fix seq names
    if in_type=='FASTA':
        check_name_compatibility(seqs,os.path.join(output_dir,'seqs_fixednames.fasta'),in_type)
    elif in_type=='PHYLIP':
        check_name_compatibility(seqs, os.path.join(output_dir, 'seqs_fixednames.phy'), in_type)

    # Create temporary directory
    tempdir = sysutils.create_tempdir('build_tree_NG', None, quiet, logfile)

    # start raxml command
    cmd1 = ['raxml-ng', '--prefix %s/%s' % (os.path.abspath(tempdir), output_name), '--threads %d' % ncpu, '--seed %d' % seed, '--model %s' % model]
    if seqs is not None:
        if in_type == 'FASTA':
            cmd1 += ['--msa', '%s' % os.path.join(output_dir,'seqs_fixednames.fasta')]
        elif in_type == 'PHYLIP':
            cmd1 += ['--msa', '%s' % os.path.join(output_dir, 'seqs_fixednames.phy')]
    if branch_length is not None:
        cmd1 += ['--brlen', '%s' % branch_length]
    if consense is not None:
        cmd1 += ['--consense', '%s' % consense]
    if pars_tree is not None and rand_tree is None:
        cmd1 += ['--tree pars{%d}' % pars_tree]
    if pars_tree is None and rand_tree is not None:
        cmd1 += ['--tree rand{%d}' % rand_tree]
    if pars_tree is not None and rand_tree is not None:
        cmd1 += ['--tree pars{%d},rand{%d}' % (pars_tree, rand_tree)]
    if user_tree is not None:
        cmd1 += ['--tree', '%s' % os.path.abspath(user_tree)]
    if search is True:
        cmd1 += ['--search']
    if search_1random is True:
        cmd1 += ['--search1']
    if all is True:
        cmd1 += ['--all']
    if constraint_tree is not None:
        cmd1 += ['--tree-constraint', '%s' % os.path.abspath(constraint_tree)]
    if outgroup is not None:
        cmd1 += ['--outgroup', '%s' % outgroup]
    if bsconverge is True:
        cmd1 += ['--bsconverge']
    if bs_msa is True:
        cmd1 += ['--bsmsa']
    if bs_trees is not None:
        cmd1 += ['--bs-trees %s' % bs_trees]
    if bs_tree_cutoff is not None:
        cmd1 += ['--bs-cutoff', '%f' % bs_tree_cutoff]
    if bs_metric is not None:
        cmd1 += ['--bs-metric', '%s' % bs_metric]
    if bootstrap is True:
        cmd1 += ['--bootstrap']
    if check is True:
        cmd1 += ['--check']
    if log is not None:
        cmd1 += ['--log', '%s' % log]
    if loglh is True:
        cmd1 += ['--loglh']
    if terrace is True:
        cmd1 += ['--terrace']
    if redo is not None:
        cmd1 += ['--redo']

    sysutils.command_runner([cmd1, ], 'build_tree_NG', quiet, logfile, debug)

    # copy files from tmpdir to output directory (note - took some out here)
    if os.path.exists(os.path.join(tempdir, '%s.raxml.bestTree' % output_name)):
        shutil.copy(os.path.join(tempdir, '%s.raxml.bestTree' % output_name), os.path.abspath(output_dir))
    if os.path.exists(os.path.join(tempdir, '%s.raxml.bestPartitionTrees' % output_name)):
        shutil.copy(os.path.join(tempdir, '%s.raxml.bestPartitionTrees' % output_name), os.path.abspath(output_dir))
    if os.path.exists(os.path.join(tempdir, '%s.raxml.bestModel' % output_name)):
        shutil.copy(os.path.join(tempdir, '%s.raxml.bestModel' % output_name), os.path.abspath(output_dir))
    if os.path.exists(os.path.join(tempdir, '%s.raxml.bootstraps' % output_name)):
        shutil.copy(os.path.join(tempdir, '%s.raxml.bootstraps' % output_name), os.path.abspath(output_dir))
    if os.path.exists(os.path.join(tempdir, '%s.raxml.bootstrapMSA.<REP>.phy' % output_name)):
        shutil.copy(os.path.join(tempdir, '%s.raxml.bootstrapMSA.<REP>.phy' % output_name), os.path.abspath(output_dir))
    if os.path.exists(os.path.join(tempdir, '%s.raxml.ckp' % output_name)):
        shutil.copy(os.path.join(tempdir, '%s.raxml.ckp' % output_name), os.path.abspath(output_dir))
    if os.path.exists(os.path.join(tempdir, '%s.raxml.consensusTree' % output_name)):
        shutil.copy(os.path.join(tempdir, '%s.raxml.consensusTree' % output_name), os.path.abspath(output_dir))
    if os.path.exists(os.path.join(tempdir, '%s.raxml.log' % output_name)):
        shutil.copy(os.path.join(tempdir, '%s.raxml.log' % output_name), os.path.abspath(output_dir))
    if os.path.exists(os.path.join(tempdir, '%s.raxml.mlTrees' % output_name)):
        shutil.copy(os.path.join(tempdir, '%s.raxml.mlTrees' % output_name), os.path.abspath(output_dir))
    if os.path.exists(os.path.join(tempdir, '%s.raxml.startTree' % output_name)):
        shutil.copy(os.path.join(tempdir, '%s.raxml.startTree' % output_name), os.path.abspath(output_dir))
    if os.path.exists(os.path.join(tempdir, '%s.raxml.support' % output_name)):
        shutil.copy(os.path.join(tempdir, '%s.raxml.support' % output_name), os.path.abspath(output_dir))
    if os.path.exists(os.path.join(tempdir, '%s.raxml.terrace' % output_name)):
        shutil.copy(os.path.join(tempdir, '%s.raxml.terrace' % output_name), os.path.abspath(output_dir))
    if os.path.exists(os.path.join(tempdir, '%s.raxml.terraceNewick' % output_name)):
        shutil.copy(os.path.join(tempdir, '%s.raxml.terraceNewick' % output_name), os.path.abspath(output_dir))

    if not keep_tmp:
        sysutils.remove_tempdir(tempdir, 'build_tree_NG', quiet, logfile)

    cmd6 = ['echo', 'Stage completed. Output files are located here: %s\n' % os.path.abspath(output_dir)]
    sysutils.command_runner([cmd6, ], 'build_tree_NG', quiet, logfile, debug)

def console():
    parser = argparse.ArgumentParser(
        description='Build Phylogenetic Tree with RAxML-NG',
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

