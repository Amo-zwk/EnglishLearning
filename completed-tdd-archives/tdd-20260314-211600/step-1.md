# Step 1 - Understand Intent

## Functional Requirements

### FR-1: Orchestrate generation for multiple input words
Accept multiple submitted words from a single page action, send one generation request per word, and return one result group per input word in the original order.

### FR-2: Preserve review content and normalized copy-format pairs
Store the full AI response for each successful word so it remains reviewable, and expose the extracted copy-format phrase pairs using the shared extraction contract without manual reshaping.

### FR-3: Isolate per-word failures without blocking other results
If one generation request fails or returns malformed data, mark only that input word as failed with an actionable status message while leaving other successful groups available, including cases where a response has zero valid copy-format pairs.

## Assumptions

- The existing API is represented in code by an injectable per-word generation service, because no concrete remote client is present in the repository.
- A malformed generation group means the API layer returned a non-text payload for one word, which should be treated as a failure for that word.
- Successful responses that contain no valid copy-format pairs are not failures; they must remain reviewable with an empty submission list.
