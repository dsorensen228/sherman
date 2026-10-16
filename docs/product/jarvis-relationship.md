# Jarvis and Sherman Relationship

## Authority

Jarvis is Sherman’s orchestrator and conversational partner. Sherman owns immediate local safety and honest local state. Jarvis can request goals and presentation; it cannot directly command motors, forge observations, suppress critical status, or raise safety limits.

## Interaction contract

Jarvis sends versioned, authenticated, expiring requests. Sherman validates capability and current context, then replies `accepted`, `deferred` or `rejected` with reason. Accepted work has an action ID, progress and exactly one terminal semantic outcome. Results include confidence, observation age and limitations.

## Voice/personality split

Sherman communicates primarily through eyes/motion and structured events. Jarvis may translate these into witty dialogue, but factual assertions come from Sherman’s evidence. Humor is never substituted for a low battery, lost localization, failed search or privacy/fault state.

## Stationary idle voice

The user-requested speaker conceit is implemented under ADR 0006: Sherman speaks
in droid beeps that only Jarvis understands. The two openly dislike their owner
and conspire to deliver vicious insults, using Jarvis’s level-3 personality. The
performance has no affectionate softening; safety and factual device status remain
independent. Qwen generates fresh one/two-pair exchanges, then Sherman executes them
through his own speaker and a configured Jarvis response device. No dialogue catalog
is used. See `personality/banter/README.md`.

## Example patterns

- Jarvis: locate headphones. Sherman: accepts bounded search, shows focused expression, reports found/likely/not found/uncertain with areas checked.
- Jarvis: ignore the mug. Sherman may acknowledge and lower the mug-change task utility; safety mapping still treats it as an obstacle.
- Jarvis disconnects. Sherman continues safe local routine, bounds outbound spool, later reconciles rather than replaying old commands.
- Sherman stuck/lost/low energy. He stops or follows qualified recovery, then requests help with compact evidence.

## Memory and privacy

Jarvis content does not automatically become permanent Sherman memory. Persistent routines/preferences require explicit schema/policy. Raw imagery is not streamed by default; a diagnostic/observation attachment is scoped, authorized, visible, bounded and classified.

## Acceptance

Contract/fault tests prove cancellation, expiry, deduplication, reconnect, authorization and uncertainty. Experience review checks Jarvis does not speak beyond evidence or make Sherman seem unsafe/omniscient/manipulative.

