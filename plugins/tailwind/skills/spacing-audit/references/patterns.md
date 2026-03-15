# Anti-Pattern Catalog

Examples use React/TSX (`className`). The same patterns apply to `class=` in Vue, Svelte,
Astro, and plain HTML.

Each pattern shows the problem structure, why it causes visual inconsistency, and the
refactored version. All examples use Tailwind CSS v4 syntax.

---

## Pattern 1: Container Fragmentation

The most common cause of "it looks uneven but I can't tell why." Items that belong to the
same visual group are split across sibling containers, each with its own spacing rules.

### Before

```tsx
{/* Group A: gap-1 governs internal spacing */}
<div className="me-1 flex gap-1">
  <a className="flex h-12 items-center" href="/social">
    <img className="h-6 w-auto" alt="Social" src="..." />
  </a>
  <button className="flex h-12 items-center px-2">
    <WrenchIcon className="h-5 w-5" />
  </button>
  <button className="flex h-8 items-center gap-1.5 rounded px-2">
    <span>B</span><span>Babylon.js</span>
  </button>
</div>

{/* Group B: completely separate spacing context */}
<div className="me-2 flex place-items-center">
  <button className="flex h-8 w-24 items-center gap-1.5 rounded px-2">
    <span>☀️</span><span>Theme</span>
  </button>
</div>
```

**Spacing between Babylon.js and Theme:** `me-1` (from Group A) + flex layout gap =
uncontrolled. **Spacing between Wrench and Babylon.js:** `gap-1` = 4px. These don't match.

### After

```tsx
{/* Single container, single gap */}
<div className="flex items-center gap-2">
  <a className="flex h-12 items-center px-2" href="/social">
    <img className="h-6 w-auto" alt="Social" src="..." />
  </a>
  <button className="flex h-12 items-center px-2">
    <WrenchIcon className="h-5 w-5" />
  </button>
  <button className="flex h-8 items-center gap-1.5 rounded px-2">
    <span>B</span><span>Babylon.js</span>
  </button>
  <button className="flex h-8 items-center gap-1.5 rounded px-2">
    <span>☀️</span><span>Theme</span>
  </button>
</div>
```

**What changed:**
- Merged two containers into one
- Removed `me-1` and `me-2` margin hacks
- Single `gap-2` governs all inter-item spacing
- Removed `w-24` from Theme (see Pattern 4)
- Added `px-2` to the social link for envelope consistency (see Pattern 3)

---

## Pattern 2: Margin/Gap Mixing

A flex parent uses `gap-*` for inter-child spacing, but individual children also carry
margin classes, creating compound spacing on specific edges.

### Before

```tsx
<nav className="flex items-center gap-3">
  <a className="px-2" href="/">Home</a>
  <a className="px-2" href="/about">About</a>
  <a className="px-2 me-4" href="/docs">Docs</a>    {/* me-4 + gap-3 = 28px right */}
  <button className="ms-2 px-3">Contact</button>     {/* ms-2 + gap-3 = 20px left */}
</nav>
```

The gap between Docs and Contact is `gap-3` (12px) + `me-4` (16px) + `ms-2` (8px) = 36px.
Every other gap is 12px. This is almost never intentional.

### After (uniform spacing)

```tsx
<nav className="flex items-center gap-3">
  <a className="px-2" href="/">Home</a>
  <a className="px-2" href="/about">About</a>
  <a className="px-2" href="/docs">Docs</a>
  <button className="px-3">Contact</button>
</nav>
```

### After (intentional section break)

If the Docs-Contact gap was meant to be a visual separator:

```tsx
<nav className="flex items-center gap-3">
  <a className="px-2" href="/">Home</a>
  <a className="px-2" href="/about">About</a>
  <a className="px-2" href="/docs">Docs</a>
  <div className="mx-1 h-5 w-px bg-slate-300" aria-hidden="true" />
  <button className="px-3">Contact</button>
</nav>
```

