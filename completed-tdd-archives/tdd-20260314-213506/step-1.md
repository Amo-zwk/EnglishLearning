# Step 1 - Understand Intent

## Functional Requirements

### FR-1: Support multiple input blocks with explicit generation
The workspace must render multiple input blocks on one page and keep generation idle until the user explicitly clicks the generate action.

### FR-2: Render grouped review cards with full AI responses
After generation, the workspace must render one grouped result card per input word, preserve the original word label, and show the full AI response inside the matching group.

### FR-3: Render editable extracted phrase review areas
Each grouped result card must include a dedicated extracted review area that contains only the extracted copy-format phrase pairs, supports a dynamic number of editable phrase boxes, and sizes phrase inputs so normal phrase lengths are readable without truncation.

### FR-4: Expose deck selection before submission
The workspace must render deck selection before submission and pass the selected deck value unchanged to the Anki submission gateway.

## Assumptions

- The personal web interface can be implemented as a server-rendered HTML workspace plus stateful Python controller methods, without requiring a browser framework.
- Inline editing can be represented by editable textarea controls bound to in-memory workspace state before submission.
- The generate action should ignore blank input blocks instead of sending empty words to the orchestrator.
