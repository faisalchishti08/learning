---
card: webdev
gi: 2
slug: frontend-vs-backend-vs-full-stack
title: Frontend vs backend vs full-stack
---

## 1. What it is

These three words describe **where code runs** and **what it's responsible for** in a web application.

- **Frontend** = everything that runs in the **user's browser** and that the user sees and touches: layout, colours, buttons, animations, form validation. Built mainly with **HTML, CSS, and JavaScript** (often a framework like React).
- **Backend** = everything that runs on the **server**, out of the user's sight: business rules, databases, authentication, payments. Built with languages like **Java, Python, Node.js, Go**, plus a database.
- **Full-stack** = a person (or codebase) that covers **both** ends — the "stack" being the whole vertical slice from browser down to database.

The frontend is the dining room; the backend is the kitchen and pantry; a full-stack developer can work in both.

## 2. Why & when

The split exists because the two halves have completely different constraints:

- The **frontend** must be fast to load, accessible, and work across devices and screen sizes. It runs on *the user's* machine, which you don't control, and it can be inspected — so it can never be trusted with secrets.
- The **backend** must be secure, correct, and scalable. It runs on *your* machine, so it guards the data and enforces the rules.

When you reach for each:

- Pure **frontend** work: a marketing site, a dashboard's UI, animations, accessibility.
- Pure **backend** work: an API, a payment processor, a scheduled job, database design.
- **Full-stack** is common at startups and on small teams where one person ships a feature end to end.

Rule of thumb: **anything secret or authoritative belongs on the backend.** Never check a password or trust a price in frontend JavaScript.

## 3. Core concept

A request flows **down the stack and back up**:

1. **Browser (frontend)** renders the UI and, when the user clicks something, sends a request.
2. **Server (backend)** receives it, runs logic, talks to the **database**, and builds a response (HTML or JSON).
3. The response travels back up to the **browser**, which updates what the user sees.

What lives where:

| Concern | Frontend | Backend |
|---|---|---|
| Look & feel (HTML/CSS) | ✅ | ❌ |
| Interactivity (clicks, animation) | ✅ | ❌ |
| Business rules / pricing | ❌ | ✅ |
| Database access | ❌ | ✅ |
| Authentication & secrets | ❌ | ✅ |
| Input validation | ✅ (for UX) | ✅ (for safety — required) |

Notice validation appears twice. The frontend validates for a **nice experience** (instant "email looks wrong"). The backend validates for **safety**, because a malicious user can bypass the frontend entirely. Frontend checks are a convenience; backend checks are the law.

## 4. Diagram

<svg viewBox="0 0 640 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Frontend in the browser talks to the backend server which talks to the database">
  <rect x="20" y="80" width="160" height="64" rx="10" fill="#1c2430" stroke="#6db33f"/>
  <text x="100" y="106" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="sans-serif">Frontend</text>
  <text x="100" y="126" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">HTML/CSS/JS · browser</text>
  <rect x="250" y="80" width="160" height="64" rx="10" fill="#1c2430" stroke="#6db33f"/>
  <text x="330" y="106" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="sans-serif">Backend</text>
  <text x="330" y="126" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">logic · server</text>
  <rect x="480" y="80" width="140" height="64" rx="10" fill="#1c2430" stroke="#6db33f"/>
  <text x="550" y="112" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="sans-serif">Database</text>
  <line x1="180" y1="112" x2="248" y2="112" stroke="#8b949e" stroke-width="2"/>
  <line x1="410" y1="112" x2="478" y2="112" stroke="#8b949e" stroke-width="2"/>
  <text x="214" y="104" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">HTTP</text>
  <text x="444" y="104" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">SQL</text>
  <text x="320" y="180" fill="#3fb950" font-size="12" text-anchor="middle" font-family="sans-serif">"full-stack" = comfortable across all three boxes</text>
</svg>

The user only ever touches the leftmost box; everything to the right is hidden.

## 5. Runnable example

One page that shows the boundary: the **frontend** (browser) calls a **backend** (Node server), which is the only place a "secret" calculation happens.

```js
// save as app.js — run with: node app.js  (built-in modules only)
const http = require("http");

http.createServer((req, res) => {
  if (req.url === "/") {
    // BACKEND serving the FRONTEND (HTML + JS)
    res.writeHead(200, { "Content-Type": "text/html" });
    res.end(`
      <h1>Price check</h1>
      <button onclick="check()">Get price</button>
      <p id="out"></p>
      <script>
        async function check() {
          const r = await fetch("/price");      // frontend asks backend
          const data = await r.json();
          document.getElementById("out").textContent = "Server says: $" + data.price;
        }
      </script>
    `);
  } else if (req.url === "/price") {
    // BACKEND logic — the real price lives here, never in the browser
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ price: 42 }));
  }
}).listen(3000, () => console.log("Open http://localhost:3000"));
```

**How to run:** `node app.js`, then open `http://localhost:3000` and click the button.

## 6. Walkthrough

- The single server does **two jobs**, chosen by `req.url`. This makes the frontend/backend boundary visible in one file.
- When you open `/`, the backend **serves the frontend**: an HTML page with a button and a small script. That HTML/JS now runs in *your browser* — it has become the frontend.
- Clicking the button runs `check()`, which calls `fetch("/price")`. This is the frontend **requesting data** from the backend — exactly the client–server exchange.
- The `/price` branch is **backend logic**. The number `42` lives on the server. The browser never knows it until it asks, and the browser can't change the server's mind.
- The response is **JSON** (`{ "price": 42 }`), which the frontend parses and shows. Notice the backend returned data, and the frontend decided how to display it — that division of labour is the whole point.

Swap `42` for a database lookup and you have a real app, with the same boundary.

## 7. Gotchas & takeaways

> **Never trust the frontend.** Anyone can open dev-tools, change the JavaScript, or call your API directly with `curl`. If a price, a permission, or a total *matters*, the backend must compute and check it. Frontend validation is for friendliness, not security.

> "Full-stack" doesn't mean "expert at everything." It means you can move across the whole stack to ship a feature, while usually being stronger on one side.

- Frontend = browser, user-facing, untrusted. Backend = server, hidden, authoritative.
- Secrets, money, and data integrity always live on the backend.
- They communicate over HTTP, usually exchanging JSON.
- Full-stack = comfortable end-to-end, browser through database.