Use a visible divider element rather than invisible margin accumulation. It's honest about
the intent and doesn't rely on margin math.

---

## Pattern 3: Padding Asymmetry Across Peer Elements

Interactive elements in the same row have different horizontal padding, causing their
content to appear unevenly positioned even when the gap between containers is uniform.

### Before

```tsx
<div className="flex items-center gap-2">
  {/* No padding — content touches the element edge */}
  <a className="flex h-12 items-center" href="/profile">
    <img className="h-6" src="avatar.png" alt="" />
  </a>
  {/* px-2 — content has 8px breathing room */}
  <button className="flex h-12 items-center px-2">
    <SettingsIcon />
  </button>
  {/* px-4 — content has 16px breathing room */}
  <button className="flex h-12 items-center px-4">
    <span>Settings</span>
  </button>
</div>
```

Visual result: the avatar crowds toward the settings icon, but "Settings" text floats
with extra internal space. The gap between elements is identical, but the perceived gap
varies because of padding differences.

### After

```tsx
<div className="flex items-center gap-2">
  <a className="flex h-12 items-center px-2" href="/profile">
    <img className="h-6" src="avatar.png" alt="" />
  </a>
  <button className="flex h-12 items-center px-2">
    <SettingsIcon />
  </button>
  <button className="flex h-12 items-center px-2">
    <span>Settings</span>
  </button>
</div>
```

**Rule of thumb:** Icon-only elements and icon+text elements in the same group should share
the same `px-*`. If text-heavy elements genuinely need more padding, that's a signal they
might belong in a different visual group or need a different component treatment.

---

## Pattern 4: Fixed Width on Content-Adaptive Elements

One item in a flex row has a fixed width while its siblings size to content, creating
uneven internal whitespace.

### Before

```tsx
<div className="flex items-center gap-2">
  <button className="flex h-8 items-center gap-1.5 rounded px-2">
    <span>B</span><span>Babylon.js</span>
  </button>
  {/* w-24 = 96px fixed, but content only needs ~80px */}
  <button className="flex h-8 w-24 items-center gap-1.5 rounded px-2">
    <span>☀️</span><span>Theme</span>
  </button>
</div>
```

"Babylon.js" button: content-sized, padding is symmetric. "Theme" button: 96px fixed width
with ~80px content = ~16px excess, distributed by `justify-center` or pooled on the right.

### After

```tsx
<div className="flex items-center gap-2">
  <button className="flex h-8 items-center gap-1.5 rounded px-2">
    <span>B</span><span>Babylon.js</span>
  </button>
  <button className="flex h-8 items-center gap-1.5 rounded px-2">
    <span>☀️</span><span>Theme</span>
  </button>
</div>
```

Remove `w-24`, let content + padding determine width. Now both buttons have identical
envelope behavior and their internal whitespace is symmetric.

**When fixed width IS appropriate:**
- Buttons in a grid layout that must align vertically
- Inputs in a form where consistent field widths improve scanability
- Elements whose content length varies dramatically (e.g., a counter that goes from "1" to
  "999") and layout shift must be prevented

---

## Pattern 5: Wrapper Nesting

Unnecessary single-child `<div>` wrappers that exist solely for alignment, adding an
extra layout level that can distort spacing.

### Before

```tsx
<div className="flex items-center gap-2">
  {/* Wrapper does nothing the button can't do */}
  <div className="flex h-full items-center">
    <button className="flex h-8 items-center gap-1.5 rounded px-2">
      <span>B</span><span>Babylon.js</span>
    </button>
  </div>
  {/* Another unnecessary wrapper */}
  <div className="flex h-full items-center">
    <button className="flex h-8 items-center gap-1.5 rounded px-2">
      <span>☀️</span><span>Theme</span>
    </button>
  </div>
</div>
```

The `gap-2` acts between the *wrappers*, which have `h-full` (stretching to parent height).
The buttons inside are `h-8`. The clickable area is `h-8`, but the gap-consuming element is
`h-full` — this can cause subtle vertical alignment differences.

