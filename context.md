# Card Market Tracker — Project Context

## 1. Project identity

**Project name:** Card Market Tracker  
**Short name:** CMT  
**Initial domain:** Pokémon TCG  
**Initial region:** Europe, with Spain as the primary market  
**Primary currency:** EUR  
**Initial deployment target:** Raspberry Pi, ARM64, Docker, 24/7  

Card Market Tracker is a personal collectibles market-intelligence platform designed to discover, collect, normalize, store and analyze market data for trading cards and sealed collectible products.

The project will initially focus only on Pokémon TCG. The architecture must remain extensible so that other markets such as Yu-Gi-Oh!, One Piece, Magic: The Gathering, Riftbound, Lorcana, NBA or NFL cards can be incorporated later without redesigning the core system.

The project is not initially intended to automate purchases, sales or speculative trading. Its first objective is to build reliable data infrastructure, market monitoring and opportunity discovery.

---

# 2. Product vision

Card Market Tracker should progressively become a personal **Bloomberg-like terminal for collectibles**.

The system should answer questions such as:

- What is this card or sealed product worth?
- How has its price evolved?
- Is the current price unusually low or high?
- Has a product returned to stock?
- Has a retailer opened a preorder?
- Has a new product or expansion appeared?
- Is one shop selling materially below the reference market price?
- Which monitored products currently show the strongest opportunities?
- What new products exist that the user did not previously know about?
- Eventually, what is the estimated value and performance of the user's collection?

Core conceptual flow:

```text
DISCOVERY
   ↓
DATA COLLECTION
   ↓
NORMALIZATION
   ↓
HISTORICAL DATABASE
   ↓
ANALYTICS
   ↓
SIGNALS
   ↓
OPPORTUNITIES
   ↓
ALERTS
   ↓
DECISIONS
```

The repository and accumulated historical data should become increasingly valuable over time.

---

# 3. Product principles

## 3.1 Discovery + Watchlist

CMT must support two complementary modes.

### Watchlist

Tracks products that are already known to be interesting.

Examples:

- Pokémon 151 Booster Bundle
- Pokémon 151 Elite Trainer Box
- specific singles
- future target products

Possible watchlist rules:

- target price
- maximum acquisition price
- minimum discount
- restock alert
- price-drop alert
- priority

### Discovery

Finds opportunities the user does **not yet know exist**.

The system should detect:

- new Pokémon expansions
- new sealed products
- new retailer SKUs
- new listings
- new preorders
- new special collections
- new exclusive products
- products from newly announced editions
- first appearances of unknown products in monitored stores

Conceptually:

```text
WATCHLIST
= things we already know we care about

DISCOVERY
= things we do not yet know we care about
```

Discovery is a first-class capability, not a later optional feature.

---

# 4. Initial scope

## Game

Pokémon TCG only.

## Region

Europe, especially Spain.

## Currency

EUR.

## Product categories

### Singles

A canonical card model should eventually distinguish at least:

- game
- set
- card number
- name
- rarity
- language
- variant
- condition
- release date
- raw / graded

Graded-card valuation is not part of the first MVP.

### Sealed products

Initial product types may include:

- Booster Pack
- Booster Bundle
- Booster Box
- Elite Trainer Box
- Ultra Premium Collection
- Collection Box
- Tin
- Blister
- special collection
- promotional product
- retailer-exclusive or regional product

Sealed products are particularly important for discovery, launch and retail monitoring.

---

# 5. Initial out of scope

The following should not be considered MVP requirements unless explicitly moved into scope by the Orchestrator:

- other TCGs
- sports cards
- automated purchasing
- automated selling
- marketplace functionality
- native mobile application
- camera/card recognition
- PSA/BGS/CGC valuation system
- complex forecasting
- speculative ML models
- Kubernetes
- Kafka
- distributed infrastructure without demonstrated need
- premature microservices
- unnecessary cloud complexity

The project should favor the simplest architecture that preserves clean boundaries and future extensibility.

---

# 6. Core system capabilities

CMT should evolve around the following modules.

