"""Read-only JSON registry validation; never import/eval code from definitions."""

from pathlib import Path
from typing import Literal, Protocol, overload

from finagent import __version__
from finagent.llm_gateway.model_registry import ModelRegistry
from finagent.llm_gateway.prompts import PromptRegistry
from finagent.policy.contracts import (
    AggregateExpr,
    BinaryExpr,
    Expression,
    FactExpr,
    RegistryBundle,
    RegistryDefinition,
)


class RegistryRowSource(Protocol):
    """Read-only adapter port; the PostgreSQL adapter is implemented in Phase2."""

    def read_registry_json(self, registry_id: str) -> str: ...


def expression_concepts(expression: Expression) -> set[str]:
    if isinstance(expression, FactExpr):
        return {expression.concept_id}
    if isinstance(expression, BinaryExpr):
        return expression_concepts(expression.left) | expression_concepts(expression.right)
    if isinstance(expression, AggregateExpr):
        return set().union(*(expression_concepts(child) for child in expression.inputs))
    return set()


def validate_bundle(
    bundle: RegistryBundle,
    *,
    require_approved: bool = True,
    available_strategies: frozenset[str] = frozenset({"single"}),
) -> None:
    groups: dict[str, tuple[RegistryDefinition, ...]] = {
        "template": bundle.templates,
        "ratio": bundle.ratios,
        "rule": bundle.rules,
        "pack": bundle.packs,
        "tool": bundle.tools,
        "role": bundle.roles,
        "applicability": bundle.applicability,
    }
    known: dict[str, set[tuple[str, str]]] = {}
    for family, entries in groups.items():
        known[family] = {(entry.id, entry.version) for entry in entries}
        if len(known[family]) != len(entries):
            raise ValueError("DUPLICATE_REGISTRY_ENTRY")
        for entry in entries:
            if require_approved and entry.status != "approved":
                raise ValueError("DRAFT_NOT_RUNTIME_ELIGIBLE")
            if not entry.source_refs or not entry.mandatory_test_refs:
                raise ValueError("SOURCE_AND_TEST_REFS_REQUIRED")
    for rule in bundle.rules:
        if (rule.template_ref.id, rule.template_ref.version) not in known["template"]:
            raise ValueError("UNKNOWN_TEMPLATE_REF")
    for ratio in bundle.ratios:
        if expression_concepts(ratio.formula) != set(ratio.input_concepts):
            raise ValueError("FORMULA_INPUT_CONCEPTS_MISMATCH")
        if ratio.definition_role == "variant" and ratio.base_definition_ref is None:
            raise ValueError("VARIANT_BASE_REQUIRED")
        if (
            ratio.base_definition_ref is not None
            and (ratio.base_definition_ref.id, ratio.base_definition_ref.version)
            not in known["ratio"]
        ):
            raise ValueError("UNKNOWN_BASE_DEFINITION")
    for role in bundle.roles:
        if role.strategy not in available_strategies:
            raise ValueError("UNSUPPORTED_STRATEGY")
        if any((ref.id, ref.version) not in known["tool"] for ref in role.allowed_tool_refs):
            raise ValueError("UNKNOWN_TOOL_REF")
    for pack in bundle.packs:
        required = tuple(int(part) for part in pack.min_core_version.split("."))
        current = tuple(int(part) for part in __version__.split("."))
        required = required + (0,) * (3 - len(required))
        if required > current:
            raise ValueError("INCOMPATIBLE_CORE_VERSION")
        if any((ref.id, ref.version) not in known["template"] for ref in pack.template_refs):
            raise ValueError("UNKNOWN_PACK_TEMPLATE_REF")
        if any(
            (item.ratio_ref.id, item.ratio_ref.version) not in known["ratio"]
            for item in pack.ratio_memberships
        ):
            raise ValueError("UNKNOWN_RATIO_REF")
        if any(
            (band.ratio_ref.id, band.ratio_ref.version) not in known["ratio"]
            for band in pack.thresholds
        ):
            raise ValueError("UNKNOWN_THRESHOLD_RATIO_REF")
        if any(
            (ref.id, ref.version) not in known["applicability"] for ref in pack.applicability_refs
        ):
            raise ValueError("UNKNOWN_APPLICABILITY_REF")
    dependencies = {
        (entry.id, entry.version): {(ref.id, ref.version) for ref in entry.dependencies}
        for entry in bundle.ratios
    }
    visited: set[tuple[str, str]] = set()
    visiting: set[tuple[str, str]] = set()

    def visit(node: tuple[str, str]) -> None:
        if node in visiting:
            raise ValueError("CYCLIC_RATIO_DEPENDENCY")
        if node in visited:
            return
        if node not in dependencies:
            raise ValueError("UNKNOWN_RATIO_DEPENDENCY")
        visiting.add(node)
        for child in dependencies[node]:
            visit(child)
        visiting.remove(node)
        visited.add(node)

    for node in dependencies:
        visit(node)
    if require_approved and ("generic", "1") not in known["pack"]:
        raise ValueError("APPROVED_GENERIC_PACK_REQUIRED")


