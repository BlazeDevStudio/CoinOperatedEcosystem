# docs/release-gates

**Purpose:** Documented financial, hardware, independent QA and signing NO-GO checks.

**Engineering role:** PHX-RELEASE + QA. This folder is organizational only and does not transfer existing code or decision authority.

**Candidate provenance:** Existing Phoenix release/QA PRs; verify exact runs before promotion. Repository: `BlazingSystems/BlazingSystems-Experiments` unless another origin is specified. No exact source revision has been selected or imported yet.

**Migration state:** STRUCTURE_CREATED (2026-10-28). Future imports require an exact source commit SHA, PR dependency review, source integrity comparison and relevant native CI verification, recorded in `MIGRATION_MANIFEST.md`.

**Safety:** Do not bypass Phoenix financial/hardware NO-GO gates. No production deployment or release is authorized by directory creation.
