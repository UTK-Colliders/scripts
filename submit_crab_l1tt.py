#!/bin/env python
"""
CRAB submission script

Usage (identical CLI to the condor version):
  python3 submit_crab_l1tt.py customise_L1TrackNtupleMaker.py DispSUSY_PU200 -n 10 -d outdir -a tag

What it does:
  1. Generates a CRAB config (crab_cfg_<sample>.py) under <outdir>/<addtag>/
  2. Submits via `crab submit` (skip with -t / --test)
"""

import os
import datetime
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("analyzer", help="CMSSW pset to run (e.g. customise_L1TrackNtupleMaker.py)",
                    default="customise_L1TrackNtupleMaker.py")
parser.add_argument("sample",  help="sample key (must match sample_dict)",
                    default="DispSUSY_PU200")
parser.add_argument("-n", "--njobs",  dest="njobs",  type=int,
                    help="number of input files to process (-1 = all)", default=-1)
parser.add_argument("-d", "--outdir", dest="outdir",
                    help="output sub-directory label",                  default="ntuples")
parser.add_argument("-a", "--addtag", dest="addtag",
                    help="additional tag for output dir / CRAB request", default="ntuples")
parser.add_argument("-c", "--cores",  dest="cores",  type=int,
                    help="number of cores per job (default 1)",         default=1)
parser.add_argument("-t", "--test",   dest="test", action="store_true",
                    help="generate config but do NOT submit",           default=False)
args = parser.parse_args()


# ── auto-detect username ───────────────────────────────────────────────
username = os.environ.get('USER') or os.environ.get('LOGNAME') or os.getlogin()
initial  = username[0]


# ── sample dictionary (same as condor version) ─────────────────────────
sample_dict = {
    'DispSUSY_PU200': '/DisplacedSUSY_stopToBottom_M-800_50mm_TuneCP5_14TeV-pythia8'
                      '/Phase2Spring24DIGIRECOMiniAOD-PU200_AllTP_140X_mcRun4_realistic_v4-v1'
                      '/GEN-SIM-DIGI-RAW-MINIAOD',
    'TTbar':          '/RelValTTbar_14TeV'
                      '/CMSSW_14_0_0_pre2-PU_133X_mcRun4_realistic_v1_STD_2026D98_PU200_RV229-v1'
                      '/GEN-SIM-DIGI-RAW',
    'DoubleMu_PU0':   '/RelValDoubleMuFlatPt1To100Dxy100GunProducer'
                       '/CMSSW_15_1_0_pre5-150X_mcRun4_realistic_v1_RV269_Run4D110_noPU-v1'
                       '/GEN-SIM-DIGI-RAW',
}


# ── derived quantities ─────────────────────────────────────────────────
ds_name   = sample_dict[args.sample]
pset      = os.path.realpath(args.analyzer)
base_out  = '%s/%s' % (args.outdir, args.addtag)
timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

# CRAB requestName: <=100 chars, [a-zA-Z0-9_] only
request_name = '%s_%s_%s_%s' % (args.sample, args.outdir, args.addtag, timestamp)
request_name = request_name.replace('-', '_').replace(' ', '_')[:100]

# Output goes to personal EOS: /eos/user/<initial>/<username>/<outdir>/<addtag>/
# T3_CH_CERNBOX maps /store/user/<user>/ -> /eos/user/<initial>/<user>/
eos_lfn_base = '/store/user/%s/%s/' % (username, base_out)

# totalUnits limits files processed (same role as -n in condor script)
total_units_line = ''
if args.njobs > 0:
    total_units_line = 'config.Data.totalUnits          = %d' % args.njobs

# ── multi-core: memory scales with cores ───────────────────────────────
mem_per_core = 2500
memory_mb    = mem_per_core * args.cores
ncores       = args.cores

# ── create output directory & write CRAB config ────────────────────────
os.makedirs(base_out, exist_ok=True)
cfg_path = os.path.join(base_out, 'crab_cfg_%s.py' % args.sample)

crab_cfg = """\
from CRABClient.UserUtilities import config
config = config()

# ── General ──────────────────────────────────────────────────────────────
config.General.requestName          = '{request_name}'
config.General.workArea             = '{base_out}/crab_projects'
config.General.transferOutputs      = True
config.General.transferLogs         = True

# ── JobType ──────────────────────────────────────────────────────────────
config.JobType.pluginName           = 'Analysis'
config.JobType.psetName             = '{pset}'
# The pset uses TFileService -> outputHLT.root; CRAB needs this declared
config.JobType.outputFiles          = ['outputHLT.root']
config.JobType.maxMemoryMB          = {memory_mb}
config.JobType.numCores             = {ncores}
# condor +JobFlavour "tomorrow" ~ 24 h
config.JobType.maxJobRuntimeMin     = 1440

# ── Data ─────────────────────────────────────────────────────────────────
config.Data.inputDataset            = '{dataset}'
config.Data.inputDBS                = 'global'
config.Data.splitting               = 'FileBased'
config.Data.unitsPerJob             = 1          # one file per job (same as condor)
{total_units_line}
config.Data.outLFNDirBase           = '{eos_lfn_base}'
config.Data.outputDatasetTag        = '{addtag}'
config.Data.publication             = False
# Allow jobs to run at ANY site (read input via XRootD) -- faster scheduling
config.Data.ignoreLocality          = True

# ── Site ─────────────────────────────────────────────────────────────────
# T3_CH_CERNBOX writes to /eos/user/<initial>/<username>/
config.Site.storageSite             = 'T3_CH_CERNBOX'
# Open up scheduling to all T1/T2/T3 sites
config.Site.whitelist               = ['T1_*', 'T2_*', 'T3_*']
""".format(
    request_name     = request_name,
    base_out         = base_out,
    pset             = pset,
    dataset          = ds_name,
    total_units_line = total_units_line,
    eos_lfn_base     = eos_lfn_base,
    addtag           = args.addtag,
    memory_mb        = memory_mb,
    ncores           = ncores,
)

with open(cfg_path, 'w') as f:
    f.write(crab_cfg)

# ── summary ─────────────────────────────────────────────────────────────
njobs_str = str(args.njobs) if args.njobs > 0 else 'ALL'
print('──────────────────────────────────────────────')
print('CRAB config written to : %s' % cfg_path)
print('Request name           : %s' % request_name)
print('Dataset                : %s' % ds_name)
print('Files to process       : %s' % njobs_str)
print('Cores / Memory per job : %d / %d MB' % (ncores, memory_mb))
print('Ignore locality        : True')
print('Output LFN base        : %s' % eos_lfn_base)
print('Storage site           : T3_CH_CERNBOX')
print('  -> /eos/user/%s/%s/%s/' % (initial, username, base_out))
print('──────────────────────────────────────────────')

if not args.test:
    cmd = 'crab submit -c %s' % cfg_path
    print('Submitting: %s' % cmd)
    os.system(cmd)
else:
    print('[TEST MODE] To submit manually run:')
    print('  crab submit -c %s' % cfg_path)
