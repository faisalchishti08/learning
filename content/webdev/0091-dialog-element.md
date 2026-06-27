---
card: webdev
gi: 91
slug: dialog-element
title: dialog element
---

## 1. What it is

`<dialog>` is a native HTML element for modal and non-modal dialogs — overlays, alerts, confirmation prompts, and lightboxes. It provides built-in:
- **Modal mode** (`showModal()`) — traps focus inside the dialog, adds a backdrop overlay, blocks interaction with the rest of the page.
- **Non-modal mode** (`show()`) — visible but doesn't block the page.
- **Accessibility** — ARIA role `dialog` and keyboard `Escape` to close are automatic in modal mode.
- **Backdrop** — a `::backdrop` pseudo-element for the dimmed overlay behind modal dialogs.

```html
<dialog id="confirm">
  <h2>Delete item?</h2>
  <p>This action cannot be undone.</p>
  <button id="cancel">Cancel</button>
  <button id="delete">Delete</button>
</dialog>

<button onclick="document.getElementById('confirm').showModal()">
  Delete
</button>
```

## 2. Why & when

Custom modals built from `<div>` required dozens of lines of JS to handle: focus trapping, backdrop, Escape key, scroll locking, ARIA roles, and return focus when closed. `<dialog>` provides all of this natively.

Use `<dialog>` for:
- Confirmation prompts ("Are you sure?")
- Alert messages
- Form dialogs (login, settings)
- Image/content lightboxes
- Any UI that temporarily takes over the user's attention

