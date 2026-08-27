# SASE migration to Prisma Access

## Drivers
- Retire the colocation-based internet egress stack, which is at end of life and cannot be
  extended to cover remote users without another hardware refresh.
- Give remote users the same inspection and policy as office users, rather than the current
  split where VPN users are backhauled and everyone else is not.
- Reduce the number of places egress policy is written from four to one.

## Scope
Migrate internet egress and private application access from the existing colocation stack to
Palo Alto Prisma Access. In scope: office egress from all sites, remote user access, and
outbound from workloads in GCP, Azure and AWS. The colocation facilities remain for private
interconnect to on-premise systems but stop performing internet egress.

## Objects
- Colocation egress stack: perimeter firewalls, proxies, TLS inspection, DNS forwarders (retiring)
- Prisma Access service connections to each cloud and to the colo (new)
- Prisma Access mobile user gateways per region (new)
- GCP, Azure and AWS landing zones - outbound paths currently egress independently per cloud
- Existing enterprise IdP for user authentication to the SASE tier
- Existing SIEM, receiving logs from the colo stack today

## Integrations
- Colo to on-premise core systems over existing private interconnect
- Prisma Access service connections to GCP, Azure and AWS transit networks
- Prisma Access to the enterprise IdP for user authentication
- Prisma Access log forwarding to the enterprise SIEM
- Third-party SaaS destinations currently reached through the colo proxy

## Environments
- Prod
- RTL - currently egresses through the same colo stack as Prod, with a separate proxy policy set
- Dev-Test - egresses directly to the internet through a cloud NAT gateway, uninspected

## Constraints
- Regions have materially different requirements: EU sites require in-region inspection and
  in-region log retention; UK sites are the regulated estate under PRA and FCA; APAC sites have
  a local data handling requirement and a different set of permitted destinations; US sites have
  the highest throughput and the loosest destination policy.
- Data residency applies to the EU and APAC regions. Inspection means decryption, so where
  inspection happens is where data is processed.
- Cardholder data traverses the payment path and is in PCI-DSS scope.
- The colo contract has a break clause that makes an 18-month migration materially cheaper
  than a 30-month one.
- Approximately 14,000 remote users at peak, 40 sites, 3 clouds, 11 regions.
- Current colo egress is roughly 9 TB/day aggregate with 2,400 allow-listed FQDNs.
