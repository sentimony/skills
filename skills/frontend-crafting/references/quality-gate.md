# Quality Gate

The technical floor beneath every workflow. Load this before building a new surface,
substantially modifying one, or writing review findings. A small local refinement uses the
compact pre-flight in `polish.md` instead.

These requirements restate widely established standards - WCAG 2.2, the WAI-ARIA Authoring
Practices, and documented platform behavior on MDN. They are written here in the skill's own
words so behavior does not depend on fetching anything at runtime; consult the primary sources
when a case is genuinely ambiguous.

## How to read the levels

| Level | Meaning | Review severity |
|---|---|---|
| MUST | Correctness or accessibility. Not subject to taste, and no brief overrides it. | P0 to P1 |
| SHOULD | Right in almost every case. A deviation needs a stated reason. | P1 to P2 |
| CONTEXTUAL | Applies only when the condition attached to it holds. | P1 to P2 when the condition holds |
| ANTI-PATTERN | A default failure to flag, not an automatic ban. Catalogued in `anti-patterns.md`. | P2 to P3 unless it also breaks a MUST |

Severity mapping is guidance for `review.md`. A MUST violation that makes the surface unusable
for someone is P0; one with a workaround is P1.

## MUST

### Semantics and structure

- Use `<button>` for actions and `<a href>` for navigation. A `div` with a click handler is never
  navigation: it is invisible to assistive technology, unreachable by keyboard, and it breaks
  opening in a new tab.
- Reach for the semantic element before reaching for an ARIA role. Native elements carry
  keyboard behavior, focus behavior, and platform conventions that a role attribute does not.
- Headings form a real hierarchy, in order, with no level skipped for visual sizing. Size is a
  styling decision; heading level is a structural one.
- Landmark structure exists: header, navigation, main, footer. One `<main>` per page.
- Lists are list elements, tables are table elements with real header cells, and a table is not
  used for layout.
- Every page has a unique, descriptive title, and the document language is declared.

### Accessible naming and status

- Icon-only controls carry an accessible name. An icon with no name is an unlabelled button.
- Images have `alt` text that conveys their purpose, or `alt=""` when they are decorative.
  Decorative images with descriptive alt text are noise for a screen reader user.
- Form controls have a programmatically associated label. Placeholder text is not a label: it
  disappears the moment the user types.
- Status that appears without a page change - validation results, save confirmations, async
  updates - is announced through a polite live region.
- Information is never carried by color alone. Add text, an icon, a pattern, or a shape.

### Contrast and text

- Body text meets a contrast ratio of at least 4.5:1 against its background; large text and
  interactive component boundaries meet at least 3:1.
- Text remains readable when the user zooms. Never disable browser zoom, and never set the
  viewport so that scaling is blocked. This is an accessibility requirement, not a preference.
- Text is real text. Text baked into an image cannot be resized, translated, selected, or read
  aloud.

### Keyboard and focus

Keyboard operability is the single most frequently broken MUST in generated interfaces. Check it
explicitly on every surface.

- Every interactive element is reachable and operable by keyboard alone: tab to it, activate it
  with Enter or Space as the element's convention requires.
- Focus order follows the visual order. Positive `tabindex` values reorder focus unpredictably and
  are not used.
- Focus is always visible. Removing the default outline without providing a clearly visible
  replacement is a defect. Prefer `:focus-visible` so pointer users are not shown rings they do
  not need.
- No keyboard trap. Focus that enters a component can leave it. Modals and drawers trap focus
  deliberately while open, return focus to the trigger on close, and close on Escape.
- A skip link lets a keyboard user jump past repeated navigation to the main content.
- A sticky header, footer, or toolbar never covers the element that just received focus. Reserve
  scroll padding so a focused element scrolls into a visible position: where the surface has a
  sticky element, check that `scroll-padding-block` accounts for its height.
- Custom components built from non-semantic elements implement the full keyboard contract for the
  pattern they imitate, including arrow-key behavior where the pattern defines it.
- Where a gesture such as swipe, drag, or pinch performs an action, an equivalent exists via
  keyboard and a single tap, unless the gesture is essential to the task.
- Hit targets are at least 24 by 24 CSS pixels, and around 44 by 44 for primary touch targets.
  Spacing counts toward the target when the element itself is small.

### Forms

- Inputs declare a correct `type` and, on touch devices, an `inputmode` that brings up the right
  keyboard.
- Inputs carry `autocomplete` and a meaningful `name` so browsers and password managers can fill
  them. Never break pasting, into any field, including one-time codes and password fields.
- Labels are clickable and, for checkboxes and radios, the label shares the control's hit target.
- The submit control is enabled before the request starts. Disabling it until every field
  validates hides the reason a user cannot proceed.
- Validation errors appear next to the field they belong to, in text, and focus moves to the
  first error on a failed submit.
- Submitting is idempotent from the user's side: a second click while a request is in flight does
  not create a second record.
- A form with unsaved changes warns before it is abandoned or destroyed by navigation.
- Font size in a text input is at least 16px on mobile. Smaller text triggers automatic zoom on
  iOS, which is the real reason people are tempted to disable zoom; fix the cause, not the symptom.

### Motion

- Respect `prefers-reduced-motion`. Under a reduced-motion preference, remove or substantially
  reduce non-essential movement, especially parallax, large translations, and autoplaying motion.
  Removing motion must not remove information or make anything unreachable.
- Animate `transform` and `opacity`. Animating layout properties such as width, height, top, or
  left forces layout work on every frame.
