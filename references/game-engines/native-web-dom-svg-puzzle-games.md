# Native Web DOM and SVG Puzzle Games

Use this reference when a small browser game is implemented with native ES modules, DOM, CSS, and SVG instead of a game engine. It describes stable design choices; check current browser and platform support when relying on a specific API.

## Responsibility boundaries

- Keep game rules and state transitions in framework-independent modules where practical.
- Use DOM for menus, settings, text, forms, and accessibility semantics.
- Use SVG for crisp, scalable boards, pieces, paths, and simple effects; keep hit targets larger than the visible artwork.
- Separate input interpretation, rules, presentation, and persistence. Render from state instead of allowing SVG nodes to become the source of game truth.
- Prefer simple data structures for a puzzle. Add a scene graph, entity system, or general engine only when measured complexity justifies it.

## Runtime

- Turn-based puzzles usually need event-driven updates, not a permanent animation loop.
- For real-time interactions, use requestAnimationFrame for presentation and a bounded fixed-step accumulator only when deterministic simulation requires it. Pause or cap work when the page is hidden; avoid unbounded catch-up after backgrounding.
- Make state transitions deterministic and test rules without a browser. Keep randomness seeded when reproducible puzzles or replays are required.
- Define keyboard, pointer, touch, focus, undo/restart, and interrupted-session behavior. Do not make drag or color the only way to act or understand state.

## Responsive and accessible presentation

- Design mobile portrait first when it is the primary target, then verify wider layouts.
- Use scalable SVG viewBoxes and CSS layout; avoid fixed pixel coordinates for the whole page.
- Provide semantic controls and text alternatives for important game state. Maintain visible focus, sufficient contrast, and usable touch targets.
- Respect reduced-motion preferences and provide controls for effects that can cause discomfort.

## Assets and persistence

- Prefer original, licensed, or clearly permitted assets. Track source, license, attribution, and modification rights.
- Keep saves small and versioned. Handle storage being unavailable, malformed, or cleared, and provide a safe reset path.
- Avoid collecting personal data for local progress. If telemetry is added, define consent, purpose, retention, and identifiers before collection.

## Verification

- Test rules and edge cases as pure functions; use browser tests for input, rendering, responsive layout, keyboard access, and save/restore journeys.
- Check performance on representative mobile hardware and sustained sessions. Verify layout, focus, and touch behavior at actual viewport sizes.
- Treat platform store policies and browser API support as current facts to recheck at implementation time.