def load_bundle(
    path: Path,
    *,
    require_approved: bool = True,
    available_strategies: frozenset[str] = frozenset({"single"}),
) -> RegistryBundle:
    return registry_bundle(
        path.read_text(encoding="utf-8"),
        require_approved=require_approved,
        available_strategies=available_strategies,
    )


@overload
def registry_bundle(
    content: str,
    *,
    kind: Literal["business"] = "business",
    require_approved: bool = True,
    available_strategies: frozenset[str] = frozenset({"single"}),
) -> RegistryBundle: ...


@overload
def registry_bundle(
    content: str,
    *,
    kind: Literal["prompt", "model"],
    require_approved: bool = True,
    available_strategies: frozenset[str] = frozenset({"single"}),
) -> PromptRegistry | ModelRegistry: ...


def registry_bundle(
    content: str,
    *,
    kind: Literal["business", "prompt", "model"] = "business",
    require_approved: bool = True,
    available_strategies: frozenset[str] = frozenset({"single"}),
) -> RegistryBundle | PromptRegistry | ModelRegistry:
    """registry.bundle: one entry gate for every disk/DB registry shape."""
    if kind != "business":
        return gateway_registry_bundle(content, kind, require_approved=require_approved)
    bundle = RegistryBundle.model_validate_json(content)
    validate_bundle(
        bundle, require_approved=require_approved, available_strategies=available_strategies
    )
    return bundle


def load_bundle_from_database(
    source: RegistryRowSource, registry_id: str, *, require_approved: bool = True
) -> RegistryBundle:
    return registry_bundle(
        source.read_registry_json(registry_id), require_approved=require_approved
    )


def gateway_registry_bundle(
    content: str, kind: Literal["prompt", "model"], *, require_approved: bool = True
) -> PromptRegistry | ModelRegistry:
    """registry.bundle gate for separate Gateway registry shapes (not business DTOs)."""
    registry: PromptRegistry | ModelRegistry
    if kind == "prompt":
        registry = PromptRegistry.model_validate_json(content)
        if require_approved and any(entry.status != "approved" for entry in registry.entries):
            raise ValueError("DRAFT_NOT_RUNTIME_ELIGIBLE")
    elif kind == "model":
        registry = ModelRegistry.model_validate_json(content)
        if require_approved and any(entry.status != "verified" for entry in registry.entries):
            raise ValueError("UNVERIFIED_MODEL_NOT_RUNTIME_ELIGIBLE")
    else:
        raise ValueError("UNKNOWN_REGISTRY_KIND")
    if require_approved and registry.status != "approved":
        raise ValueError("DRAFT_NOT_RUNTIME_ELIGIBLE")
    return registry


def load_gateway_registry(
    path: Path, kind: Literal["prompt", "model"], *, require_approved: bool = True
) -> PromptRegistry | ModelRegistry:
    return registry_bundle(
        path.read_text(encoding="utf-8"), kind=kind, require_approved=require_approved
    )


def load_gateway_registry_from_database(
    source: RegistryRowSource,
    registry_id: str,
    kind: Literal["prompt", "model"],
    *,
    require_approved: bool = True,
) -> PromptRegistry | ModelRegistry:
    return registry_bundle(
        source.read_registry_json(registry_id), kind=kind, require_approved=require_approved
    )
