# RAN Reference Guide

## Container Image

```
registry.redhat.io/openshift4/ztp-site-generate-rhel8:v{version}
```

The image exposes an `extract` command that streams a path as a tar on
stdout. Run it and unpack `/home/ztp/`:
```bash
podman run --log-driver=none --rm registry.redhat.io/openshift4/ztp-site-generate-rhel8:v{version} extract /home/ztp --tar | tar x -C {output_dir}
```
This unpacks the contents of the container's `/home/ztp/` into
`{output_dir}` (see Directory Layout below). `docker run` works the same
way if `podman` isn't available.

## Directory Layout

```
{output_dir}/
├── source-crs/                           # Individual CR YAMLs (flat)
├── argocd/example/acmpolicygenerator/    # PolicyGenerator examples
│   ├── acm-common-ranGen.yaml
│   ├── acm-group-du-sno-ranGen.yaml
│   ├── acm-group-du-standard-ranGen.yaml
│   └── acm-example-sno-site.yaml
└── reference/                            # Telco-reference by operator
```

`source-crs/` structure may change between versions (flat vs operator
subdirectories). Check for backward-compatible symlinks.

## PolicyGenerator Naming

RAN uses `acm-*-ranGen.yaml` organized by scope:
- `acm-common-ranGen.yaml` -- shared (subscriptions, operators)
- `acm-group-du-sno-ranGen.yaml` -- single-node DU profile
- `acm-group-du-standard-ranGen.yaml` -- multi-node standard DU
- `acm-example-sno-site.yaml` -- site-specific per-cluster

Hierarchy: common → group (by topology) → site.

## Discovering the CR Catalog

Do not rely on a hardcoded operator or CR list — it changes between
versions. Derive the catalog from the extracted reference for each
version being compared:

- Enumerate `source-crs/` for the shipped CRs.
- Required vs optional status comes from the reference PG examples:
  uncommented in all examples means required; commented out or
  example-specific means optional.
- Derive the operator set from the Subscription CRs (`spec.name`
  gives the operator).

CR matching rules are common across use cases — see
`cr-matching-heuristics.md`.
