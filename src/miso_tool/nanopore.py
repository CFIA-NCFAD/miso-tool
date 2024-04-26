import pandas as pd

from miso_tool.const.nanopore import nbd114_96, rbk11096
from miso_tool.util import revcomp


def get_rbk11096_barcode(barcode: str) -> str | None:
    if barcode in rbk11096:
        return rbk11096[barcode]
    else:
        rc = revcomp(barcode)
        if rc in rbk11096:
            return rbk11096[rc]
        else:
            return None


def get_nbd11496_barcode(barcode: str) -> str | None:
    if barcode in nbd114_96:
        return nbd114_96[barcode]
    else:
        rc = revcomp(barcode)
        if rc in nbd114_96:
            return nbd114_96[rc]
        else:
            return None


def get_nanopore_sample_run_infos(filtered_entries):
    out = []
    for entry in filtered_entries:
        barcode = entry["barcode"]
        if barcode and barcode.startswith("barcode"):
            out.append(entry)
            continue
        flowcell = entry["flowcell"]
        if flowcell.startswith("FLO") or "Nanopore" in flowcell:
            out.append(entry)
            continue
    return out


def to_nanopore_nextflow_df(nanopore_sample_run_infos: list[dict], use_clean_names: bool = False) -> pd.DataFrame:
    nanopore_entries = []
    for entry in nanopore_sample_run_infos:
        nanopore_entries.append(
            {
                "sample": entry["clean_submission_name"] if use_clean_names else entry["submission_name"],
                "reads": f'{entry["run_path"]}/fastq_pass/{entry["barcode"]}',
            }
        )
    return pd.DataFrame(nanopore_entries)
