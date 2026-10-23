# Version Bumping

## Version Bumping

After processing all checklist items, walk the version-bumping section:
- Update `metadata.name` version suffixes in PolicyGenerator YAML
- Update `policyDefaults.namespace`
- Update `placement.labelSelector` version labels
- Update Namespace and ManagedClusterSetBinding resources
- For CatalogSource image tags: update those that track the OCP version.
  If a tag doesn't match the current version (partner pinned it to
  something else), flag as `[~] ⚠ REVIEW` in the checklist and
  preserve the partner's value.

## Template ConfigMaps

ConfigMaps used as hub templates (referenced by `{{hub ... hub}}`
lookups) need the same namespace updates as CRs. If the version
bumping step changed CR namespaces, update the template ConfigMap
namespaces to match — lookups will break if the namespace is stale.

Also scan ConfigMap `data:` sections for version-bearing content
(e.g. catalog index tags, image references). Flag these with
`⚠ REVIEW` — they may need updating for the target version.

## Parent Kustomization

After creating the new version directory, update the `kustomization.yaml`
in the parent directory to add the new version directory to the
`generators:` or `resources:` list. Without this entry, kustomize
won't process the new version's policies.
