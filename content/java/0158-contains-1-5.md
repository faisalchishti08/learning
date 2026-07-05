---
card: java
gi: 158
slug: contains-1-5
title: contains() (1.5)
---

## 1. What it is

`String.contains(CharSequence s)`, added in Java 1.5, returns `true` if the string contains the given sequence of characters anywhere within it — as a literal substring, not a pattern. It is functionally equivalent to checking `indexOf(s) >= 0`, but reads more directly as a yes/no question, without needing to think about index positions at all.

```java
String sentence = "The quick brown fox";

System.out.println(sentence.contains("quick"));  // true
System.out.println(sentence.contains("Quick"));  // false — case-sensitive
System.out.println(sentence.contains(""));       // true — every string "contains" the empty string
```

`contains` accepts a `CharSequence`, not just a `String` — since `String` (and `StringBuilder`) both implement `CharSequence`, you can pass either directly without conversion.

## 2. Why & when

`contains` is the clearest way to ask "does this text include this substring anywhere?" whenever you don't need to know *where* the match is, only *whether* one exists:

- **Simple membership checks** — does an error message mention "timeout"? Does a file path include a particular directory name?
- **Filtering collections** — keeping only strings that contain a search term, a common building block for simple search features.
- **Readability over `indexOf`** — `if (text.contains("keyword"))` is more direct and self-explanatory than `if (text.indexOf("keyword") >= 0)`, even though both produce identical results.

Reach for `indexOf` instead of `contains` specifically when you need the match's *position*, not just its presence — `contains` deliberately throws away that information, since it only returns a boolean.

## 3. Core concept

```java
import java.util.ArrayList;
import java.util.List;

public class ContainsDemo {
    public static void main(String[] args) {
        String[] logLines = {
            "INFO: Server started",
            "ERROR: Connection timeout",
            "INFO: Request processed",
            "ERROR: Disk full"
        };

        List<String> errors = new ArrayList<>();
        for (String line : logLines) {
            if (line.contains("ERROR")) {
                errors.add(line);
            }
        }

        System.out.println(errors);
        // [ERROR: Connection timeout, ERROR: Disk full]
    }
}
```

`line.contains("ERROR")` is checked for each log line, and only the lines that actually contain that literal substring are collected — this pattern (filter a collection by substring containment) is one of the most common uses of `contains`.

## 4. Diagram

<svg viewBox="0 0 700 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Contains diagram: the string ERROR colon connection timeout is checked against the substring ERROR, returning true because that exact text appears somewhere within the larger string, regardless of its exact position.">
  <rect x="8" y="8" width="684" height="124" rx="8" fill="#0d1117"/>
  <text x="350" y="22" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">"ERROR: Connection timeout".contains("ERROR")</text>

  <rect x="60" y="45" width="90" height="28" rx="4" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="105" y="64" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">ERROR</text>
  <rect x="150" y="45" width="330" height="28" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="315" y="64" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">: Connection timeout</text>

  <text x="350" y="95" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">contains("ERROR") -&gt; true (match found, position not reported)</text>

  <text x="350" y="115" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">contains() only answers yes/no — use indexOf() if you also need to know WHERE the match is.</text>
</svg>

`contains` answers only "is it in there anywhere?" — position information is deliberately discarded.

## 5. Runnable example

Scenario: a simple content moderation filter that flags messages containing banned words — starting with a basic single-word check, then extending it to check against a list of multiple banned words, then hardening it to be case-insensitive and to report which specific word triggered the flag.

### Level 1 — Basic

```java
public class ModerationBasic {
    public static void main(String[] args) {
        String message = "This product is absolutely amazing, buy now!";

        if (message.contains("buy now")) {
            System.out.println("Flagged: contains promotional language");
        } else {
            System.out.println("Message OK");
        }
    }
}
```

**How to run:** `java ModerationBasic.java`

`message.contains("buy now")` checks whether that exact literal phrase appears anywhere in `message` — it does (at the end), so the message is flagged.

### Level 2 — Intermediate

Same moderation filter, now checking against **several banned words** in a list, flagging a message if it contains any one of them.

```java
import java.util.List;

public class ModerationIntermediate {
    public static void main(String[] args) {
        List<String> bannedWords = List.of("buy now", "act fast", "limited offer");
        String[] messages = {
            "This product is amazing, buy now!",
            "Just a regular update, nothing special.",
            "Act fast, this deal won't last!"
        };

        for (String message : messages) {
            boolean flagged = false;
            for (String banned : bannedWords) {
                if (message.contains(banned)) {
                    flagged = true;
                    break; // no need to keep checking once one banned word is found
                }
            }
            System.out.println(message + " -> " + (flagged ? "FLAGGED" : "OK"));
        }
    }
}
```

