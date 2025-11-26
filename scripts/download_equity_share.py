"""Download household equity share data from the OECD Financial Indicators dashboard.

The script targets the ``DF_FIN_DASH_S1M`` dataset (data structure ``DSD_FIN_DASH``)
and the ``LES1M_F51AS`` measure, which reports household holdings of listed and
unlisted shares as a percent of financial assets (unit ``PT_FAS_S1M``). The SDMX key
follows the ``FREQ.REF_AREA.MEASURE.UNIT`` pattern documented on the OECD Data
Explorer "How to access OECD data via API" page.
"""
from __future__ import annotations

from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Dict, List

import pandas as pd
import requests
from requests import RequestException

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_PATH = DATA_DIR / "household_equity_share.csv"

OECD_BASE = (
    "https://stats.oecd.org/SDMX-JSON/data/DSD_FIN_DASH@DF_FIN_DASH_S1M/"
    "A.{country}.LES1M_F51AS.PT_FAS_S1M/all?contentType=csv"
)

COUNTRY_MAP: Dict[str, str] = {
    "USA": "United States",
    "DEU": "Germany",
    "JPN": "Japan",
    "CHN": "China",
}


@dataclass
class CountryResult:
    country_code: str
    country_name: str
    frame: pd.DataFrame


def fetch_country(country_code: str, country_name: str) -> CountryResult:
    url = OECD_BASE.format(country=country_code)
    print(f"Requesting {url}")

    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
    except RequestException as exc:
        raise RuntimeError(
            "Failed to download data. Ensure internet access to stats.oecd.org and that any "
            "required HTTP/HTTPS proxy is configured."
        ) from exc

    df = pd.read_csv(StringIO(response.text))

    if df.empty:
        raise ValueError(f"Received an empty response from OECD for {country_code}")

    if {"TIME_PERIOD", "OBS_VALUE"} - set(df.columns):
        raise ValueError(f"Unexpected columns in OECD response for {country_code}: {df.columns}")

    df = df.loc[:, ["TIME_PERIOD", "OBS_VALUE"]].rename(
        columns={"TIME_PERIOD": "date", "OBS_VALUE": "equity_share"}
    )
    df["date"] = pd.to_datetime(df["date"] + "-12-31")
    df["country"] = country_name
    df = df[["date", "country", "equity_share"]].sort_values("date")
    return CountryResult(country_code=country_code, country_name=country_name, frame=df)


def combine_results(results: List[CountryResult]) -> pd.DataFrame:
    frames = [result.frame for result in results]
    return pd.concat(frames, ignore_index=True).sort_values(["country", "date"])


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    results: List[CountryResult] = []
    for code, name in COUNTRY_MAP.items():
        print(f"Fetching {name} ({code}) from OECD DF_FIN_DASH_S1M…")
        result = fetch_country(code, name)
        results.append(result)

    combined = combine_results(results)
    combined.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved {len(combined)} rows to {OUTPUT_PATH.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
