import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


def has_samples(run: dict) -> bool:
    if "positions" in run:
        positions = run.get("positions", None)
        if positions:
            if len(positions) > 1:
                logger.warning(f"More than one position in run '{run['name']}'! N={len(positions)}")
            position = positions[0]
            if "samples" in position:
                return bool(position.get("samples", None))
    return False


def group_runs_by(id_to_run: dict[int, dict], key: str) -> dict:
    groups = defaultdict(list)
    for seqrun in id_to_run.values():
        if key in seqrun:
            groups[seqrun[key]].append(seqrun)
        else:
            groups["OTHER"].append(seqrun)
    return groups


def get_sample_ldi_to_run(id_to_run: dict[int, dict]) -> dict[str, list[dict]]:
    sample_ldi_to_run = defaultdict(list)
    for run in id_to_run.values():
        if has_samples(run):
            positions = run.get("positions", None)
            if positions and len(positions) > 0:
                if len(positions) > 1:
                    logger.warning(f"More than one position in run {run['name']}")
                position = positions[0]
                samples = position.get("samples", None)
                if samples:
                    for sample in samples:
                        sample_id = sample["id"]
                        sample_ldi_to_run[sample_id].append(run)
    return sample_ldi_to_run
