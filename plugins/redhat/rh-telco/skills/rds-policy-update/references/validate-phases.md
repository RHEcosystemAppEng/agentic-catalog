# Validation (POC)

Dry-run validation against the hub -- read-only, nothing written to etcd.
The target namespace must exist on the hub.

## What It Catches

- Type mismatches (string where bool expected)
- Invalid enum values (remediationAction must be "inform" or "enforce")
- Structural errors (array vs scalar)

Error format:
```
The Policy "name" is invalid:
* spec.remediationAction: Unsupported value: 12345: supported values: "Inform", "inform", "Enforce", "enforce"
* spec.disabled: Invalid value: "string": spec.disabled in body must be of type boolean: "string"
```

## What It Does NOT Catch

- Unknown fields inside objectDefinition (Policy CRD uses
  x-kubernetes-preserve-unknown-fields)
- Invalid embedded CR content (opaque to Policy CRD)
- Missing CRDs on spoke clusters
- Unresolvable hub templates
- Runtime operator webhook rejections

## Offline Mode

When no hub is available, schema validation against the Policy CRD can
catch structural errors without a cluster. Less coverage than dry-run
but suitable for CI pipelines or detached workflows.

## Retry

Diagnose error, propose fix, wait for user approval, retry. If the same
error persists or you're not making progress after 2-3 attempts, escalate
to the user with full context rather than looping.