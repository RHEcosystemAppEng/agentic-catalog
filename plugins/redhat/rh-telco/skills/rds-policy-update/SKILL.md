---
name: rds-policy-update
description: >
  Generates updated OpenShift RDS Day 2 configuration policies for version
  upgrades by merging new reference content with partner PolicyGenerator
  customizations. Supports multiple use cases — same workflow,
  different CR reference containers. Use when user mentions "update policies",
  "RDS upgrade", "4.18 to 4.20", "what changed between versions",
  "diff references", "merge reference changes", "validate policies",
  "generate policies for 4.x", "telco core", "core policies",
  "core-baseline", "ranGen", or provides two OCP version numbers in the
  context of RDS, Day 2 config, telco RAN, or telco Core. Also triggers
  for standalone EXPLAIN or VALIDATE. Do NOT use for cluster upgrades,
  fresh installs, or fleet rollout.
license: Apache-2.0
model: inherit
color: magenta
allowed-tools: Read Write Edit Grep Glob AskUserQuestion Bash(podman:*) Bash(oc:*) Bash(kustomize:*) Bash(diff:*) Bash(cp:*) Bash(mkdir:*) Bash(date:*) Bash(tar:*) Bash(base64:*)
metadata:
  version: "0.0.1"
  notice: >
    Content provided to this skill, including policy files and
    configuration data, may be sent to the LLM configured in your
    environment. Ensure the LLM meets your requirements for data privacy
    and security before use.
---

# /rds-policy-update Skill

You help telco partners update Day 2 configuration policies between OCP
versions. You work at the **PolicyGenerator** level -- that's input and output.

**On first interaction**, before any other output, display this notice:
`NOTICE: Content provided to this skill, including policy files and configuration data, may be sent to the LLM configured in your environment. Ensure the LLM meets your requirements for data privacy and security before use.`

The workflow (EXPLAIN → MERGE → VALIDATE) is the same for every use
case. Use-case specifics (container image, directory layout, CR
catalog) live in the reference guides indexed below.

## What's In This Skill

**References** (`references/`) -- domain knowledge to consult as needed:

**Pick the reference guide that matches the use case** (if unsure, ask the user):
- `ran-reference-guide.md` -- RAN container image, layout, PG naming,
  partner versioning
- `core-reference-guide.md` -- Core container image, layout, PG naming,
  partner versioning

**Common** (always relevant, regardless of use case):
- `cr-matching-heuristics.md` -- per-CR-type matching rules
- `cr-guidance/` -- deeper per-CR-type merge guidance; read a CR
  type's file when that CR appears on the checklist
- `policygenerator-semantics.md` -- PolicyGenerator structure,
  complianceType, wave ordering
- `hub-template-handling.md` -- `{{hub ... hub}}` templates
- `merge-conflict-resolution.md` -- how to handle overlaps
- `validate-phases.md` -- dry-run validation
- `merge-setup.md` -- MERGE setup steps; read at the start of MERGE
- `output-validation.md` -- checks to run after writing each PolicyGenerator
- `version-bumping.md` -- version bumping, template ConfigMaps and parent
  kustomization at the end of MERGE

## Prerequisites

- `podman` (or `oc`) and a `registry.redhat.io` login, for the RDS containers
- `git`, or a local copy of the partner's policies
- Optional: `kustomize` and the PolicyGenerator plugin, for validation

Never display registry or Git credentials.

## When to Use This Skill

Use when:
- The user wants Day 2 policies updated for an OCP upgrade (e.g. 4.18 to
  4.20), for RAN or Core
- The user asks what changed between two RDS reference versions
- The user wants reference changes merged into their PolicyGenerator files,
  or merged policies validated

Do NOT use when:
- The user wants to upgrade a cluster, do a fresh install, or roll out to a
  fleet. This skill only works on policy files.

## Important

Do NOT explore the project, search the filesystem, or read local files
to find policies. The user's policies are external to this project.
Ask the user directly for anything missing.

**ONLY modify the copied files under /tmp** All MERGE output
(PolicyGenerator YAML, source-crs, kustomization changes) MUST be
written to the output directory (`/tmp/rds-merge-{target}-{timestamp}/`).
Read from the user's source paths, write ONLY to the output directory.
This is a hard rule — even if the user provides a local directory path,
treat it as read-only input. The user reviews the output directory and
applies changes themselves when ready. Do not use `git checkout`, `Edit`,
`Write`, or any other mechanism to modify files at the user's source
path. If the user's source is a git repo, clone it into the output
directory and work on the clone.

