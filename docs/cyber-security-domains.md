# Cyber Security Domains — Comprehensive Reference

*Practitioner/architect-level taxonomy of the cyber security field, organised into logical groupings. Canonical framework anchors (CISSP, NIST CSF) are mapped at the end.*

> **Cloud vs traditional infrastructure:** Cloud security (group 3) is kept deliberately separate from traditional/on-premises infrastructure (group 7). The split is intentional — cloud shifts the trust boundary (shared responsibility), the control plane (API-driven, ephemeral), the identity model (entitlements at scale), and the tooling (CSPM/CNAPP/CIEM) far enough from data-centre security that treating them as one domain hides real risk. Where a concern genuinely spans both (e.g. container/Kubernetes platforms, workload identity), it is noted rather than duplicated.

---

## 1. Governance, Risk & Compliance (GRC)
- **Security governance & strategy** — operating model, ownership, board reporting
- **Risk management** — assessment, treatment, quantification (FAIR)
- **Regulatory compliance** — PRA/FCA, DORA, PCI-DSS, GDPR, sector rules
- **Policy, standards & control frameworks** — ISO 27001, NIST CSF/800-53, CIS
- **Audit & assurance** — control testing, evidence, certification
- **Third-party / supply-chain risk** — vendor, CTP (SS6/24), concentration risk
- **Privacy & data protection** — DPIA, data subject rights, data ethics
- **Model risk (for AI/analytics)** — SS1/23, explainability, validation

## 2. Security Architecture & Engineering
- **Enterprise & solution security architecture** — SABSA/TOGAF-aligned design
- **Secure design principles & patterns** — defence-in-depth, least privilege
- **Zero Trust architecture** — identity-centric, continuous verification
- **Cryptography & key management** — algorithms, PKI, HSM, BYOK/HYOK
- **Architecture-as-Code & policy-as-code** — drift detection, OPA/Rego gates
- **Security patterns & reference architectures** — reusable, governed building blocks

## 3. Cloud Security Architecture
- **Cloud security architecture & landing zones** — secure baseline, org hierarchy, guardrails (CAF, Well-Architected)
- **Shared responsibility model** — provider vs customer boundary per service model (IaaS/PaaS/SaaS)
- **Cloud Security Posture Management (CSPM)** — misconfiguration detection, compliance drift
- **Cloud Workload Protection (CWPP)** — runtime protection for VMs, containers, serverless
- **Cloud-Native Application Protection (CNAPP)** — consolidated posture + workload + identity + data
- **Cloud Infrastructure Entitlement Management (CIEM)** — permissions, least privilege at scale
- **Cloud network security** — VPC/VNet design, private connectivity, egress control, micro-segmentation
- **Cloud data security & DSPM** — encryption, KMS/HSM, data discovery and posture
- **Serverless & PaaS security** — function isolation, event-driven trust, managed-service hardening
- **SaaS Security Posture Management (SSPM)** — third-party SaaS configuration and access risk
- **Multi-cloud & hybrid security** — consistent policy and identity across providers
- **Cloud governance & guardrails** — landing-zone policy, org policy/SCP, policy-as-code enforcement

## 4. Identity & Access Management (IAM)
- **Authentication** — MFA, passwordless, credential lifecycle
- **Authorisation** — RBAC/ABAC/ReBAC, policy decision points
- **Federation & SSO** — SAML/OIDC, trust relationships
- **Privileged Access Management (PAM)** — JIT/JEA, break-glass
- **Identity Governance & Administration (IGA)** — JML, entitlement review
- **Workload / machine identity & secrets management** — federation, rotation *(spans cloud and on-prem)*

## 5. Application & Product Security
- **Secure SDLC / DevSecOps** — shift-left, CI-gated controls
- **Application security testing** — SAST, DAST, IAST, SCA
- **API security** — authN/Z, schema governance, abuse protection
- **Software supply-chain security** — SLSA, SBOM, signing (Sigstore), provenance
- **Threat modelling** — as a programme, not an event (STRIDE, IriusRisk)
- **Product security** — security embedded in product lifecycle and roadmap

## 6. Data Security
- **Data classification & governance** — sensitivity, ownership, lineage
- **Encryption at rest & in transit** — TLS floors, mTLS, field-level
- **Data Loss Prevention (DLP)** — egress control, exfil detection
- **Tokenisation & masking** — non-prod data handling
- **Data residency & sovereignty** — cross-border flow control
- **Database & storage security** — access, activity monitoring

## 7. Infrastructure & Endpoint Security (Traditional / On-Premises)
- **Endpoint security** — EDR/XDR, device hardening
- **Server & host security** — OS baseline, patching, hardening (physical and virtual)
- **Data centre & virtualisation security** — hypervisor, storage/SAN fabric, host isolation
- **Traditional network security** — perimeter & internal firewalls, IDS/IPS, NAC, segmentation, DNS security, remote access/VPN
- **Container & Kubernetes platform security** — admission control, image hygiene *(platform layer; runs on-prem or cloud)*
- **Mobile security** — MDM, app hardening
- **OT / ICS / IoT security** — safety-critical, protocol-aware controls

## 8. Security Operations (SecOps)
- **Security monitoring & SIEM** — log collection, correlation
- **Detection engineering** — use-case development, tuning
- **Threat intelligence** — strategic/operational/tactical CTI
- **Threat hunting** — hypothesis-driven proactive search
- **Incident response** — playbooks, containment, recovery
- **Digital forensics** — evidence handling, root-cause analysis
- **Vulnerability & threat management (TVM)** — exploitability-aware prioritisation (KEV, EPSS)
- **SOAR / automation** — response orchestration

## 9. Offensive Security / Adversary Simulation
- **Penetration testing** — scoped technical assessment
- **Red teaming** — objective-based adversary emulation
- **Purple teaming** — detection/response validation with blue team
- **Vulnerability disclosure & bug bounty** — coordinated intake
- **Exploit & security research** — capability development

## 10. Resilience & Continuity
- **Business continuity (BCP)** — critical service continuity
- **Disaster recovery (DR)** — RTO/RPO, failover
- **Cyber resilience** — withstand/recover under active attack
- **Crisis & incident management** — command, comms, coordination
- **Backup & recovery integrity** — immutability, restore assurance

## 11. Human & Organisational Security
- **Security awareness & training** — behaviour change
- **Human risk management** — phishing resistance, risk scoring
- **Insider threat** — detection, deterrence, investigation
- **Security culture** — norms, tone from the top

## 12. Physical & Environmental Security
- **Physical access control** — facilities, data centres
- **Environmental controls** — power, cooling, monitoring
- **Cyber-physical convergence** — where physical meets digital

## 13. Emerging & Specialised
- **AI/ML security** — model security, adversarial ML, prompt injection, agentic-system risk
- **Post-quantum / crypto-agility** — PQC migration readiness
- **Blockchain / DLT security** — smart-contract, key custody
- **Sector-specific cyber** — space/satellite, automotive, medical device

---

## Framework anchors

- **CISSP eight domains** — Security & Risk Management, Asset Security, Security Architecture & Engineering, Communication & Network Security, IAM, Security Assessment & Testing, Security Operations, Software Development Security. These are a coarser cut of groups 1–9 above. Note CISSP folds cloud into architecture and network domains; this taxonomy separates it deliberately.
- **NIST CSF 2.0** — six functions: Govern, Identify, Protect, Detect, Respond, Recover. These are *lifecycle phases* applied across every domain, not domains themselves. Treat the list above as the "what" and CSF as the "when/how" overlay.
