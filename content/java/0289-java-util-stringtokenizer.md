---
card: java
gi: 289
slug: java-util-stringtokenizer
title: java.util.StringTokenizer
---

## 1. What it is

`java.util.StringTokenizer` is a legacy class that breaks a string into pieces ("tokens") separated by a set of delimiter characters, letting you walk through the pieces one at a time. It predates `String.split` and the `java.util.regex` package, so it uses simple character matching rather than regular expressions.

```java
import java.util.StringTokenizer;

public class StringTokenizerDemo {
    public static void main(String[] args) {
        StringTokenizer st = new StringTokenizer("red,green,blue", ",");
        while (st.hasMoreTokens()) {
            System.out.println(st.nextToken());
        }
    }
}
```

`new StringTokenizer("red,green,blue", ",")` sets the comma as the delimiter; `hasMoreTokens()`/`nextToken()` then step through `"red"`, `"green"`, `"blue"` one by one.

## 2. Why & when

`StringTokenizer` exists because early Java had no regex support and no `String.split`. It solved the everyday need to chop simple, single-character-delimited text (CSV-like data, space-separated words) into pieces without writing manual index arithmetic.

- **Lightweight splitting** — for a single fixed delimiter character (or a small set of them), it avoids the overhead of compiling a regex pattern.
- **Streaming-style access** — tokens are produced one at a time via `hasMoreTokens`/`nextToken`, rather than materializing a full array up front, which mattered more when memory was scarcer.
- **Legacy code maintenance** — you will still meet it in older codebases parsing simple config lines or protocol messages.

For new code, prefer `String.split(regex)` (more powerful, handles regex patterns and multi-character delimiters) or `java.util.regex.Pattern` for anything beyond trivial splitting. `StringTokenizer` is worth knowing to read old code, not to write new code.

## 3. Core concept

```java
import java.util.StringTokenizer;

public class StringTokenizerCore {
    public static void main(String[] args) {
        StringTokenizer st = new StringTokenizer("one two  three", " ");
        System.out.println("Token count: " + st.countTokens());
        while (st.hasMoreTokens()) {
            System.out.println("[" + st.nextToken() + "]");
        }
    }
}
```

Each delimiter character (here, a space) separates tokens; consecutive delimiters (`"two  three"` has two spaces) are treated as one boundary, so empty tokens are never produced — this is a key difference from `String.split`, which by default *does* produce empty strings between consecutive delimiters.

## 4. Diagram

<svg viewBox="0 0 620 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A string is scanned left to right, delimiter characters are skipped, and each run of non-delimiter characters becomes one token">
  <rect x="8" y="8" width="604" height="144" rx="8" fill="#0d1117"/>
  <text x="20" y="35" fill="#e6edf3" font-size="13" font-family="monospace">"red,green,blue"</text>
  <rect x="20" y="50" width="40" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="40" y="70" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="monospace">red</text>
  <text x="65" y="70" fill="#8b949e" font-size="14" text-anchor="middle">,</text>
  <rect x="80" y="50" width="55" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="107" y="70" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="monospace">green</text>
  <text x="140" y="70" fill="#8b949e" font-size="14" text-anchor="middle">,</text>
  <rect x="150" y="50" width="45" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="172" y="70" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="monospace">blue</text>
  <text x="20" y="115" fill="#79c0ff" font-size="12" font-family="sans-serif">nextToken() -&gt; "red" -&gt; "green" -&gt; "blue" -&gt; hasMoreTokens() false</text>
</svg>

Delimiters mark boundaries; they are discarded, never returned as tokens themselves.

## 5. Runnable example

Scenario: parsing a simple pipe-delimited log line, evolved from a basic split into a small hand-rolled CSV-ish parser that copes with mixed whitespace and reports malformed lines.

### Level 1 — Basic

```java
import java.util.StringTokenizer;

public class TokenizerBasic {
    public static void main(String[] args) {
        String line = "INFO|2026-07-06|server started";
        StringTokenizer st = new StringTokenizer(line, "|");
        while (st.hasMoreTokens()) {
            System.out.println(st.nextToken());
        }
    }
}
```

**How to run:** `java TokenizerBasic.java`

Splits the log line on `|` and prints each field on its own line: the level, the date, and the message.

### Level 2 — Intermediate

Same log-parsing idea, now collecting the fields into an array so they can be addressed by position instead of only iterated.

```java
import java.util.StringTokenizer;

public class TokenizerIntermediate {
    public static void main(String[] args) {
        String line = "WARN|2026-07-06|disk usage high";
        StringTokenizer st = new StringTokenizer(line, "|");

        String[] fields = new String[st.countTokens()];
        int i = 0;
        while (st.hasMoreTokens()) {
            fields[i++] = st.nextToken();
        }

        System.out.println("Level: " + fields[0]);
        System.out.println("Date: " + fields[1]);
        System.out.println("Message: " + fields[2]);
    }
}
```

**How to run:** `java TokenizerIntermediate.java`