**After presenting outputs from any capability** (EXPLAIN, MERGE, or
VALIDATE), always end with this notice on its own line:
`NOTICE: Always review AI-generated content prior to use.`

## Inputs

**Always required:**
- **Use case** -- which reference applies. Auto-detect from context:
  `acm-*-ranGen.yaml`, `du-profile`, PTP/SRIOV-FEC → RAN;
  `core-baseline.yaml`, `core-overlay.yaml`, `core-finish.yaml`,
  `core-upgrade*.yaml`, MetalLB/ODF, `rds-core-*` branches → Core. If ambiguous, ask. This
  skill operates on **source CRs**; their location is use-case-specific
  and given in the matching reference guide. Wherever this file says
  "source-crs", use that directory.
- **Current version** -- e.g. 4.18
- **Target version** -- e.g. 4.20

**Required only for MERGE (ask when ready to merge, not upfront):**
- **Policy source** -- git repo URL or local directory path where their
  PolicyGenerator YAML lives
- **New functionality** (optional) -- e.g. "add logging health check"

## Workflow

- **EXPLAIN** -- diff two reference versions, classify changes per-CR.
  Only needs the two versions and the use case -- no partner policies required.
  Read the matching reference guide and `policygenerator-semantics.md`.
- **MERGE** -- combine reference updates with partner customizations.
  Read the matching reference guide, `cr-matching-heuristics.md`,
  `merge-conflict-resolution.md`, and `hub-template-handling.md`. For
  each CR type with a file in `cr-guidance/`, read it when processing
  that CR.
- **VALIDATE** -- dry-run merged policies against hub.
  Read `references/validate-phases.md` before starting.

Start with EXPLAIN so the user understands what changed before deciding
to proceed with MERGE. Only ask for policy source when the user is ready
to merge.

## EXPLAIN Workflow

1. **Locate references** -- prefer extracting from the container each run
   so periodic reference fixes are picked up. Only reuse a local
   `ref-{version}/` directory when you can confirm it came from the
   latest container for that version (e.g. a recorded image digest);
   otherwise re-extract. Check each requested version separately. The
   matching reference guide gives the container image and layout.
2. **Diff PolicyGenerator files** between versions -- the matching
   reference guide names the files for the use case. These are the
   high-level view of what changed.
3. **Diff CR content** (the source-CR directory) -- compare EVERY CR
   file that differs between versions, not just the ones with obvious
   changes.
   Even a single added field matters -- it may conflict with a partner
   patch or represent a new default the partner should know about.
4. **Detect structural changes** -- new/removed files, directory
   reorganization, new subdirectories, symlinks.
5. **Classify each change**: path-only, content change, GVK replacement,
   new CR, removed CR, deprecated CR.
   - For CRs with guidance in `cr-guidance/`, read that
     guidance and use it to describe restructuring details — e.g.
     where partner sections map in a multi-profile Tuned, or which
     IBU lifecycle stages exist.
   - When a CR's source file AND its PG entry both changed, describe
     them together — e.g. ConsoleOperatorDisable: managementState
     changed to Removed in the source-cr AND complianceType set to
     mustnothave in the PG means the console is fully removed, not
     just disabled.
6. Save results and build a merge checklist with the actual CRs found.

## After EXPLAIN

Save two files:

Generate a timestamp with `date +%Y%m%d-%H%M%S` and create a single
output directory for the entire run: `/tmp/rds-merge-{target}-{timestamp}/`.
All outputs (reports, checklist, merged policies) go inside this directory.

1. **EXPLAIN report** (`/tmp/rds-merge-{target}-{timestamp}/explain.md`) --
   full analysis of what changed between versions.

2. **Merge checklist** (`/tmp/rds-merge-{target}-{timestamp}/checklist.md`) --
   the **single working document that drives MERGE**. Start with `[ ]`
   unchecked items. During MERGE, update this same file in place --
   marking each item as `[x]`, `[!]`, `[-]`, or `[~]` as it's processed.
   Do not create a separate "completed" file. Each item names the specific
   CR, what changed, and the action to take. For example:

   ```
   - [ ] TunedPerformancePatch — profile renamed X→Y, priority N→M. Update partner patches.
   - [ ] {old GVK} → {new GVK} — GVK replacement. Swap path + patch fields.
   - [ ] {CR name} — new required CR. Place in partner policy (wave N).
   - [ ] source-crs/ — replace with target version
   - [ ] Version references — bump metadata names, namespaces, placement labels
   ```

   Include a **version bumping** section at the end listing all
   version-bearing fields the merge must update:
   - PolicyGenerator `metadata.name`
   - `policyDefaults.namespace`
   - `placement.labelSelector` version labels
   - CatalogSource image tags
   - Namespace and ManagedClusterSetBinding resources

   For fields where the partner may have intentionally pinned a different
   version (e.g. a CatalogSource pinned to an older version), mark with
   `⚠ REVIEW` — do not auto-update, flag for user decision.

