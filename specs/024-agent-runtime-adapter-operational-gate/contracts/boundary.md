# Boundary Contract

- Core packages must not import `openai`, `agents`, `langchain`, `langgraph`, `crewai`, `autogen`, `semantic_kernel`, model SDKs, browser libraries, storage clients, queue clients, or `veracrawl.adapters`.
- CLI may use `importlib` dynamic loading but must not statically import concrete framework adapter modules or SDKs.
- Adapter-owned modules may implement deterministic contract adapters and future real SDK adapters.
- Framework-native state can be persisted only as diagnostic refs and never as canonical VeraCrawl state.
- Missing live SDK/runtime refs produce `needs_review`.
- Raw prompt, raw response, raw credential, or raw tool-secret serialization fails.
