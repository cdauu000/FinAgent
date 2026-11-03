"""Owner-approved freeze policy; none of the current finite enums are extensible."""

from collections.abc import Mapping

FROZEN_VERSIONS = (
    "canonical/1",
    "api/1",
    "event/1",
    "spack/1",
    "role/1",
    "tool/1",
    "template/1",
    "ratio-def/1",
    "rule/1",
    "policy/1",
    "applicability/1",
    "gateway/1",
    "prompt/1",
    "model-registry/1",
)


def validate_frozen_index(manifest: Mapping[str, object]) -> None:
    expected = {
        (version, mode, version.replace("/", "-") + "." + mode + ".json")
        for version in FROZEN_VERSIONS
        for mode in ("validation", "serialization")
    }
    entries = manifest.get("schemas")
    if not isinstance(entries, list) or len(entries) != len(expected):
        raise ValueError("FROZEN_SCHEMA_GROUP_SET_MISMATCH")
    actual = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("FROZEN_SCHEMA_GROUP_SET_MISMATCH")
        if not all(isinstance(entry.get(key), str) for key in ("version", "mode", "file")):
            raise ValueError("FROZEN_SCHEMA_GROUP_SET_MISMATCH")
        actual.add((entry.get("version"), entry.get("mode"), entry.get("file")))
    if actual != expected:
        raise ValueError("FROZEN_SCHEMA_GROUP_SET_MISMATCH")


COMPAT_POLICY = {
    "same_major": "optional_fields_and_new_DTOs_only",
    "breaking": "major_bump_with_ADR_migration_full_snapshot_suite",
    "enum_policy": {
        "default": "closed",
        "extensible": [],
        "extensible_requires": "explicit_declaration_and_tested_fallback_branch",
        "exhaustive_error_event_effect_task_status_changes": "breaking",
    },
    "canonical_window": {
        "version": "canonical/1",
        "ends_at": "first_real_data_persistence_P2.01",
        "before_first_write": "breaking_requires_ADR_previous_hash_and_diff",
        "after_first_write": "strict_major_version_policy",
        "lifecycle_ref": "schemas/lifecycle/canonical-1.json",
    },
    "registry_loads": "all_disk_and_DB_paths_must_pass_registry.bundle",
    "regressions": "each_discovered_defect_requires_negative_schema_review_case",
    "a61": "approved_technical_bounds_never_truncate_real_data",
    "token_copy_probe": "NOT_RUN_until_owner_supplies_keys_no_threshold",
}
