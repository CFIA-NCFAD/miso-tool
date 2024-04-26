import pandas as pd

from miso_tool.barcodes.nanopore import NBD114_96, RBK110_96
from miso_tool.util import revcomp


def get_rbk11096_barcode(barcode: str) -> str | None:
    if barcode in RBK110_96:
        return RBK110_96[barcode]
    rc = revcomp(barcode)
    return RBK110_96[rc] if rc in RBK110_96 else None


def get_nbd11496_barcode(barcode: str) -> str | None:
    if barcode in NBD114_96:
        return NBD114_96[barcode]
    rc = revcomp(barcode)
    return NBD114_96[rc] if rc in NBD114_96 else None


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
    nanopore_entries = [
        {
            "sample": entry["clean_submission_name"] if use_clean_names else entry["submission_name"],
            "reads": f'{entry["run_path"]}/fastq_pass/{entry["barcode"]}',
        }
        for entry in nanopore_sample_run_infos
    ]
    return pd.DataFrame(nanopore_entries)
