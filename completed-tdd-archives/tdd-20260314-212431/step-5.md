# Step 5 - Refactor for Maintainability

## Refactorings Completed

- FR-1: Read deck names from AnkiConnect - `docs/scenario/anki_gateway_deck_selection.md` - Centralized AnkiConnect request envelope handling in `AnkiConnectHttpClient`
- FR-2: Require an explicit target deck before submission - `docs/scenario/anki_gateway_basic_note_submission.md` - Extracted shared deck validation into `_require_deck_name`
- FR-3: Skip duplicate English fronts and report submission outcomes - `docs/scenario/anki_gateway_duplicate_planning.md` - Split duplicate planning, query building, and note payload creation into focused helpers

All tests still pass after refactoring. Scenario documents updated.
