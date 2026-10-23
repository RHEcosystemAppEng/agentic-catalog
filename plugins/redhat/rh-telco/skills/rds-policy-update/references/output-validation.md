# Output Validation (Write → Read → Verify → Fix)


**Automatic validation:** a hook runs `kustomize build` after every
Write/Edit of a PolicyGenerator YAML — errors feed back automatically.

After writing each PolicyGenerator file, **read the file back** and
run these checks against the actual written content — not your memory
of what you wrote. If any check fails, fix the file with an Edit and
re-read to confirm the fix.

1. **Content preservation check** -- for every manifest in the partner's
   INPUT file, verify the OUTPUT file has a corresponding manifest. For
   every patch field in the input, verify it exists in the output. If
   a field from the partner's input is missing from the output, you
   dropped partner content -- add it back immediately. Never silently
   remove a partner patch field without the user confirming removal.
2. **YAML nesting** -- `metadata:`, `spec:`, `data:`, `status:` must be
   siblings at the same indent level under each CR patch — not nested
   under each other. If you find nesting errors, **do not fix them** —
   these are pre-existing partner issues. Preserve the partner's original
   structure and flag as `NOTE: pre-existing issue` in the checklist.
3. **Redundant overlay sweep** -- for every patched field in every
   manifest, read the target version's source-cr file and compare. If
   the patch value matches the source-cr default, flag as `[~]`
   redundant. This catches overlays the per-item processing missed.
   **Critical:** a partner field is only redundant if its value is
   character-for-character identical to the source-cr default. If the
   values differ at all, it is a partner customization -- preserve it.
4. **New reference field sweep** -- for every manifest the partner uses,
   compare the partner's patch fields against the target version's
   source-cr. If the source-cr added a new field the partner doesn't
   patch (e.g. `ptpSchedulingPolicy`), flag it as available in the
   checklist -- do not inject it into the partner's patches.
5. **Semver sweep on written files** -- read each written PG file and
   search for any remaining occurrence of the source version (e.g.
   `4.18`). This catches version-bearing annotations, image tags, and
   labels that the version bumping step missed. If found, update them
   and note the change in `checklist.md`.

Preserve the partner's original YAML quoting conventions exactly.
Different quote styles (`"value"` vs `'value'` vs `value`) can
produce functionally different strings in some contexts.
