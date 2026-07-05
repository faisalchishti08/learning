---
card: java
gi: 151
slug: equals-equalsignorecase
title: equals() & equalsIgnoreCase()
---

## 1. What it is

`String.equals(Object other)` compares two strings **character by character** and returns `true` only if both have the exact same length and every corresponding character matches, case included. `equalsIgnoreCase(String other)` performs the same comparison but treats uppercase and lowercase letters as equivalent (`'A'` matches `'a'`). Both are the correct way to compare string *content* — unlike `==`, which compares object identity (see the earlier string-pool topic).

```java
String a = "Hello";
String b = "hello";
String c = "Hello";

System.out.println(a.equals(b));           // false — case differs
System.out.println(a.equals(c));           // true  — identical content
System.out.println(a.equalsIgnoreCase(b)); // true  — case ignored
```

`equals` overrides the default `Object.equals`, which would otherwise just compare identity (equivalent to `==`) — `String` is one of the many classes that provides a meaningful, content-based `equals` implementation.

## 2. Why & when

Content comparison is needed constantly, and `equals`/`equalsIgnoreCase` are the standard, correct tools:

- **Any time two strings are compared for "are these the same text?"** — validating user input against an expected value, checking a command against a known keyword, comparing keys.
- **`equalsIgnoreCase` specifically** for comparisons where case shouldn't matter — usernames, file extensions, command keywords typed by a user who might use any capitalization.
- **Never `==`** for this purpose — as covered in the string pool topic, `==` only happens to work for some literal comparisons and fails unpredictably for strings built at runtime.

`equals` is also what many other parts of the language rely on implicitly: `HashMap`/`HashSet` use `equals` (paired with `hashCode`) to determine whether two keys are "the same," and `List.contains(...)` uses `equals` to check membership.

## 3. Core concept

```java
public class EqualsDemo {
    public static void main(String[] args) {
        String input = "YES";
        String[] validAnswers = { "yes", "y" };

        boolean matched = false;
        for (String valid : validAnswers) {
            if (input.equalsIgnoreCase(valid)) {
                matched = true;
                break;
            }
        }
        System.out.println("Matched: " + matched); // true — "YES" matches "yes" ignoring case
    }
}
```

`input.equalsIgnoreCase(valid)` is checked against each entry in `validAnswers` in turn — the loop stops (`break`) the moment a case-insensitive match is found, correctly recognizing `"YES"` as equivalent to `"yes"` even though a plain `.equals()` would have rejected it.

## 4. Diagram

<svg viewBox="0 0 700 155" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Equals versus equalsIgnoreCase diagram: comparing Hello and hello with equals returns false because case differs at every letter, while equalsIgnoreCase returns true because it treats corresponding uppercase and lowercase letters as matching.">
  <rect x="8" y="8" width="684" height="139" rx="8" fill="#0d1117"/>
  <text x="350" y="22" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">"Hello".equals("hello") vs "Hello".equalsIgnoreCase("hello")</text>

  <rect x="60" y="40" width="120" height="26" rx="4" fill="#1c2430" stroke="#e6edf3"/>
  <text x="120" y="58" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">"Hello"</text>
  <rect x="200" y="40" width="120" height="26" rx="4" fill="#1c2430" stroke="#e6edf3"/>
  <text x="260" y="58" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">"hello"</text>

  <text x="450" y="45" fill="#f85149" font-size="9" font-family="monospace">.equals()      -&gt; false</text>
  <text x="450" y="65" fill="#6db33f" font-size="9" font-family="monospace">.equalsIgnoreCase() -&gt; true</text>

  <text x="120" y="90" fill="#f85149" font-size="8" text-anchor="middle" font-family="sans-serif">'H' vs 'h' — different chars to equals()</text>
  <text x="260" y="90" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">'H' vs 'h' — same letter to equalsIgnoreCase()</text>

  <text x="350" y="125" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">Both methods still require matching length and matching characters at every position —</text>
  <text x="350" y="140" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">equalsIgnoreCase just treats case variants of the same letter as equal.</text>
</svg>

`equals` is case-sensitive throughout; `equalsIgnoreCase` treats corresponding upper/lowercase letters as matching.

## 5. Runnable example

Scenario: a simple command dispatcher that reacts to typed text commands — starting with exact, case-sensitive matching, then relaxing it to be case-insensitive for usability, then hardening it against `null` input and trimming stray whitespace before comparing.

### Level 1 — Basic

```java
public class CommandBasic {
    public static void main(String[] args) {
        String command = "START";

        if (command.equals("start")) {
            System.out.println("Starting...");
        } else {
            System.out.println("Unknown command: " + command);
        }
    }
}
```

**How to run:** `java CommandBasic.java`

`"START".equals("start")` is `false` — the two strings differ in case at every letter, and `equals` is strictly case-sensitive. The program prints `"Unknown command: START"`, which is likely not the intended, user-friendly behavior for a command interpreter.

