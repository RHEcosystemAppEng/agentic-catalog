# TunedPerformancePatch — Restructure Guidance

The reference TunedPerformancePatch was restructured from a single
profile to 4 architecture-specific profiles:

- `ran-du-performance` — top-level, includes `ran-du-performance-architecture-common`
- `ran-du-performance-architecture-common` — cross-arch settings
- `ran-du-common-aarch64` — ARM-specific
- `ran-du-common-x86` — x86-specific

## Content accounting

When restructuring a partner's single-profile Tuned into the new
multi-profile layout, account for EVERY section in the partner's
original data block: `[main]`, `[sysctl]`, `[scheduler]`, `[service]`,
`[bootloader]`. After writing the merged patches, list which partner
section ended up in which profile. If any section from the partner's
input is not present in any output profile, you dropped content — add
it back to the correct profile immediately.

Typical placement:
- `[sysctl]` partner entries → `ran-du-performance-architecture-common`
- `[scheduler]` partner entries → `ran-du-common-x86` (x86-specific)
- `[service]` partner entries → `ran-du-performance-architecture-common`
- `[bootloader]` partner entries → `ran-du-common-x86` (x86-specific)

## Include-chain-aware redundancy check

Before marking a partner's Tuned patch value as redundant against a
source-cr sub-profile value, check the partner's `include=` line:

- If the partner's `include=` chains to the sub-profile containing
  the value → the value IS redundant (`[~]`), partner can remove it.
- If the partner overrides `include=` and skips that sub-profile →
  the value is NOT redundant. The partner's direct specification is
  the only way those settings get applied. Preserve it and note that
  the include chain skips `{sub-profile}`.

When the partner's `include=` line differs from the reference, note
this as a structural divergence in the checklist so the user is aware.

## Other changes

- Profile name: `performance-patch` → `ran-du-performance`
- Priority: 19 → 18