- Never use `transition: all`. It animates properties you did not intend, including ones added
  later.
- Anything that autoplays, moves, or scrolls for more than five seconds has a control to pause or
  stop it.
- Animations are interruptible. A user action during an animation takes effect immediately rather
  than queuing behind it.
- Nothing flashes more than three times per second.

### Interactive states

- Hover, active, and focus states are visibly distinct from the resting state and from each other.
  Hover-only affordance leaves touch and keyboard users without feedback.
- Disabled controls look disabled and explain, somewhere reachable, why they are disabled.
- Every surface that can load, be empty, or fail has a designed state for each. An empty state
  says what belongs here and how to get it; an error state says what happened and what to do next.
- Destructive actions require a confirmation or offer an undo. Undo is usually the better design:
  a confirmation dialog that appears every time is dismissed without reading.

### Layout stability and media

- Images, video, and embeds declare dimensions or an aspect ratio so nothing shifts when they
  load.
- Content that arrives late - banners, ads, async panels - has space reserved rather than pushing
  the page down under the user's pointer.
- Text overflow is handled deliberately: truncate, clamp, or wrap long words. Set `min-width: 0`
  on flex children that must be allowed to shrink, since the default minimum size prevents
  truncation from working.
- Any surface showing user-generated content survives both an extremely short and an extremely
  long value, and a missing one.
- Nothing overflows horizontally at common viewport widths.

## SHOULD

- Long lists are virtualized once their length makes rendering or scrolling perceptibly slow.
- Layout is not read and written in the same frame. Batch DOM reads, then writes, and avoid
  measuring inside a render path.
- Fonts are preloaded and use `font-display: swap` so text is readable before the webfont arrives.
  Limit the number of families and weights actually shipped.
- Origins needed early are hinted with `preconnect` or `dns-prefetch`.
- Use video for anything that would otherwise be a large animated GIF.
- Images are served in a modern format at appropriate sizes, with lazy loading below the fold and
  eager loading for the largest element in the first viewport.
- Safe-area insets are respected on devices with notches, rounded corners, or gesture bars, so
  content and fixed controls are not obscured.
- Dates, times, numbers, and currency are formatted through the platform's internationalization
  APIs rather than hand-built strings, so they follow the user's locale.
- Language preference is detected from the browser's stated languages, never inferred from IP
  geolocation. Where someone is has no bearing on what they read.
- Newer perceptual contrast models predict readability better than the WCAG 2 ratio in some
  cases, particularly for dark themes. Treat them as an additional check; the WCAG 2 ratio remains
  the requirement.
- Style hooks are named for what an element is rather than where it sits. A class named for a
  position stops being true the moment the element moves; a class named for its role survives.
- Interactive elements are not nested inside other interactive elements.

## CONTEXTUAL

### When the surface holds application state (Operate)

- The URL reflects the state a user would want to return to or share: filters, tab, page, sort,
  selected record. Reloading lands in the same place.
- Navigation between views uses real links so that middle-click, modifier-click, and browser
  history behave as expected.
- Back and forward move through the state a user perceives as navigation, not through every
  intermediate change.
- Optimistic updates reconcile with the server response and roll back visibly on failure.

### When the surface has more than one theme

- The browser is told which color schemes are supported so form controls, scrollbars, and the
  address bar match.
- Contrast requirements hold in every theme independently. A palette that passes in light and
  fails in dark passes nothing.
- No hardcoded color values bypass the theme layer. These are invisible until the other theme is
  selected.
- Theme choice persists and does not flash the wrong theme on load.

### When the interface is translated

- Layouts survive text expansion; many languages run considerably longer than English.
- Brand names that must not be machine-translated are marked as such.
- Right-to-left support uses logical properties for spacing and alignment rather than physical
  left and right.
- The document's `lang` describes its primary language, and any passage in another language has a
  matching `lang` on the nearest containing element so assistive technology uses the right
  pronunciation rules.
- A partially translated interface is treated as an explicit product state. Unplanned mixtures of
  interface languages under one `lang` value are a finding, even when every individual string is
  understandable.

### When the surface renders on the server

Example (React, Vue, Svelte with server-side rendering): output that differs between server and
client causes a hydration mismatch. Values that vary per render - current time, random values,
locale-formatted output, anything read from browser-only APIs - are computed after mount or made
deterministic. This applies only to server-rendered stacks; a static or purely client-rendered
surface has no such requirement.

## Content and copy

Copy is design material, and these are checkable rather than matters of taste:

- Labels name what the user is doing or controlling, not what the code calls it.
- The same action uses the same word everywhere in a flow. A control labelled Save on one screen
  and Update on the next reads as two different actions.
- Empty, loading, and error text says something useful. An error that says something went wrong
  tells the user nothing they had not already noticed.
- Content is real, or is honestly marked as placeholder. Lorem ipsum shipped to a review is a
  finding.
- Precise-looking figures are sourced or labelled as examples.
- Capitalization follows the product's existing convention. Where none exists, the choice is part
  of the design decision. The requirement is consistency across the whole interface, not a
  particular style.
- Punctuation, quotation marks, and number formatting follow the conventions of the product's
  language rather than a single locale's habits.

## Working with the stack

- Verify a dependency is present before importing it, and prefer what the project already uses.
  A new library for something the incumbent stack already does is a cost the surface does not need.
- When a well-known component exists as a maintained package the project already depends on, use
  it rather than reimplementing its accessibility behavior by hand.
