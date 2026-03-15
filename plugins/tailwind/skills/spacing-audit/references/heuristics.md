# Detection Heuristics

Seven heuristics for identifying spacing inconsistencies in Tailwind CSS v4+ components.
Ordered from most impactful (catches the biggest visual bugs) to most granular.

All search commands use the generalized attribute pattern `(class|className)=` and scan
all common template file types. Adjust the glob list if your project uses additional
template extensions.

---

## H1: Container Fragmentation

**What to look for:** Adjacent `<div>` or semantic elements at the same DOM level that
each contain items belonging to the same visual group, but use separate spacing strategies.

**Structural signal:**

```tsx
<div className="flex gap-1">     {/* Container A */}
  <Item1 /><Item2 /><Item3 />
</div>
<div className="me-2 flex">      {/* Container B — different spacing */}
  <Item4 />
</div>
```

Items 1-4 look like one row, but the gap between Item3 and Item4 is governed by `me-1`
(margin-end on Container A) + the flex layout, not by `gap-1`. The visual result: the last
gap is wider than the others.

**Detection method:**
1. Identify the visual group (items that appear to be peers in the same row/column).
2. Walk up the DOM — are all peers children of the same flex/grid parent?
3. If not, the group is fragmented. Flag it.

**Tailwind classes that suggest fragmentation when found on adjacent containers:**
- `me-*`, `ms-*`, `mr-*`, `ml-*`, `mx-*` on a container that is a sibling of another
  flex container at the same level
- Different `gap-*` values on sibling containers in the same visual row

---

## H2: Margin/Gap Mixing

**What to look for:** A flex/grid parent has `gap-*` AND one or more children have
margin classes (`m-*`, `mx-*`, `my-*`, `me-*`, `ms-*`, `mt-*`, `mb-*`, `mr-*`, `ml-*`).

**Why it's a problem:** `gap-*` creates uniform spacing between all children. Adding margin
to specific children creates compound spacing (gap + margin) on one side, breaking uniformity.

**Detection — search patterns:**

Find flex/grid parents with gap:

```bash
rg -n '(class|className)="[^"]*flex[^"]*gap-' -g '*.{tsx,jsx,vue,svelte,astro,html}'
```

Then check their direct children for margin classes:

```bash
rg -n '(class|className)="[^"]*m[trblxyse]-' -g '*.{tsx,jsx,vue,svelte,astro,html}'
```

**Exception:** Margin on the *first* or *last* child for edge inset (e.g., `ms-2` on the
first item to offset from the container edge) is sometimes intentional. `gap-*` only
governs inter-item space, not edge space. But parent padding (`ps-2` on the flex parent)
is cleaner.

---

## H3: Padding Asymmetry Across Peer Interactive Elements

**What to look for:** Buttons, links, toggles, or dropdowns that are visual peers
(same row, same apparent role) but have different `px-*`, `py-*`, or `p-*` values.

**Why it matters:** Padding defines the "envelope" of an interactive element — the space
between its content and its clickable boundary. When peers have different padding, their
content appears unevenly spaced even if the gap between them is uniform, because the
visual weight shifts.

**Detection method:**
1. Identify all interactive elements (`<button>`, `<a>`, clickable `<div>`) in the same
   flex container.
2. Extract their padding classes.
3. Compare. Flag any mismatches.

**Common manifestation:**

```tsx
<a className="flex items-center h-12">              {/* no px */}
  <img className="h-6" />
</a>
<button className="px-2 ...">                       {/* px-2 */}
  <WrenchIcon />
</button>
<button className="px-2 gap-1.5 ...">               {/* px-2, but also internal gap */}
  <span>B</span><span>Babylon.js</span>
</button>
```

The link has no horizontal padding, so its content sits closer to the neighboring
items than the button's content does.

---

## H4: Fixed Width on Content-Adaptive Elements

**What to look for:** An element in a flex row has a fixed width class (`w-*`) while its
siblings size to content (no width class, or `w-auto`).

**Why it's a problem:** Fixed width creates rigid internal whitespace that doesn't adapt.
If the content is shorter than the fixed width, extra space pools on one side (depending on
justify-content and text-align). This makes the item look wider than its peers, even if the
gap between items is identical.

**Detection — search pattern:**

Find fixed-width classes on flex children (exclude `w-auto`, `w-fit`, `w-min`, `w-max`
which are content-adaptive):

