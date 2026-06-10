from __future__ import annotations

import argparse
import sys

from .analyzer import build_report, render_markdown
from .save_reader import SaveReadError, read_save


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze a Stellaris save file.")
    parser.add_argument("save_file", help="Path to a Stellaris .sav file")
    args = parser.parse_args(argv)

    try:
        save = read_save(args.save_file)
    except SaveReadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    report = build_report(save)
    print(render_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

