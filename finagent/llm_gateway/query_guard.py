"""Conservative local allowlist guard; uncertain language stays on the local path."""

import re
import unicodedata
from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID, uuid4

from finagent.contracts.base import Scope, Tier, exact_decimal
from finagent.llm_gateway.contracts import Clarification, IntentPayload, SessionSelection
from finagent.llm_gateway.model_registry import ModelCapability
from finagent.llm_gateway.tokens import RunTokenAllocator

VOCABULARY = frozenset(
    [
        "doanh",
        "thu",
        "lợi",
        "nhuận",
        "tài",
        "sản",
        "nợ",
        "vốn",
        "chủ",
        "sở",
        "hữu",
        "thanh",
        "toán",
        "hiện",
        "hành",
        "nhanh",
        "tiền",
        "mặt",
        "tỷ",
        "lệ",
        "chỉ",
        "số",
        "biên",
        "gộp",
        "ròng",
        "vòng",
        "quay",
        "hàng",
        "tồn",
        "kho",
        "phải",
        "khách",
        "hàng",
        "dòng",
        "hoạt",
        "động",
        "kinh",
        "doanh",
        "hợp",
        "nhất",
        "riêng",
        "quý",
        "kỳ",
        "năm",
        "trước",
        "hiện",
        "tại",
        "so",
        "sánh",
        "tính",
        "xem",
        "giải",
        "thích",
        "kiểm",
        "tra",
        "đúng",
        "sai",
        "là",
        "có",
        "không",
        "của",
        "và",
        "với",
        "cho",
        "tôi",
        "theo",
        "công",
        "ty",
        "báo",
        "cáo",
        "đã",
        "chọn",
        "roa",
        "roe",
        "icr",
        "current",
        "quick",
        "cash",
        "debt",
        "ratio",
        "equity",
        "ocf",
        "piotroski",
        "xu",
        "hướng",
        "phân",
        "tích",
        "bằng",
        "kết",
        "quả",
        "này",
        "số",
        "liệu",
        "từ",
    ]
)
NUMBER = re.compile(
    r"(?P<number>[\-−]?\(?\d(?:[\d., \u00a0]*\d)?\)?)"
    r"\s*(?P<unit>%|tỷ|triệu|đồng|vnd)?",
    re.IGNORECASE,
)
PERIOD = re.compile(r"quý\s+([1-4])\s*(?:[/\-]|năm)?\s*(20\d{2})", re.IGNORECASE)


