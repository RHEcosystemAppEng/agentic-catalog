# CR Matching Heuristics

Common per-CR-type matching rules for all use cases.

Match by **GVK + resource identity** (metadata.name, metadata.namespace).
Never match by policy name, file name, or file structure.

## Confidence Levels

**Exact:** Same GVK + same name. Merge automatically -- unless a per-GVK
rule below overrides name-based matching or restricts auto-update (see
"Per-GVK Matching Fields").

**Fuzzy:** Same GVK, different name, similar spec structure. Always requires
user confirmation.

How to assess similarity:
1. Compare spec field paths (not values -- values differ due to customization)
2. Look for shared structural patterns (same nested objects, same array structures)
3. If there's only one CR of that Kind in both sets, it's likely a match

**No match:** Custom content, leave untouched.

## 1-to-N Matching

One reference CR may map to multiple partner CRs (e.g. partner has 3
SriovNetworkNodePolicy variants for different node types). A reference change
may need to be replicated across all matches. Present all candidates to the user.

## Per-GVK Matching Fields

These per-GVK rules take precedence over the generic "same GVK + same
name" exact match above. Apply the resource's field-based matching, and
honor any never-auto-update restriction (e.g. Secret), before merging --
even when the names are identical.

### SriovNetworkNodePolicy
- Primary: `spec.deviceType`, `spec.resourceName`
- Secondary: `spec.pfNames`, `spec.numVfs`
- Note: reference uses template variables ($deviceType, $pfNames, etc.).
  Partner values replace these. 1-to-N matching is common.

### PtpConfig
- Primary: `spec.profile[].ptp4lOpts`, `spec.profile[].phc2sysOpts`
- Secondary: `spec.profile[].interface`
- Hardest matching case. Reference has ordinary clock, boundary clock,
  grandmaster, dual-follower variants. Partners rename them all and may
  use a subset. Match by PTP profile type, not name.

### PerformanceProfile
- Primary: `spec.cpu.isolated`, `spec.cpu.reserved`
- Secondary: `spec.hugepages`, `spec.realTimeKernel`
- Usually 1-to-1 but partner may have per-hardware-type variants.
- When multiple PerformanceProfiles exist (e.g. one per
  MachineConfigPool), match by role/intent (e.g. high-throughput vs
  control-plane), not name. The reference `spec.nodeSelector` is usually
  a placeholder that will NOT equal the partner's -- use it only as a
  weak hint and confirm the mapping with the user.

### Subscription
- Primary: `spec.name` (operator name)
- Usually exact match since operator names are standardized.
- Watch for `spec.channel` version bumps.

### Tuned
- Primary: `spec.profile[].name`, `spec.recommend[].priority`
- Reference may rename profiles between versions. Match by profile
  content structure and recommend priority, not name.
- Profile hierarchy may change (single profile split into multiple
  arch-specific profiles). Compare the data sections.
- When per-MachineConfigPool Tuned CRs exist, match by role/intent, not
  name. As with PerformanceProfile, the reference selector
  (`spec.recommend[].machineConfigLabels`, e.g.
  `machineconfiguration.openshift.io/role: $mcp`) is usually a
  placeholder that won't equal the partner's -- treat it as a weak hint
  and confirm.

### MachineConfig
- Primary: `metadata.name` prefix pattern, `spec.config.storage.files[].path`
- Match by what files/units the MachineConfig manages.

### BGPPeer (MetalLB)
- Primary: `spec.peerASN`, `spec.peerAddress`
- 1-to-N matching is common (one reference peer, many partner peers).

### Secret
- Never auto-update any Secret, even on an exact GVK + name match.
  Secrets carry partner- or environment-specific data (e.g.
  `rook-ceph-external-cluster-details` for external Ceph/ODF, pull
  secrets, MetalLB/BGP credentials). Flag for user review only.

## GVK Replacements

Between versions, a CR's GVK may change entirely. Detect by looking for:
1. A CR file removed in the new version (not just moved to a subdirectory)
2. A new CR file added that serves the same purpose
3. The old and new CRs have similar spec structure but different apiVersion/kind

Treat as removal + addition, but present as a replacement to the user.
Carry over partner customizations where fields map between old and new
GVK. When fields are renamed between the old and new API (e.g. a spec
list field changes name), map the partner's patch values to the new
field names. Read both the old and new source-cr files side by side to
identify which fields were renamed vs which are genuinely new.
Flag fields that don't have a direct mapping.

See `merge-conflict-resolution.md` "GVK Replacement Procedure" for the
step-by-step merge process.

## Escalation

- Fuzzy match with high similarity: recommend accepting, still ask
- Fuzzy match with low similarity: flag as uncertain
- Multiple candidates: ask user to select
- No match for a modified reference CR: ask if they want to add it