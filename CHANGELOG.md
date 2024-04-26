# miso-tool changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.6](https://github.com/CFIA-NCFAD/miso-tool/releases/tag/0.0.6) - 2024-04-26

Add support for Nanopore native barcoding kit SQK-NBD114-96.

## [0.0.5](https://github.com/CFIA-NCFAD/miso-tool/releases/tag/0.0.5) - 2023-12-

Illumina MiSeq with MiSeq Control Software v4.0.0 outputs FASTQ files to a different destination. This version of miso-tool adds support for this new destination.

## [0.0.4](https://github.com/CFIA-NCFAD/miso-tool/releases/tag/0.0.4) - 2023-12-18

Added support for SQK-RBK114-96, which has the same barcode sequences as SQK-RBK110-96.

## [0.0.3](https://github.com/CFIA-NCFAD/miso-tool/releases/tag/0.0.3) - 2023-11-15

Add Rich as dependency since it's not automatically installed with Typer.

## [0.0.2](https://github.com/CFIA-NCFAD/miso-tool/releases/tag/0.0.2) - 2023-11-15

Fixed issue with Nanopore samplesheet generation when the barcode is not specified (i.e. `None`).

## [0.0.1](https://github.com/CFIA-NCFAD/miso-tool/releases/tag/0.0.1) - 2023-11-15

First release of miso-tool.