**How to run:** `java ModerationIntermediate.java`

The inner loop checks `message.contains(banned)` against each entry in `bannedWords` in turn, `break`ing as soon as any one matches — this correctly flags the first and third messages (which contain `"buy now"` and, notice, the second message's `"Act fast"` does *not* match `"act fast"` due to the differing case, a limitation this level doesn't yet address).

### Level 3 — Advanced

Same filter, now made **case-insensitive** (so `"Act fast"` correctly matches the banned phrase `"act fast"`) and reporting **which specific word** triggered the flag, rather than just a boolean.

```java
import java.util.List;
import java.util.Optional;

public class ModerationAdvanced {

    static Optional<String> findBannedWord(String message, List<String> bannedWords) {
        if (message == null) {
            return Optional.empty();
        }
        String lowerMessage = message.toLowerCase();
        for (String banned : bannedWords) {
            if (lowerMessage.contains(banned.toLowerCase())) {
                return Optional.of(banned); // return the ORIGINAL casing of the banned word, for a clear report
            }
        }
        return Optional.empty();
    }

    public static void main(String[] args) {
        List<String> bannedWords = List.of("buy now", "act fast", "limited offer");
        String[] messages = {
            "This product is amazing, BUY NOW!",
            "Just a regular update.",
            "Act Fast, this deal won't last!",
            null
        };

        for (String message : messages) {
            Optional<String> match = findBannedWord(message, bannedWords);
            if (match.isPresent()) {
                System.out.println(message + " -> FLAGGED for: " + match.get());
            } else {
                System.out.println(message + " -> OK");
            }
        }
    }
}
```

**How to run:** `java ModerationAdvanced.java`

`lowerMessage = message.toLowerCase()` and `banned.toLowerCase()` are both lowercased before the `contains` check, so the comparison is effectively case-insensitive even though `contains` itself never stops being case-sensitive — this is the same technique used earlier for case-insensitive `equals`/`startsWith` checks. The method returns an `Optional<String>` holding the *original*, correctly-cased banned word (not the lowercased version used for matching), so the report to the user shows `"buy now"` or `"act fast"` in their natural form.

## 6. Walkthrough

Trace `findBannedWord("Act Fast, this deal won't last!", bannedWords)`:

**Null check.** The message is not `null`, so execution proceeds.

**Lowercasing.** `lowerMessage = message.toLowerCase()` produces `"act fast, this deal won't last!"` — a separate, fully lowercased copy; the original `message` (with its original mixed case) is untouched and still available for the final report.

**First banned word: "buy now".** `banned.toLowerCase()` gives `"buy now"`. `lowerMessage.contains("buy now")` is `false` — this phrase doesn't appear anywhere in the lowercased message.

**Second banned word: "act fast".** `banned.toLowerCase()` gives `"act fast"`. `lowerMessage.contains("act fast")` is `true` — the lowercased message does contain this exact phrase (originally written as `"Act Fast"` in the source, but that distinction is erased in `lowerMessage`). The method returns `Optional.of("act fast")` — note this is the *original* list entry `"act fast"`, already lowercase in this particular case, but the pattern preserves whatever casing the banned-word list itself used.

```
message = "Act Fast, this deal won't last!"
lowerMessage = "act fast, this deal won't last!"
check "buy now":     lowerMessage.contains("buy now")  -> false
check "act fast":    lowerMessage.contains("act fast") -> true -> return Optional.of("act fast")
```

**Final output.** For the four messages: `"BUY NOW!"` message → `FLAGGED for: buy now`; the regular update → `OK`; `"Act Fast..."` → `FLAGGED for: act fast` (as traced); and `null` → caught by the null check inside `findBannedWord`, returning `Optional.empty()`, so `main` prints `null -> OK`.

## 7. Gotchas & takeaways

> **`contains` is strictly case-sensitive, exactly like `startsWith`/`endsWith`** — `"HELLO".contains("hello")` is `false`. Lowercase both the haystack and the needle before comparing if the check should be case-insensitive, since there is no built-in case-insensitive overload.

> **`contains` only tells you *whether* a match exists, never *where*** — if your logic needs the match's position (to extract text around it, for instance), use `indexOf` instead, which `contains` is essentially built on top of internally.

- `contains(CharSequence)` checks for a literal substring's presence anywhere in a string and returns a simple boolean.
- It reads more directly than the equivalent `indexOf(s) >= 0`, and is the preferred choice whenever position information isn't needed.
- Combine with `.toLowerCase()` on both sides for case-insensitive substring checks.
- For filtering a list by substring membership, loop and check `contains` per element, `break`ing early once a match against any one of several target terms is found if only presence (not every match) matters.
