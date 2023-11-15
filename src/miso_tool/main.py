import logging
from collections import defaultdict
from pathlib import Path
from typing import Optional

import pandas as pd

from miso_tool.cleaning import fix_lsts_sample_name
from miso_tool.illumina import get_illumina_sample_run_infos, to_illumina_nextflow_df
from miso_tool.io import parse_runs_from_json, parse_samples_json
from miso_tool.nanopore import get_nanopore_sample_run_infos, to_nanopore_nextflow_df
from miso_tool.samples import SamplesRunsInfo, get_sample_and_run_infos, process_samples
from miso_tool.seqruns import get_sample_ldi_to_run, has_samples

logger = logging.getLogger(__name__)


def process(
    outdir: Path,
    samples_json: Path,
    runs_json: Path,
    samples_list: Optional[Path],
    sample_run_info_csv: Optional[Path],
    nanopore_nextflow_samplesheet: Optional[Path],
    illumina_nextflow_samplesheet: Optional[Path],
):
    id_to_sample = parse_samples_json(samples_json)
    logger.info(f"Loaded {len(id_to_sample)} samples from {samples_json}")
    id_to_run = parse_runs_from_json(runs_json)
    logger.info(f"Loaded {len(id_to_run)} runs from {runs_json}")
    runs_with_samples = {k: v for k, v in id_to_run.items() if has_samples(v)}
    runs_with_no_samples = {k: v for k, v in id_to_run.items() if not has_samples(v)}
    sample_ldi_to_run = get_sample_ldi_to_run(runs_with_samples)
    logger.info(f"Found {len(runs_with_samples)} runs with samples")
    logger.warning(f"Found {len(runs_with_no_samples)} runs with no samples!")
    sri: SamplesRunsInfo = process_samples(id_to_sample)
    sri.id_to_run = id_to_run
    sri.runs_with_samples = runs_with_samples
    sri.runs_with_no_samples = runs_with_no_samples
    sri.sample_ldi_to_run = sample_ldi_to_run
    original_to_clean_sample_id = clean_all_sample_names(sri)
    clean_to_original_sample_ids = defaultdict(list)
    for k, v in original_to_clean_sample_id.items():
        clean_to_original_sample_ids[v].append(k)
    with open(outdir / "original_to_clean_sample_id.txt", "w") as f:
        for k, v in original_to_clean_sample_id.items():
            if k != v:
                f.write(f"{k}\t{v}\n")
    if samples_list is not None:
        sample_ids = [line.strip() for line in samples_list.read_text().splitlines() if line.strip()]
        logger.info(f"Loaded {len(sample_ids)} sample IDs from {samples_list}")
        if len(sample_ids) == 0:
            error_msg = f"No samples found! Are you sure '{samples_list}' contains sample IDs?"
            raise Exception(error_msg)
        sample_ids_set = set(sample_ids)
        missing = sample_ids_set - set(original_to_clean_sample_id.keys()) - set(clean_to_original_sample_ids.keys())
        if len(missing) > 0:
            logger.warning(f"Missing {len(missing)} sample IDs: {missing}")
        else:
            logger.info(
                f"All {len(sample_ids)} samples found! "
                f"{len(sample_ids_set & set(original_to_clean_sample_id.keys()))} / {len(sample_ids_set)} "
                "original sample IDs. "
                f"{len(sample_ids_set & set(clean_to_original_sample_ids.keys()))} / {len(sample_ids_set)} "
                " clean sample IDs"
            )
    else:
        # get identity samples with LDI children and linked to a run
        sample_ids = []
        for ldi in sample_ldi_to_run.keys():
            if ldi in sri.ldi_sample_to_root_name:
                sample_ids.append(sri.ldi_sample_to_root_name[ldi])
            else:
                logger.warning(
                    f'Could not find root/identity sample for {ldi} (run {sample_ldi_to_run[ldi][0]["name"]})'
                )
        logger.info(f"Processing all {len(sample_ids)} samples associated with sequencing runs.")

    entries, runs_without_rundir = get_sample_and_run_infos(sri.sample_ldi_to_run, sri.ldi_sample_to_path)
    df_all_entries = pd.DataFrame(entries)
    df_all_entries.to_csv(outdir / "all_sample_run_info.csv", index=False)
    logger.info(f'Wrote {len(entries)} entries to {outdir / "all_sample_run_info.csv"}')
    with open(outdir / "runs_without_rundir.txt", "w") as f:
        for run in runs_without_rundir:
            f.write(f"{run}\n")
    subname_to_entry = defaultdict(list)
    for entry in entries:
        subname_to_entry[entry["submission_name"]].append(entry)
    logger.info(f"Found {len(subname_to_entry)} unique submission names")
    clean_name_to_entry = defaultdict(list)
    for entry in entries:
        submission_name = entry["submission_name"]
        clean_name = original_to_clean_sample_id.get(submission_name, submission_name)
        entry["clean_submission_name"] = clean_name
        clean_name_to_entry[clean_name].append(entry)
    logger.info(f"Found {len(clean_name_to_entry)} unique clean sample names")
    filtered_entries = []
    for sample_id in sample_ids:
        if sample_id in clean_name_to_entry:
            filtered_entries.extend(clean_name_to_entry[sample_id])
        elif sample_id in subname_to_entry:
            filtered_entries.extend(subname_to_entry[sample_id])
        else:
            logger.warning(f"Could not find sample {sample_id}")
    if len(filtered_entries) == 0:
        error_msg = (
            f"No entries found! Are you sure '{samples_list}' "
            f"has sample IDs present in MISO Identity Sample external names?"
        )
        raise ValueError(error_msg)
    logger.info(f"Found {len(filtered_entries)} entries for {len(sample_ids)} samples")
    if len(filtered_entries) < len(sample_ids):
        logger.warning(f"Found {len(filtered_entries)} entries but {len(sample_ids)} sample IDs")
        clean_submission_names = {x["clean_submission_name"] for x in filtered_entries}
        missing = set(sample_ids) - clean_submission_names
        logger.warning(f"Missing {len(missing)} sample IDs: {missing}")
    df = pd.DataFrame(filtered_entries)
    if sample_run_info_csv is None:
        sample_run_info_csv = outdir / "sample_run_info.csv"
    df.to_csv(sample_run_info_csv, index=False)
    logger.info(f"Wrote {len(df)} entries to {sample_run_info_csv}")
    nanopore_sample_run_infos = get_nanopore_sample_run_infos(filtered_entries)
    if len(nanopore_sample_run_infos) > 0:
        df_nanopore_original = to_nanopore_nextflow_df(nanopore_sample_run_infos, use_clean_names=False)
        df_nanopore_original.to_csv(outdir / "nanopore_nextflow_samplesheet_original.csv", index=False)
        df_nanopore_clean = to_nanopore_nextflow_df(nanopore_sample_run_infos, use_clean_names=True)
        df_nanopore_clean.to_csv(outdir / "nanopore_nextflow_samplesheet_clean.csv", index=False)
        logger.info(
            f'Wrote {len(nanopore_sample_run_infos)} entries to '
            f'"{outdir / "nanopore_nextflow_samplesheet_original.csv"}" and '
            f'"{outdir / "nanopore_nextflow_samplesheet_clean.csv"}"'
        )
        if nanopore_nextflow_samplesheet is not None:
            df_nanopore_clean.to_csv(nanopore_nextflow_samplesheet, index=False)
            logger.info(f'Wrote {len(nanopore_sample_run_infos)} entries to "{nanopore_nextflow_samplesheet}"')
    if illumina_nextflow_samplesheet is not None:
        logger.info(f"Illumina Nextflow samplesheet specified: {illumina_nextflow_samplesheet}")
        illumina_sample_run_infos = get_illumina_sample_run_infos(filtered_entries)
        logger.info(f"Found {len(illumina_sample_run_infos)} Illumina sample run infos")
        if len(illumina_sample_run_infos) > 0:
            logger.warning(f"Linking {len(illumina_sample_run_infos)} MISO samples to Illumina reads may take a while.")

            df_illumina_original, df_illumina_clean = to_illumina_nextflow_df(illumina_sample_run_infos)
            df_illumina_original.to_csv(outdir / "illumina_nextflow_samplesheet_original.csv", index=False)
            df_illumina_original.to_csv(illumina_nextflow_samplesheet, index=False)
            logger.info(
                f'Wrote {len(illumina_sample_run_infos)} entries with unmodified sample names to '
                f'"{illumina_nextflow_samplesheet}" and '
                f'"{outdir / "illumina_nextflow_samplesheet_original.csv"}"'
            )
            df_illumina_clean.to_csv(outdir / "illumina_nextflow_samplesheet_clean.csv", index=False)
            logger.info(
                f'Wrote {len(illumina_sample_run_infos)} entries with cleaned sample names to '
                f'"{outdir / "illumina_nextflow_samplesheet_clean.csv"}"'
            )
    logger.info(f'Done! See "{outdir}" for output files.')


