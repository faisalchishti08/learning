---
card: java
gi: 157
slug: startswith-endswith
title: startsWith() / endsWith()
---

## 1. What it is

`startsWith(String prefix)` returns `true` if a string begins with the exact given text; `endsWith(String suffix)` returns `true` if it ends with the exact given text. Both are case-sensitive, literal comparisons — no regular expressions involved — and both come from a family of overloads, including `startsWith(String prefix, int offset)`, which checks for the prefix starting at a given position rather than at index 0.

```java
String filename = "report_final.pdf";

System.out.println(filename.startsWith("report"));  // true
System.out.println(filename.endsWith(".pdf"));       // true
System.out.println(filename.startsWith("Report"));   // false — case-sensitive
System.out.println(filename.startsWith("final", 7)); // true — checks starting at index 7
```

`startsWith("final", 7)` behaves like calling `startsWith` on `filename.substring(7)`, but without the cost of actually creating that substring — it's a convenient, more direct way to check a prefix at a known offset.

## 2. Why & when

`startsWith`/`endsWith` are the direct, readable tools for a very common question: "does this text begin/end with something specific?"

- **File extension checks** — `filename.endsWith(".pdf")` is simpler and clearer than manually finding the last dot and comparing the substring.
- **Protocol/scheme checks** — `url.startsWith("https://")` to distinguish secure from insecure URLs, or to validate an expected format.
- **Namespace or prefix-based filtering** — checking if an identifier, key, or path belongs to a particular group (`key.startsWith("config.")`).
- **Command parsing** — recognizing a command by its leading keyword before extracting arguments from the rest of the string.

For anything beyond an exact literal prefix/suffix — pattern-based matching, case-insensitivity — combine with `toLowerCase()` first, or reach for regular expressions (`matches`) instead.

## 3. Core concept

```java
public class StartsEndsDemo {
    public static void main(String[] args) {
        String[] files = { "report.pdf", "image.png", "archive.tar.gz", "notes.PDF" };

        for (String file : files) {
            if (file.endsWith(".pdf")) {
                System.out.println(file + " is a PDF");
            } else if (file.toLowerCase().endsWith(".pdf")) {
                System.out.println(file + " is a PDF (different case)");
            } else {
                System.out.println(file + " is not a PDF");
            }
        }
    }
}
```

The first check, `file.endsWith(".pdf")`, is strictly case-sensitive and misses `"notes.PDF"` entirely — the second check demonstrates the standard fix: normalizing the string's case with `toLowerCase()` before applying the same, still-case-sensitive `endsWith` check against a lowercase pattern.

## 4. Diagram

<svg viewBox="0 0 700 145" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="startsWith and endsWith diagram: the filename report underscore final dot pdf; startsWith checks the beginning of the string against report, and endsWith checks the very end of the string against dot pdf." >
  <rect x="8" y="8" width="684" height="129" rx="8" fill="#0d1117"/>
  <text x="350" y="22" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">"report_final.pdf" — checking the two ends of the string</text>

  <rect x="60" y="45" width="90" height="28" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="105" y="64" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">report</text>
  <rect x="150" y="45" width="270" height="28" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="285" y="64" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">_final</text>
  <rect x="420" y="45" width="60" height="28" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="450" y="64" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">.pdf</text>

  <text x="105" y="88" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">startsWith("report") -&gt; true</text>
  <text x="450" y="88" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">endsWith(".pdf") -&gt; true</text>

  <text x="350" y="118" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">Both checks are exact, case-sensitive, literal comparisons — no pattern matching involved.</text>
</svg>

`startsWith` and `endsWith` check exact text at each end of the string, independently of each other.

## 5. Runnable example

Scenario: a simple URL router that dispatches requests based on their path prefix — starting with basic prefix-based routing, then adding suffix-based content-type detection, then hardening both checks to be robust against trailing slashes and case differences that real-world URLs commonly have.

### Level 1 — Basic

```java
public class RouterBasic {
    public static void main(String[] args) {
        String[] paths = { "/api/users", "/api/orders", "/static/logo.png" };

        for (String path : paths) {
            if (path.startsWith("/api/")) {
                System.out.println(path + " -> API handler");
            } else {
                System.out.println(path + " -> static file handler");
            }
        }
    }
}
```

**How to run:** `java RouterBasic.java`

`path.startsWith("/api/")` checks whether each path begins with exactly that literal text — the first two paths match and route to the API handler, while `/static/logo.png` does not, falling through to the static file handler.

### Level 2 — Intermediate

Same router, now also inspecting the **file extension** with `endsWith` to pick a content type for static files, combining prefix and suffix checks in one pass.

```java
public class RouterIntermediate {
    public static void main(String[] args) {
        String[] paths = { "/api/users", "/static/logo.png", "/static/style.css", "/static/data.json" };

        for (String path : paths) {
            if (path.startsWith("/api/")) {
                System.out.println(path + " -> API handler");
            } else if (path.endsWith(".png") || path.endsWith(".jpg")) {
                System.out.println(path + " -> image content-type");
            } else if (path.endsWith(".css")) {
                System.out.println(path + " -> stylesheet content-type");
            } else {
                System.out.println(path + " -> generic content-type");
            }
        }
    }
}
```

