# Step 1 - Understand Intent

## Functional Requirements

### FR-1: Read deck names from AnkiConnect
The gateway must call the user's local AnkiConnect interface to fetch deck names and return them as a selectable list without altering deck-name text.

### FR-2: Require an explicit target deck before submission
The submission flow must reject note creation when no target deck is chosen so the caller cannot accidentally add notes to an implicit default deck.

### FR-3: Skip duplicate English fronts and report submission outcomes
The gateway must check existing Anki notes by the English Front value, create only non-duplicate Basic notes with Front mapped to English and Back mapped to Chinese, and report submitted, skipped, and failed counts separately.

## Assumptions

- The local AnkiConnect API uses version 6 and exposes `deckNames`, `findNotes`, and `addNotes` actions.
- Duplicate detection is based on exact Anki Front field text after the upstream extraction contract has already normalized surrounding whitespace.
- Failed counts are derived from `addNotes` results where AnkiConnect returns `None` for a note that was attempted but not added.
