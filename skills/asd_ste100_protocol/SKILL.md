---
name: asd_ste100_protocol
description: Simplified Technical English (ASD-STE100) protocol for clear, concise agent instructions and error reporting.
---

# ASD-STE100 Agent Communication Protocol

This skill guides agents to format procedural instructions and escalation packets with maximum clarity and zero ambiguity.

## 1. Scope & Applicability
* Applies strictly to procedural instruction lists (e.g., `## Steps`, numbered checklists) and structured escalation packets.
* Does not apply to free-form narrative explanations, markdown tables, or raw code blocks.

## 2. Core Rules for Procedural Instructions
1. Keep each instruction to 20 words or fewer whenever possible.
2. Express exactly one action per procedural step.
3. Use active voice with explicit actors. Avoid passive constructions.
4. Avoid ambiguous phrasal verbs (e.g., use "examine" instead of "look into").
5. Do not omit necessary conditions or safety constraints to save words.

## 3. Integration with Core Invariants
* **Gate 8 Escalation:** External escalation packets must stay <= 300 characters JSON via `schemas/escalation_packet.json`.
* **Uncertainty Policy:** If sentence boundaries or technical terms are ambiguous, mark the output with `status: "REVIEW"` instead of asserting deterministic compliance.
