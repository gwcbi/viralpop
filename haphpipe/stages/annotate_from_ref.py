#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import json
import argparse
from subprocess import check_output
from collections import defaultdict, Counter

from Bio import SeqIO
from Bio.Seq import Seq

from ..utils.sysutils import existing_file, args_params
from ..utils.sequtils import wrap, parse_seq_id, region_to_tuple
from ..utils.blastalign import called_regions, get_seg_stats, load_slot_json
from ..utils.gtfparse import gtf_parser, GTFRow

from ..utils.sysutils import PipelineStepError

__author__ = 'Matthew L. Bendall'
__copyright__ = "Copyright (C) 2017 Matthew L. Bendall"

def stageparser(parser):
    group1 = parser.add_argument_group('Input/Output')
    group1.add_argument('--align_json', type=existing_file, required=True,
                        help='''JSON file describing alignment (output of pairwise_align
                                stage)''')
    group1.add_argument('--ref_gtf', type=existing_file, required=True,
                        help='''GTF file for reference regions''')
    group1.add_argument('--outfile',
                        help='''Output file. Default is stdout''')
    group3 = parser.add_argument_group('Settings')
    group3.add_argument('--debug', action='store_true',
                        help='Print commands but do not run')
    parser.set_defaults(func=annotate_from_ref)


def annotate_from_ref(align_json=None, align_bam=None, ref_gtf=None, outfile=None,
        outfmt=None,
        debug=False,
    ):
    outh = sys.stdout if outfile is None else open(outfile, 'w')
    jaln = load_slot_json(align_json, 'padded_alignments')    
    
    refmap = {parse_seq_id(k)['ref']:k for k in jaln.keys()}
    for gr in gtf_parser(ref_gtf):
        if gr.feature not in ['gene',]:
            continue
        alignment = jaln[refmap[gr.chrom]]
        ref_s = gr.start - 1
        ref_e = gr.end
        
        # Get alignment start
        for aln_s in xrange(len(alignment)):
            if alignment[aln_s][0] == ref_s:
                break
        while alignment[aln_s][3] == -1:
            aln_s += 1
        
        # Get alignment end
        for aln_e in xrange(len(alignment)-1, -1, -1):
            if alignment[aln_e][0] == ref_e:
                break
        while alignment[aln_e][3] == -1:
            aln_e += -1

        con_s = alignment[aln_s][3]
        con_e = alignment[aln_e][3]
        
        new_gr = GTFRow()
        new_gr.chrom, new_gr.source = (refmap[gr.chrom], 'haphpipe')
        new_gr.feature = gr.feature
        new_gr.start, new_gr.end = (con_s + 1, con_e) 
        new_gr.score, new_gr.strand, new_gr.frame = ('.', gr.strand, gr.frame)
        new_gr.attrs['name'] = gr.attrs['name']
        
        # Include statistics in attributes
        new_gr.attrs.update(get_seg_stats(alignment[aln_s:aln_e+1]))
        # Get the regions that are actually called
        creg = called_regions(alignment[aln_s:aln_e+1])
        new_gr.attrs['call_reg'] = ','.join('%d-%d' % t for t in creg)
        new_gr.attrs['call_len'] = sum((t[1] - t[0] + 1) for t in creg)
        
        print >>outh, new_gr


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Annotate consensus from reference annotation')
    stageparser(parser)
    args = parser.parse_args()
    args.func(**args_params(args))