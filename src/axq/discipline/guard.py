"""Pure deterministic Discipline Guard downstream of Master evidence fusion."""

from __future__ import annotations

from datetime import datetime, timedelta

from axq.discipline.contracts import (
    DisciplineContext,
    DisciplineCounters,
    DisciplineOutcome,
    DisciplinePolicy,
    DisciplineReason,
    DisciplineResult,
    DisciplineState,
    DuplicateStatus,
    EntryIntent,
    LossStreakReset,
    ReentryPolicy,
    ReentryStatus,
)
from axq.master import MasterProposal
from axq.schemas import Signal


def default_demo_discipline_policy() -> DisciplinePolicy:
    """Return intentionally permissive Demo defaults, not optimized trading truth."""
    return DisciplinePolicy(
        policy_version="demo-v1",
        max_trades_per_day=16,
        max_trades_per_session=10,
        max_simultaneous_positions=1,
        ordinary_cooldown_seconds=60,
        stop_loss_cooldown_seconds=300,
        post_rejection_cooldown_seconds=0,
        same_direction_reentry_cooldown_seconds=300,
        consecutive_loss_threshold=3,
        loss_streak_pause_seconds=900,
        loss_streak_reset=LossStreakReset.AFTER_NON_LOSS_EXIT,
        prevent_duplicate_setup=True,
        prevent_duplicate_thesis=True,
        prevent_same_direction_position=True,
        reentry_policy=ReentryPolicy.AFTER_EXIT_WITH_NEW_SETUP,
    )


def _outcome(
    proposal: MasterProposal,
    context: DisciplineContext,
    state: DisciplineState,
    policy: DisciplinePolicy,
    *,
    result: DisciplineResult,
    reason: DisciplineReason,
    rationale: str,
    next_eligible_at: datetime | None = None,
    duplicate_status: DuplicateStatus = DuplicateStatus.NONE,
    reentry_status: ReentryStatus | None = None,
) -> DisciplineOutcome:
    return DisciplineOutcome(
        master_proposal_id=proposal.proposal_id,
        evidence_bundle_id=proposal.bundle_id,
        discipline_policy_id=policy.policy_id,
        discipline_policy_version=policy.policy_version,
        discipline_state_id=state.state_id,
        discipline_context_id=context.context_id,
        setup_id=context.setup_id,
        thesis_id=context.thesis_id,
        scenario_id=context.scenario_id,
        as_of=proposal.as_of,
        available_at=max(proposal.as_of, context.available_at, state.available_at),
        master_decision=proposal.decision,
        result=result,
        eligible_for_risk=result is DisciplineResult.PASS,
        reason_codes=(reason,),
        counters=DisciplineCounters(
            trades_today=state.trades_today,
            trades_this_session=state.trades_this_session,
            consecutive_losses=state.consecutive_losses,
            active_positions=len(state.active_positions),
        ),
        next_eligible_at=next_eligible_at,
        duplicate_status=duplicate_status,
        reentry_status=(
            reentry_status
            if reentry_status is not None
            else ReentryStatus.ALLOWED
            if context.entry_intent is EntryIntent.REENTRY
            and result is DisciplineResult.PASS
            else ReentryStatus.NOT_REENTRY
        ),
        rationale=rationale,
    )


def _cooldown_end(value: datetime | None, seconds: int) -> datetime | None:
    return value + timedelta(seconds=seconds) if value is not None and seconds else None