class LocalOnly(ValueError):
    def __init__(self, reason: str, clarification: Clarification | None = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.clarification = clarification


@dataclass(frozen=True)
class KnownEntity:
    internal_id: UUID
    aliases: tuple[str, ...]


@dataclass(frozen=True, repr=False)
class UserNumber:
    raw: str
    value: Decimal
    unit: str


@dataclass(frozen=True)
class GuardedRun:
    payload: IntentPayload
    run_id: UUID
    numbers: dict[str, UserNumber] = field(repr=False)
    identities: dict[UUID, str] = field(repr=False)


def private_eligible(
    tier: Tier,
    *,
    tenant_opt_in: bool,
    max_retention_days: int | None,
    capability: ModelCapability | None,
    terms_review_current: bool = False,
) -> bool:
    if tier == Tier.STRICT_PRIVATE or capability is None or capability.status != "verified":
        return False
    if tier == Tier.PUBLIC:
        return True
    if (
        not tenant_opt_in
        or max_retention_days is None
        or max_retention_days < 0
        or not terms_review_current
    ):
        return False
    if capability.training_use != "none_verified" or not capability.terms_evidence_refs:
        return False
    if capability.retention.kind == "none_verified":
        return True
    return (
        capability.retention.kind == "limited" and capability.retention.days <= max_retention_days
    )


def parse_user_number(raw: str, unit: str) -> UserNumber:
    text = raw.strip().replace("−", "-").replace("\u00a0", "").replace(" ", "")
    if text.startswith("(") and text.endswith(")"):
        text = "-" + text[1:-1]
    if "." in text:
        integral, _, fractional = text.partition(",")
        if not re.fullmatch(r"-?[0-9]{1,3}(?:\.[0-9]{3})+", integral):
            raise LocalOnly("NUMBER_FORMAT_AMBIGUOUS")
        text = integral.replace(".", "") + ("." + fractional if fractional else "")
    else:
        text = text.replace(",", ".")
    try:
        value = exact_decimal(text)
        multiplier = {"tỷ": Decimal(10**9), "triệu": Decimal(10**6), "%": Decimal("0.01")}
        # Decimal multiplication uses an explicit local context, never binary float.
        from decimal import localcontext

        with localcontext() as ctx:
            ctx.prec = 38
            normalized = value * multiplier.get(unit, Decimal(1))
        if len(value.as_tuple().digits) + (9 if unit == "tỷ" else 6 if unit == "triệu" else 0) > 38:
            raise LocalOnly("USER_NUMBER_PRECISION_EXCEEDED")
        return UserNumber(raw=raw, value=normalized, unit=unit or "unspecified")
    except ValueError as exc:
        raise LocalOnly("NUMBER_FORMAT_AMBIGUOUS") from exc


def guard_query(
    question: str,
    entities: tuple[KnownEntity, ...],
    *,
    selected_entity: UUID | None,
    period_code: str | None,
    scope: Scope | None,
    tier: Tier = Tier.PRIVATE,
    tenant_opt_in: bool = False,
    max_retention_days: int | None = None,
    capability: ModelCapability | None = None,
    terms_review_current: bool = False,
) -> GuardedRun:
    if tier != Tier.PUBLIC and not private_eligible(
        tier,
        tenant_opt_in=tenant_opt_in,
        max_retention_days=max_retention_days,
        capability=capability,
        terms_review_current=terms_review_current,
    ):
        raise LocalOnly("PRIVATE_LOCAL_ONLY")
    if not question or len(question) > 4096 or any(ch in question for ch in "\n\r\t|<>\\"):
        raise LocalOnly("DOCUMENT_OR_OVERSIZE_QUERY")
    normalized = unicodedata.normalize("NFKC", question).casefold()
    if re.search(r"https?://|www\.|\b(?:ent|num)_|\d\s*[-–]\s*\d", normalized):
        raise LocalOnly("UNSAFE_QUERY_STRUCTURE")
    if scope == Scope.SEPARATE and "hợp nhất" in normalized:
        raise LocalOnly("SCOPE_MISMATCH")
    if scope == Scope.CONSOLIDATED and "riêng" in normalized:
        raise LocalOnly("SCOPE_MISMATCH")
    allocator = RunTokenAllocator(question)
    identities: dict[UUID, str] = {}
    for entity in entities:
        for alias in sorted(entity.aliases, key=len, reverse=True):
            pattern = re.compile(
                r"(?<!\w)" + re.escape(unicodedata.normalize("NFKC", alias).casefold()) + r"(?!\w)"
            )
            if pattern.search(normalized):
                token = identities.setdefault(
                    entity.internal_id, allocator.allocate("ent", entity.internal_id)
                )
                normalized = pattern.sub(token, normalized)
    if len(identities) > 1 or selected_entity is None:
        raise LocalOnly("ENTITY_SELECTION_REQUIRED", Clarification.ENTITY)
    if identities and selected_entity not in identities:
        raise LocalOnly("ENTITY_SELECTION_MISMATCH", Clarification.ENTITY)
    if selected_entity not in {entity.internal_id for entity in entities}:
        raise LocalOnly("UNKNOWN_ENTITY", Clarification.ENTITY)
    token = identities.setdefault(selected_entity, allocator.allocate("ent", selected_entity))
    if period_code is None:
        raise LocalOnly("PERIOD_SELECTION_REQUIRED", Clarification.PERIOD)
    if scope is None:
        raise LocalOnly("SCOPE_SELECTION_REQUIRED", Clarification.SCOPE)

    def replace_period(match: re.Match[str]) -> str:
        if period_code != f"q{match[1]}_{match[2]}":
            raise LocalOnly("PERIOD_SELECTION_MISMATCH", Clarification.PERIOD)
        return "kỳ đã chọn"

    normalized = PERIOD.sub(replace_period, normalized)
    numbers: dict[str, UserNumber] = {}

    def replace_number(match: re.Match[str]) -> str:
        placeholder = allocator.allocate("num", uuid4())
        numbers[placeholder] = parse_user_number(match["number"], (match["unit"] or "").casefold())
        return placeholder + " "

    # Protect random aliases from the numeric scanner by processing literal segments only.
    pieces = re.split(r"(ent_[0-9abcdefghjkmnpqrstvwxyz]{8})", normalized)
    normalized = "".join(
        piece
        if re.fullmatch(r"ent_[0-9abcdefghjkmnpqrstvwxyz]{8}", piece)
        else NUMBER.sub(replace_number, piece)
        for piece in pieces
    )
    words = re.findall(r"[\w]+", normalized)
    approved_tokens = set(identities.values()) | set(numbers)
    if any(word not in VOCABULARY and word not in approved_tokens for word in words):
        raise LocalOnly("UNPROVEN_QUERY_VOCABULARY")
    query = " ".join(words)
    if len(query) > 4096:
        raise LocalOnly("MASKED_QUERY_OVERSIZE")
    payload = IntentPayload(
        query=query,
        selection=SessionSelection(
            entity_token=token,
            period_code=period_code,
            scope=scope,
            selection_revision=1,
        ),
        number_placeholders=tuple(numbers),
    )
    return GuardedRun(
        payload=payload, run_id=allocator.run_id, numbers=numbers, identities=identities
    )


def clarification_text(reason: Clarification) -> str:
    return {
        Clarification.ENTITY: "Bạn muốn xem doanh nghiệp nào?",
        Clarification.PERIOD: "Bạn muốn xem kỳ báo cáo nào?",
        Clarification.SCOPE: "Bạn muốn xem báo cáo riêng hay hợp nhất?",
        Clarification.RATIO: "Bạn muốn xem chỉ số nào?",
        Clarification.AMBIGUOUS_REQUEST: "Bạn muốn xem nội dung nào trong báo cáo?",
    }[reason]
