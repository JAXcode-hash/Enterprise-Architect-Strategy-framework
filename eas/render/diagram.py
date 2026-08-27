"""End-to-end flow diagram, generated from the selected positions.

The diagram is not decorative. It is drawn from what the domains actually
chose, so a public ingress only appears if a network option put one there,
and a token vault only appears if the data position introduced one. Emitted as
Mermaid so it renders in the repository and in the project dashboard.
"""

from __future__ import annotations


def _caps(catalogue, selection) -> set[str]:
    out: set[str] = set()
    for opt in selection.values():
        out |= catalogue.expand(opt.provides)
    return out


def e2e_flow(catalogue, selection, intake) -> str:
    c = _caps(catalogue, selection)
    ids = {o.id for o in selection.values()}
    L: list[str] = ["flowchart LR"]

    public = "network.ingress.waf" in c or intake.signal_on("internet-facing") or \
        intake.signal_on("customer-facing")
    private_only = "network.private.only" in c
    inspected = "network.egress.inspected" in c
    micro = "network.segmentation.micro" in c
    gateway = "integration.gateway.managed" in c
    tokenised = "data.tokenised" in c
    events = "integration.async.idempotent" in c
    third_party = "integration.thirdparty.registered" in c
    multi_region = "resilience.multi-region" in c

    if public:
        L += [
            "  subgraph EXT[\"Untrusted - public internet\"]",
            "    USER([\"Customers / partners\"])",
            "  end",
            "  subgraph EDGE[\"Trust boundary 1 - public edge\"]",
            "    WAF[\"WAF, DDoS and bot protection\"]" if "network.ingress.waf" in c
            else "    WAF[\"Public endpoint - NO WAF SELECTED\"]",
            "  end",
            "  USER --> WAF",
        ]

    L += ["  subgraph APP[\"Trust boundary 2 - application plane\"]"]
    if gateway:
        L.append("    GW[\"API gateway - authN, authZ, rate limit, per-edge log\"]")
    L.append("    SVC[\"In-scope services\"]")
    if events:
        L.append("    BUS[(\"Event backbone - governed schemas, retained\")]")
    if micro:
        L.append("    MESH{{\"Default-deny east-west, identity-aware policy\"}}")
    L.append("  end")

    L += ["  subgraph DATA[\"Trust boundary 3 - data plane\"]"]
    if tokenised:
        L.append("    VAULT[\"Token vault - real values\"]")
        L.append("    STORE[(\"Application stores - tokens only\")]")
    else:
        L.append("    STORE[(\"Application stores\")]")
    L.append("    BAK[(\"Backups\")]")
    L.append("  end")

    L += ["  subgraph CTRL[\"Control plane\"]",
          "    IDP[\"Identity provider\"]"]
    if "identity.pdp.central" in c:
        L.append("    PDP[\"Policy decision point\"]")
    if "data.key.customer-managed" in c or "data.key.hyok" in c:
        L.append("    KMS[\"Key management\"]")
    if "secops.log.type1" in c:
        L.append("    SIEM[\"Central detection platform<br/>Type 1 - security monitoring fn\"]")
    elif "secops.ingestion.compatible" in c:
        L.append("    SIEM[/\"Central detection platform<br/>Type 1 - standards-ready,<br/>not connected\"/]")
    else:
        L.append("    SIEM[/\"Central detection platform<br/>Type 1 - NOT CONNECTED,<br/>no ingestion compatibility\"/]")
    if "secops.log.type2" in c:
        L.append("    COMP[\"Enterprise compliance platform<br/>Type 2 - governance fn\"]")
    L.append("    OBS[\"Local operational logging<br/>Type 3 - technology owner\"]")
    L.append("  end")

    if public:
        L.append(f"  WAF --> {'GW' if gateway else 'SVC'}")
    if gateway:
        L.append("  GW --> SVC")
    if micro:
        L.append("  SVC --- MESH")
    if events:
        L.append("  SVC <--> BUS")
    if tokenised:
        L += ["  SVC -->|\"tokenise on entry\"| VAULT", "  VAULT --> STORE", "  SVC --> STORE"]
    else:
        L.append("  SVC --> STORE")
    L.append("  STORE --> BAK")

    L += ["  SVC -.->|\"authenticate\"| IDP"]
    if "identity.pdp.central" in c:
        L.append("  SVC -.->|\"authorise\"| PDP")
    if "data.key.customer-managed" in c or "data.key.hyok" in c:
        L.append("  STORE -.->|\"key operations\"| KMS")
    if "secops.log.type1" in c:
        L.append("  SVC -.->|\"Type 1 detection sources\"| SIEM")
        if gateway:
            L.append("  GW -.->|\"per-edge log\"| SIEM")
    else:
        L.append("  SVC -. \"awaiting engagement\" .-> SIEM")
    if "secops.log.type2" in c:
        L.append("  SVC -.->|\"Type 2 compliance records\"| COMP")
    L.append("  SVC -.->|\"Type 3 telemetry\"| OBS")

    egress_label = (
        "L7 inspected, FQDN allow-list, DLP" if inspected and "data.dlp.egress" in c
        else "L7 inspected, FQDN allow-list" if inspected
        else "shared NAT / proxy - NOT inspected"
    )
    L += ["  subgraph EGR[\"Trust boundary 4 - egress\"]",
          f"    PROXY[\"Egress control - {egress_label}\"]", "  end",
          "  SVC --> PROXY"]
    if third_party:
        L += ["  subgraph TP[\"Registered third parties - materiality assessed\"]",
              "    T1EXT([\"Material third party\"])", "  end", "  PROXY --> T1EXT"]
    else:
        L.append("  PROXY --> INET([\"External destinations\"])")
    if "secops.detection.egress" in c:
        L.append("  PROXY -.->|\"egress detection\"| SIEM")

    if multi_region:
        L += ["  subgraph R2[\"Second region\"]",
              "    STORE2[(\"Replica / standby stores\")]", "  end",
              "  STORE ==>|\"replication - check residency\"| STORE2"]

    if private_only:
        L.append("  classDef privateNote fill:#eef,stroke:#557")
    return "\n".join(L)


def dependency_graph(catalogue, selection, roadmap) -> str:
    L = ["flowchart TD"]
    for code, item in roadmap["domain_schedule"].items():
        L.append(f"  {code}[\"{code}<br/>{item['option']}<br/>{item['weeks']:g}w\"]")
    for a, b in roadmap["dependency_edges"]:
        L.append(f"  {a} --> {b}")
    return "\n".join(L)
