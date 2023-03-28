# Scripts to process and plot experiments results
## Overview
The scripts in this directory serve the processing and plotting of the experiment results as
described in Section 6 _Comparison of Low-power Transports_ and Section 7 _Evaluation of Caching for
  DoC_.

- `parse_baseline_results.py`: Parses the logs of [`baseline` experiments][experiment types] and
  reformats them to CSV tables.
- `parse_comp_results.py`: Parses the logs of [`comp` experiments][experiment types] and reformats
  them to CSV tables.
- `parse_max_age_results.py`: Parses the logs of [`max_age` experiments][experiment types] and
  reformats them to CSV tables.
- `parse_max_age_link_util.py`: Parses the PCAP files of [`max_age` experiments][experiment types]
  for link utilization and stores the results in
  [`doc-eval-max_age-link_utilization.csv`](../../results/doc-eval-max_age-link_utilization.csv) in
  the results directory.
- `collect_build_sizes.py`: Builds the [DoC client] and parses out the build sizes for a selection
  of its modules under different compile time configurations.


[experiment types]: ./../exp_ctrl/#experiment-types
[DoC client]: ./../../apps/requester
