# Requirements Checklist: Production Run Control API

- [x] Scope is production run control, not live acquisition.
- [x] Run start requires objective, plan, approval, budget, and policy snapshot refs.
- [x] Lifecycle transitions are typed and replayable.
- [x] Negative fixtures cover policy denial, missing approval, missing budget, invalid transition, and missing replay.
- [x] Downstream specs 040, 041, 044, 049, and 054 can depend on this control plane.
