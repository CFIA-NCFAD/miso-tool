import logging
import re
from collections import defaultdict
from pathlib import Path
from typing import Optional

import pandas as pd
from tqdm import tqdm

NUMBER_OF_PAIRED_END_READS = 2
illumina_read_regex = re.compile(r"^([\w\-\_]+)_S\d+_L\d+_R[12]_001\.fastq\.gz$")

logger = logging.getLogger(__name__)


def get_illumina_samplesheet_path(illumina_run_path: Path) -> Optional[Path]:
    sample_sheet_path = illumina_run_path / "Data/Intensities/BaseCalls/SampleSheet.csv"
    if sample_sheet_path.exists():
        return sample_sheet_path
    for path in illumina_run_path.rglob("SampleSheetUsed.csv"):
        return path
    return None


def read_illumina_samplesheet(path: Path) -> pd.DataFrame:
    with open(path) as fh:
        for line in fh:
            stripped_line = line.strip()
            if stripped_line.startswith("[Data]"):
                break
        return pd.read_csv(fh)


def link_sample_ids_to_reads(
    illumina_runs: list[tuple[str, Path]],
) -> tuple[dict[str, pd.DataFrame], dict[str, dict[str, list[Path]]], set[tuple[str, str]]]:
    illumina_run_to_samplesheet = {}
    irun_to_sample_id_to_paths: dict[str, dict[str, list[Path]]] = {}
    sampleids_not_found = set()
    for run_name, run_path in tqdm(illumina_runs, desc="Processing Illumina runs"):
        try:
            ss = get_illumina_samplesheet_path(run_path)
            if ss is None:
                logger.warning(f"No samplesheet found for run '{run_name}' at '{run_path}'")
                continue
            df_illumina_ss = read_illumina_samplesheet(ss)
            illumina_run_to_samplesheet[run_name] = df_illumina_ss
            id_to_path = defaultdict(list)
            fastqdir = next(ss.parent.rglob("*.fastq.gz")).parent
            for p in fastqdir.glob("*.fastq.gz"):
                m = illumina_read_regex.match(p.name)
                if not m:
                    logger.warning(f"Could not parse {p.name}")
                    continue
                sample_id = m.groups()[0]
                # clean Illumina samplesheet.csv sample ID to match FASTQ filename prefix
                sample_id = sample_id.replace("_", "-").replace("--", "-")
                id_to_path[sample_id].append(p)
            for sid, paths in id_to_path.items():
                if len(paths) != NUMBER_OF_PAIRED_END_READS:
                    logger.warning(f"Could not find both reads for {sid}")
                    continue
            for row in df_illumina_ss.itertuples():
                sample_id = row.Sample_ID
                sample_id = sample_id.replace("_", "-").replace("--", "-")
                if sample_id not in id_to_path:
                    sampleids_not_found.add((sample_id, run_name))
                    continue
                if run_name not in irun_to_sample_id_to_paths:
                    irun_to_sample_id_to_paths[run_name] = {sample_id: id_to_path[sample_id]}
                else:
                    irun_to_sample_id_to_paths[run_name][sample_id] = id_to_path[sample_id]
        except FileNotFoundError:
            logger.warning(f"Could not find samplesheet for {run_name}")
    return illumina_run_to_samplesheet, irun_to_sample_id_to_paths, sampleids_not_found


def find_illumina_sample_id_by_indexes(df: pd.DataFrame, index: str, index2: str) -> str:
    sample_ids = df.query(f'index == "{index}" and index2 == "{index2}"')["Sample_ID"]
    if len(sample_ids) > 0:
        return sample_ids.values[0].replace("_", "-").replace("--", "-")
    return ""


def illumina_run_sample_to_nextflow_samplesheet_entry(
    sample_run_info: dict,
    irun_to_sample_id_to_paths: dict[str, dict[str, list[Path]]],
    irun_to_samplesheet: dict[str, pd.DataFrame],
    use_clean_sample_names: bool = False,
) -> dict[str, str] | None:
    submission_name = (
        sample_run_info["submission_name"] if not use_clean_sample_names else sample_run_info["clean_submission_name"]
    )
    run_name = sample_run_info["run_name"]
    barcode = sample_run_info["barcode"]
    barcode_two = sample_run_info["barcode_two"]
    if barcode and barcode_two:
        sample_id = find_illumina_sample_id_by_indexes(irun_to_samplesheet[run_name], barcode, barcode_two)
        if sample_id:
            reads_paths = irun_to_sample_id_to_paths[run_name][sample_id]
            reads_paths.sort()

            return {
                "sample": submission_name,
                "fastq_1": str(reads_paths[0].resolve().absolute()),
                "fastq_2": str(reads_paths[1].resolve().absolute()),
            }
    return None


def to_illumina_nextflow_df(illumina_sample_run_infos: list[dict]) -> tuple[pd.DataFrame, pd.DataFrame]:
    illumina_entries_clean = []
    illumina_entries_original = []
    runs_dict = {x["run_name"]: Path(x["run_path"]) for x in illumina_sample_run_infos}
    runs = list(runs_dict.items())
    logger.info(f"Checking that all {len(runs)} Illumina runs have a SampleSheet.csv file that can be read.")
    for run_name, run_path in tqdm(runs, desc="Checking Illumina runs"):
        ss = get_illumina_samplesheet_path(run_path)
        if ss is None:
            logger.warning(f"No samplesheet found for run '{run_name}' at '{run_path}'")
            continue
        if not ss.exists() or not ss.is_file() or not ss.stat().st_size > 0:
            error_msg = f"Could not find samplesheet.csv for {run_name} at '{ss}'"
            raise FileNotFoundError(error_msg)
    logger.info(f"Reading SampleSheet.csv files for {len(runs)} Illumina runs")
    illumina_run_to_samplesheet, irun_to_sample_id_to_paths, sampleids_not_found = link_sample_ids_to_reads(runs)
    if len(sampleids_not_found) > 0:
        logger.warning(f"Could not find {len(sampleids_not_found)} sample IDs in Illumina runs: {sampleids_not_found}")
    for entry in illumina_sample_run_infos:
        nf_entry_clean = illumina_run_sample_to_nextflow_samplesheet_entry(
            entry, irun_to_sample_id_to_paths, illumina_run_to_samplesheet, use_clean_sample_names=True
        )
        nf_entry_original = illumina_run_sample_to_nextflow_samplesheet_entry(
            entry, irun_to_sample_id_to_paths, illumina_run_to_samplesheet, use_clean_sample_names=False
        )
        if nf_entry_clean:
            illumina_entries_clean.append(nf_entry_clean)
        if nf_entry_original:
            illumina_entries_original.append(nf_entry_original)
    return pd.DataFrame(illumina_entries_original), pd.DataFrame(illumina_entries_clean)


def get_illumina_sample_run_infos(filtered_entries):
    out = []
    # regex to match run name, e.g. 200319_M04594_0113_000000000-G55GW
    regex_illumina_run_name = re.compile(r"^\d{6}_\w+_\d{4}_\d{9}-\w{5}$")
    for entry in filtered_entries:
        run_name = entry["run_name"]
        if regex_illumina_run_name.match(run_name):
            out.append(entry)
            continue
        barcode = entry.get("barcode", None)
        barcode2 = entry.get("barcode_two", None)
        if barcode and barcode2:
            out.append(entry)
            continue
        flowcell = entry["flowcell"]
        if "MiSeq" in flowcell:
            out.append(entry)
            continue
    return out
