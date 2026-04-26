# Requirements: Dual Filtering System (Main Screen)

This document specifies the logic and interaction for the new dual filtering system on the Main Screen. It replaces the previous single-cycle filtering approach.

## 1. Dual Filter Logic
The Main Screen must implement two independent filters that work simultaneously (using AND logic):

### Filter A: Favorites Toggle
- **States:** `All` (Show everything) vs. `Favorites Only` (Show only chains marked with a star).
- **Default:** `All`.
- **Interaction:** `CTRL+F` toggles this state.
- **Visuals:** Integrated into the combined filter widget.

### Filter B: Network Type Cycle
- **States:** `ALL` -> `TESTNET` -> `MAINNET` (Rotates in this order).
- **Default:** `ALL`.
- **Interaction:** `CTRL+T` cycles through these types.
- **Visuals:** Integrated into the combined filter widget.

## 2. Combined Behavior
The list of chains displayed is the intersection of both filters:
- If Filter A is `Favorites Only` and Filter B is `TESTNET`, only chains that are **both** favorites **and** testnets are shown.
- If no chains match the combined criteria, the list should display a "No results found" message.

## 3. UI/UX Requirements
- **Single Widget Visual:** Both filter states must be displayed in a single UI widget.
- **Format:** `Filter: [* ]TYPE`
    - `TYPE` is one of `ALL`, `TESTNET`, `MAINNET`.
    - `*` prefix is visible **only** when the Favorites filter is active.
- **Examples:**
    - `Filter: ALL` (Default)
    - `Filter: TESTNET` (Only type filter active)
    - `Filter: * ALL` (Only favorites filter active)
    - `Filter: * MAINNET` (Both filters active)
- **Persistence:** The filter state should be persisted during the session.

## 4. Interaction Summary
| Key | Action | Behavior |
|-----|--------|----------|
| `CTRL+F` | Toggle Favorites Filter | Toggles `*` prefix on/off |
| `CTRL+T` | Cycle Network Type | Cycles `ALL` -> `TESTNET` -> `MAINNET` |
