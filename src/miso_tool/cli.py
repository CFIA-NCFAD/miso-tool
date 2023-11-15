#!/usr/bin/env python
import logging
import sys
from pathlib import Path
from typing import Optional

import typer

from miso_tool.__about__ import __version__
from miso_tool.main import process

EPILOG = (
    f"miso-tool version {__version__}; "
    f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
)

app = typer.Typer(rich_markup_mode="markdown", epilog=EPILOG)

logger = logging.getLogger(__name__)


def init_logging(level: int):
    from rich.logging import RichHandler
    from rich.traceback import install

    install(show_locals=False, width=200, word_wrap=True)
    logging.basicConfig(
        format="%(message)s",
        datefmt="[%Y-%m-%d %X]",
        level=level,
        handlers=[RichHandler(rich_tracebacks=True, tracebacks_show_locals=True)],
    )


def version_callback(value: bool):
    if value:
        typer.echo(f"miso-tool version {__version__}")
        raise typer.Exit()


@app.command(epilog=EPILOG)
def run(
    samples_json: Path = typer.Option(..., "--samples-json", "-s", help="MISO Pinery Samples JSON file"),
    runs_json: Path = typer.Option(..., "--runs-json", "-r", help="MISO Pinery Runs JSON file"),
    samples_list: Optional[Path] = typer.Option(
        None, "--samples-list", "-l", help="Samples to retrieve (one per line)"
    ),
    outdir: Path = typer.Option(Path("miso-tool-outdir"), "--outdir", "-o", help="Output directory"),
    sample_run_info_csv: Optional[Path] = typer.Option(
        None, "--sample-run-info-csv", "-S", help="MISO Pinery Sample Run Info CSV file"
    ),
    nanopore_nextflow_samplesheet: Optional[Path] = typer.Option(
        None, "--nanopore-nextflow-samplesheet", "-N", help="Nanopore Nextflow samplesheet"
    ),
    illumina_nextflow_samplesheet: Optional[Path] = typer.Option(
        None, "--illumina-nextflow-samplesheet", "-I", help="Illumina Nextflow samplesheet"
    ),
    force: bool = typer.Option(False, "--force", "-f", is_flag=True, help="Overwrite existing files"),
    verbose: bool = typer.Option(False, "--verbose", "-v", is_flag=True),
    version: Optional[bool] = typer.Option(  # noqa: ARG001
        None,
        "--version",
        "-V",
        callback=version_callback,
        help=f"Print 'gfflu version {__version__}' and exit",
    ),
):
    """Parse the samples and sequencing runs info from MISO Pinery JSON files and generate Nextflow samplesheets
    and other files

    ---

    By default, all samples are processed. Use --samples-list to specify a list of samples to process.

    > **NOTE**: An Illumina Nextflow samplesheet.csv will only be generated if specified and if all Illumina runs have
    a SampleSheet.csv file that can be read.


    The output directory will contain the following files:

    - `runs_without_rundir.txt`: list of MISO run IDs without a corresponding run directory

    - `all_sample_run_info.csv`: table of all samples and their associated sequencing runs

    - `original_to_clean_sample_id.txt`: table of original sample IDs and their clean versions

    - `nanopore_nextflow_samplesheet_{clean,original}.csv`: Nextflow samplesheet for Nanopore runs with clean and
    original sample names

    - `illumina_nextflow_samplesheet_{clean,original}.csv`: Nextflow samplesheet for Illumina runs with clean and
    original sample names

    - `sample_run_info.csv`: table of user-specified samples and their associated sequencing runs
    """
    init_logging(logging.DEBUG if verbose else logging.INFO)
    # run CLI mode
    if samples_json is None:
        typer.echo("ERROR: --samples-json is required")
        raise typer.Exit(1)
    if not samples_json.exists():
        typer.echo(f"ERROR: {samples_json} does not exist")
        raise typer.Exit(1)
    if runs_json is None:
        typer.echo("ERROR: --runs-json is required")
        raise typer.Exit(1)
    if not runs_json.exists():
        typer.echo(f"ERROR: {runs_json} does not exist")
        raise typer.Exit(1)
    if samples_list is None:
        logger.warning("--samples-list not specified, will process all samples")
    if samples_list is not None and not samples_list.exists():
        typer.echo(f"ERROR: {samples_list} does not exist")
        raise typer.Exit(1)
    if sample_run_info_csv is not None and sample_run_info_csv.exists() and not force:
        typer.echo(f"ERROR: {sample_run_info_csv} exists, use --force to overwrite")
        raise typer.Exit(1)
    if nanopore_nextflow_samplesheet is not None and nanopore_nextflow_samplesheet.exists() and not force:
        typer.echo(f"ERROR: {nanopore_nextflow_samplesheet} exists, use --force to overwrite")
        raise typer.Exit(1)
    if illumina_nextflow_samplesheet is not None and illumina_nextflow_samplesheet.exists() and not force:
        typer.echo(f"ERROR: {illumina_nextflow_samplesheet} exists, use --force to overwrite")
        raise typer.Exit(1)
    if outdir.exists() and not force:
        typer.echo(f"ERROR: {outdir} exists, use --force to overwrite")
        raise typer.Exit(1)
    if not outdir.exists():
        outdir.mkdir(parents=True)
    process(
        outdir=outdir,
        samples_json=samples_json,
        runs_json=runs_json,
        samples_list=samples_list,
        sample_run_info_csv=sample_run_info_csv,
        nanopore_nextflow_samplesheet=nanopore_nextflow_samplesheet,
        illumina_nextflow_samplesheet=illumina_nextflow_samplesheet,
    )


if __name__ == "__main__":
    app()
