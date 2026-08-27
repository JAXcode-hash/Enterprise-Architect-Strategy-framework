# Payments API modernisation

## Drivers
- Meet the PSD2 open banking mandate for account information and payment initiation.
- Retire the current bespoke integration layer, which is a single point of failure and cannot
  be changed without a full regression cycle.
- Reduce the cost of the annual PCI assessment by shrinking the assessed estate.

## Scope
We will expose a PSD2-compliant open banking API on AWS, fronted by a managed gateway, serving
registered third-party providers. Cardholder data is in scope for the payment initiation
journey. The API sits in front of the existing core banking platform, reached over the current
private interconnect.

## Objects
- Open banking API tier (new)
- Consent management service (new)
- Existing core banking platform (unchanged, integration only)
- Existing fraud decisioning service (unchanged, integration only)
- Customer identity store (existing, extended)

## Integrations
- TPP-facing API over the public internet
- Core banking over the existing private interconnect
- Fraud decisioning over an internal synchronous API
- Payment scheme connectivity via a material third-party processor
- Nightly reconciliation file transfer to finance

## Environments
- Prod
- RTL (currently refreshed from a masked production extract each month)
- Dev-Test (currently holds a full production copy, unmasked)

## Constraints
- Hard regulatory date of Q3 2026. This is externally imposed and immovable.
- DORA and PCI-DSS v4 both apply. The service is classified as an important business service
  with an impact tolerance of 4 hours.
- Multi-region failover is required.
- The payment processor is assessed as a material third party.
- Peak is approximately 900 API requests per second, with roughly 40,000 payment initiations a
  day.
