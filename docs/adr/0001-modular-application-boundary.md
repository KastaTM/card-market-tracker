# ADR-0001: Modular application boundary

## Context

P0 needs a working baseline while the product will later ingest different providers and retain a canonical domain. Distributed services or a full feature tree would add operational cost before any provider is validated.

## Decision

Use one installable Python application. P0 implements only CLI, configuration, and logging modules. Future source adapters must validate external input before normalized ingestion and domain use. Provider identifiers remain outside core domain identity. Add modules when a phase delivers real behavior.

## Alternatives

Microservices were rejected for P0 because there is no scaling or independent deployment need. A broad hierarchy of empty catalog/retail/discovery modules was rejected because it would falsely imply contracts and behavior. A single undifferentiated script was rejected because it would blur configuration and observability boundaries.

## Consequences

The baseline is small, installable, and reviewable. Later features require deliberate interfaces and may add dependencies when justified. Canonical identity, commercial schema, and scheduling remain undecided.

## Status

Accepted for P0 implementation; this does not close the phase.

## Revisit conditions

Revisit when a phase demonstrates a concrete need for a separate deployment unit or different dependency direction.
