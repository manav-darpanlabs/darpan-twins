import argparse
import json
import os
import sys

# Ensure project root is on sys.path when running as a script
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from twins.card_parser import extract_from_image


def load_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract restaurant card fields from screenshot(s)")
    parser.add_argument("--a", required=True, help="Path to Card A image (png/jpg)")
    parser.add_argument("--b", required=False, help="Path to Card B image (png/jpg)")
    parser.add_argument("--out", default="cards.json", help="Where to write extracted JSON")
    args = parser.parse_args()

    out = {}
    out["A"] = extract_from_image(load_bytes(args.a))
    if args.b:
        out["B"] = extract_from_image(load_bytes(args.b))

    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


