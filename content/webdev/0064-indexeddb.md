---
card: webdev
gi: 64
slug: indexeddb
title: IndexedDB
---

## 1. What it is

**IndexedDB** is a browser-built-in, transactional, object-oriented database. Unlike `localStorage` (limited to string key-value pairs), IndexedDB can store:
- JavaScript objects (including `Blob`, `ArrayBuffer`, `File`)
- Large amounts of data (typically hundreds of MB, sometimes GBs)
- Structured records queryable by indexed fields

It's asynchronous — operations return events or Promises and never block the main thread. IndexedDB is the right tool when `localStorage` is too small or too flat.

## 2. Why & when

`localStorage` tops out at ~5 MB and stores only strings. For richer client-side persistence, IndexedDB offers:

| Need | Solution |
|------|---------|
| Offline caching of API responses | Store JSON objects in an object store |
| Storing large files client-side | Blob/ArrayBuffer storage |
| Query by field, not just key | Create indexes on object properties |
| Multiple writes that must all succeed or all fail | Transactions |
| Progressive Web App (PWA) offline data | IndexedDB + Service Worker |

Use IndexedDB when:
- Data exceeds a few MB.
- You need to query by more than one field.
- You're building offline-capable features.
- You need to store binary data (images, audio) without a server round-trip.

## 3. Core concept

Analogy: IndexedDB is like a small SQL database in your browser — but without SQL. Instead of tables, it has **object stores**. Instead of rows, it has **records** (plain JS objects). Instead of WHERE clauses, it has **indexes** and **cursors**.

Key concepts:

| Term | Meaning |
|------|---------|
| **Database** | Top-level container, has a name and version |
| **Object store** | Equivalent to a table; stores JS objects |
| **Record** | One object, identified by a key |
| **Index** | Secondary key path to query by other fields |
| **Transaction** | Groups reads/writes; all succeed or all roll back |
| **Cursor** | Iterator over a range of records |

Opening a database and upgrading the schema:
```js
const request = indexedDB.open("myDB", 1);
request.onupgradeneeded = (event) => {
  const db = event.target.result;
  const store = db.createObjectStore("notes", { keyPath: "id", autoIncrement: true });
  store.createIndex("by_date", "date", { unique: false });
};
```

All data operations happen inside a transaction:
```js
const tx = db.transaction("notes", "readwrite");
const store = tx.objectStore("notes");
store.add({ title: "Hello", date: "2026-01-01" });
```

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="IndexedDB structure: database contains object stores, each store has records and optional indexes">
  <defs>
    <marker id="arr64" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Database -->
  <rect x="10" y="70" width="120" height="80" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="70" y="105" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Database</text>
  <text x="70" y="122" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">"myDB" v1</text>

  <!-- Object store: notes -->
  <rect x="180" y="30" width="150" height="70" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="255" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Object Store</text>
  <text x="255" y="72" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">"notes" keyPath: id</text>
  <text x="255" y="88" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">index: by_date</text>

  <!-- Object store: users -->
  <rect x="180" y="120" width="150" height="60" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="255" y="145" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Object Store</text>
  <text x="255" y="162" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">"users" keyPath: email</text>

  <!-- Records -->
  <rect x="390" y="20" width="230" height="80" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="505" y="42" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Records in "notes"</text>
  <text x="505" y="58" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">{"id":1,"title":"Hello","date":"2026-01-01"}</text>
  <text x="505" y="74" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">{"id":2,"title":"World","date":"2026-01-02"}</text>
  <text x="505" y="90" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">query by date via index</text>

  <!-- Arrows -->
  <line x1="132" y1="100" x2="178" y2="65" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr64)"/>
  <line x1="132" y1="110" x2="178" y2="150" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr64)"/>
  <line x1="332" y1="55" x2="388" y2="55" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr64)"/>
</svg>

One database holds multiple object stores; each store holds records queryable via indexes.

## 5. Runnable example

