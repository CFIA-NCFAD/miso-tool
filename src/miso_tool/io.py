import json
from pathlib import Path


def parse_runs_from_json(runs_json: Path) -> dict[int, dict]:
    with open(runs_json) as f:
        runs = json.load(f)
        id_to_run = {}
        for seqrun in runs:
            if "id" in seqrun and isinstance(seqrun["id"], int):
                id_to_run[seqrun["id"]] = seqrun
        return id_to_run


def parse_samples_json(json_path: Path) -> dict[str, dict]:
    with json_path.open() as f:
        samples = json.load(f)
    return {s["id"]: s for s in samples}
