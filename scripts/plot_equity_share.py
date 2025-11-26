from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "household_equity_share.csv"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "outputs" / "equity_share_timeseries.png"


COUNTRY_ORDER = ["United States", "Germany", "Japan", "China"]


def load_data(path: Path) -> pd.DataFrame:
    """Load the equity share dataset sorted by date and country."""
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run `python scripts/download_equity_share.py` to fetch the OECD data."
        )

    df = pd.read_csv(path, parse_dates=["date"])
    df = df.sort_values(["country", "date"])
    return df


def plot_equity_share(df: pd.DataFrame) -> None:
    """Plot equity share time series for the selected countries."""
    fig, ax = plt.subplots(figsize=(10, 6))

    for country in COUNTRY_ORDER:
        country_df = df[df["country"] == country]
        ax.plot(country_df["date"], country_df["equity_share"], label=country)

    ax.set_title("Household Wealth Allocated to Equities")
    ax.set_xlabel("Year")
    ax.set_ylabel("Equity share of household wealth (%)")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda val, _: f"{val:.0f}%"))
    ax.xaxis.set_major_locator(mdates.YearLocator(base=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    fig.autofmt_xdate()
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(OUTPUT_PATH, dpi=300)
    plt.close(fig)


def main() -> None:
    df = load_data(DATA_PATH)
    plot_equity_share(df)


if __name__ == "__main__":
    main()
