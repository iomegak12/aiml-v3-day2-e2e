"""Generate the synthetic NetCore TAC tickets dataset as a CSV file.

Usage:
    uv run python scripts/generate_tickets.py --n 2000 --seed 42 --output data/netcore_tickets.csv
"""

import argparse
from pathlib import Path

from netcore_tac.dataset import build_dataset

DEFAULT_OUTPUT = Path(__file__).resolve().parent.parent / "data" / "netcore_tickets.csv"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Argument list; ``None`` reads ``sys.argv``.

    Returns:
        Namespace with ``n``, ``seed`` and ``output``.
    """
    parser = argparse.ArgumentParser(description="Generate synthetic NetCore TAC tickets.")
    parser.add_argument("--n", type=int, default=2000, help="number of rows (default: 2000)")
    parser.add_argument("--seed", type=int, default=42, help="random seed (default: 42)")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help="output CSV path (default: data/netcore_tickets.csv)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> Path:
    """Build the dataset and write it to CSV.

    Args:
        argv: Argument list; ``None`` reads ``sys.argv``.

    Returns:
        Path of the written CSV file.
    """
    args = parse_args(argv)
    df = build_dataset(n=args.n, seed=args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False)
    print(f"Wrote {len(df)} rows to {args.output}")
    return args.output


if __name__ == "__main__":
    main()
