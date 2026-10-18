# Merge Conflict Resolution

## Customization Preservation

All partner customizations preserved by default. No classification as
intentional vs stale (stale workaround detection is future scope).

## Non-overlapping Changes

Reference changes fields the partner hasn't customized -- apply automatically.

Example: reference bumps `spec.channel: "4.18"` to `"4.20"`, partner hasn't
patched channel -- update automatically.

## Redundant Overlays

Partner patches a field to the same value the reference already has. The
patch is unnecessary -- it does nothing. Note it as redundant in the
checklist so the partner can clean it up if they choose.

Example: reference has `spec.channel: "stable"`, partner patches channel
to `"stable"` -- redundant, mark as `[!] redundant overlay, consider removing`.

## True Conflicts

Both sides changed the same field. Flag for human review with:
- Field path
- Reference old value and new value
- Partner's current value
- Why the reference changed (from EXPLAIN output)
- User chooses: accept reference, keep partner, or provide different value

Example: reference changes `spec.deviceType: netdevice` to `vfio-pci`,
partner has `netdevice` as explicit patch -- conflict, user decides.

## CR Removal

Removing a CR from a policy does NOT remove it from clusters. Need
`complianceType: mustnothave` for actual removal. If reference includes
a removal policy, include it in the merge.

If partner has customizations on a CR being removed, flag for user --
they may still need it.

When the source-cr file for a manifest no longer exists in the target
version, the manifest entry must be removed from the partner's output --
policy generation will fail if it references a missing file. If the
partner has patches on this manifest, flag as `[!]` before removing:
the partner may need to provide their own copy of the source-cr file
or migrate to a replacement CR.

## New CRs from Reference

Only add CRs that are new and required in the target version. Do NOT
add optional or commented-out reference CRs. The reference examples
include many optional configurations -- only the partner's existing
CRs plus genuinely new required CRs belong in the output.

When adding a required new CR, place in closest-fit existing partner
policy based on:
1. Same wave grouping
2. Similar content (e.g. logging CRs go with existing logging policy)
3. If no clear fit, ask the user which policy to add it to

Preserve partner naming conventions for the policy.

## Partner-Duplicated CRs

A partner may have created their own variant of a reference CR --
same GVK and purpose but different name or modified content (e.g. a
custom `AcmePerformanceProfile.yaml` that's a fork of the reference
`PerformanceProfile.yaml`). This means the partner doesn't benefit
from upstream fixes and improvements to the source CR.

Detection: during matching, if a partner manifest's GVK and key fields
closely match a reference source CR but the path or resource name
differs, it may be a duplicate.

Action: flag it and suggest migrating back to the reference source CR
with patches for their customizations. Present the diff between their
variant and the reference CR so they can see what they'd gain. Do not
silently replace -- the partner may have a reason for the fork.

## Version-Pinned Values

Partners may intentionally pin a version that differs from the current
OCP version. Common examples:
- CatalogSource image tags pinned to an older release
- Subscription channels set to a specific version
- Image references with explicit version tags

Detection: if a version-bearing field doesn't match the current (old)
OCP version, the partner likely pinned it intentionally.

Action: do NOT auto-update. Mark with `⚠ REVIEW` and present to user
with the current value and what the "expected" bump would be. Let the
user decide.

## GVK Replacement Procedure

When processing a GVK replacement during merge, update three things:

1. **Manifest path** -- swap the old source-cr filename to the new one
2. **Patch field names** -- if the API renamed fields between old and new
   GVK, rename them in the partner's patches. Carry the partner's VALUES
   to the new field names. Read both old and new source-cr files side by
   side to identify field renames (e.g. a list field renamed from one
   convention to another).
3. **apiVersion/kind** -- if the partner patches apiVersion or kind
   directly, update to the new GVK values.

The partner's actual customization values must survive the migration.
Only the structural wrapper (paths, field names, GVK) changes. If a
field in the old API has no counterpart in the new API, flag as `[!]`.

## CR Restructure Placement

When a CR's internal structure is reorganized between versions (e.g. one
profile split into multiple architecture-specific profiles, one list
reorganized into named sections), determine where partner customizations
belong in the new structure:

1. Read the target version's base source-CR to understand each new
   section's purpose (architecture scope, hardware type, functional role).
2. Match partner customizations to sections by purpose --
   architecture-level settings go in the architecture section,
   hardware-specific settings go in the hardware section, etc.
3. If a partner customization doesn't clearly belong in any new section,
   flag as `[!]` and ask the user.

Do not place all partner content in the first section by default --
this is a common agent mistake that creates incorrect output.

## Uncertainty Rule

When not 100% sure a change is safe, **leave the partner's value alone**
and flag it. Present:
- What the checklist says to change
- What the partner currently has
- Why you're uncertain

It is always safer to flag something and let the user decide than to
silently apply a change that might break their deployment.

## New Functionality from User

When the user requests new features (e.g. "add logging health check"),
treat as an additional merge step after reference updates. The user's
description guides what to add; reference CRs for the target version
provide the implementation.