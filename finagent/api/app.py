"""Phase 0 process health only; deliberately cannot claim service readiness."""

from typing import Any

from fastapi import FastAPI

from finagent import __version__
from finagent.api.contracts import Health, Readiness
from finagent.contracts.validator_catalog import validator_catalog


class FinAgentAPI(FastAPI):
    def openapi(self) -> dict[str, Any]:
        # Decorate the real cache after FastAPI handles route-version invalidation.
        schema = super().openapi()
        schema["x-finagent-custom-validators"] = validator_catalog()
        schema["x-finagent-schema-review"] = {
            "status": "frozen",
            "frozen": True,
            "groups": 14,
            "scope": "Frozen DTOs, preflight and loader validators; "
            "not deployed business endpoints",
            "approval": "project_owner_explicit_freeze",
            "deferred_controls": [
                "full_query_guard",
                "name_and_number_word_guard",
                "renderer",
                "output_verifier",
                "Redis_quota_fairness",
                "provider_adapters",
            ],
        }
        return schema


def create_app() -> FastAPI:
    app = FinAgentAPI(title="FinAgent", version=__version__, docs_url=None, redoc_url=None)

    @app.get("/health", response_model=Health)
    def health() -> Health:
        return Health(version=__version__)

    @app.get("/health/ready", response_model=Readiness, status_code=503)
    def readiness() -> Readiness:
        return Readiness(reasons=("PERSISTENCE_NOT_IMPLEMENTED",))

    return app
