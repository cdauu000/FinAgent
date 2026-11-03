"""Explicitly unavailable skeleton; never pretends to consume queued jobs."""


def main() -> None:
    raise SystemExit("WORKER_NOT_IMPLEMENTED_PHASE0")


if __name__ == "__main__":
    main()
