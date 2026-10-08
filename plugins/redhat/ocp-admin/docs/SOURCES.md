# Red Hat Documentation Sources

This document provides attribution for all official Red Hat documentation sources used in the ocp-admin knowledge base.

## Source Attribution Table

| Category | Document Title | Official Source URL | Sections Referenced | Last Verified |
|----------|---------------|---------------------|-------------------|---------------|
| **OpenShift Installation** | Installing on bare metal with the Assisted Installer | [docs.openshift.com](https://docs.openshift.com/container-platform/latest/installing/installing_with_agent_based_installer/preparing-to-install-with-agent-based-installer.html) | Cluster creation, host requirements, network configuration | 2026-03-31 |
| **OpenShift Installation** | Assisted Installer for OpenShift Container Platform | [console.redhat.com](https://console.redhat.com/openshift/assisted-installer/clusters) | Web UI, API access, cluster lifecycle | 2026-03-31 |
| **OpenShift Installation** | Installing a single-node OpenShift cluster | [docs.openshift.com](https://docs.openshift.com/container-platform/latest/installing/installing_sno/install-sno-installing-sno.html) | SNO requirements, configuration, deployment | 2026-03-31 |
| **OpenShift Networking** | Understanding networking | [docs.openshift.com](https://docs.openshift.com/container-platform/latest/networking/understanding-networking.html) | Network configuration, CNI, service networking | 2026-03-31 |
| **OpenShift Networking** | Configuring ingress cluster traffic | [docs.openshift.com](https://docs.openshift.com/container-platform/latest/networking/configuring_ingress_cluster_traffic/index.html) | Ingress VIP, load balancers, routes | 2026-03-31 |
| **OpenShift Networking** | Network configuration with nmstate | [docs.openshift.com](https://docs.openshift.com/container-platform/latest/networking/k8s_nmstate/k8s-nmstate-about-the-k8s-nmstate-operator.html) | Static networking, nmstate configuration | 2026-03-31 |
| **OpenShift Storage** | Understanding persistent storage | [docs.openshift.com](https://docs.openshift.com/container-platform/latest/storage/understanding-persistent-storage.html) | Storage classes, PVs, PVCs, storage providers | 2026-03-31 |
| **OpenShift Storage** | Dynamic provisioning | [docs.openshift.com](https://docs.openshift.com/container-platform/latest/storage/dynamic-provisioning.html) | Storage class configuration, volume provisioning | 2026-03-31 |
| **OpenShift Authentication** | Understanding identity provider configuration | [docs.openshift.com](https://docs.openshift.com/container-platform/latest/authentication/understanding-identity-provider.html) | IDP types, OAuth configuration, user management | 2026-03-31 |
| **OpenShift Authentication** | Configuring LDAP identity provider | [docs.openshift.com](https://docs.openshift.com/container-platform/latest/authentication/identity_providers/configuring-ldap-identity-provider.html) | LDAP integration, bind credentials, user mapping | 2026-03-31 |
| **OpenShift RBAC** | Using RBAC to define and apply permissions | [docs.openshift.com](https://docs.openshift.com/container-platform/latest/authentication/using-rbac.html) | Roles, role bindings, cluster roles, security context constraints | 2026-03-31 |
| **OpenShift Security** | Managing security context constraints | [docs.openshift.com](https://docs.openshift.com/container-platform/latest/authentication/managing-security-context-constraints.html) | SCC policies, pod security, privilege escalation | 2026-03-31 |
| **OpenShift Security** | Updating cluster certificates | [docs.openshift.com](https://docs.openshift.com/container-platform/latest/security/certificate_types_descriptions/user-provided-certificates-for-api-server.html) | Certificate rotation, CA management, TLS configuration | 2026-03-31 |
| **OpenShift Backup/Restore** | Backing up etcd data | [docs.openshift.com](https://docs.openshift.com/container-platform/latest/backup_and_restore/control_plane_backup_and_restore/backing-up-etcd.html) | etcd backup procedures, cluster state recovery | 2026-03-31 |
| **OpenShift Backup/Restore** | Disaster recovery | [docs.openshift.com](https://docs.openshift.com/container-platform/latest/backup_and_restore/control_plane_backup_and_restore/disaster_recovery/about-disaster-recovery.html) | Recovery procedures, cluster restoration | 2026-03-31 |
| **OpenShift Cluster Manager** | Red Hat Hybrid Cloud Console | [console.redhat.com/openshift](https://console.redhat.com/openshift) | OCM API, cluster lifecycle, managed services | 2026-03-31 |
| **ROSA** | Red Hat OpenShift Service on AWS | [docs.openshift.com/rosa](https://docs.openshift.com/rosa/welcome/index.html) | ROSA deployment, AWS integration, managed service | 2026-03-31 |
| **ARO** | Azure Red Hat OpenShift | [docs.openshift.com/aro](https://docs.openshift.com/aro/welcome/index.html) | ARO deployment, Azure integration, managed service | 2026-03-31 |
| **OSD** | OpenShift Dedicated | [docs.openshift.com/dedicated](https://docs.openshift.com/dedicated/welcome/index.html) | OSD deployment, cloud provider integration | 2026-03-31 |
| **Host Requirements** | Minimum hardware requirements | [docs.openshift.com](https://docs.openshift.com/container-platform/latest/installing/installing_bare_metal/installing-bare-metal.html#minimum-resource-requirements_installing-bare-metal) | CPU, memory, storage, network requirements | 2026-03-31 |
| **Day-2 Operations** | Post-installation configuration | [docs.openshift.com](https://docs.openshift.com/container-platform/latest/post_installation_configuration/index.html) | Cluster customization, node management, monitoring | 2026-03-31 |
| **Multi-Cluster Management** | Advanced Cluster Management for Kubernetes | [access.redhat.com/documentation/en-us/red_hat_advanced_cluster_management_for_kubernetes](https://access.redhat.com/documentation/en-us/red_hat_advanced_cluster_management_for_kubernetes) | Multi-cluster operations, fleet management, governance | 2026-03-31 |

## Documentation Categories

### OpenShift Installation & Configuration
- **Primary Source**: OpenShift Container Platform Documentation (docs.openshift.com)
- **Focus**: Assisted Installer, bare metal installation, SNO deployment, cluster lifecycle
- **Versions Covered**: OpenShift 4.12-4.18
- **Update Frequency**: Per-release documentation updates

### Managed OpenShift Services
- **Primary Sources**: ROSA, ARO, OSD product documentation + Red Hat Hybrid Cloud Console
- **Focus**: Managed service deployment, cloud provider integration, OCM API
- **Current Versions**: ROSA 4.16+, ARO 4.12+, OSD 4.12+
- **Update Frequency**: Continuous updates with service releases

### OpenShift Networking
- **Primary Source**: OpenShift Networking Documentation
- **Focus**: CNI configuration, service networking, ingress, static networking, nmstate
- **Versions Covered**: OpenShift 4.12+
- **Update Frequency**: Per-release feature additions

### OpenShift Storage
- **Primary Source**: OpenShift Storage Documentation
- **Focus**: Persistent storage, storage classes, dynamic provisioning, CSI drivers
- **Versions Covered**: OpenShift 4.12+
- **Update Frequency**: Per-release storage provider updates

### OpenShift Security & Authentication
- **Primary Source**: OpenShift Authentication & Security Documentation
- **Focus**: Identity providers (LDAP, OAuth), RBAC, SCC, certificate management
- **Versions Covered**: OpenShift 4.12+
- **Update Frequency**: Security advisories and per-release updates

### Backup & Disaster Recovery
- **Primary Source**: OpenShift Backup and Restore Documentation
- **Focus**: etcd backup, cluster recovery, disaster recovery procedures
- **Versions Covered**: OpenShift 4.12+
- **Update Frequency**: Per-release backup mechanism updates

### Multi-Cluster Management
- **Primary Source**: Red Hat Advanced Cluster Management (RHACM) Documentation
- **Focus**: Fleet management, governance, multi-cluster operations, service account authentication
- **Versions Covered**: RHACM 2.6+
- **Update Frequency**: Per-release feature updates

## Additional Resources

### Red Hat APIs
- **Assisted Installer API**: `https://api.openshift.com/api/assisted-install/v2` - Self-managed cluster lifecycle
- **OpenShift Cluster Manager API**: `https://api.openshift.com/api/clusters_mgmt/v1` - Managed service clusters (ROSA, ARO, OSD)
- **API Documentation**: [api.openshift.com](https://api.openshift.com) - Complete API reference

### Red Hat Support
- **Knowledge Base**: [access.redhat.com/solutions](https://access.redhat.com/solutions) - Troubleshooting articles, known issues
- **Customer Portal**: [access.redhat.com](https://access.redhat.com) - Support cases, entitlements, downloads

## Verification Process

All documentation sources:
1. Are official Red Hat product documentation or Red Hat-maintained services
2. Have been verified as accessible as of the "Last Verified" date
3. Include specific sections referenced in the ocp-admin documentation
4. Are kept current with the latest OpenShift releases and API changes

Last full verification: 2026-03-31