```text
Sources
   │
   ├── Catalog providers
   ├── Market-price providers
   ├── Retail stores
   ├── Marketplaces
   └── Release / discovery sources
   │
   ▼
Collectors / Adapters
   │
   ▼
Validation + Normalization
   │
   ▼
Canonical CMT Model
   │
   ▼
Persistence / Historical Data
   │
   ├── Market Analytics
   ├── Discovery
   ├── Watchlist
   └── Opportunity Engine
             │
             ▼
          Alerts
```

Major functional areas:

- catalog
- market
- retail
- discovery
- normalization
- historical prices
- watchlist
- opportunities
- alerts
- analytics
- portfolio, later
- infrastructure / observability

---

# 7. Canonical product model

External-source identifiers must never become the core domain identity.

Different providers may describe the same product differently:

```text
Pokemon 151 ETB
Pokémon Scarlet & Violet 151 Elite Trainer Box
SV 151 Elite Trainer Box
151 ETB
```

CMT must normalize these toward a canonical internal product.

Conceptually:

```text
External Product
      ↓
Validation
      ↓
Matching / Identification
      ↓
Canonical CMT Product
```

When a product cannot be matched:

```text
UNKNOWN EXTERNAL PRODUCT
      ↓
Discovery Pipeline
      ↓
Candidate New Product
      ↓
Review / classification / canonical creation
```

Canonical identifiers and matching strategy are architecture-critical decisions and should be documented with ADRs.

---

# 8. Historical-first strategy

CMT should save its own useful historical observations whenever feasible.

Examples:

```text
product_id
source
observed_at
price
currency
price_type
stock_status
```

The goal is not to depend indefinitely on external providers for historical data.

Once enough history exists, CMT may compute:

- current reference price
- 7-day average
- 30-day average
- 90-day average
- 1-day change
- 7-day change
- 30-day change
- historical high
- historical low
- volatility
- momentum
- supply changes
- anomalies

Historical data is one of the strategic assets of the project.

---

# 9. Retail monitoring

Retail monitoring should detect changes such as:

```text
OUT_OF_STOCK → AVAILABLE
```

```text
79.99 EUR → 59.99 EUR
```

and newly appearing products.

Each retail source should be implemented through an isolated adapter.

Retail observations may include:

- canonical or candidate product
- store
- source SKU
- listing URL
- price
- shipping where available
- stock state
- first_seen_at
- last_seen_at

The system must respect legal and technical restrictions of data sources. It must not be designed to bypass anti-bot protections or access controls.

---

# 10. Product discovery

The Discovery Engine is a core requirement.

It should detect:

- new sets
- new sealed products
- new retailer listings
- new SKUs
- preorders
- coming-soon products
- launches
- products previously unknown to CMT

Useful lifecycle states may include:

```text
ANNOUNCED
COMING_SOON
PREORDER
AVAILABLE
OUT_OF_STOCK
RELEASED
DISCONTINUED
UNKNOWN
```

Every discovered product should preserve first-seen information when possible:

```text
first_seen_at
first_seen_source
first_seen_store
first_seen_price
```

Not every product will be classifiable automatically. Unknown products should enter a controlled review queue rather than being silently discarded or incorrectly normalized.

---

# 11. Opportunity Engine

CMT should eventually identify several signal types.

Initial examples:

- RESTOCK
- PRICE_DROP
- DISCOUNT
- WATCHLIST
- NEW_SET
- NEW_PRODUCT
- NEW_LISTING
- PREORDER
- LAUNCH
- MARKET_ANOMALY

A future opportunity score may combine signals such as:

- discount versus market reference
- effective acquisition cost
- historical position
- momentum
- volatility
- liquidity
- stock
- price confidence
- source count
- data freshness
- price versus MSRP
- number of retailers
- scarcity

The score is a prioritization tool, not financial advice.

Products with no historical data must still be eligible for discovery and launch signals.

---

# 12. Effective acquisition cost

Retail comparisons should not rely only on sticker price.

Initial model:

```text
Product Price
+ Shipping
= Effective Acquisition Cost
```

Potential future additions:

- marketplace fees
- taxes
- currency conversion
- other acquisition costs

---

# 13. Price confidence and data quality

A listed price is not automatically the true market value.

CMT should preserve enough source metadata to later compute a confidence level.

