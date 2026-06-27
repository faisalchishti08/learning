---
card: webdev
gi: 3
slug: web-page-vs-web-site-vs-web-app
title: Web page vs web site vs web app
---

## 1. What it is

Three words people use loosely, but they describe a **ladder of increasing interactivity**:

- A **web page** is a *single* document delivered to the browser — one HTML file, like one page in a book.
- A **web site** is a *collection of related web pages* under one domain, linked together — the whole book. A blog, a company's marketing site, Wikipedia.
- A **web app** (web application) is a site that behaves like *software*: you don't just read it, you **do** things — log in, edit, drag, save. Gmail, Google Docs, Trello, Figma.

The line between "site" and "app" is fuzzy and about **degree of interactivity and state**, not a hard rule.

## 2. Why & when

Naming the difference matters because it changes **how you build and host** the thing:

- A **web page / static site** can be plain files on cheap static hosting (GitHub Pages, Netlify). Fast, secure, almost free.
- A **web app** usually needs a backend, a database, user accounts, and ongoing logic — more moving parts, more cost, more to secure.

When to aim for each:

- **Web page/site:** content that mostly *informs* — a landing page, documentation, a portfolio, a news article.
- **Web app:** when users need to *accomplish tasks* and the page must remember state, react instantly, and persist data — a dashboard, an editor, a booking system.

Choosing "site" when you only need a site saves enormous complexity. Don't build a single-page app to show three paragraphs of text.

## 3. Core concept

Think of it as three rungs:

1. **Web page** — one URL → one HTML document. Static content. You read it and maybe click a link to another page.
2. **Web site** — many pages, shared navigation, shared design, one domain. Still mostly "read" experiences; each click typically loads a new page from the server.
3. **Web app** — rich interaction *without* always reloading. JavaScript updates the screen in place, talks to APIs in the background, and keeps **state** (what you're editing, who you're logged in as). It feels like a desktop program that happens to run in a browser.

Two technical signals push something from "site" toward "app":

- **State**: does it remember and change things as you use it (a half-written email, a shopping cart)? Apps are stateful.
- **In-place updates**: does the screen change without a full page reload? Apps use JavaScript/AJAX to update fragments.

A useful mental test: *"Am I mostly reading, or mostly doing?"* Reading → site. Doing → app.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A ladder from single page to website to web app with rising interactivity">
  <rect x="30" y="140" width="160" height="48" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="110" y="162" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">Web page</text>
  <text x="110" y="178" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">1 document</text>
  <rect x="240" y="90" width="160" height="48" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="112" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">Web site</text>
  <text x="320" y="128" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">many linked pages</text>
  <rect x="450" y="40" width="160" height="48" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="530" y="62" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">Web app</text>
  <text x="530" y="78" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">stateful + interactive</text>
  <line x1="40" y1="195" x2="600" y2="195" stroke="#30363d" stroke-width="1"/>
  <text x="320" y="208" fill="#3fb950" font-size="11" text-anchor="middle" font-family="sans-serif">→ more interactivity, more state, more moving parts →</text>
</svg>

Each rung adds interactivity and state; the cost and complexity rise with it.

## 5. Runnable example

Watch a single **web page** become **app-like** by adding state and in-place updates — no reload, just JavaScript.

```html
<!doctype html>
<html lang="en">
  <body>
    <h1>Counter</h1>
    <!-- A plain page would just show text. The script below makes it an "app". -->
    <button id="btn">Clicked 0 times</button>

    <script>
      let count = 0;                 // <-- STATE: the app remembers this
      const btn = document.getElementById("btn");
      btn.addEventListener("click", () => {
        count++;                      // change state
        btn.textContent = "Clicked " + count + " times"; // update screen in place
      });
    </script>
  </body>
</html>
```

**How to run:** save as `counter.html`, double-click to open in a browser, and click the button repeatedly.

## 6. Walkthrough

- Without the `<script>`, this file is a **web page**: static HTML you simply read. Add a few pages with links and it's a **web site**.
- `let count = 0` introduces **state** — a value the page remembers between clicks. State is the hallmark of an *app*.
- `addEventListener("click", ...)` makes the page **react** to the user instead of just displaying. The handler runs every click.
- `count++` changes the state, and `btn.textContent = ...` updates **only that element** — the page never reloads. This "change the screen in place" behaviour is what makes web apps feel like software.
- It's still one file, yet it already crossed from "page" toward "app" the moment it gained memory and interactivity. Scale this idea up (many components, a backend, saved data) and you get Gmail.

## 7. Gotchas & takeaways

> Don't over-engineer. If you're showing mostly text, a **static site** is faster, cheaper, safer, and easier to maintain than a JavaScript app. Reach for an "app" only when interactivity and state actually demand it.

> The boundaries are **conventions, not laws.** A "site" with one interactive widget is fine; nobody will arrest you for calling it the wrong word. The useful question is always "reading or doing?"

- Page = one document. Site = many linked pages. App = software-in-a-browser with state.
- The jump to "app" is driven by **state** + **in-place updates**, not by any single feature.
- Match the build to the need: static hosting for content, a full stack for true apps.
