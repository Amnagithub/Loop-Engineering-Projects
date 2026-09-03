#!/usr/bin/env python3
"""The one-secret task used by the Secrets Drill (Project 10).

Reads DUMMY_SECRET_TOKEN from the *process environment* - never from a file -
and proves it has the secret by HMAC-signing a fixed probe message with it,
then writes proof.json.

Usage:
    python task.py [-o PATH]     write proof to PATH (default: proof.json in
                                 this script's folder)

Exit code: 0 on success, 1 when the secret is not in the environment.

Discipline demonstrated here: the program never prints the full secret. It
prints a masked key id (first 6 + last 4 characters) only.
"""

import argparse
import hashlib
import hmac
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

SECRET_NAME = "DUMMY_SECRET_TOKEN"
PROBE = b"secrets-drill-probe"


def mask(value: str) -> str:
    if len(value) <= 12:
        return value[:1] + "..." + value[-1:]
    return value[:6] + "..." + value[-4:]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--out", default=None,
                        help="where to write proof.json")
    args = parser.parse_args()

    value = os.environ.get(SECRET_NAME, "")
    if not value:
        print(
            f"FAIL: {SECRET_NAME} is not set in the environment.",
            file=sys.stderr,
        )
        print(
            "The secret never arrived: there is no .env in a cloud clone, and "
            "no environment variable was injected, so the task cannot run.",
            file=sys.stderr,
        )
        return 1

    digest = hmac.new(value.encode(), PROBE, hashlib.sha256).hexdigest()
    proof = {
        "ok": True,
        "task": "secrets-drill",
        "secret_name": SECRET_NAME,
        "key_id": mask(value),
        "probe": PROBE.decode(),
        "probe_hmac_sha256": digest,
        "at": datetime.now(timezone.utc).isoformat(),
    }

    out = Path(args.out) if args.out else Path(__file__).with_name("proof.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(proof, indent=2), encoding="utf-8")
    print(
        f"SUCCESS: {SECRET_NAME} obtained from the process environment "
        f"(key_id {mask(value)}). Proof written to {out}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