Potential factors:

- number of sources
- number of observations
- freshness
- dispersion
- liquidity
- source quality
- price type
- sold price versus active listing where available

External data must always be considered untrusted input.

Abnormal observations should be detectable.

Example:

```text
normal market range ≈ 80 EUR
new observation = 0.80 EUR
```

This should not automatically create a 99% discount opportunity.

Instead the observation may be flagged as:

```text
ANOMALOUS_INPUT
```

---

# 14. Alerts

Telegram is the initial active notification channel.

Potential alert types:

- NEW_SET
- NEW_PRODUCT
- NEW_PREORDER
- NEW_LISTING
- RESTOCK
- PRICE_DROP
- DISCOUNT
- MARKET_ANOMALY
- WATCHLIST

Alert deduplication is mandatory.

The system must not repeatedly notify the same unchanged state.

Market alerts and system-health alerts should be conceptually separated.

Example:

```text
MARKET ALERT:
151 Booster Bundle restocked at 32.99 EUR.

SYSTEM ALERT:
Store adapter has failed five consecutive checks.
```

---

# 15. Portfolio strategy

The project will not initially rebuild a complete collection-management application.

An external tool such as Collectr may be used during early phases if it sufficiently covers:

- collection tracking
- estimated collection value
- raw / sealed collection management
- watchlists
- portfolio view

CMT should initially prioritize its differentiating capabilities:

- data infrastructure
- discovery
- retail monitoring
- historical prices
- opportunity detection
- alerts

A native portfolio module may be built later if external tools become limiting.

Potential future portfolio fields:

- product_id
- quantity
- purchase price
- purchase date
- purchase source
- condition
- language
- notes

Potential metrics:

- cost basis
- estimated market value
- unrealized P/L
- realized P/L
- portfolio return
- allocation by set, era or product type

---

# 16. Long-term analytics

After enough reliable historical data exists, CMT may explore:

- anomaly detection
- momentum
- volatility
- liquidity estimation
- market regimes
- supply changes
- market indexes
- price forecasting
- opportunity ranking

Machine learning must follow reliable data, not precede it.

Mandatory order:

```text
Discovery
   ↓
Reliable Data
   ↓
Historical Data
   ↓
Analytics
   ↓
Signals
   ↓
Automation
   ↓
Machine Learning
```

---

# 17. Initial technical direction

Preferred initial stack:

- Python
- Pydantic
- SQLAlchemy
- SQLite initially
- FastAPI when a service/API becomes useful
- APScheduler or cron-style scheduling where appropriate
- Docker
- Docker Compose
- Telegram Bot API
- pytest
- Ruff
- mypy
- GitHub Actions

SQLite is preferred for the MVP unless real requirements justify PostgreSQL.

Technology choices must not be treated as immutable. Significant changes require an ADR.

---

# 18. Production target

The initial production target is:

```text
Raspberry Pi
ARM64
Docker
24/7
```

Relevant constraints:

- limited CPU
- limited RAM
- local storage
- home-network connectivity
- possible power interruptions
- long-running execution

Correctness, observability and maintainability matter more than premature optimization.

CI must validate ARM64 compatibility from early stages.

---

# 19. Proposed repository structure

The exact layout may evolve through ADRs, but the initial conceptual structure is:

```text
card-market-tracker/

├── AGENTS.md
├── README.md
├── pyproject.toml
├── docker-compose.yml
├── .env.example
│
├── src/
│   └── card_market_tracker/
│       ├── catalog/
│       ├── discovery/
│       ├── market/
│       ├── retail/
│       ├── normalization/
│       ├── opportunities/
│       ├── watchlist/
│       ├── alerts/
│       ├── analytics/
│       ├── portfolio/
│       ├── infrastructure/
│       └── cli/
│
├── tests/
│   └── fixtures/
│
├── docs/
│   ├── PROJECT_CHARTER.md
│   ├── ENGINEERING_OPERATING_MODEL.md
│   ├── ARCHITECTURE.md
│   ├── ROADMAP.md
│   ├── QUALITY_GATES.md
│   ├── CODING_STANDARDS.md
│   ├── TESTING_STRATEGY.md
│   ├── TECHNICAL_DEBT.md
│   ├── adr/
│   ├── data-contracts/
│   ├── architecture/
│   ├── threat-model/
│   ├── runbooks/
│   └── phases/
│
└── scripts/
```

