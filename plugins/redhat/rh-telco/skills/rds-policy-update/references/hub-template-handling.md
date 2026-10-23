# Hub Template Handling

## Syntax

Hub templates use `{{hub ... hub}}` delimiters and resolve at policy
evaluation time from hub resources -- not at generation time.

```yaml
spec:
  profile:
    - name: "{{hub fromConfigMap "" (printf "%s-ptpconfig" .ManagedClusterName) "profile-name" hub}}"
      interface: "{{hub fromConfigMap "" (printf "%s-ptpconfig" .ManagedClusterName) "interface" hub}}"
```

Common functions:
- `fromConfigMap <ns> <name> <key>` -- read from ConfigMap
- `fromSecret <ns> <name> <key>` -- read from Secret
- `.ManagedClusterName` -- the bound cluster's name
- `printf` -- string formatting (typically for per-cluster resource names)

## Preserving Hardcoded Overrides

If a partner hardcoded a value instead of using a hub template, preserve
it -- even if the reference changes the template. Hardcoding is intentional.

Detect by comparing: if the partner's value is a plain string (no
`{{hub ... hub}}` delimiters) where the reference uses a template,
it's a hardcoded override.

Example:
- Reference: `"{{hub fromConfigMap "" (printf "%s-ptpconfig" .ManagedClusterName) "interface" hub}}"`
- Partner: `interface: "ens5f0"`
- Result: keep `"ens5f0"` -- do NOT replace with the template

## New Templates from Reference

When the reference adds new hub templates in the target version, include
them in merged output but flag in the report. They need per-cluster
ConfigMap/Secret values populated before policies will work.

List the specific ConfigMap/Secret names and keys needed.

## Template Changes Between Versions

- Partner uses template as-is: update to new version's template
- Partner hardcoded the value: preserve hardcoded value
- Partner modified the template expression: treat as customization,
  flag if underlying structure changed

## Validation Limitation

Hub templates cannot be validated during dry-run or schema validation.
Template expressions are opaque strings until the policy controller
evaluates them on the hub. Field-level correctness of templated values
is only verifiable through inform-mode compliance checking (future scope).