```html
<!-- indexeddb-demo.html — open in any browser, no server needed -->
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>IndexedDB demo</title></head>
<body>
<h2>IndexedDB Notes</h2>
<input id="title" value="" title="Note title" style="margin-right:8px">
<button onclick="addNote()">Add note</button>
<button onclick="listNotes()">List notes</button>
<button onclick="clearNotes()">Clear all</button>
<pre id="out" style="background:#1c2430;color:#e6edf3;padding:1em;margin-top:1em;min-height:80px"></pre>

<script>
let db;
const DB_NAME = "notesDB", STORE = "notes", VERSION = 1;

function log(msg) { document.getElementById("out").textContent += msg + "\n"; }
function clearLog() { document.getElementById("out").textContent = ""; }

// Open (or create) the database
const req = indexedDB.open(DB_NAME, VERSION);
req.onupgradeneeded = e => {
  const store = e.target.result.createObjectStore(STORE, { keyPath: "id", autoIncrement: true });
  store.createIndex("by_date", "date", { unique: false });
};
req.onsuccess = e => { db = e.target.result; clearLog(); log("DB ready."); };
req.onerror = e => { log("DB error: " + e.target.error); };

function addNote() {
  const title = document.getElementById("title").value.trim();
  if (!title) return;
  const tx = db.transaction(STORE, "readwrite");
  tx.objectStore(STORE).add({ title, date: new Date().toISOString() });
  tx.oncomplete = () => { clearLog(); log(`Added: "${title}"`); listNotes(); };
  tx.onerror = e => log("Error: " + e.target.error);
}

function listNotes() {
  clearLog();
  const tx = db.transaction(STORE, "readonly");
  tx.objectStore(STORE).openCursor().onsuccess = e => {
    const cursor = e.target.result;
    if (!cursor) { log("---"); return; }
    log(`[${cursor.value.id}] ${cursor.value.title} (${cursor.value.date.slice(0,10)})`);
    cursor.continue();
  };
}

function clearNotes() {
  const tx = db.transaction(STORE, "readwrite");
  tx.objectStore(STORE).clear();
  tx.oncomplete = () => { clearLog(); log("All notes deleted."); };
}
</script>
</body>
</html>
```

**How to run:** save as `indexeddb-demo.html`, open in a browser. Add notes, refresh the page, list them again — they persist. Inspect in DevTools → Application → IndexedDB.

## 6. Walkthrough

- `indexedDB.open(DB_NAME, VERSION)` opens the database. If it doesn't exist, it's created. If `VERSION` is higher than the stored version, `onupgradeneeded` fires.
- `onupgradeneeded` runs only on version change — the right place to create or modify object stores and indexes. `autoIncrement: true` means the `id` field is an auto-incrementing integer primary key.
- `createIndex("by_date", "date", ...)` allows querying records by `date` field later (not shown here for brevity, but `store.index("by_date").getAll(...)` would use it).
- `db.transaction(STORE, "readwrite")` opens a transaction. All `objectStore` operations within one transaction are atomic — if one fails, none commit.
- `openCursor()` iterates all records. Each `cursor.continue()` fires `onsuccess` again with the next record; when the store is exhausted, `cursor` is `null`.
- Data persists across page reloads — visible in DevTools → Application → IndexedDB.

## 7. Gotchas & takeaways

> **IndexedDB is fully asynchronous** — all operations use callbacks or (with wrappers like `idb`) Promises. You cannot do synchronous reads like `localStorage.getItem`. Plan your data access around async flows.

> **Schema changes must increment the version number.** Changing the version triggers `onupgradeneeded`. Editing the schema without a version bump does nothing — the existing database is reused unchanged.

- IndexedDB is per-origin — `http://` and `https://` on the same host are different databases.
- Storage limits are generous (often GBs) but quota is shared with Cache Storage — browsers may evict data if the device is low on space.
- For a nicer API (Promises instead of events), use the `idb` library (tiny, ~3 KB) — the raw API is verbose.
- IndexedDB is unavailable in some private browsing modes (Firefox) or throws quota errors — handle `onerror` gracefully.
- Ideal pairing: IndexedDB for offline data + Cache Storage for offline assets + Service Worker for routing.