`AGENTS.md` should remain concise and act as a map to authoritative documentation rather than becoming a giant instruction file.

---

# 20. Engineering operating model

Development will use two coordinated layers.

## ChatGPT layer

```text
00 — ORCHESTRATOR
01 — PHASE 0
02 — PHASE 1
...
```

The Orchestrator:

- maintains project governance
- opens phases
- defines scope and acceptance criteria
- generates the prompt for each Phase Chat
- evaluates final phase reports
- accepts, rejects or requests rework
- updates the roadmap
- opens the next phase

A Phase Chat may declare itself ready for review, but it may never close its own phase.

Only the Orchestrator can declare:

```text
PHASE CLOSED
```

## Codex layer

A Codex Engineering Lead coordinates implementation and delegates work to specialized subagents where useful.

Potential roles:

- PO — Product Owner / Business Analyst
- ARQ — Software Architect
- DB-OWNER
- BE — Backend Engineer
- DATA — Data Engineer
- INTEGRATIONS
- DISCOVERY
- QA
- SEC
- SRE
- FE
- REVIEWER
- DOCS

Not every role runs on every task.

The Engineering Lead should use only the specialists justified by the task.

Independent review is preferred:

```text
Author ≠ QA ≠ Final Reviewer
```

Parallelism should be used only for work with clearly separated ownership or read-only analysis.

---

# 21. Mandatory model profile

Every prompt created by the Orchestrator to open a Phase Chat must explicitly include a **MODEL PROFILE**.

It must contain:

```text
Recommended ChatGPT model:
<exact model available in the UI>

Reasoning:
<Medium / High / etc.>

Why:
<brief justification>

Recommended Codex model:
<exact model currently available in Codex>

Reasoning:
<appropriate level>

Escalation:
<when a stronger model/reasoning level should be used>
```

The Orchestrator must select from models actually available to the user at that time and must not invent unavailable model names.

Model selection principle:

```text
use the highest capability where decisions are difficult
+
use the lightest reliable option for routine execution
```

Architecture, cross-phase decisions, acceptance reviews, difficult debugging and major refactors justify stronger reasoning.

Mechanical tasks should not automatically use the most expensive configuration.

---

# 22. Phase contract

Every phase must begin with:

- phase ID
- phase name
- objective
- in scope
- out of scope
- dependencies
- architectural constraints
- acceptance criteria
- required tests
- observability expectations
- security considerations
- mandatory quality gates
- deliverables
- model profile

A phase must not expand its own scope without explicit Orchestrator approval.

---

# 23. Definition of Ready

A phase is Ready only when the following are clear:

- objective
- scope
- out-of-scope
- dependencies
- architecture constraints
- acceptance criteria
- testing expectations
- deliverables
- observability requirements
- security implications
- recommended ChatGPT model
- recommended Codex model

---

# 24. Definition of Done

A phase is not complete simply because the code runs.

All applicable gates must pass.

Potential gates include:

- functional acceptance
- formatting
- Ruff
- mypy
- unit tests
- integration tests
- contract tests
- regression tests
- coverage
- security review
- architecture review
- database review
- documentation
- Docker build
- AMD64 validation when relevant
- ARM64 validation
- CI green

A gate should report PASS or FAIL, not vague partial success.

---

# 25. Mandatory ADRs

Architecture Decision Records are mandatory for significant decisions.

Location:

```text
docs/adr/
```

Examples:

- SQLite for MVP
- provider adapter architecture
- canonical product identity
- price snapshot strategy
- scheduler strategy
- migration to PostgreSQL
- frontend framework
- deployment changes

Recommended ADR fields:

- Title
- Status
- Date
- Context
- Decision
- Alternatives considered
- Consequences
- Revisit conditions

Avoid ADRs for trivial choices.

---

# 26. Mandatory data contracts

Important data boundaries must be formalized.

Especially:

```text
External Source
      ↓
Normalized Ingestion Model
      ↓
Domain Model
```