### Level 2 — Intermediate

Same dispatcher, now using `equalsIgnoreCase` so the command works regardless of how the user capitalizes it.

```java
public class CommandIntermediate {
    public static void main(String[] args) {
        String[] commands = { "START", "Stop", "pause", "EXIT" };

        for (String command : commands) {
            if (command.equalsIgnoreCase("start")) {
                System.out.println("Starting...");
            } else if (command.equalsIgnoreCase("stop")) {
                System.out.println("Stopping...");
            } else {
                System.out.println("Unknown command: " + command);
            }
        }
    }
}
```

**How to run:** `java CommandIntermediate.java`

`equalsIgnoreCase` makes `"START"`, `"Stop"`, and any other capitalization variant of the recognized keywords match correctly, regardless of how the user happened to type them — `"pause"` and `"EXIT"` still fall through to the `else` branch, since they're not recognized commands at all, capitalization aside.

### Level 3 — Advanced

Same dispatcher, now defensively handling **`null`** input and **surrounding whitespace** (a user might type `"  start  "` with accidental leading/trailing spaces) before comparing.

```java
public class CommandAdvanced {

    static String dispatch(String rawCommand) {
        if (rawCommand == null) {
            return "No command provided";
        }
        String command = rawCommand.trim();

        if (command.equalsIgnoreCase("start")) {
            return "Starting...";
        } else if (command.equalsIgnoreCase("stop")) {
            return "Stopping...";
        } else if (command.isEmpty()) {
            return "Empty command after trimming";
        } else {
            return "Unknown command: " + command;
        }
    }

    public static void main(String[] args) {
        String[] commands = { "START", "  stop  ", null, "   ", "restart" };
        for (String command : commands) {
            System.out.println("input=" + command + " -> " + dispatch(command));
        }
    }
}
```

**How to run:** `java CommandAdvanced.java`

The `null` check runs first, before `.trim()` is ever called — calling `.trim()` on a `null` reference would itself throw a `NullPointerException`. After trimming, `"  stop  "` becomes `"stop"`, which correctly matches `equalsIgnoreCase("stop")`, even though the original, untrimmed input would not have matched due to the surrounding spaces. A string of only whitespace (`"   "`) trims down to `""`, which is caught by the explicit `isEmpty()` check rather than falling through to the generic "unknown command" message.

## 6. Walkthrough

Trace `dispatch("  stop  ")`:

**Null check.** `rawCommand` is not `null`, so execution proceeds.

**Trimming.** `rawCommand.trim()` removes the leading and trailing spaces, producing `command = "stop"` — a new string, distinct from `rawCommand`, per `String`'s immutability.

**First comparison.** `command.equalsIgnoreCase("start")` compares `"stop"` against `"start"` character by character (case-insensitively): `'s'`≈`'s'`, but then `'t'` vs `'t'`... actually the strings have different lengths in general, but here both `"stop"` and `"start"` differ enough that the comparison returns `false` (they're simply not the same word), so this branch is skipped.

**Second comparison.** `command.equalsIgnoreCase("stop")` compares `"stop"` against `"stop"` — identical content, case-insensitively equal (here, identical case too) — returns `true`. The method returns `"Stopping..."`.

```
rawCommand = "  stop  "
null check: not null -> continue
trim() -> "stop"
equalsIgnoreCase("start")? false -> skip
equalsIgnoreCase("stop")?  true  -> return "Stopping..."
```

**Final output.** For the five inputs: `"START"` → `Starting...`; `"  stop  "` → `Stopping...` (as traced); `null` → `No command provided`; `"   "` → `Empty command after trimming` (trims to `""`); `"restart"` → `Unknown command: restart`.

## 7. Gotchas & takeaways

> **`==` and `.equals()` are not interchangeable for `String` content comparison — `==` compares object identity, `.equals()` compares actual characters.** Always use `.equals()` (or `.equalsIgnoreCase()`) to check whether two strings represent the same text, regardless of how either string was created.

> **Calling `.equals()` (or `.trim()`, or any method) on a possibly-`null` string throws a `NullPointerException` — check for `null` first**, or place a known non-`null` constant on the left side of the comparison (`"stop".equalsIgnoreCase(command)`), which safely returns `false` if `command` is `null`, as covered in the string-pool topic.

- `.equals()` compares string content exactly, character by character, including case; `.equalsIgnoreCase()` does the same but treats corresponding upper/lowercase letters as equal.
- Always use `.equals()`/`.equalsIgnoreCase()`, never `==`, to compare string content.
- `.trim()` combined with `.equalsIgnoreCase()` is a common, user-friendly pattern for comparing text a person typed, tolerating both stray whitespace and inconsistent capitalization.
- Guard against `null` before calling any string method on a variable whose value might legitimately be missing.