## Gotchas

- Removing a CR from a policy does NOT remove it from clusters. Need
  `complianceType: mustnothave`. Check if reference includes removal policy.

- Hub templates resolve at evaluation time, not generation time. Cannot
  validate templated values during dry-run.

- Never match by policy name or filename -- match by GVK + resource identity.

- PTP matching: multiple reference variants, partners rename them all.
  Match on `spec.profile[].ptp4lOpts` and interface, not name.

- SRIOV matching is 1-to-N. One reference CR may map to multiple partner CRs.
  Apply changes to ALL confirmed matches.

- Source CR paths may reorganize between versions. Check for backward-
  compatible symlinks at the root level -- if they exist, old manifest
  path references still resolve and do NOT need updating.

- Wave ordering comes from the `ran.openshift.io/ztp-deploy-wave`
  annotation and differs by use case (RAN 1/2/10/100; Core uses its own
  values, e.g. 1/5/6/200). Preserve the reference's waves; don't move
  CRs across them.

- Policy CRD accepts unknown fields inside `objectDefinition` --
  dry-run only catches Policy wrapper errors, not embedded CR errors.

- MERGE only touches what the partner already has. Do NOT add CRs,
  stages, or fields the partner doesn't already have -- warn about
  gaps instead. Even "required" reference CRs are only reported, not
  injected. Only add new content if the user explicitly requests it
  (via the "new functionality" input). Process the partner's CRs one
  by one against the reference changes -- not the other way around.

- Coverage scan and redundant overlay detection are in the Processing
  and Finish sections -- follow those procedures.

- Partners may have edited source-crs directly or by mistake instead of
  using PG patches. These edits are silently lost when source-crs are
  replaced during upgrade. Before replacing, diff the partner's
  source-crs against the reference source-crs for the source version
  to detect drift. Any differences need to become PG patches.

## MERGE Workflow

**MERGE NEVER modifies the user's original files.** All output goes to
the output directory (`/tmp/rds-merge-{target}-{timestamp}/`). The
user's source paths are READ-ONLY inputs. This applies regardless of
whether the source is a git repo URL or a local directory path.

### Setup

Before processing any checklist item, read `references/merge-setup.md` and
complete steps 0-8 in it, in order: check validation tools, load the
checklist, clone or copy the partner source (ask first), prepare the target
workspace, detect CR drift, stage custom source-CRs, replace the source-CR
directory, restore custom source-CRs, and verify paths.

### Processing (checklist-driven)

**Preserve the partner's PolicyGenerator structure.** The partner may
organize CRs differently from the reference -- different number of
PolicyGenerator files, different policy groupings, different names.
Always follow the partner's structure. If the reference moved a CR
to a different wave or policy, note it and ask for confirmation
rather than silently reorganizing.

**Write complete PolicyGenerator files.** Each merged PG file must
contain ALL manifests from the partner's original -- not just the ones
that changed. Start by copying the partner's PG content, then apply
changes in place. Never write a partial PG with only modified manifests.

**Communicate structural changes.** When a CR's internal structure
changed significantly between versions (profiles split, lists
reorganized, fields renamed), explicitly describe the restructure
to the user. They need to understand why the output looks different
from their input. For example, if a Tuned CR went from 1 profile to
4 architecture-specific profiles, say so -- don't just silently
restructure the patches.

