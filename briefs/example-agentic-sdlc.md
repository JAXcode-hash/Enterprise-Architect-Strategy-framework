# AI agents in the CI/CD pipeline - agentic SDLC

## Drivers
- Reduce cycle time from commit to production by having agents perform the work that currently
  waits on a human: writing tests, triaging failures, drafting remediation for scanner findings,
  and preparing release notes.
- Improve consistency of security remediation, which today depends on which engineer picks up
  the finding.
- Establish the pattern before teams adopt agent tooling independently and unsupervised.

## Scope
Introduce AI agents into the existing CI/CD pipeline so that parts of the software development
lifecycle are performed by agents rather than by people. Agents will read repository content,
propose code changes, run pipeline stages, and in later phases merge low-risk changes without a
human reviewer. The pipeline builds and deploys the customer-facing services.

## Objects
- Agent orchestration service running inside the CI environment (new)
- Model gateway with prompt and response filtering (new)
- Source repositories and their CI runners (existing)
- Artefact registry and deployment pipeline (existing)
- Secrets store used by the pipeline (existing)
- Security scanners producing findings the agents will act on (existing)

## Integrations
- Agents to the source repositories, with commit and pull request rights
- Agents to the model gateway, and from there to two external model providers
- Agents to the CI runner control plane to trigger and read pipeline stages
- Agents to the artefact registry and the deployment pipeline
- Agents to the security scanners and the ticketing system
- Agents to internal documentation and design records used as grounding context

## Environments
- Prod - deployment pipeline that reaches production
- RTL - full pipeline against a production-like environment; agents will run here first
- Dev-Test - agents run against feature branches with no deployment rights

## Constraints
- The organisation is regulated under PRA and FCA, with DORA applying. Model risk governance
  under SS1/23 applies to any model influencing a material decision.
- The customer-facing services this pipeline deploys form an important business service.
- Two external model providers are involved and at least one is assessed as material.
- Agents will read internal design records and source code as grounding context; some of that
  content is Restricted.
- A hard commitment has been made to demonstrate the pattern by the end of the next financial
  year.
- Expected volume: 400 agent invocations per day at steady state, rising to 2,000.
