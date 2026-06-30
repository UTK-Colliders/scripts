# Scripts
Useful scripts frequently used in HEP

# L1NtubleMaker Crab Jobs
To submit L1NtubleMaker Crab Jobs:

1- Put [submit_crab_l1tt.py](https://github.com/UTK-Colliders/scripts/blob/main/submit_crab_l1tt.py) and [customise_L1TrackNtupleMaker.py](https://github.com/UTK-Colliders/scripts/blob/main/customise_L1TrackNtupleMaker.py) in your `src/L1Trigger/TrackFindingTracklet/test` directory

2- Run `voms-proxy-init --rfc --voms cms -valid 192:00` and `cmsenv`

3- Run `python3 submit_crab_l1tt.py customise_L1TrackNtupleMaker.py <sample> -n 10 -d outdir -a tag`

You can use one of the samples defined in [sample_dict](https://github.com/UTK-Colliders/scripts/blob/5dcee048f6ee8d313d11dcdccc5c1013b8486589/submit_crab_l1tt.py#L39) or define your own

This will:

A- Generate a CRAB config (`crab_cfg_<sample>.py`) under `<outdir>/<addtag>/` 

B- Submit via `crab submit` (you can skip submission with `-t / --test` if you want check the crab_cfg file first)
