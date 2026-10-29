# Decision: pin Logo V2 as the ecosystem design anchor

**Date:** 2026-10-30  
**Status:** Accepted for migration staging; runtime adoption remains product-scoped.

## Intent

Give CORE, RENTAL, PISONET and CONTROLLERS one visual source of truth while preserving the owner's exact Logo V2 artwork and its provenance.

## Approaches considered

1. Reuse the reconstructed SVG set. Rejected because the source repository explicitly identifies it as approximate and not the approved master.
2. Copy the complete 7.8 MB editor package into this migration scaffold. Rejected because the immutable source repository already preserves it, and duplicating PSD/ORA/PDF files here adds drift without helping runtime integration.
3. Pin the exact owner board, package hashes and printed design tokens in a small contract. Selected because it keeps the authority verifiable, survives repository renames through commit/blob identities, and lets each product adopt the identity through a separately reviewed change.

## Decision

The immutable owner board at `BlazeDevStudio/BlazingSystems@8b08add6319df58a8c8cd1a41d1dcd6f4caab04c` is the visual authority. This repository records its blob identity, SHA-256, printed palette, Montserrat typography, motto and pillars. Product UIs use the tokens in `branding/Logo-V2/brand-tokens.css`; the logo itself must be sourced from the exact package or a later owner-approved master.

The previous reconstructed SVGs are not accepted as production masters. Product names remain outside the Blaze Systems mark. Safety and financial states keep their semantic colors.

## Scope and limits

This decision adds documentation and tokens only. It does not alter an app, installer, firmware image, icon resource, payment behavior, signing pipeline or release status. Each product integration must cite the consumed asset hash and include visual/accessibility evidence.
