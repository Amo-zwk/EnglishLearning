# Step 1 - Understand Intent

## Functional Requirements

### FR-1: Represent one extraction request
The contract must model one input word together with the AI response text that will be parsed for copy-format phrase pairs.

### FR-2: Return normalized phrase pairs
The extraction result must preserve the input word reference and return a dynamic list of phrase pairs where each item contains one English front value and one Chinese back value from copy-format segments only.

### FR-3: Ignore invalid or non-copy-format content
The parser must ignore explanation text, reject malformed copy-format segments, and return an empty phrase list when no valid copy-format pairs exist.

### FR-4: Provide a stable dedupe key
The dedupe key must be derived from the English front value exactly as stored for Anki submission, which means surrounding whitespace is normalized away before storage and dedupe.

## Assumptions

- A valid copy-format segment follows the prompt convention `(复制专用: $English front$ $Chinese back$)`.
- Surrounding whitespace around captured front and back values should be trimmed before they are stored in the normalized result.
- Empty strings after trimming are invalid and must not produce placeholder cards.