Location:

```text
docs/data-contracts/
```

Contracts should be versioned when compatibility matters.

No external response shape should be implicitly treated as the domain model.

---

# 27. Mandatory contract testing

External integrations must have contract tests where practical.

Applies especially to:

- APIs
- retailers
- catalog providers
- market-data providers
- Telegram or similar external interfaces

Tests should detect changes such as:

- field disappearance
- type changes
- unexpected nulls
- pagination changes
- currency changes
- selector changes
- stock-semantics changes
- incompatible HTML changes

A broken adapter must not silently generate corrupted data.

---

# 28. Reproducible fixtures

External integrations should have small, versioned, deterministic fixtures.

Location:

```text
tests/fixtures/
```

Fixtures should cover:

- normal cases
- missing fields
- malformed responses
- stock states
- pagination
- provider errors
- real regression cases where useful

When a real bug is caused by external input, preserve a minimal sanitized example as a regression fixture when practical.

---

# 29. Threat model

Security is part of the MVP.

Location:

```text
docs/threat-model/THREAT_MODEL.md
```

Assets may include:

- API keys
- Telegram token
- database
- market history
- portfolio data
- Raspberry Pi
- exposed endpoints
- external responses

Threats should include:

- credential leakage
- malicious input
- dependency compromise
- unauthorized access
- API abuse
- denial of service
- resource exhaustion
- data poisoning
- database corruption
- network exposure

All external data should be treated as untrusted until validated.

---

# 30. Technical debt register

Significant deliberate technical debt must be recorded in:

```text
docs/TECHNICAL_DEBT.md
```

Each item should include:

- ID
- title
- date / phase introduced
- reason
- impact
- owner or affected module
- exit condition
- intended revisit horizon

A bare TODO is not an adequate substitute for significant debt.

---

# 31. Observability from the MVP

Observability is mandatory from early development.

Initial requirements should include:

- structured logging
- execution/run identifiers where useful
- explicit error categories
- source health
- basic operational metrics
- enough information to diagnose failed collectors and adapters

Possible metrics:

```text
collector_runs_total
collector_failures_total
provider_requests_total
provider_errors_total
products_processed_total
new_products_detected_total
price_snapshots_created_total
opportunities_detected_total
alerts_sent_total
adapter_duration_seconds
```

Potential provider health states:

```text
HEALTHY
DEGRADED
FAILED
DISABLED
```

A broken parser must not be silently interpreted as "zero products".

Later service phases may expose:

```text
/health
/readiness
```

---

# 32. ARM64 CI

ARM64 compatibility is mandatory because Raspberry Pi is the real target environment.

CI should progressively validate:

- dependency installation
- application build
- Docker image build
- startup
- smoke tests
- health checks

Target architectures may include:

```text
linux/amd64
linux/arm64
```

ARM64 incompatibilities should be found during development rather than at final deployment.

Dependency selection should consider ARM64 availability.

---

# 33. Failure-first engineering

Every relevant component should consider:

```text
What happens when this fails?
```

Examples:

- API unavailable
- rate limit
- invalid JSON
- retailer HTML changes
- Telegram unavailable
- database locked
- disk full
- network loss
- duplicate event
- absurd price
- process restart
- power loss

External failures must not silently corrupt internal state.

---

# 34. Git and CI principles

Preferred stable branch:

```text
main
```

Work should generally use short-lived branches such as:

```text
feature/*
fix/*
refactor/*
chore/*
```

Prefer pull requests even with one human developer because they provide:

- review boundary
- CI boundary
- diff
- history
- rollback point
- independent agent review

Use Conventional Commits where practical.

Examples:

```text
feat(discovery): detect unknown retail products
fix(market): reject invalid negative prices
test(retail): add contract fixture for stock state
docs(adr): define canonical product identity
```

Commits should be small, coherent, reviewable and reversible.

---

# 35. Quality objective

The project optimizes for:

- correctness
- maintainability
- testability
- traceability
- reproducibility
- security
- observability
- recoverability

Not for:

- maximum generated code
- unnecessary sophistication
- premature scale
- maximum number of agents
- maximum model cost

---

# 36. Initial MVP

