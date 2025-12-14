## 2025-12-14 - Accessible Interactive Cards
**Learning:** Interactive cards (like agent selectors) implemented as clickable `div`s exclude keyboard users.
**Action:** Use `motion.button` (or `<button>`) with `type='button'` and explicit `text-left` styling to maintain layout while gaining free accessibility wins (keyboard focus, screen reader support).
