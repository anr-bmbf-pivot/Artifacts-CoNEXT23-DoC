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
- `plot_common.py`: Base module for all plotting (`plot_*.py`) scripts.
- `plot_pkt_sizes.py`: Plots the link layer packet sizes of the different message types seen in our
  [`comp` experiments][experiment types] as depicted in Figure 7 in our paper.
- `plot_pkt_sizes_coap.py`: Plots the link layer packet sizes of the different message types seen in
  our [`comp` experiments][experiment types] when using block-wise or GET method as depicted in
  Figure 13 in our paper.
- `plot_pkt_sizes_hypo.py`: Plots the link layer packet sizes of the different message types similar
  to Figure 7 in our paper for different hypothetical packet headers in the lower layers and based
  on the key statistical values for name lengths in DNS from Section 3 of our paper.
- `plot_pkt_sizes_slides.py`: Plots the link layer packet sizes of the different message types seen
  in our [`comp` experiments][experiment types] similar to Figure 7 in our paper but split up for
  slide decks that compare the packet sizes to the resolution time CDFs generated with
  `plot_comp_cdf.py`.
- `plot_build_sizes.py`: Using the output of `collect_build_sizes.py` it plots the build sizes of
  the different compile-time configurations for the [DoC client] as depicted in Figure 8 of our
  paper.
- `plot_baseline.py`: Plots DNS query timestamp to resolution time, similar to Figure 2 in
  [An Empirical Study of the Cost of DNS-over-HTTPS by Böttger et al.][10.1145/3355369.3355575] for
  the [`baseline` experiments][experiment types].
- `plot_baseline_trans.py`: Plots a transmission graph with the DNS query timestamp to event time
  offset to DNS query, similar to Figure 12 in our paper for the
  [`baseline` experiments][experiment types].
- `plot_comp_cdf.py`: Plots the resolution time CDFs for the non-blockwise [`comp`
  experiments][experiment types] as depicted in Figure 9 in our paper.
- `plot_comp_cdf_blockwise.py`: Plots the resolution time CDFs for for block-wise runs of the
  [`comp` experiments][experiment types] as depicted in Figure 10 in our paper.
- `plot_comp_trans.py`: Plots a transmission graph with the DNS query timestamp to event time
  offset to DNS query, similar to Figure 12 in our paper for the [`comp` experiments][experiment
  types].
- `plot_max_age_cdf.py`: Plots the resolution time CDFs for the [`max_age` experiments][experiment
  types], similar to Figures 9 and 10 in our paper.
- `plot_max_age_link_util.py`: Plots a link utilization plot with distance to sink to bytes and L2
  frames, respectively, similar to Figure 11 in our paper for [`max_age` experiments][experiment
  types].
- `plot_max_age_trans.py`: Plots a transmission graph with the DNS query timestamp to event time
  offset to DNS query, as dipicted in Figure 12 in our paper for the [`max_age`
  experiments][experiment types].
- `plot_done.py`: Plots a matrix of all possible and required experiment run configurations and
  how many of each are still missing for the full set of 10 runs.
- `plot_all.sh`: Calls all `plot_*.py` scripts for plots that are provided in our paper.

[experiment types]: ./../exp_ctrl/#experiment-types
[DoC client]: ./../../apps/requester
[10.1145/3355369.3355575]: https://doi.org/10.1145/3355369.3355575