`st.countTokens()` is called *before* consuming any tokens to size the array correctly; each call to `nextToken()` both returns a field and advances the internal position, so the loop fills `fields` left to right.

### Level 3 — Advanced

Same log parser, now handling multiple delimiter characters (both `|` and stray spaces around fields) and guarding against a malformed line that doesn't have exactly three fields.

```java
import java.util.StringTokenizer;

public class TokenizerAdvanced {
    static String[] parseLogLine(String line) {
        StringTokenizer st = new StringTokenizer(line, "| ");
        String[] fields = new String[st.countTokens()];
        int i = 0;
        while (st.hasMoreTokens()) {
            fields[i++] = st.nextToken();
        }
        return fields;
    }

    public static void main(String[] args) {
        String[] lines = {
            "INFO|2026-07-06|server started",
            "ERROR | 2026-07-06 | disk failure detected",
            "BAD LINE WITH NO PIPES"
        };

        for (String line : lines) {
            String[] fields = parseLogLine(line);
            if (fields.length < 3) {
                System.out.println("Malformed line, skipping: \"" + line + "\"");
                continue;
            }
            System.out.println(fields[0] + " @ " + fields[1] + " -> " + fields[2]);
        }
    }
}
```

**How to run:** `java TokenizerAdvanced.java`

Using `"| "` as the delimiter set means either a pipe *or* a space ends a token, so `"ERROR | 2026-07-06 | disk failure detected"` still yields exactly three sensible fields even with stray spaces around the pipes; `"BAD LINE WITH NO PIPES"` has no `|` at all, so it tokenizes into five single-word fields, and the length check catches it as malformed before it can be misread as valid data.

## 6. Walkthrough

Trace the `for` loop in `TokenizerAdvanced.main` over the three input lines.

**First line, `"INFO|2026-07-06|server started"`.** `parseLogLine` constructs `new StringTokenizer(line, "| ")`. Scanning left to right, the tokenizer treats every `|` and every space as a boundary: it produces `"INFO"`, `"2026-07-06"`, `"server"`, `"started"` — four tokens, not three, because the space inside `"server started"` also splits. `fields.length` is `4`, which is `>= 3`, so the malformed check passes (even though the message got split in two) — printed as `"INFO @ 2026-07-06 -> server"`, silently dropping `"started"`. This is a real, callable-out limitation, not a hidden detail.

**Second line, `"ERROR | 2026-07-06 | disk failure detected"`.** Tokenizing on `"| "` produces `"ERROR"`, `"2026-07-06"`, `"disk"`, `"failure"`, `"detected"` — five tokens. Again only the first three are used for the printed message, so the output is `"ERROR @ 2026-07-06 -> disk"`.

**Third line, `"BAD LINE WITH NO PIPES"`.** No `|` characters exist, but spaces still split it into five word-tokens: `"BAD"`, `"LINE"`, `"WITH"`, `"NO"`, `"PIPES"`. `fields.length` is `5`, which passes the `>= 3` check, so this line is (incorrectly, for this simplistic parser) treated as valid and printed as `"BAD @ LINE -> WITH"`.

```
"INFO|2026-07-06|server started"        -> [INFO, 2026-07-06, server, started]     -> "INFO @ 2026-07-06 -> server"
"ERROR | 2026-07-06 | disk failure..."  -> [ERROR, 2026-07-06, disk, failure, ...] -> "ERROR @ 2026-07-06 -> disk"
"BAD LINE WITH NO PIPES"                -> [BAD, LINE, WITH, NO, PIPES]            -> "BAD @ LINE -> WITH"
```

**Illustrative output:**
```
INFO @ 2026-07-06 -> server
ERROR @ 2026-07-06 -> disk
BAD @ LINE -> WITH
```

This program deliberately demonstrates a real weakness of `StringTokenizer`: because it treats every delimiter character as equivalent and collapses runs of them, it cannot distinguish "the message field legitimately contains a space" from "a field boundary." A regex-based split on a single `\\|` character would have avoided this exact bug.

## 7. Gotchas & takeaways

> `StringTokenizer` treats each character in its delimiter string as an *independent* delimiter, not as a multi-character delimiter sequence. `new StringTokenizer(line, "| ")` splits on `|` **or** space, not on the literal two-character sequence `"| "`. This is the single most common source of confusion when migrating old code.

> Consecutive delimiters never produce empty tokens (unlike `String.split`, which does by default). If your data can legitimately contain empty fields (e.g. CSV `"a,,c"` meaning an empty middle field), `StringTokenizer` will silently swallow that emptiness — `"a,,c"` tokenizes to just `"a"` and `"c"`, losing the fact that there were three fields.

- `StringTokenizer` is a pre-regex, single/multi-character-delimiter splitter; it does not understand regular expressions.
- `hasMoreTokens()` / `nextToken()` walk forward one token at a time; `countTokens()` reports how many remain without consuming any.
- Consecutive delimiters are collapsed — no empty tokens are ever produced, which can silently hide malformed data with missing fields.
- For new code, prefer `String.split(regex)` or `java.util.regex.Pattern`, which are more precise and far more capable.