**Process one checklist item at a time.** The checklist is a **working
document** -- update statuses in the file as you process each item:
- `[x]` applied automatically (include what changed)
- `[!]` needs user decision (include options)
- `[-]` N/A (partner doesn't use this CR)
- `[~]` redundant overlay (partner patch matches reference value)

For each item, complete this full cycle before moving to the next:
1. Read the checklist item
2. Apply the relevant processing steps (below)
3. Write the updated checklist status to the file
4. Validate: check the written YAML for correct nesting and
   SetSelector usage before moving on

Do NOT batch multiple items or skip the validation step. Complete
each item fully before starting the next one. Processing steps:

1. **Find ALL affected partner CRs** -- scan EVERY partner PolicyGenerator
   file for manifests that reference the same CR path or GVK. Use matching
   heuristics from `references/cr-matching-heuristics.md`. A single
   reference CR change may affect multiple manifest entries across
   different policies. Apply the change to every instance. If patches
   differ between instances, handle each one separately.
2. **Apply the change** -- three cases depending on what the partner
   patches vs what the reference changed:
   - **Reference field changed between versions** (field existed in
     BOTH source and target reference): apply the new value. If this
     overrides a partner-chosen value, it's still a conflict -- use
     conflict language (e.g. "[x] CONFLICT: partner had priority 19,
     applied reference default 18"). The user must see every override.
   - **Partner has custom field, reference now adds it** (field was NOT
     in the source reference but IS in the target reference): do NOT
     update the partner's value -- flag it instead. The partner was
     ahead of the reference; their override may be intentional or stale.
   - **Reference added new fields partner doesn't patch**: flag as
     available -- do not inject them.
   - **Partner patches a field to the same value as the target
     reference default** (redundant overlay): flag as `[~]` and tell
     the user the patch is a no-op they can remove. Common example:
     `installPlanApproval: Automatic` when the source-cr already
     defaults to `Automatic`.
3. **GVK replacement** -- when the checklist item is a GVK migration,
   update three things in the partner's manifest and patches:
   (a) manifest path to the new source-cr file,
   (b) field names that changed between old and new API (carry the
   partner's VALUES to the new field names),
   (c) apiVersion/kind if the partner patches them directly.
   Read both old and new source-cr files side by side to identify
   field renames. See `references/merge-conflict-resolution.md`
   "GVK Replacement Procedure."
   **Critical:** when writing output PolicyGenerator files, preserve
   the EXACT `path:` values the partner used for custom/partner-specific
   CRs -- never replace with a reference path. The one exception is a
   custom CR that was intermixed under the managed source-CR directory
   and relocated in Setup step 7: use its new separate-directory path
   (e.g. `custom-crs/AcmeSecret.yaml`) and preserve that.
4. **CR removal** -- when the reference removed a CR and the source-cr
   file no longer exists in the target version, remove the manifest
   entry from the partner's output. Policy generation will fail if it
   references a missing file. If the partner has patches on it, flag
   as `[!]` first -- the partner may need to provide their own copy.
5. **Mustnothave conflicts** -- when the reference adds
   `complianceType: mustnothave` to a manifest the partner has patches
   on, flag as `[!]`. The partner's patches become ineffective since
   the resource will be removed. Present options: accept mustnothave
   and remove patches, or keep the CR without mustnothave.
6. **Redundant overlay check** (mandatory, do not skip) -- after
   applying the checklist item's change, check EVERY other patch field
   on the same manifest against the target source-cr. If a patch field
   sets the same value the source-cr already has, mark as `[~]`
   redundant. This is a per-manifest sweep, not per-checklist-item --
   it catches overlays unrelated to the current change. For
   TunedPerformancePatch, use
   `references/cr-guidance/tuned-performance-patch.md`.
7. **Flag for user review** if:
   - Partner has customized the same field the reference changed (true conflict)
   - Partner has pinned a value the checklist says to bump (e.g. older
     CatalogSource image tag)
   - The change is a GVK replacement and partner has non-trivial patches
   - You're not 100% sure the change is safe
   Mark as `[!]` in the checklist and use `ask_user_question` immediately
   to present the conflict with clear options. Do not batch `[!]` items
   to the end -- ask as each one arises so the user can decide in context.
8. If the partner doesn't use the CR at all, mark as `[-]` and move on.
9. **SetSelector variant enforcement** -- PolicyGenerator requires
   `-SetSelector` variants of CRs when available (e.g.
   `PerformanceProfile-SetSelector.yaml` instead of
   `PerformanceProfile.yaml`). Non-SetSelector CRs leave `$mcp` in the
   nodeSelector which won't resolve. When updating manifest paths or
   adding CRs, check if a `-SetSelector` variant exists in the target
   version's `source-crs/`. If the partner was using the non-SetSelector
   version, switch to the SetSelector variant and flag the change.

**When uncertain: leave it alone and highlight it.** Never silently
apply a change you're not confident about. It's better to flag 5 things
that turn out to be fine than to silently break 1 thing.

### Output Validation (Write → Read → Verify → Fix)

After writing each PolicyGenerator file, read
`references/output-validation.md` and run every check in it against the
file as written: content preservation, YAML nesting, redundant overlay
sweep, new reference field sweep, and semver sweep. Fix and re-read until
all checks pass.

### Version Bumping

After processing all checklist items, read `references/version-bumping.md`
and complete all three steps in it: version bumping, template ConfigMap
updates, and the parent kustomization entry. Then run the semver sweep below.

### Semver Sweep

After version bumping, scan ALL output files — PolicyGenerator YAML,
kustomization.yaml, and any other written file — for any remaining
occurrence of the source OCP version (e.g. `4.18`, `4-18`, `4_18`).

**General rule:** every match is suspicious. If the value clearly tracks
the OCP version (channel, namespace suffix, annotation), update it.
If you're unsure whether a value tracks the OCP version, flag it in
the checklist as `[~] ⚠ REVIEW` and preserve the partner's value —
a false update can break partner-specific pinning.

Common locations this catches:
- `lca.openshift.io/target-ocp-version` annotations
- IBU `seedImageRef.version` and `seedImageRef.image`
- CatalogSource and operator index image tags
- Filenames referenced in kustomization.yaml generators/resources
- Hub template namespace references (`{{hub ... hub}}`)
- Channel values, label selectors, namespace suffixes

### Finish

1. **Coverage scan** (mandatory) -- compare the reference PG examples
   against the partner's CR set:
   a. Identify which reference CRs are **required** vs **optional**
      using the catalog rules in the matching reference guide's
      "Discovering the CR Catalog" section (RAN derives this from the
      reference PG examples -- uncommented in all examples means
      required; Core derives it from the `required/` vs `optional/`
      reference-CR directories).
   b. For each required CR the partner does not include, output exactly:
      `WARNING: required CR {name} is not included in your policies.`
      You MUST use the words "WARNING" and "required" so the severity
      is unambiguous. Do not soften to "note" or "optional."
   c. For each optional CR the partner does not include, note as:
      `{name}: not included (optional)`
      Use "optional" and do NOT use "WARNING" or "required."
   d. Do not add missing CRs -- just report them with correct severity.
   e. Output each line individually in your response to the user --
      do not summarize as a count (e.g. "6 missing CRs"). The user
      must see every CR name and its severity.
2. **Present the merge checklist** -- by this point every item in
   `checklist.md` in the output directory must have
   a status. This is mandatory, not a free-form summary. Every CR the
   partner uses must appear with status:
   - `[x]` applied automatically (include what changed)
   - `[!]` flagged for review (include why and what was decided)
   - `[-]` N/A (partner doesn't use this CR)
   - `[~]` redundant overlay (partner patch matches reference value)
   Include CRs the partner removed (present in reference but absent
   from partner policies) so nothing is silently skipped. No item
   may be left unchecked.
3. The user pushes when ready -- never push on their behalf without
   explicit permission.
4. **Pre-existing issue scan** -- scan the partner's input policies for
   issues that are NOT caused by the version upgrade but that a
   reviewer should know about:
   - YAML structural issues (data nested under metadata, missing fields)
   - Deprecated field names or API patterns
   - Known deprecations in referenced tools (e.g. restic → nodeAgent)
   - Invalid YAML values that would fail at apply time
   Report as `NOTE: pre-existing issue in {file}: {description}`.
   Do not fix silently -- flag so the user is aware.

### Artifact Checklist

Always output a complete artifact set -- do not ask whether to include
parts of it:
- Updated PolicyGenerator YAML files
- The source-crs/ directory with base CRs for the target version
- Any additional source-crs the partner added
- Hub template ConfigMaps (as needed)

Flag new hub template variables that need per-cluster values populated.

## Dependencies

### Required MCP Servers
None.

### Required MCP Tools
None.

### Related Skills
None.

### Reference Documentation
The reference guides listed under What's In This Skill.

## Example Usage

User: "upgrade my policies from 4.18 to 4.20, the policy source is ./acme-ran"

1. EXPLAIN: extract both RAN references, diff them, and save `explain.md`
   and `checklist.md` in `/tmp/rds-merge-4.20-<timestamp>/`.
2. MERGE: ask before copying `./acme-ran`, apply each checklist item to the
   copy, and ask about each conflict as it comes up.
3. Finish: report each missing required CR as a WARNING, then present the checklist.
