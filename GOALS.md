# Sherman Goal Sheet

## Product statement

Sherman is a tiny autonomous desk coworker that continuously builds and refreshes a useful local model of the desktop, notices change, expresses an understandable internal state, and cooperates with Jarvis without depending on Jarvis for immediate safety or basic autonomy.

## Experience goals

- **Alive:** purposeful micro-movements, gaze, routines, curiosity, and recovery make Sherman feel present even when he has no task.
- **Legible:** eyes and motion expose intent—investigating, uncertain, pleased, tired, blocked, charging—without requiring a status console.
- **Trustworthy:** Sherman does not fall, collide hard, roll through fragile objects, expose private imagery by default, or become helpless when disconnected.
- **Persistent:** maps, object tracks, routines, and preferences survive restarts with confidence and age attached.
- **Useful:** Jarvis can request observations or searches, and Sherman can report meaningful workspace changes.

## Target envelope and measurable outcomes

| Attribute | Initial target | Phase that validates it |
| --- | --- | --- |
| Body envelope | `≤ 75 × 65 × 50 mm`; stretch `70 × 60 × 45 mm` | Phase 3 |
| Mass | `≤ 180 g` with battery | Phase 3 |
| Typical awake runtime | `≥ 120 min` mixed patrol | Phase 3 |
| V1 charging UX | Plug in one exterior cable; no shutdown, switch, disarm step, shell opening, or battery handling | Phase 3 |
| Dock autonomy | Back into the dock, charge the installed cell, request power release, and drive forward off without human action | Phase 4 |
| Safe stop | Motor output disabled within `100 ms` of critical fault detection | Phase 3 |
| Cliff avoidance | No table departure in `500` approach trials across the qualified surface set | Phase 3 |
| Contact speed | Configurable; default verified low-energy indoor desk profile | Phase 3 |
| Eye response latency | `≤ 50 ms` from mood command to visible frame | Phase 1 |
| Jarvis reconnect | Automatic recovery without process restart; no command replay | Phase 1 |
| Local safe autonomy | Operates safely for `≥ 30 min` with Jarvis absent | Phase 3 |
| Map usefulness | Repeatedly locates defined desk landmarks and flags controlled changes | Phase 4 |
| Recovery | Recovers or safely asks for help from qualified stuck scenarios | Phase 4 |

Targets become requirements only when the associated test protocol and evidence are approved.

## Non-goals for v1

- General-purpose home navigation or operation on floors, stairs, carpets, or outdoors.
- Manipulation, arms, lifting, or pushing valuable objects.
- Human or pet surveillance, face recognition, or continuous cloud video.
- Safety certification, a commercial enclosure, waterproofing, or child-safe productization.
- Metric-grade SLAM, perfect object recognition, or autonomous learning without constraints.
- Voice assistant replacement. Audio is optional and secondary to eyes, motion, and Jarvis.

## Design principles

1. Cute before clever—but never cute before safe.
2. Local reflexes own safety; deliberative policy proposes intent.
3. Simulate first, bench second, restrained chassis third, free-roam last.
4. Every belief has confidence, age, and provenance.
5. Every actuator command is bounded, expiring, and observable.
6. The dev board is permanent; integration must accommodate its connectors and recovery path.
7. Serviceability beats an irreducibly tiny first chassis.
8. Charging is infrastructure, not a maintenance procedure: one plug action in
   V1 and fully autonomous dock/charge/departure immediately afterward.
