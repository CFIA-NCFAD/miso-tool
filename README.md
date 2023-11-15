# miso-tool

[![PyPI - Version](https://img.shields.io/pypi/v/miso-tool.svg)](https://pypi.org/project/miso-tool)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/miso-tool.svg)](https://pypi.org/project/miso-tool)

-----

**Table of Contents**

- [Installation](#installation)
- [License](#license)

## About

The **miso-tool** helps you to parse the samples and sequencing runs info from [MISO](https://github.com/miso-lims/miso-lims/) [Pinery](https://github.com/oicr-gsi/pinery) JSON files and generate [Nextflow](https://www.nextflow.io/) samplesheets, sample run info tables, and other useful files.

## Installation

Install from PyPI using `pip` with:

```console
pip install miso-tool
```

## Usage

```
miso-tool --help

 Usage: miso-tool [OPTIONS]

 Parse the samples and sequencing runs info from MISO Pinery JSON files and generate Nextflow samplesheets and other files
 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
 By default, all samples are processed. Use --samples-list to specify a list of samples to process.

 ▌ NOTE: An Illumina Nextflow samplesheet.csv will only be generated if specified and if all Illumina runs have a SampleSheet.csv file that can be read. The output directory will contain the following files:

  • runs_without_rundir.txt: list of MISO run IDs without a corresponding run directory
  • all_sample_run_info.csv: table of all samples and their associated sequencing runs
  • original_to_clean_sample_id.txt: table of original sample IDs and their clean versions
  • nanopore_nextflow_samplesheet_{clean,original}.csv: Nextflow samplesheet for Nanopore runs with clean and original sample names
  • illumina_nextflow_samplesheet_{clean,original}.csv: Nextflow samplesheet for Illumina runs with clean and original sample names
  • sample_run_info.csv: table of user-specified samples and their associated sequencing runs

╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *  --samples-json                   -s      PATH                             MISO Pinery Samples JSON file                                                                                                                                   │
│                                                                              [default: None]                                                                                                                                                 │
│                                                                              [required]                                                                                                                                                      │
│ *  --runs-json                      -r      PATH                             MISO Pinery Runs JSON file                                                                                                                                      │
│                                                                              [default: None]                                                                                                                                                 │
│                                                                              [required]                                                                                                                                                      │
│    --samples-list                   -l      PATH                             Samples to retrieve (one per line)                                                                                                                              │
│                                                                              [default: None]                                                                                                                                                 │
│    --outdir                         -o      PATH                             Output directory                                                                                                                                                │
│                                                                              [default: miso-tool-outdir]                                                                                                                                     │
│    --sample-run-info-csv            -S      PATH                             MISO Pinery Sample Run Info CSV file                                                                                                                            │
│                                                                              [default: None]                                                                                                                                                 │
│    --nanopore-nextflow-samplesheet  -N      PATH                             Nanopore Nextflow samplesheet                                                                                                                                   │
│                                                                              [default: None]                                                                                                                                                 │
│    --illumina-nextflow-samplesheet  -I      PATH                             Illumina Nextflow samplesheet                                                                                                                                   │
│                                                                              [default: None]                                                                                                                                                 │
│    --force                          -f                                       Overwrite existing files                                                                                                                                        │
│    --verbose                        -v                                                                                                                                                                                                       │
│    --version                        -V                                       Print 'gfflu version 0.0.2' and exit                                                                                                                            │
│    --install-completion                     [bash|zsh|fish|powershell|pwsh]  Install completion for the specified shell.                                                                                                                     │
│                                                                              [default: None]                                                                                                                                                 │
│    --show-completion                        [bash|zsh|fish|powershell|pwsh]  Show completion for the specified shell, to copy it or customize the installation.                                                                              │
│                                                                              [default: None]                                                                                                                                                 │
│    --help                                                                    Show this message and exit.                                                                                                                                     │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

 miso-tool version 0.0.2; Python 3.11.5

```

Typical usage:

```bash
miso-tool \
  --samples-json /path/to/samples.json \
  --runs-json /path/to/runs.json \
  --samples-list /path/to/samples.txt \
  --sample-run-info-csv sample-run-info.csv \
  --nanopore-nextflow-samplesheet nanopore-samplesheet.csv \
  --illumina-nextflow-samplesheet illumina-samplesheet.csv \
  --outdir miso-tool-outdir
```

## License

`miso-tool` is distributed under the terms of the [Apache License 2.0](LICENSE.txt).
