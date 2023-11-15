import logging
import re
from datetime import datetime
from typing import Optional

import pendulum

logger = logging.getLogger(__name__)

YEARS = list(range(2000, datetime.utcnow().year))

VALID_SAMPLE_CODES = [
    "OTH",
    "FAV",
    "FMA",
    "AI",
    "IM",
]
sample_code_regex = "|".join(VALID_SAMPLE_CODES)
invalid_chars_regex = re.compile(r"[^\w\-]")


def fix_lsts_sample_name(
    value: str,
    run_start_date: Optional[str] = None,
) -> str | None:
    try:
        value = invalid_chars_regex.sub("-", value)
        value = re.sub(r"-+", "-", value)
        value = value.strip("-")
        m = re.match(r"^(WIN-AH-\d{4}-(" + sample_code_regex + r")-\d{4})-(\d+)$", value)
        if m:
            # if regular LSTS name format, return it
            prefix, _, suffix = m.groups()
            # remove leading zeros in suffix number
            suffix = int(suffix)
            return f"{prefix}-{suffix}"
        # remove OS suffix if present
        value = re.sub(r"[\-_]OS", "", value)
        m = re.match(r"^(WIN-AH-)?(2\d{3})-(" + sample_code_regex + r")-?(\d+)[\-_]?(.*)$", value)
        if m:
            _, year, sample_code, sample_number, extra_stuff = m.groups()
            return f"WIN-AH-{year}-{sample_code}-{sample_number:>04}-{extra_stuff}"
        m = re.match(r".*(" + sample_code_regex + r")-?(\d+)([\-_]\d+)?[\-_]?(.*)$", value)
        if m:
            sample_code, sample_number, extra_num, extra_stuff = m.groups()
            year = None
            if extra_num in YEARS:
                year = extra_num
            if year is None and run_start_date is not None:
                dt = pendulum.parse(run_start_date)
                if hasattr(dt, "year"):
                    year = dt.year
                    logger.warning(
                        f"Could not parse year from sample name '{value}'. "
                        f"Assuming year is {year} based on run start date '{run_start_date}'."
                    )
            if year is None:
                current_year = datetime.utcnow().year
                logger.warning(
                    f"Could not parse year from sample name '{value}'. "
                    f"Assuming year is current year: {current_year}"
                )
                year = current_year
            return f"WIN-AH-{year}-{sample_code}-{sample_number:>04}-{extra_stuff}"
        return value
    except ValueError:
        return value
