# Sovereign AI platform for customer servicing

## Drivers
- Deploy LLM-assisted customer servicing across the retail estate, reducing handling time on
  routine enquiries.
- Do it under a sovereignty commitment already made to the regulator and to corporate clients.
- Establish the platform pattern the rest of the group will adopt, rather than a point solution.

## Scope
Stand up a UK-only sovereign platform hosting LLM inference over customer records, serving an
important business service. Kubernetes across two hyperscalers to avoid concentration in a
single cloud provider. Retrieval-augmented generation over customer correspondence, product
holdings and servicing history.

## Objects
- Inference platform (new, Kubernetes, dual-cloud)
- Retrieval and embedding store over customer records (new)
- Model gateway with prompt and response filtering (new)
- Agent orchestration tier (new)
- Existing CRM and servicing platforms (integration only)
- Existing data lake (source for retrieval, integration only)

## Integrations
- Servicing agent desktop to the model gateway
- Model gateway to two hyperscaler inference endpoints
- Retrieval store to the existing data lake
- Agent orchestration to CRM and to the core servicing platform
- Two material third-party model providers and one critical infrastructure provider

## Environments
- Prod (UK regions only)
- RTL (currently uses a real production data extract for retrieval quality testing)
- Dev-Test (synthetic prompts, but a real embedding index)

## Constraints
- Data residency is mandatory and contractual. No cross-border processing, including vendor
  support access.
- PRA, FCA, DORA and SS1/23 all apply. Model risk governance is required and the scoring behind
  any automated decision must be decomposable.
- Multi-region active-active within the UK is required for the important business service.
- Several material third parties and at least one critical third party.
- Hard regulatory date of Q4 2026.
- Real production data is currently used in test for retrieval quality measurement.
- Peak of 60 inference requests per second, growing to an estimated 400 within two years.
