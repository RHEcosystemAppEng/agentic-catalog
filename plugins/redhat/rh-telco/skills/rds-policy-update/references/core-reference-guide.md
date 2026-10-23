# Core Reference Guide

This file provides additional content for the Core use case: container
image, directory layout, PG naming, and CR catalog discovery. The
EXPLAIN → MERGE → VALIDATE workflow and PolicyGenerator format are
common to all use cases.

## Container Image

```
registry.redhat.io/openshift4/openshift-telco-core-rds-rhel9:v{version}
```

The image emits its contents as a base64-encoded tar on stdout. Log in
to the registry first, then run the image and unpack the stream:
```bash
podman login registry.redhat.io
podman run --rm registry.redhat.io/openshift4/openshift-telco-core-rds-rhel9:v{version} | base64 -d | tar xv -C {output_dir}
```
This unpacks a `telco-core-rds/` tree into `{output_dir}` (see Directory
Layout below). Do NOT use `podman cp` or `oc image extract` -- this
image streams its content rather than laying it out on the image
filesystem.

## Directory Layout

```
telco-core-rds/configuration/
├── <PolicyGenerator files>     # active PG files are listed in
│                               #   kustomization.yaml `generators:` -- e.g.
│                               #   core-baseline.yaml, core-overlay.yaml,
│                               #   core-upgrade.yaml, core-finish.yaml
├── kustomization.yaml
├── template-values/            # ConfigMaps for hub-side templating
├── reference-crs/              # MERGE source CRs (deployable)
│   ├── required/               # Must be present for conformant cluster
│   └── optional/               # Partner chooses which to include
└── reference-crs-kube-compare/ # cluster-compare templates -- ignore for
                                #   EXPLAIN/MERGE (not source CRs)
```

Notes:
- MERGE source CRs live in `reference-crs/`, split into `required/` and
  `optional/` subdirectories. Ignore the sibling
  `reference-crs-kube-compare/` tree -- it holds cluster-compare
  templates, not deployable source CRs
- Do not hardcode the PolicyGenerator filenames; they change between
  versions. Take the active PG files from the `generators:` list in
  `kustomization.yaml` (each is a `kind: PolicyGenerator`) -- do not glob
  `*.yaml`, which also matches `ns.yaml` and inactive files

## Discovering the CR Catalog

Do not rely on a hardcoded operator or CR list — it changes between
versions. Derive the catalog from the extracted reference for each
version being compared:

- Enumerate `reference-crs/required/` and `reference-crs/optional/`
  for the shipped CRs and their required/optional status.
- Derive the operator set from the Subscription CRs (`spec.name`
  gives the operator).

CR matching rules are common across use cases — see
`cr-matching-heuristics.md`.
