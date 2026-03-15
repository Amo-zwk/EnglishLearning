# Step 1 - Understand Intent

## Functional Requirements

### FR-1: Submit reviewed phrase groups with visible outcome buckets
The composed workspace flow must keep word entry, phrase generation, phrase review, deck selection, and Anki submission on one page. It must allow phrase-pair selection, submit reviewed phrase groups through the Anki gateway, and display submitted, skipped, and failed outcomes in distinct per-group status buckets so duplicate skips are visible during feedback.

### FR-2: Preserve editable review state across partial submission failures
When one phrase group fails during submission, the workspace must preserve reviewed phrase edits and previously completed groups so the user can retry only the failed group without regenerating unaffected results.

## Assumptions

- The existing server-rendered Python workspace remains the correct UI surface for this task, so the composed flow is represented through controller state plus rendered HTML rather than a separate browser framework.
- "Selected phrase pairs" means each extracted phrase pair can be individually toggled for submission, with extracted pairs selected by default after generation.
- Duplicate visibility is satisfied by showing skipped counts and skipped phrase texts in submission feedback, even if duplicates are not precomputed before the user clicks submit.
