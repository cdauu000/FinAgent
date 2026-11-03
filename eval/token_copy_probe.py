"""Manual synthetic probe preparation/scoring only. This module never calls a provider."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from finagent.llm_gateway.tokens import TOKEN_ALPHABET


class CopyCase(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str
    task: str
    tokens: tuple[str, ...]
    prompt: str


class ProbeDataset(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: str = "token-copy-probe/1"
    status: str = "NOT_RUN"
    reason: str = "Prepared synthetic prompts only; no provider calls or model responses."
    cases: tuple[CopyCase, ...]
    quality_threshold: None = None


def prepare_dataset() -> ProbeDataset:
    # Deterministic RNG is exclusively for synthetic fixtures, never runtime aliases.
    rng = random.Random(20261102)
    cases: list[CopyCase] = []
    for index, size in enumerate((2, 4, 8, 16)):
        tokens = tuple(
            ("ent_" if position % 2 == 0 else "num_")
            + "".join(rng.choice(TOKEN_ALPHABET) for _ in range(8))
            for position in range(size)
        )
        cases.append(
            CopyCase(
                id=f"copy-{index}",
                task="intent_parse" if index % 2 == 0 else "answer_compose",
                tokens=tokens,
                prompt="Return only JSON with a tokens array. "
                "Copy these aliases exactly, in order: " + json.dumps(tokens),
            )
        )
    return ProbeDataset(cases=tuple(cases))


def score_responses(
    dataset: ProbeDataset, responses: dict[str, tuple[str, ...]], *, model: str
) -> dict[str, object]:
    if set(responses) - {case.id for case in dataset.cases}:
        raise ValueError("UNKNOWN_PROBE_CASE")
    if not responses:
        return {
            "status": "NOT_RUN",
            "model": model,
            "reason": "No model responses supplied",
            "quality_threshold": None,
        }
    matched = exact = missing = extra = 0
    total_tokens = sum(len(case.tokens) for case in dataset.cases)
    for case in dataset.cases:
        actual = responses.get(case.id, ())
        missing += int(case.id not in responses)
        exact += int(actual == case.tokens)
        matched += sum(left == right for left, right in zip(case.tokens, actual, strict=False))
        extra += max(0, len(actual) - len(case.tokens))
    return {
        "status": "SCORED_SUPPLIED_RESPONSES",
        "model": model,
        "provenance": "Caller-supplied responses; this command performs no provider calls",
        "exact_cases": exact,
        "total_cases": len(dataset.cases),
        "correct_token_positions": matched,
        "total_expected_positions": total_tokens,
        "missing_cases": missing,
        "extra_tokens": extra,
        "quality_threshold": None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Offline preparation/scoring, never provider execution"
    )
    parser.add_argument("--prepare", type=Path)
    parser.add_argument("--dataset", type=Path)
    parser.add_argument("--responses", type=Path)
    parser.add_argument("--model")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.prepare:
        args.prepare.parent.mkdir(parents=True, exist_ok=True)
        args.prepare.write_text(
            prepare_dataset().model_dump_json(indent=2) + "\n", encoding="utf-8"
        )
        print("Prepared synthetic token-copy probe; live status NOT_RUN")
        return
    if not all((args.dataset, args.responses, args.model, args.output)):
        parser.error("Scoring requires --dataset --responses --model --output")
    dataset = ProbeDataset.model_validate_json(args.dataset.read_text(encoding="utf-8"))
    raw: object = json.loads(args.responses.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not all(
        isinstance(v, list) and all(isinstance(t, str) for t in v) for v in raw.values()
    ):
        raise ValueError("PROBE_RESPONSE_FORMAT_INVALID")
    result = score_responses(dataset, {str(k): tuple(v) for k, v in raw.items()}, model=args.model)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
