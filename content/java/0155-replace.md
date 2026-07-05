---
card: java
gi: 155
slug: replace
title: replace()
---

## 1. What it is

`String.replace(...)` returns a new string with every occurrence of a target character or literal substring replaced by a replacement — every match is replaced, not just the first. There are two overloads: `replace(char oldChar, char newChar)` for single characters, and `replace(CharSequence target, CharSequence replacement)` for substrings. Both treat their target as **literal text**, not a pattern — unlike `replaceAll`, which interprets its first argument as a regular expression.

```java
String phone = "555-123-4567";
System.out.println(phone.replace('-', '.'));         // "555.123.4567" — every '-' replaced
System.out.println(phone.replace("123", "999"));      // "555-999-4567" — literal substring replaced

String path = "C:\\Users\\alice";
System.out.println(path.replace("\\", "/"));          // "C:/Users/alice" — '\' has no regex meaning here, unlike in replaceAll
```

Because `replace` treats its arguments literally, characters that would be special in a regular expression (like `.`, `\`, or `*`) are matched and replaced exactly as written, with no need to escape them — this is precisely why `replace` is often the safer, simpler choice over `replaceAll` when no actual pattern matching is needed.

## 2. Why & when

`replace` is the right tool whenever you need to substitute **exact, literal text** everywhere it appears:

- **Normalizing separators** — converting all backslashes to forward slashes in a path, or all dashes to a consistent character in a formatted code.
- **Simple text substitution** — replacing a stand-in token, a known literal character, or an exact known substring, with no pattern matching involved.
- **Avoiding regex pitfalls** — since `replace` doesn't interpret its arguments as regular expressions, it's the correct choice when the string to replace might itself contain regex-special characters (like a literal `.` or `\`) that would otherwise need escaping if you used `replaceAll`.

Reach for `replaceAll` (or `Pattern`/`Matcher` directly) only when you genuinely need pattern-based matching — for example, replacing "any sequence of digits" rather than one specific literal substring; for exact literal replacement, `replace` is simpler and less error-prone.

## 3. Core concept

```java
public class ReplaceDemo {
    public static void main(String[] args) {
        String template = "Hello, {name}! You have {count} new messages.";

        String filled = template.replace("{name}", "Alice").replace("{count}", "3");
        System.out.println(filled);
        // "Hello, Alice! You have 3 new messages."
    }
}
```

Each `.replace(...)` call substitutes one literal stand-in token with a real value, and the calls are chained so the second `.replace(...)` operates on the result of the first — this is a simple, hand-rolled template-filling pattern built entirely from literal substring replacement, with no regular expressions involved at all.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Replace diagram: the template string Hello comma curly brace name curly brace exclamation point has its literal token replaced by Alice, producing Hello comma Alice exclamation point, with every other character in the template left untouched.">
  <rect x="8" y="8" width="684" height="134" rx="8" fill="#0d1117"/>
  <text x="350" y="22" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">template.replace("{name}", "Alice") — literal substring swap</text>

  <rect x="60" y="45" width="90" height="26" rx="3" fill="#1c2430" stroke="#e6edf3"/>
  <text x="105" y="63" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">"Hello, "</text>
  <rect x="150" y="45" width="90" height="26" rx="3" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="195" y="63" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">"{name}"</text>
  <rect x="240" y="45" width="30" height="26" rx="3" fill="#1c2430" stroke="#e6edf3"/>
  <text x="255" y="63" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">"!"</text>

  <path d="M 195 71 L 195 95" stroke="#6db33f" stroke-width="2" marker-end="url(#a)"/>
  <rect x="150" y="95" width="90" height="26" rx="3" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="195" y="113" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">"Alice"</text>

  <text x="350" y="130" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">Only the exact literal text "{name}" is matched and swapped — everything else in the template is copied as-is.</text>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker></defs>
</svg>

`replace` matches the literal target text exactly and swaps in the replacement, leaving surrounding text untouched.

## 5. Runnable example

Scenario: sanitizing a filename by replacing characters that aren't safe for a filesystem — starting with a basic single-character replacement, then extending it to replace several unsafe characters in sequence, then hardening it into a reusable sanitizer that also collapses repeated replacement characters into one.

### Level 1 — Basic

```java
public class SanitizeBasic {
    public static void main(String[] args) {
        String filename = "report/final draft.pdf";

        String safe = filename.replace('/', '_');
        System.out.println(safe); // "report_final draft.pdf"
    }
}
```

**How to run:** `java SanitizeBasic.java`

`replace('/', '_')` swaps every forward slash for an underscore — here there's only one, so `"report/final draft.pdf"` becomes `"report_final draft.pdf"`; the space and the dot are left completely untouched, since neither matches the target character `'/'`.

### Level 2 — Intermediate

Same sanitization, now replacing **several different unsafe characters** in sequence by chaining multiple `replace` calls — spaces, slashes, and colons all become underscores.

```java
public class SanitizeIntermediate {
    public static void main(String[] args) {
        String filename = "report: final/draft v2.pdf";

        String safe = filename
            .replace(' ', '_')
            .replace('/', '_')
            .replace(':', '_');

        System.out.println(safe); // "report__final_draft_v2.pdf"
    }
}
```

**How to run:** `java SanitizeIntermediate.java`

Each `.replace(...)` call operates on the result of the previous one — `.replace(' ', '_')` runs first, replacing all four spaces; the result is then fed into `.replace('/', '_')`, which replaces the slash; and that result feeds into `.replace(':', '_')`, replacing the colon. The output shows two consecutive underscores (`"report__final..."`) exactly where a colon-then-space originally sat side by side — each was replaced independently, with no special handling of adjacent replacements.

### Level 3 — Advanced

Same sanitizer, now built as a **reusable method** that also **collapses repeated underscores** (from adjacent unsafe characters, as seen above) down to a single one, using `replace(CharSequence, CharSequence)` for the collapsing step since it needs to match a run of characters, not just one.

```java
public class SanitizeAdvanced {

    static String sanitizeFilename(String filename) {
        if (filename == null || filename.trim().isEmpty()) {
            throw new IllegalArgumentException("Filename cannot be null or blank");
        }

        String result = filename.trim()
            .replace(' ', '_')
            .replace('/', '_')
            .replace(':', '_')
            .replace('\\', '_');

        // Collapse doubled-up underscores that can result from adjacent replaced characters
        while (result.contains("__")) {
            result = result.replace("__", "_");
        }

        return result;
    }

    public static void main(String[] args) {
        String[] filenames = { "report: final/draft v2.pdf", "simple.txt", "  ", null };

        for (String filename : filenames) {
            try {
                System.out.println(filename + " -> " + sanitizeFilename(filename));
            } catch (IllegalArgumentException e) {
                System.out.println(filename + " -> rejected: " + e.getMessage());
            }
        }
    }
}
```

**How to run:** `java SanitizeAdvanced.java`

The `while (result.contains("__"))` loop repeatedly calls `replace("__", "_")` until no doubled underscore remains — a single pass of `replace("__", "_")` on `"a___b"` (three underscores) would only reduce it to `"a_b"` in the two-argument, non-overlapping-scan sense actually only reduces `"___"` to `"_"` in effect since replace scans left to right for non-overlapping matches, but the loop guarantees correctness regardless of how many consecutive underscores accumulated, by repeating until `contains("__")` is finally `false`.

## 6. Walkthrough

Trace `sanitizeFilename("report: final/draft v2.pdf")`:

**Validation.** The trimmed input isn't blank, so no exception is thrown.

**Chained character replacements.** `.trim()` has no visible effect here (no leading/trailing whitespace). `.replace(' ', '_')` replaces all four spaces, producing `"report:_final/draft_v2.pdf"`. `.replace('/', '_')` replaces the slash: `"report:_final_draft_v2.pdf"`. `.replace(':', '_')` replaces the colon: `"report__final_draft_v2.pdf"` — notice the colon and the space that immediately followed it were adjacent, so replacing both independently produced two underscores side by side. `.replace('\\', '_')` finds no backslashes, so it has no effect.

**Collapsing loop.** `result.contains("__")` is `true` (the doubled underscore from the previous step). `result = result.replace("__", "_")` scans left to right and replaces that one occurrence, producing `"report_final_draft_v2.pdf"`. The loop checks `contains("__")` again — now `false` — and exits.

```
"report: final/draft v2.pdf"
  .replace(' ','_')  -> "report:_final/draft_v2.pdf"
  .replace('/','_')  -> "report:_final_draft_v2.pdf"
  .replace(':','_')  -> "report__final_draft_v2.pdf"   (colon and space were adjacent -> double underscore)
  .replace('\\','_') -> unchanged (no backslashes)
collapse loop: contains("__")? yes -> replace -> "report_final_draft_v2.pdf"
              contains("__")? no  -> done
```

**Final output.** The four filenames produce: `report: final/draft v2.pdf -> report_final_draft_v2.pdf` (as traced); `simple.txt -> simple.txt` (unchanged, nothing to replace); `   -> rejected: Filename cannot be null or blank` (trims to empty, caught by the guard clause); and `null -> rejected: Filename cannot be null or blank`.

## 7. Gotchas & takeaways

> **`replace` treats its arguments as literal text, not a regular expression — this is different from the similarly-named `replaceAll`, which *does* interpret its first argument as regex.** `str.replace(".", "_")` replaces every literal dot; `str.replaceAll(".", "_")` would replace *every single character* in the string, since `.` is a regex wildcard meaning "any character" — a very easy and dangerous mix-up.

> **Replacing characters that happen to sit adjacent to each other after substitution can produce unwanted doubled-up replacement characters** (as seen with the colon-then-space in the walkthrough) — if this matters for your use case, follow up with a collapsing step (as in Level 3), rather than assuming replacements never interact with one another.

- `replace(char, char)` and `replace(CharSequence, CharSequence)` both replace every literal occurrence, not just the first, and both return a new string.
- `replace` is safer than `replaceAll` when no actual regex pattern matching is needed, since it never misinterprets regex-special characters like `.` or `\`.
- Chaining multiple `.replace(...)` calls applies each one to the previous call's result, in the exact order written.
- Adjacent characters replaced independently by separate `.replace(...)` calls can combine into unwanted repeated sequences; a follow-up collapsing step handles this if it matters.