```bash
rg -n '(class|className)="[^"]*\bw-[0-9]' -g '*.{tsx,jsx,vue,svelte,astro,html}'
```

**Special case:** `min-w-*` or `max-w-*` constrain rather than fix width, and are usually
fine. The flag is for `w-*` that sets a specific width.

---

## H5: Wrapper Nesting (Single-Child Alignment Wrappers)

**What to look for:** A `<div>` with flex alignment classes (`flex items-center`,
`flex justify-center`) that wraps exactly one child element.

**Why it matters:** Each wrapper introduces a new layout context. In a flex parent with
`gap-*`, the gap applies between the wrappers, not between the visible content. If some
items have wrappers and some don't, the effective visual spacing varies because wrappers
may have different intrinsic sizes than their content.

**Detection example:**

```tsx
{/* Wrapper adds a layout level */}
<div className="flex h-full items-center">
  <button>Only Child</button>
</div>

{/* vs direct child */}
<button className="flex items-center">Direct</button>
```

**When the wrapper is justified:**
- The wrapper adds padding/background/border not suitable on the child
- The wrapper groups multiple children (not a single-child wrapper)
- The child can't receive flex alignment classes (rare with modern elements)

If none of these apply, flatten: move the alignment classes onto the child.

---

## H6: Hit Target Inconsistency

**What to look for:** Interactive peer elements with different height classes.

**Why it matters:** Uneven hit targets cause alignment jitter (items shift vertically)
and feel inconsistent to click/tap. In a nav bar, all interactive elements should have
the same height even if their visual content height varies.

**Detection method:**
1. Collect height classes (`h-*`) from all interactive elements in the group.
2. Compare. Common bad pattern: one link is `h-6`, buttons are `h-8`, the bar is `h-12`.
3. The tallest element sets the "rail height." Others should match the rail or the
   intended interactive height.

**Common fix:** Use the bar height (`h-12`) as the hit target for all items, and
`items-center` to vertically center the visual content within. The visual content height
(icon size, text line-height) can vary, but the clickable area should not.

---

## H7: space-x/space-y Mixed with gap

**What to look for:** `space-x-*` or `space-y-*` on a container that also has `gap-*`.

**Why:** `space-x-*` applies `margin-left` to all children except the first. `gap-*`
applies spacing via the CSS `gap` property. When both are present, children get
gap + margin = doubled spacing. This is almost always a mistake from incremental migration.

**Detection — search patterns:**

Find containers with both gap and space utilities:

```bash
rg -n '(class|className)="[^"]*gap-[^"]*space-[xy]-' -g '*.{tsx,jsx,vue,svelte,astro,html}'
```

```bash
rg -n '(class|className)="[^"]*space-[xy]-[^"]*gap-' -g '*.{tsx,jsx,vue,svelte,astro,html}'
```

**Fix:** Remove `space-*` and keep `gap-*`. They do the same job; `gap` is the modern
approach and doesn't have the first/last-child edge cases.

---

## Search Shortcuts

Quick commands to scan a codebase for potential issues. All examples use `rg` (ripgrep)
syntax.

Find flex containers with gap and children with margins:

```bash
rg -n '(class|className)="[^"]*flex[^"]*gap-' -g '*.{tsx,jsx,vue,svelte,astro,html}' | head -20
```

Find fixed widths on elements that might be flex children:

```bash
rg -n '(class|className)="[^"]*\bw-[0-9]' -g '*.{tsx,jsx,vue,svelte,astro,html}' | head -20
```

Find space-x/y alongside gap:

```bash
rg -n '(class|className)="[^"]*gap-[^"]*space-' -g '*.{tsx,jsx,vue,svelte,astro,html}'
```

```bash
rg -n '(class|className)="[^"]*space-[^"]*gap-' -g '*.{tsx,jsx,vue,svelte,astro,html}'
```

Find margin classes on elements inside flex containers (needs manual review):

```bash
rg -n '(class|className)="[^"]*m[ersltbxy]-[0-9]' -g '*.{tsx,jsx,vue,svelte,astro,html}' | head -20
```

Find single-child flex wrappers (heuristic: div with flex + items-center):

```bash
rg -n '<div (class|className)="[^"]*flex[^"]*items-center[^"]*">' -g '*.{tsx,jsx,vue,svelte,astro,html}' | head -20
```

These are starting points. Each match needs manual review to determine if it's actually
a problem in context.
