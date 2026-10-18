# ImageBasedUpgrade (IBU) — Lifecycle Stages

The reference IBU lifecycle uses 3 stages, each in its own policy:

1. **Prep** — `stage: Prep`, includes `seedImageRef` (version + image),
   `oadpContent`, optional `extraManifests`
2. **Upgrade** — `stage: Upgrade`
3. **Finalize** — `stage: Idle` (returns to Idle after upgrade completes)

## Stage completeness check

Compare the partner's IBU stage policies against the reference. If the
partner is missing a stage the reference has (e.g. missing the Upgrade
stage), flag it explicitly:
`WARNING: partner IBU is missing the {stage} stage — reference has
Prep, Upgrade, and Finalize.`

Do not add the missing stage — just warn. The partner may have a valid
reason for omitting it, and adding unrequested content risks breaking
their workflow.