def clean_all_sample_names(samples_runs_info: SamplesRunsInfo) -> dict[str, str]:
    original_to_clean_sample_id = {}
    for ldi_sample_id, submission_name in samples_runs_info.ldi_sample_to_root_name.items():
        runs = samples_runs_info.sample_ldi_to_run[ldi_sample_id]
        if len(runs) == 0:
            run = None
        elif len(runs) > 1:
            logger.warning(f"Found multiple runs for '{submission_name}'. Using the first one.")
            run = runs[0]
        else:
            run = runs[0]
        clean_name = fix_lsts_sample_name(
            submission_name, run_start_date=run["start_date"] if run and "start_date" in run else None
        )
        original_to_clean_sample_id[submission_name] = clean_name
    return original_to_clean_sample_id


def get_run(samples_runs_info: SamplesRunsInfo, sample_id: str) -> dict | None:
    run = None
    if sample_id in samples_runs_info.ext_name_to_ldi_samples:
        ldi_samples = samples_runs_info.ext_name_to_ldi_samples[sample_id]
        if len(ldi_samples) > 1:
            logger.warning(
                f"Found multiple LDI samples for {sample_id} ({ldi_samples}). Using the first one linked to run."
            )
        run = None
        for ldi_sample in ldi_samples:
            runs = samples_runs_info.sample_ldi_to_run[ldi_sample]
            if len(runs) == 0:
                logger.warning(f"Could not find run for {sample_id} and LDI sample {ldi_sample}")
                continue
            if len(runs) > 1:
                logger.warning(f"Found multiple runs for {sample_id}. Using the first one.")
                run = runs[0]
                break
    return run
