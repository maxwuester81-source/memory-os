# Gate contract

Status: PREPARED / NOT YET EXECUTED ON MAX HOST

## G0 Isolation
PASS when no canonical systems are writable from the harness.

## G1 LM Studio
PASS when /v1/models and /v1/chat/completions respond locally.

## G2 Multi-tool
PASS only when Qwen calls get_alpha, consumes its tool result, then calls multiply, consumes that result, and returns GATE_PASS=51.

## G3 Resume
Not implemented in the stateless harness. Must be tested through the selected persistent Paperclip adapter/bridge before residents exist.

## G4 Paperclip
After G2 PASS, connect the same deterministic task to Paperclip. The generic process adapter alone is not sufficient evidence for G3 because its documented runs do not preserve conversational session state.

## Stop conditions
Any malformed tool arguments, premature final answer, missing second tool call, context loss, or canonical write capability => FAIL CLOSED.