### After

```tsx
<div className="flex items-center gap-2">
  <button className="flex h-8 items-center gap-1.5 rounded px-2">
    <span>B</span><span>Babylon.js</span>
  </button>
  <button className="flex h-8 items-center gap-1.5 rounded px-2">
    <span>☀️</span><span>Theme</span>
  </button>
</div>
```

Buttons are direct children of the gap container. `items-center` on the parent handles
vertical centering. No wrappers needed.

---

## Pattern 6: Hit Target Inconsistency

Peer interactive elements with different height classes, creating uneven clickable areas
and potential vertical alignment jitter.

### Before

```tsx
<div className="flex items-center gap-2">
  <a className="flex h-6 items-center">           {/* h-6 = 24px */}
    <img className="h-6" src="icon.svg" alt="" />
  </a>
  <button className="flex h-12 items-center px-2"> {/* h-12 = 48px */}
    <WrenchIcon />
  </button>
  <button className="flex h-8 items-center px-2">  {/* h-8 = 32px */}
    <span>Menu</span>
  </button>
</div>
```

Three different hit target heights. The `h-6` link is especially problematic — hard to
click on mobile and misaligned with the nav bar's visual rail.

### After

```tsx
<div className="flex items-center gap-2">
  <a className="flex h-12 items-center px-2">       {/* matches bar height */}
    <img className="h-6" src="icon.svg" alt="" />   {/* visual size unchanged */}
  </a>
  <button className="flex h-12 items-center px-2">
    <WrenchIcon className="h-5 w-5" />
  </button>
  <button className="flex h-12 items-center px-2">
    <span>Menu</span>
  </button>
</div>
```

All items use `h-12` (the nav bar height) as their hit target. Visual content inside retains
its original size. The clickable area is uniform; the visual content is centered within it.

---

## Pattern 7: space-x/space-y + gap Collision

Both `space-x-*` and `gap-*` on the same container. They do the same job via different
CSS mechanisms, and they stack.

### Before

```tsx
<div className="flex gap-2 space-x-3">
  <span>Tag 1</span>
  <span>Tag 2</span>
  <span>Tag 3</span>
</div>
```

Effective spacing: `gap` (8px) + `margin-left` (12px) = 20px between items. First item has
no `space-x` margin but still has gap, so the spacing after the first item differs from
subsequent items.

### After

```tsx
<div className="flex gap-3">
  <span>Tag 1</span>
  <span>Tag 2</span>
  <span>Tag 3</span>
</div>
```

Pick one mechanism. `gap` is the modern standard and doesn't have first/last-child edge
cases.

---

## Quick Decision Tree

When diagnosing a spacing issue between items A and B:

```
Is A in a different container than B?
+-- Yes --> Pattern 1 (Container Fragmentation). Merge containers.
+-- No --> Does the parent have gap-*?
    +-- Yes --> Does A or B also have margin?
    |   +-- Yes --> Pattern 2 (Margin/Gap Mixing). Remove margin.
    |   +-- No --> Do A and B have different px-*?
    |       +-- Yes --> Pattern 3 (Padding Asymmetry). Standardize.
    |       +-- No --> Does A or B have a fixed w-*?
    |           +-- Yes --> Pattern 4 (Fixed Width). Remove w-*.
    |           +-- No --> Check for wrapper nesting (Pattern 5).
    |               +-- No --> Do A and B have different h-* classes?
    |                   +-- Yes --> Pattern 6 (Hit Target). Standardize heights.
    |                   +-- No --> Does the parent have both gap-* and space-*?
    |                       +-- Yes --> Pattern 7 (space + gap). Remove space-*.
    |                       +-- No --> Spacing may be correct. Verify visually.
    +-- No --> Is spacing done via margins?
        +-- Yes --> Add gap-* to parent, remove margins.
```
