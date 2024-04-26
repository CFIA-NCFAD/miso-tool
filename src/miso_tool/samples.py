import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from miso_tool.nanopore import get_nbd11496_barcode, get_rbk11096_barcode

logger = logging.getLogger(__name__)


@dataclass
class SamplesRunsInfo:
    id_to_sample: dict[str, dict]
    id_to_run: dict[int, dict]
    runs_with_samples: dict[int, dict]
    runs_with_no_samples: dict[int, dict]
    sample_ldi_to_run: dict[str, list[dict]]
    ldi_sample_to_path: dict[str, list[dict]]
    ext_name_to_ldi_samples: dict[str, list[str]]
    ldi_sample_to_organism: dict[str, str]
    ldi_sample_to_root_name: dict[str, str]


def parse_samples_json(json_path: Path) -> dict[str, dict]:
    with json_path.open() as f:
        samples = json.load(f)
    return {s["id"]: s for s in samples}


def get_identity_sample_from_path(sample_path: list[dict]) -> dict | None:
    for x in sample_path:
        try:
            if x["sample_type"] == "Identity":
                return x
        except KeyError:
            continue
    return None


def get_parents_path(sample_id: str, id_to_data: dict) -> list[dict]:
    out = []
    sample_data = id_to_data[sample_id]
    out.append(sample_data)
    while "parents" in sample_data:
        sample_data = id_to_data[sample_data["parents"][0]["id"]]
        out.append(sample_data)
    return out


def find_terminal_samples(samples: dict[str, dict]) -> dict[str, dict]:
    return {k: s for k, s in samples.items() if "children" not in s}


def process_samples(id_to_sample: dict[str, dict]) -> SamplesRunsInfo:
    terminal_samples = find_terminal_samples(id_to_sample)
    # for LDI prefix samples, group by root sample external name
    ldi_samples: dict[str, dict] = {k: s for k, s in terminal_samples.items() if k.startswith("LDI")}
    ldi_sample_to_path: dict[str, list[dict]] = {k: get_parents_path(k, id_to_sample) for k in ldi_samples.keys()}
    ldi_sample_to_root: dict[str, dict] = {}  # type: ignore
    for k, v in ldi_sample_to_path.items():
        if v is None:
            continue
        ident_sample = get_identity_sample_from_path(v)
        if ident_sample is None:
            continue
        ldi_sample_to_root[k] = ident_sample

    ldi_sample_to_organism: dict[str, str] = {}
    for k, v in ldi_sample_to_root.items():  # type: ignore
        if v is None:
            continue
        organism = get_organism(v)  # type: ignore
        if organism is None:
            continue
        ldi_sample_to_organism[k] = organism
    ldi_sample_to_root_name: dict[str, str] = {}
    for k, v in ldi_sample_to_root.items():  # type: ignore
        if v is None:
            continue
        name = get_external_name(v)  # type: ignore
        if name is None:
            continue
        ldi_sample_to_root_name[k] = name
    ext_name_to_ldi_samples: dict[str, list[str]] = {}
    for k, v in ldi_sample_to_root_name.items():  # type: ignore
        if v is None:
            continue
        if v not in ext_name_to_ldi_samples:
            ext_name_to_ldi_samples[v] = [k]  # type: ignore
        else:
            ext_name_to_ldi_samples[v].append(k)  # type: ignore
    return SamplesRunsInfo(
        id_to_sample=id_to_sample,
        id_to_run={},
        runs_with_samples={},
        runs_with_no_samples={},
        sample_ldi_to_run={},
        ldi_sample_to_path=ldi_sample_to_path,
        ext_name_to_ldi_samples=ext_name_to_ldi_samples,
        ldi_sample_to_organism=ldi_sample_to_organism,
        ldi_sample_to_root_name=ldi_sample_to_root_name,
    )