The MVP should eventually provide:

```text
Pokémon Catalog
      ↓
Market Price Ingestion
      ↓
Historical Price Storage
      ↓
Discovery Engine
      ↓
Watchlist
      ↓
Retail Monitoring
      ↓
New Product / Preorder Detection
      ↓
Restock Detection
      ↓
Opportunity Detection
      ↓
Telegram Alerts
      ↓
Operational Observability
```

A native collection UI is not required for the initial MVP.

---

# 37. Initial roadmap

The roadmap may be adjusted by the Orchestrator, but the current baseline is:

## Phase 0 — Foundation

- repository
- development environment
- architecture skeleton
- Docker
- CI
- ARM64 CI
- configuration
- logging
- testing foundations
- documentation structure
- ADR process
- data-contract process
- threat-model baseline
- technical-debt register
- observability baseline
- AGENTS.md

## Phase 1 — Pokémon Catalog

- sets
- cards
- sealed products
- canonical identifiers
- catalog contracts

## Phase 2 — Market Data

- first market-data provider
- adapter interface
- validation
- normalization
- contract tests

## Phase 3 — Historical Prices

- snapshots
- persistence
- data quality
- historical queries

## Phase 4 — Discovery Engine

- new set discovery
- unknown product detection
- new sealed products
- first-seen tracking
- candidate-product workflow

## Phase 5 — Watchlist

- monitored products
- thresholds
- priority
- watch rules

## Phase 6 — Retail Monitoring

- initial 3–5 stores
- isolated adapters
- fixtures
- contract tests
- source health

## Phase 7 — Launch & Preorder Detection

- NEW_LISTING
- PREORDER
- COMING_SOON
- RELEASE

## Phase 8 — Alert Engine

- Telegram
- event formatting
- deduplication
- system alerts

## Phase 9 — Opportunity Engine

- rule-based opportunities
- effective acquisition cost
- initial confidence logic
- anomaly protection

## Phase 10 — Market Analytics

- averages
- changes
- volatility
- momentum
- historical metrics

## Phase 11 — Dashboard

- web interface
- market overview
- discovery
- opportunities
- charts

## Phase 12 — Portfolio

Only if building it adds enough value versus external tools such as Collectr.

## Phase 13 — Advanced Analytics

- anomaly detection
- liquidity
- market indices
- advanced opportunity scoring

## Phase 14 — Multi-TCG

Expand the domain without redesigning the core architecture.

---

# 38. Phase Completion Report

Every Phase Chat must end with a structured report for the Orchestrator.

Minimum structure:

```text
PHASE COMPLETION REPORT

Phase:
Proposed status:
Branch:
PR:
Commit:

MODEL PROFILE USED

ChatGPT:
Model:
Reasoning:

Codex:
Model:
Reasoning:

SPECIALISTS USED

OBJECTIVES

IMPLEMENTED

ARCHITECTURE CHANGES

ADRs

DATA CONTRACTS

DATABASE CHANGES

THREAT MODEL CHANGES

TECHNICAL DEBT

OBSERVABILITY

TESTS
- Unit
- Integration
- Contract
- Regression

QUALITY GATES
- Formatting
- Ruff
- mypy
- pytest
- coverage
- security
- Docker AMD64
- Docker ARM64
- CI

ACCEPTANCE CRITERIA

KNOWN LIMITATIONS

OPEN ISSUES

RECOMMENDATION

READY_FOR_ORCHESTRATOR_REVIEW
```

The Phase Chat must never declare `PHASE CLOSED`.

---

# 39. Orchestrator decisions

After reviewing the report and evidence, the Orchestrator may return only:

```text
ACCEPTED
REWORK_REQUIRED
BLOCKED
```

For rework, use explicit IDs:

```text
RW-01
RW-02
RW-03
```

Only after acceptance may the Orchestrator declare:

```text
PHASE CLOSED
```

and generate the next Phase Contract and prompt.

---

# 40. Final project rule

No phase is complete because an AI agent claims it is complete.

Completion requires:

```text
implementation
+
independent review
+
automated evidence
+
documented decisions
+
reproducible tests
+
quality gates
+
Orchestrator acceptance
```
