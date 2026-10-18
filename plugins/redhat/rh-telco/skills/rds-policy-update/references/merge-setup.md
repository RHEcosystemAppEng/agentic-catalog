# MERGE Setup


0. **Check validation tools** -- run `command -v kustomize` and check
   for the PolicyGenerator plugin binary at
   `~/.config/kustomize/plugin/policy.open-cluster-management.io/v1/policygenerator/PolicyGenerator`.
   If either is missing, tell the user:
   "Validation hook won't run — install kustomize and the PolicyGenerator
   plugin for automatic error catching during merge. See docs/HOOKS.md."
   This is informational, not a blocker — continue with the merge.
1. **Load the merge checklist** from the output directory
   (`/tmp/rds-merge-{target}-{timestamp}/checklist.md`).
   This is the driver -- every change comes from this list.
2. **Clone or copy** the partner's policy source into the output
   directory (`/tmp/rds-merge-{target}-{timestamp}/partner/`).
   - If a git repo URL: clone into the output directory.
   - If a local directory path: `cp -a` the directory into the output
     directory. Do NOT modify the original.
   - Ask the user for permission before cloning/copying.
3. **Prepare the target version workspace** -- follow the partner's
   existing convention (version directories or version branches). Copy
   the partner's current version content as the starting point. Also
   follow the partner's PolicyGenerator file naming convention -- if
   they use e.g. `core-baseline-production.yaml`, keep that pattern
   rather than renaming to the reference names.
4. **CR drift detection** -- before replacing the source-CR directory,
   diff every CR file the partner references (via `path:` in
   their PG manifests) against the corresponding reference CR
   for the **source** version. Any field that differs is a direct
   edit the partner made instead of using a PG patch. These edits
   will be silently lost when source-crs are replaced with the target
   version. For each diff found:
   - Flag as `[!]` in the checklist
   - Show the exact field, partner's value, and reference default
   - Warn that the edit will be lost on source-crs replacement
   - Suggest adding a PG patch to preserve the customization
   Only diff source-crs the partner actually references in their PG
   manifests — ignore unused files.
5. **Identify and stage custom source-CRs** -- before replacing the
   directory, compare each `path:` in the partner's PolicyGenerator
   against the reference PG examples for the source version. If a partner
   path differs from the reference path for the same CR kind, the partner
   has a custom source-CR (e.g. a custom `sriovOperatorConfigForSNO.yaml`
   instead of the reference `SriovOperatorConfig.yaml`). Stage these files
   aside so the next step's replacement can't delete them.
6. **Replace the source-CR directory** for the target version. Extract
   from the container using the method in the matching reference guide
   (it differs by use case — e.g. Core streams a base64 tar, so `oc
   image extract` does not apply). Prefer re-extracting each run; reuse
   a local `ref-{version}/` only when confirmed latest, per EXPLAIN
   step 1.
7. **Restore staged custom source-CRs** -- copy the files staged in
   step 5 back into the output, in a directory **separate** from the
   managed reference source-CRs (e.g. `custom-crs/`) -- never intermixed
   under the reference source-CR directory, which is replaced wholesale
   on upgrade (anything under it is lost). If the partner had intermixed
   custom CRs under the managed directory, relocate them to the separate
   directory and update the `path:` references in their PolicyGenerator,
   flagging the change. These custom files must be:
   - Preserved unchanged during merge (do not replace with reference paths)
   - Never overwritten by a reference-delivered source-CR
   - Flagged for user review (the custom CR may need updates for the
     target version's API changes)
8. **Verify paths** -- check that every managed reference `path:` the
   partner uses still resolves in the new source-CR directory (including
   backward-compatible symlinks); if one is missing, the merge must
   update it to the new reference location. For relocated custom-CR paths
   (e.g. `custom-crs/...` from step 7), verify them against the separate
   custom directory and leave them pointing there -- do not redirect a
   custom CR's `path:` into the reference source-CR directory.