def get_sample_run_info(
    lib_aliquot_id: str,
    sample_path: list[dict],
    run: dict,
) -> dict:
    sample_root = get_identity_sample_from_path(sample_path)
    sample_organism = get_organism(sample_root)
    sample_root_name = get_external_name(sample_root)
    run_name = run["name"]
    run_path = run.get("run_directory", None)
    start_date = run["start_date"]
    created_date = run["created_date"]
    modified_date = run["modified_date"]
    completion_date = run.get("completion_date", None)
    seq_kit = run.get("sequencingKit", None)
    flowcell = run["containerModel"]
    flowcell_id = run["barcode"]
    barcode, barcode_two = get_sample_barcode(lib_aliquot_id, run)

    return {
        "library_aliquot_id": lib_aliquot_id,
        "identity_sample_id": sample_root["id"] if sample_root else None,
        "submission_name": sample_root_name,
        "organism": sample_organism,
        "run_name": run_name,
        "run_path": run_path,
        "start_date": start_date,
        "created_date": created_date,
        "modified_date": modified_date,
        "completion_date": completion_date,
        "sequencing_kit": seq_kit,
        "flowcell": flowcell,
        "flowcell_id": flowcell_id,
        "barcode": barcode,
        "barcode_two": barcode_two,
    }


def get_sample_and_run_infos(
    sample_to_runs: dict[str, list[dict]],
    sample_to_path: dict[str, list[dict]],
) -> tuple[list[dict], set[int]]:
    out = []
    runs_missing_dirpath = set()
    for sample_id, runs in sample_to_runs.items():
        for run in runs:
            run_path = run.get("run_directory", None)
            if run_path is None:
                runs_missing_dirpath.add(run["id"])
            sample_path = sample_to_path[sample_id]
            sample_info = get_sample_run_info(sample_id, sample_path, run)
            out.append(sample_info)
    logger.warning(f"Found {len(runs_missing_dirpath)} runs with no run_directory")
    return out, runs_missing_dirpath


def get_attr(sample_data: dict | None, attribute: str) -> str | None:
    if sample_data is None:
        return None
    if "attributes" not in sample_data:
        return None
    for attr in sample_data["attributes"]:
        if attr["name"] == attribute:
            return attr["value"]
    return None


def get_organism(sample_data: dict | None) -> str | None:
    return get_attr(sample_data, "Organism")


def get_external_name(sample_data: dict | None) -> str | None:
    return get_attr(sample_data, "External Name")


def get_sample_category(sample_data: dict | None) -> str | None:
    return get_attr(sample_data, "Sample Category")


def get_tissue_origin(sample_data: dict | None) -> str | None:
    return get_attr(sample_data, "Tissue Origin")


def get_tissue_type(sample_data: dict | None) -> str | None:
    return get_attr(sample_data, "Tissue Type")


def get_first_child(sample_data: dict, id_to_data: dict) -> dict | None:
    if "children" not in sample_data or len(sample_data["children"]) == 0:
        return None
    return id_to_data[sample_data["children"][0]["id"]]


def get_sample_barcode(sampleid: str, run: dict) -> Tuple[Optional[str], Optional[str]]:
    for position in run["positions"]:
        for sample in position["samples"]:
            if sample["id"] == sampleid:
                barcode = sample.get("barcode", None)
                if not barcode:
                    return None, None
                barcode_two = sample.get("barcode_two", None)
                seqkit = run.get("sequencingKit", None)
                if seqkit is not None and seqkit in ("SQK-RBK110-96", "SQK-RBK114-96"):
                    barcode = get_rbk11096_barcode(barcode)
                    if barcode is None:
                        error_msg = f"Could not find RBK110-96/RBK114-96 barcode for {sampleid} in run {run['name']}"
                        raise ValueError(error_msg)
                    return barcode, None
                elif seqkit is not None and seqkit in ("SQK-NBD114-96",):
                    barcode = get_nbd11496_barcode(barcode)
                    if barcode is None:
                        error_msg = f"Could not find NBD114-96 barcode for {sampleid} in run {run['name']}"
                        raise ValueError(error_msg)
                    return barcode, None
                else:
                    return barcode, barcode_two
    error_msg = f"Could not find sample {sampleid} in run {run['name']}"
    raise ValueError(error_msg)
