# Phase 8 Task 8 Shared-Kernel Candidate Driver V1 Design

## Purpose

Evaluate one frozen configuration candidate through the existing Phase 6/7 deterministic system
replay and emit the same `CanonicalMetricSampleArtifact` consumed by Tasks 6 and 7. V1 supports
only a reviewed `MASTER_FUSION` override. It does not create a second strategy, tune parameters,
touch Final OOS, contact MT5, promote a proposal, deploy, or mutate the production runtime.

## Shared-kernel injection boundary

`SharedKernelPolicySet` is the sole composition input added to `run_system_replay`. It contains the
existing Fusion, Discipline, Risk, Execution, Position Management, Position Action, and Scenario
policies and has a content-addressed identity. `default_shared_kernel_policy_set()` builds exactly
the policies currently constructed inside system replay. Calling `run_system_replay` without a
policy set therefore retains the current Phase 7 byte-level behavior.

`FrozenSharedKernelCandidateConfig` binds an exact proposal, candidate, plan, baseline policy-set
identity, source identity, and one complete `FusionPolicy`. Its target is fixed to
`MASTER_FUSION`; no generic object path, callable, plugin, or scattered override is accepted. The
driver starts from the exact default set and replaces only `fusion_policy`. Every other shared
kernel component remains unchanged and executes through the existing orchestrator and replay
transport.

## Governed inputs and identity

`SharedKernelReplayDataManifest` describes one DEVELOPMENT or VALIDATION CSV bundle. It contains
strict UTC coverage, row count, and exact SHA-256 references for the four required files:
`xauusd_m5.csv`, `xauusd_m15.csv`, `xauusd_h1.csv`, and `xauusd_h4.csv`. Filesystem paths are
operational arguments and never semantic identity. Final OOS is rejected by every contract and has
no service parameter.

`SharedKernelCandidateRequest` binds the exact proposal/candidate/plan/config, engine kind/version,
evaluation run key, deterministic seed/environment, and sorted data-manifest references. Its
strict-UTC `requested_at` is audit metadata excluded from `request_id`.

`SharedKernelCandidateAudit` binds the request, authoritative records, configuration, input
manifests, per-scope replay metric digests, canonical output artifact references, engine/version,
seed/environment, and terminal status. Strict-UTC `started_at` and `completed_at` are excluded from
`audit_id`. Equivalent semantic inputs and bytes therefore reuse request, output, and audit IDs
across later retries.

## Execution and metric production

The service loads the authoritative proposal, candidate, and evaluation plan from existing stores,
requires the proposal to be `CANDIDATE`, and checks exact linkage. The candidate must be
`CONFIGURATION`, target `MASTER_FUSION`, name the frozen configuration as `config_identity`, and
carry its exact canonical artifact reference. The request seed/environment must equal the plan.

For each required DEVELOPMENT or VALIDATION scope, the service verifies the manifest against the
canonical CSV bytes, invokes the existing `run_system_replay` with the resolved policy set, and
reads its deterministic metrics and outcome artifacts. The V1 metric extractor is a closed map from
preregistered scoped keys to shared replay facts:

- `<scope>_master_actionable_rate`
- `<scope>_discipline_pass_rate`
- `<scope>_risk_pass_rate`
- `<scope>_execution_intent_count`
- `<scope>_completed_trade_count`
- `<scope>_realized_pnl_usd`
- `<scope>_max_drawdown_usd`

Each requested key becomes a one-value `MetricSampleSeries`. Unknown keys fail closed. The emitted
artifact contains exactly the non-Final-OOS metrics preregistered for that scope and passes directly
to Task 6 without translation.

## Persistence and recovery

Migration 012 adds append-only request, input-manifest, replay-result, canonical-output, and terminal
audit tables. UPDATE and DELETE are rejected. Re-appending identical content is idempotent;
conflicting content under an existing semantic ID fails. A completed request is loaded and its
digests revalidated without rerunning the shared kernel, even when operational timestamps differ.
An incomplete request is not considered successful and may execute only while authoritative
governance still permits it.

## CLI and controlled validation

The reflection CLI gains `run-shared-kernel-candidate`, `show-shared-kernel-candidate`, and
`shared-kernel-candidate-summary`. The first validation uses generated deterministic synthetic CSVs
only. Tests prove default replay byte parity, exact one-policy replacement, Final OOS rejection,
closed metric selection, Task 6 compatibility, idempotent reuse, and absence of MT5/broker or
production-runtime mutation paths. The seven baseline proposals are never executed.
