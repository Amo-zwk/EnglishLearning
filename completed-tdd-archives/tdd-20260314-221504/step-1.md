# Step 1 - Understand Intent

## Functional Requirements

### FR-1: Serve a browser-loadable HTML workspace entry route
The project must expose a local HTTP entrypoint that returns a complete HTML document for the review workspace. The document must contain the review workspace root, preserve multiple input blocks, and expose an explicit generate control so the user can load the page in a browser and start the workflow.

### FR-2: Build the web app around configurable generation and existing workspace orchestration
The web app factory must reuse the existing Python review workspace, generation orchestrator, and Anki gateway modules instead of duplicating their business logic. The generation connection must be configurable through a clear adapter seam so a caller can inject or configure the generation callable without mutating workspace logic.

### FR-3: Round-trip reviewed edits and submission through the HTTP layer
The HTTP layer must preserve generated result groups, show the full AI response and extracted review content, forward reviewed phrase edits and deck selection unchanged into the existing workspace controller, and support full generate-to-submit flow feedback on the same page.

## Assumptions

- A lightweight standard-library WSGI server is sufficient for the local entrypoint because the task only requires a runnable local browser experience.
- The HTML interface can remain server-rendered and form-based, which aligns with the existing Python-only architecture and avoids introducing a separate frontend stack.
- The generation adapter seam can default to a local demo adapter so the site is runnable without code edits, while still allowing a real local adapter to be selected with an environment variable.
