"""Manual local tooling limited to the owner's Phase1a exception."""

import argparse
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from finagent.contracts.base import ExecutionContext, Mode, RegistryRef, Tier
from finagent.contracts.errors import ProcessingError
from finagent.corpus.contracts import CorpusManifest, GoldDocument
from finagent.corpus.review_tools import ReferenceFrames, build_manifest, export_review_bundle
from finagent.extraction.media import WindowsMedia


def main() -> None:
    parser = argparse.ArgumentParser(description="Local supplied reports only; no OCR/KPI/provider")
    commands = parser.add_subparsers(dest="command", required=True)
    inventory_parser = commands.add_parser("manifest")
    inventory_parser.add_argument("--previous", type=Path)
    review = commands.add_parser("review")
    review.add_argument("--report", required=True)
    review.add_argument("--candidates", required=True, type=Path)
    review.add_argument("--frames", required=True, type=Path)
    review.add_argument("--dpi", type=int, choices=[300, 400], default=300)
    for sub in (inventory_parser, review):
        sub.add_argument("--output", type=Path, default=Path("data/runtime/phase1a") / uuid4().hex)
    args = parser.parse_args()
    root = Path.cwd().resolve()
    media = WindowsMedia(root / "data/runtime/phase1a-work")
    if args.command == "manifest":
        previous = (
            CorpusManifest.model_validate_json(args.previous.read_text(encoding="utf-8"))
            if args.previous
            else None
        )
        manifest = build_manifest(root, args.output, media, previous)
        print(
            json.dumps(
                {
                    "real_reports": len(manifest.entries),
                    "output": str(args.output),
                    "phase0": "INCOMPLETE_NO_GO",
                    "ocr": "NOT_RUN",
                }
            )
        )
    else:
        candidates = GoldDocument.model_validate_json(args.candidates.read_text(encoding="utf-8"))
        data = json.loads(args.frames.read_text(encoding="utf-8"))
        frames = ReferenceFrames.model_validate(
            {"source_sha256": data["source_sha256"], "rasters": data["rasters"]}
        )
        ctx = ExecutionContext(
            tenant_id="local-review",
            principal_id="phase1a-local-user",
            permissions=("document:read", "review:read"),
            request_id="req-" + uuid4().hex,
            trace_id="trace-" + uuid4().hex,
            policy_ref=RegistryRef(id="local-phase1a", version="1"),
            mode=Mode.STRICT,
            source_tier=Tier.PRIVATE,
            deadline=datetime.now(UTC) + timedelta(minutes=30),
        )
        bundle = export_review_bundle(
            root, args.report, candidates, frames, args.output, ctx, media, dpi=args.dpi
        )
        print(
            json.dumps({"output": str(args.output), "status": bundle["status"], "ocr": "NOT_RUN"})
        )


if __name__ == "__main__":
    try:
        main()
    except ProcessingError as exc:
        print(json.dumps({"status": "FAILED", "code": exc.code}))
        raise SystemExit(1) from None