**How to run:** `java RouterIntermediate.java`

The chain checks `startsWith` first (routing API calls away entirely), then falls into a series of `endsWith` checks for the remaining static paths — `path.endsWith(".png") || path.endsWith(".jpg")` combines two suffix checks with `||` to treat either image extension the same way, and `/static/data.json` falls through every specific check to the generic branch.

### Level 3 — Advanced

Same router, now robust against **trailing slashes** (`"/api/users/"` should route the same as `"/api/users"`) and **case-insensitive extensions** (`.PNG` should be treated the same as `.png`), both common real-world inconsistencies that strict `startsWith`/`endsWith` alone would mishandle.

```java
public class RouterAdvanced {

    static String route(String rawPath) {
        if (rawPath == null || rawPath.isEmpty()) {
            return "invalid path";
        }

        // Normalize: strip exactly one trailing slash, if present (but not the root "/")
        String path = rawPath;
        if (path.length() > 1 && path.endsWith("/")) {
            path = path.substring(0, path.length() - 1);
        }

        if (path.startsWith("/api/")) {
            return "API handler for " + path;
        }

        String lowerPath = path.toLowerCase();
        if (lowerPath.endsWith(".png") || lowerPath.endsWith(".jpg")) {
            return "image content-type for " + path;
        } else if (lowerPath.endsWith(".css")) {
            return "stylesheet content-type for " + path;
        } else {
            return "generic content-type for " + path;
        }
    }

    public static void main(String[] args) {
        String[] paths = { "/api/users/", "/static/logo.PNG", "/static/style.css/", null, "" };
        for (String path : paths) {
            System.out.println(path + " -> " + route(path));
        }
    }
}
```

**How to run:** `java RouterAdvanced.java`

The trailing-slash normalization (`if (path.length() > 1 && path.endsWith("/")) path = path.substring(0, path.length() - 1);`) runs once, before any routing decision, so `"/api/users/"` is treated identically to `"/api/users"` — the `length() > 1` guard specifically avoids stripping the slash from the bare root path `"/"` itself, which would otherwise become an empty string. `lowerPath.endsWith(".png")` operates on a lowercased copy of the (already slash-normalized) path, so `"/static/logo.PNG"` correctly matches despite its uppercase extension, without affecting the case of the path used in the returned message.

## 6. Walkthrough

Trace `route("/static/logo.PNG")`:

**Null/empty check.** The input is neither `null` nor empty, so execution proceeds.

**Trailing-slash normalization.** `path.length() > 1` is `true`, but `path.endsWith("/")` is `false` (`"/static/logo.PNG"` doesn't end in a slash), so `path` is left unchanged.

**API prefix check.** `path.startsWith("/api/")` is `false` — this isn't an API path.

**Case normalization for extension check.** `lowerPath = path.toLowerCase()` produces `"/static/logo.png"` — a separate, lowercased copy; `path` itself, used later in the returned message, remains `"/static/logo.PNG"` with its original casing intact.

**Extension check.** `lowerPath.endsWith(".png")` is now `true` (comparing against the lowercased copy), so the method returns `"image content-type for /static/logo.PNG"` — note the *original*, un-lowercased `path` appears in the message, not `lowerPath`.

```
rawPath = "/static/logo.PNG"
null/empty? no -> continue
trailing slash? no -> path unchanged: "/static/logo.PNG"
startsWith("/api/")? false -> not an API path
lowerPath = "/static/logo.png"
lowerPath.endsWith(".png")? true -> return "image content-type for /static/logo.PNG"
```

**Final output.** For the five inputs: `/api/users/` (slash stripped, then matches `/api/`) → `API handler for /api/users`; `/static/logo.PNG` → as traced, `image content-type for /static/logo.PNG`; `/static/style.css/` (slash stripped first) → `stylesheet content-type for /static/style.css`; `null` and `""` → both caught by the initial guard, printing `invalid path`.

## 7. Gotchas & takeaways

> **`startsWith`/`endsWith` are strictly case-sensitive** — `"Report.PDF".endsWith(".pdf")` is `false`. If case shouldn't matter, normalize with `.toLowerCase()` on both the string being checked and the literal pattern *before* comparing, rather than assuming either method has a case-insensitive mode built in.

> **Real-world paths and URLs often carry incidental variation (trailing slashes, mixed case) that strict literal `startsWith`/`endsWith` checks don't account for** — normalize the input (strip trailing slashes, lowercase for extension checks) before applying these methods, exactly as Level 3 does, rather than writing separate checks for every variant.

- `startsWith(prefix)`/`endsWith(suffix)` perform exact, case-sensitive literal comparisons at the beginning/end of a string respectively.
- The `startsWith(prefix, offset)` overload checks for a prefix starting at a specific index, avoiding the need to create a substring first.
- Combine with `.toLowerCase()` for case-insensitive prefix/suffix checks, since neither method has a built-in case-insensitive variant.
- Normalize input (trailing slashes, casing) before routing or dispatching decisions based on `startsWith`/`endsWith`, to handle the natural variation real-world data tends to have.
