"""Tiny CLI shim so `uvx vacant google.com` works.

For heavy use prefer the native binary (`brew install alltuner/tap/vacant` or
`cargo install vacant`) — Python startup overhead matters when checking one
domain at a time.
"""

import argparse
import json
import sys

from vacant import Status, check_many


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="vacant",
        description="Check domain availability via authoritative DNS.",
    )
    parser.add_argument("domains", nargs="*", help="Domains to check; reads stdin if empty.")
    parser.add_argument(
        "-o",
        "--output",
        choices=["jsonl", "text"],
        default="jsonl",
        help="Output format (default: jsonl).",
    )
    parser.add_argument("--concurrency", type=int, default=64)
    parser.add_argument("--timeout", type=float, default=4.0)
    args = parser.parse_args()

    inputs = list(args.domains) or [
        line.strip() for line in sys.stdin if line.strip() and not line.startswith("#")
    ]

    if not inputs:
        parser.print_help(sys.stderr)
        sys.exit(2)

    results = check_many(inputs, concurrency=args.concurrency, timeout=args.timeout)

    if args.output == "jsonl":
        for r in results:
            print(json.dumps({"domain": r.domain or r.input, "status": r.status.value}))
    else:
        for r in results:
            print(r.domain or r.input)

    if any(r.status is Status.UNKNOWN for r in results):
        sys.exit(2)


if __name__ == "__main__":
    main()