def evaluate_discipline(
    proposal: MasterProposal,
    context: DisciplineContext,
    state: DisciplineState,
    policy: DisciplinePolicy,
) -> DisciplineOutcome:
    """Apply behavioral cadence rules without financial risk or execution authority."""
    if state.policy_id != policy.policy_id:
        raise ValueError("discipline state policy does not match evaluation policy")
    if context.as_of != proposal.as_of:
        raise ValueError("discipline context as_of must match Master proposal")
    if (
        context.available_at > proposal.as_of
        or state.available_at > proposal.as_of
        or state.as_of > proposal.as_of
    ):
        raise ValueError("discipline inputs are not causally available")

    if proposal.decision is Signal.HOLD:
        return _outcome(
            proposal,
            context,
            state,
            policy,
            result=DisciplineResult.NO_ACTION,
            reason=DisciplineReason.MASTER_HOLD,
            rationale="Master produced no actionable proposal.",
        )

    if state.trading_day != context.trading_day or state.session_id != context.session_id:
        return _outcome(
            proposal,
            context,
            state,
            policy,
            result=DisciplineResult.PAUSE,
            reason=DisciplineReason.STATE_SCOPE_MISMATCH,
            rationale="Discipline counters have not been rolled into the current day/session.",
        )

    if state.paused_until is not None and proposal.as_of < state.paused_until:
        return _outcome(
            proposal,
            context,
            state,
            policy,
            result=DisciplineResult.PAUSE,
            reason=DisciplineReason.POLICY_PAUSE,
            rationale=state.pause_reason or "A persisted behavioral pause is active.",
            next_eligible_at=state.paused_until,
        )

    if state.consecutive_losses >= policy.consecutive_loss_threshold:
        pause_anchor = state.last_stop_loss_at or state.last_exit_at or state.as_of
        pause_end = pause_anchor + timedelta(seconds=policy.loss_streak_pause_seconds)
        if proposal.as_of < pause_end:
            return _outcome(
                proposal,
                context,
                state,
                policy,
                result=DisciplineResult.PAUSE,
                reason=DisciplineReason.LOSS_STREAK_PAUSE,
                rationale="The configured consecutive-loss pause is active.",
                next_eligible_at=pause_end,
            )

    if context.setup_id is None or context.thesis_id is None:
        return _outcome(
            proposal,
            context,
            state,
            policy,
            result=DisciplineResult.REJECT,
            reason=DisciplineReason.MISSING_STABLE_IDENTITY,
            rationale="Actionable proposals require stable setup and thesis identity.",
        )

    if proposal.proposal_id in {
        state.last_accepted_master_proposal_id,
        state.last_rejected_master_proposal_id,
    }:
        return _outcome(
            proposal,
            context,
            state,
            policy,
            result=DisciplineResult.REJECT,
            reason=DisciplineReason.DUPLICATE_PROPOSAL,
            rationale="This exact Master proposal was already handled.",
            duplicate_status=DuplicateStatus.DUPLICATE_PROPOSAL,
        )

    if policy.prevent_duplicate_setup and context.setup_id in state.active_setup_ids:
        return _outcome(
            proposal,
            context,
            state,
            policy,
            result=DisciplineResult.REJECT,
            reason=DisciplineReason.ACTIVE_SETUP,
            rationale="The setup already has an active disciplined entry.",
            duplicate_status=DuplicateStatus.ACTIVE_SETUP,
        )
    if policy.prevent_duplicate_setup and context.setup_id in state.recently_executed_setup_ids:
        return _outcome(
            proposal,
            context,
            state,
            policy,
            result=DisciplineResult.REJECT,
            reason=DisciplineReason.DUPLICATE_SETUP,
            rationale="The stable setup identity was already executed.",
            duplicate_status=DuplicateStatus.DUPLICATE_SETUP,
        )

    if context.entry_intent is EntryIntent.REENTRY:
        if policy.reentry_policy is ReentryPolicy.DISABLED:
            return _outcome(
                proposal,
                context,
                state,
                policy,
                result=DisciplineResult.REJECT,
                reason=DisciplineReason.REENTRY_DISABLED,
                rationale="The active policy disables re-entry.",
                reentry_status=ReentryStatus.POLICY_BLOCKED,
            )
        if context.thesis_id not in state.recently_executed_thesis_ids:
            return _outcome(
                proposal,
                context,
                state,
                policy,
                result=DisciplineResult.REJECT,
                reason=DisciplineReason.REENTRY_NOT_PREVIOUSLY_EXECUTED,
                rationale="Re-entry must reference a previously executed thesis.",
                reentry_status=ReentryStatus.NOT_PREVIOUSLY_EXECUTED,
            )
        if context.thesis_id in state.active_thesis_ids:
            return _outcome(
                proposal,
                context,
                state,
                policy,
                result=DisciplineResult.REJECT,
                reason=DisciplineReason.ACTIVE_THESIS,
                rationale="The thesis remains active and cannot be re-entered.",
                duplicate_status=DuplicateStatus.ACTIVE_THESIS,
                reentry_status=ReentryStatus.ACTIVE_THESIS,
            )
        if state.last_exit_at is None:
            return _outcome(
                proposal,
                context,
                state,
                policy,
                result=DisciplineResult.REJECT,
                reason=DisciplineReason.REENTRY_MISSING_EXIT,
                rationale="Re-entry requires a causally recorded prior exit.",
                reentry_status=ReentryStatus.MISSING_EXIT,
            )
        reentry_end = _cooldown_end(
            state.last_exit_at, policy.same_direction_reentry_cooldown_seconds
        )
        if (
            reentry_end is not None
            and state.last_entry_direction is proposal.decision
            and proposal.as_of < reentry_end
        ):
            return _outcome(
                proposal,
                context,
                state,
                policy,
                result=DisciplineResult.REJECT,
                reason=DisciplineReason.REENTRY_COOLDOWN,
                rationale="The same-direction re-entry cooldown is active.",
                next_eligible_at=reentry_end,
                reentry_status=ReentryStatus.COOLDOWN,
            )
    elif policy.prevent_duplicate_thesis and context.thesis_id in {
        *state.active_thesis_ids,
        *state.recently_executed_thesis_ids,
    }:
        active = context.thesis_id in state.active_thesis_ids
        return _outcome(
            proposal,
            context,
            state,
            policy,
            result=DisciplineResult.REJECT,
            reason=(
                DisciplineReason.ACTIVE_THESIS
                if active
                else DisciplineReason.DUPLICATE_THESIS
            ),
            rationale=(
                "The thesis already has an active disciplined entry."
                if active
                else "The stable thesis identity was already executed."
            ),
            duplicate_status=(
                DuplicateStatus.ACTIVE_THESIS if active else DuplicateStatus.DUPLICATE_THESIS
            ),
        )

    if len(state.active_positions) >= policy.max_simultaneous_positions:
        return _outcome(
            proposal,
            context,
            state,
            policy,
            result=DisciplineResult.REJECT,
            reason=DisciplineReason.MAX_SIMULTANEOUS_POSITIONS,
            rationale="The behavioral simultaneous-position cap is reached.",
        )
    if policy.prevent_same_direction_position and any(
        item.direction is proposal.decision for item in state.active_positions
    ):
        return _outcome(
            proposal,
            context,
            state,
            policy,
            result=DisciplineResult.REJECT,
            reason=DisciplineReason.SAME_DIRECTION_POSITION_ACTIVE,
            rationale="A position in the proposed direction is already active.",
        )

    if state.trades_today >= policy.max_trades_per_day:
        return _outcome(
            proposal,
            context,
            state,
            policy,
            result=DisciplineResult.REJECT,
            reason=DisciplineReason.DAILY_TRADE_CAP,
            rationale="The configured daily behavioral trade cap is reached.",
        )
    if state.trades_this_session >= policy.max_trades_per_session:
        return _outcome(
            proposal,
            context,
            state,
            policy,
            result=DisciplineResult.REJECT,
            reason=DisciplineReason.SESSION_TRADE_CAP,
            rationale="The configured session behavioral trade cap is reached.",
        )

    cooldowns = (
        (
            state.last_stop_loss_at,
            policy.stop_loss_cooldown_seconds,
            DisciplineReason.STOP_LOSS_COOLDOWN,
            "The post-stop-loss cooldown is active.",
        ),
        (
            state.last_entry_at,
            policy.ordinary_cooldown_seconds,
            DisciplineReason.ORDINARY_COOLDOWN,
            "The ordinary post-entry cooldown is active.",
        ),
        (
            state.last_rejection_at,
            policy.post_rejection_cooldown_seconds,
            DisciplineReason.POST_REJECTION_COOLDOWN,
            "The optional post-rejection cooldown is active.",
        ),
    )
    for timestamp, seconds, reason, rationale in cooldowns:
        cooldown_end = _cooldown_end(timestamp, seconds)
        if cooldown_end is not None and proposal.as_of < cooldown_end:
            return _outcome(
                proposal,
                context,
                state,
                policy,
                result=DisciplineResult.REJECT,
                reason=reason,
                rationale=rationale,
                next_eligible_at=cooldown_end,
            )

    return _outcome(
        proposal,
        context,
        state,
        policy,
        result=DisciplineResult.PASS,
        reason=DisciplineReason.PASSED,
        rationale="The proposal passed all configured behavioral discipline rules.",
    )