Don't use `<dialog>` for:
- Toast notifications (they're non-blocking; use ARIA live regions instead)
- Dropdown menus (use `<select>` or custom elements)
- Persistent sidepanels (use CSS layout, not `<dialog>`)

## 3. Core concept

Think of `<dialog>` like a **physical counter window at a government office**. When a modal dialog opens (`showModal()`), a window slides open (the dialog appears), a barrier drops between you and the rest of the building (the backdrop), and all office activity behind you is paused — you must deal with this window before going anywhere else. When you close it (`close()`), the window shuts, the barrier lifts, and you're back where you were.

**API:**

```js
const dialog = document.querySelector("dialog");

// Open as modal (focus trap + backdrop + Escape)
dialog.showModal();

// Open as non-modal (no focus trap, no backdrop)
dialog.show();

// Close (works in both modes)
dialog.close();

// Close with a return value (readable in the close event)
dialog.close("confirmed");

// Listen for close
dialog.addEventListener("close", () => {
  console.log("Return value:", dialog.returnValue); // "confirmed"
});
```

**The `<form method="dialog">`:**
A form inside a `<dialog>` with `method="dialog"` submits by closing the dialog. The submit button's value becomes `dialog.returnValue`.

```html
<dialog id="confirm">
  <form method="dialog">
    <p>Are you sure?</p>
    <button value="cancel">Cancel</button>
    <button value="ok">OK</button>
  </form>
</dialog>
```

**Styling:**

```css
/* The dialog box itself */
dialog {
  border: none;
  border-radius: 8px;
  padding: 2rem;
  max-width: 400px;
}

/* The dark overlay behind the modal */
dialog::backdrop {
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(2px);
}
```

**`open` attribute:** like `<details>`, `<dialog>` has a boolean `open` attribute that reflects visible state. Setting `dialog.open = true` is equivalent to `dialog.show()` (non-modal). For modal, always use `dialog.showModal()`.

## 4. Diagram

<svg viewBox="0 0 600 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Page with backdrop and dialog in the centre, showing focus trap inside the dialog and blocked content behind it">
  <!-- Page background -->
  <rect x="10" y="10" width="580" height="240" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="60" y="40" fill="#8b949e" font-size="11" font-family="sans-serif">Page content (blocked — pointer-events disabled while modal is open)</text>
  <rect x="20" y="50" width="200" height="30" rx="3" fill="#8b949e" opacity="0.2"/>
  <rect x="20" y="90" width="300" height="14" rx="2" fill="#8b949e" opacity="0.2"/>
  <rect x="20" y="112" width="250" height="14" rx="2" fill="#8b949e" opacity="0.2"/>
  <rect x="20" y="134" width="280" height="14" rx="2" fill="#8b949e" opacity="0.2"/>

  <!-- ::backdrop -->
  <rect x="10" y="10" width="580" height="240" rx="6" fill="rgba(0,0,0,0.55)"/>
  <text x="300" y="235" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">::backdrop pseudo-element</text>

  <!-- Dialog box -->
  <rect x="165" y="55" width="270" height="160" rx="8" fill="#f6f8fa" stroke="#6db33f" stroke-width="2"/>
  <text x="300" y="85" fill="#1a1a1a" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">Delete item?</text>
  <text x="300" y="108" fill="#444" font-size="10" text-anchor="middle" font-family="sans-serif">This action cannot be undone.</text>

  <!-- Buttons -->
  <rect x="175" y="155" width="95" height="30" rx="4" fill="#8b949e"/>
  <text x="222" y="175" fill="white" font-size="11" text-anchor="middle" font-family="sans-serif">Cancel</text>

  <rect x="285" y="155" width="95" height="30" rx="4" fill="#f85149"/>
  <text x="332" y="175" fill="white" font-size="11" text-anchor="middle" font-family="sans-serif">Delete</text>

  <!-- Focus trap indicator -->
  <rect x="160" y="48" width="280" height="175" rx="10" fill="none" stroke="#6db33f" stroke-width="1.5" stroke-dasharray="5,3"/>
  <text x="300" y="46" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">focus trapped inside</text>
</svg>

Modal dialog: backdrop blocks the page, focus is trapped inside, Escape closes it — all built in by the browser.

## 5. Runnable example

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>dialog element</title>
  <style>
    body { font-family: sans-serif; padding: 2rem; background: #1c2430; color: #e6edf3; }
    button { padding: 0.5rem 1.25rem; border-radius: 5px; border: none; cursor: pointer; font-size: 1rem; }
    .btn-primary  { background: #6db33f; color: white; }
    .btn-danger   { background: #f85149; color: white; }
    .btn-ghost    { background: transparent; color: #e6edf3; border: 1px solid #8b949e; }

    dialog {
      border: none;
      border-radius: 10px;
      padding: 2rem;
      max-width: 380px;
      width: 90%;
      box-shadow: 0 20px 60px rgba(0,0,0,0.5);
      background: white;
      color: #1a1a1a;
    }
    dialog h2 { margin: 0 0 0.5rem; }
    dialog p  { margin: 0 0 1.5rem; color: #555; }
    dialog .actions { display: flex; gap: 0.75rem; justify-content: flex-end; }

    dialog::backdrop {
      background: rgba(0, 0, 0, 0.6);
      backdrop-filter: blur(3px);
    }
  </style>
</head>
<body>
  <h1>Delete File</h1>
  <p>Select a file to manage:</p>
  <button class="btn-danger" id="open-modal">Delete report.pdf</button>

  <!-- The dialog -->
  <dialog id="confirm-dialog">
    <h2>Delete report.pdf?</h2>
    <p>This file will be permanently deleted and cannot be recovered.</p>
    <div class="actions">
      <button class="btn-ghost" id="btn-cancel">Cancel</button>
      <button class="btn-danger" id="btn-delete">Delete</button>
    </div>
  </dialog>

  <!-- Non-modal example -->
  <button class="btn-ghost" id="open-info" style="margin-top:1rem">Show info (non-modal)</button>
  <dialog id="info-dialog">
    <p>This is a non-modal dialog — the page behind is still usable.</p>
    <button class="btn-ghost" id="close-info">Close</button>
  </dialog>

  <p id="result" style="margin-top:1rem;color:#6db33f"></p>

  <script>
    const dialog = document.getElementById("confirm-dialog");
    const result = document.getElementById("result");

    document.getElementById("open-modal").addEventListener("click", () => {
      dialog.showModal();
    });

    document.getElementById("btn-cancel").addEventListener("click", () => {
      dialog.close("cancelled");
    });

    document.getElementById("btn-delete").addEventListener("click", () => {
      dialog.close("deleted");
    });

    dialog.addEventListener("close", () => {
      result.textContent = `Dialog closed with: "${dialog.returnValue}"`;
    });

    // Close on backdrop click
    dialog.addEventListener("click", (e) => {
      if (e.target === dialog) dialog.close("backdrop");
    });

    // Non-modal
    const infoDialog = document.getElementById("info-dialog");
    document.getElementById("open-info").addEventListener("click", () => infoDialog.show());
    document.getElementById("close-info").addEventListener("click", () => infoDialog.close());
  </script>
</body>
</html>
```

**How to run:** save as `dialog.html`, open in a browser. Click "Delete report.pdf" to open the modal. Press Escape or click Cancel or Delete to close it.

## 6. Walkthrough

- `dialog.showModal()` — opens the dialog in modal mode. The browser automatically: adds the `open` attribute, traps Tab focus inside the dialog, registers Escape to close, and activates the `::backdrop`.
- `dialog.close("deleted")` — closes and sets `dialog.returnValue = "deleted"`. The `close` event fires next.
- `dialog.addEventListener("close", ...)` — the handler reads `dialog.returnValue` to decide what happened. This pattern (open → user action → close with value → handle in event) is clean and avoids global state.
- Backdrop click detection: `e.target === dialog` is true when the click lands on the `<dialog>` element itself (the backdrop area), not on any of its children. This is a standard pattern for "click outside to close."
- `infoDialog.show()` — non-modal: the dialog appears but page interaction continues. No backdrop is shown, Escape key has no effect.

## 7. Gotchas & takeaways

> **`dialog.open = true` is not the same as `dialog.showModal()`.** Setting the attribute or property opens the dialog non-modally. Use `showModal()` explicitly when you need focus trapping and a backdrop.

> **Focus must land somewhere inside the dialog on open.** If the dialog has no interactive element, focus goes to the dialog element itself. Best practice: auto-focus the first interactive element with `autofocus` attribute: `<button autofocus>Cancel</button>`.

> **Scroll lock is not automatic.** `<dialog>` in modal mode traps focus but does not prevent scroll on the `<body>`. Add `body { overflow: hidden }` when the dialog opens if you want scroll to stop.

- `showModal()` = modal (focus trapped, backdrop, Escape closes); `show()` = non-modal.
- `dialog.close(returnValue)` sets `dialog.returnValue`; `close` event fires after.
- `<form method="dialog">` inside `<dialog>`: submit button's `value` becomes `returnValue`.
- Style the backdrop with `dialog::backdrop`.
- Backdrop click: check `e.target === dialog` to detect clicks outside the dialog content.
- Always put `autofocus` on the first or primary action button for focus management.
