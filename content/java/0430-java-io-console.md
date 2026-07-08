---
card: java
gi: 430
slug: java-io-console
title: java.io.Console
---

## 1. What it is

`java.io.Console`, added in Java 6, gives access to the character-based console device associated with the current JVM, obtained via `System.console()`. Its two standout features over reading `System.in` directly: `readLine(prompt)` combines showing a prompt and reading a line of input in one call, and — the big one — `readPassword(prompt)` reads a line **without echoing it to the screen**, returning it as a `char[]` rather than a `String`, specifically so sensitive input like passwords never appears on screen or lingers as an immutable `String` in memory.

## 2. Why & when

Reading input via `System.in` (wrapped in a `Scanner` or `BufferedReader`) always echoes whatever the user types back to the screen — fine for most input, but a real problem for passwords or other secrets, which would otherwise be visible to anyone glancing at the screen (or worse, present in terminal scrollback/screen-recording). `Console.readPassword()` solves this at the terminal level, suppressing the echo entirely. It also returns a `char[]` instead of a `String` deliberately — a `String` is immutable and can't be reliably cleared from memory once created, while a `char[]` can be explicitly overwritten (`Arrays.fill(password, ' ')`) the moment it's no longer needed, shrinking the window where the plaintext secret sits in memory.

`System.console()` is the piece to understand carefully: it returns `null` whenever the JVM isn't attached to a real interactive terminal — this includes running from many IDEs' "Run" windows, when input/output has been redirected or piped, and in various CI/automation contexts. Production code that reads sensitive input must always check for `null` and provide a sensible fallback or clear failure, rather than assuming a console is always available.

## 3. Core concept

```java
import java.io.Console;
import java.util.Arrays;

Console console = System.console();
if (console == null) {
    // No interactive terminal attached -- this is common, not an edge case, handle it deliberately
    throw new IllegalStateException("No console available");
}

String name = console.readLine("Enter your name: ");        // prompt + read, echoed normally
char[] password = console.readPassword("Password: ");        // prompt + read, NOT echoed, returns char[]

// ... use password ...
Arrays.fill(password, ' '); // clear it from memory once done -- can't do this with an immutable String
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="readLine echoes typed characters back to the screen as usual; readPassword suppresses the echo entirely and returns a mutable char array instead of an immutable String">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <text x="20" y="26" fill="#79c0ff" font-size="11" font-family="sans-serif">console.readLine("Name: ")</text>
  <rect x="30" y="38" width="250" height="26" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="155" y="56" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Name: Alice   (typed chars ECHOED)</text>

  <text x="20" y="100" fill="#f85149" font-size="11" font-family="sans-serif">console.readPassword("Password: ")</text>
  <rect x="30" y="112" width="250" height="26" rx="4" fill="#1c2430" stroke="#f85149"/><text x="155" y="130" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">Password:            (NOTHING shown)</text>

  <text x="470" y="90" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Result type:</text>
  <text x="470" y="110" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">readLine -&gt; String</text>
  <text x="470" y="128" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">readPassword -&gt; char[] (clearable)</text>
</svg>

`readPassword` differs from `readLine` in two ways at once: no visible echo, and a mutable result type you can wipe from memory.

## 5. Runnable example

Scenario: a simple login prompt reading a username and password — the same login flow, evolved from a basic `Console.readLine` prompt, through securely reading a password with `readPassword`, to gracefully handling the very common case where `System.console()` returns `null` by falling back to a `Scanner`-based prompt.

### Level 1 — Basic

```java
import java.io.Console;

public class ConsoleBasic {
    public static void main(String[] args) {
        Console console = System.console();
        if (console == null) {
            System.out.println("No console available (not running in an interactive terminal) -- see Level 3 for a fallback.");
            return;
        }
        String name = console.readLine("Enter your name: ");
        console.printf("Hello, %s!%n", name);
    }
}
```

**How to run:** `java ConsoleBasic.java` (from a real terminal, to see the interactive prompt; running it redirected or from many IDE consoles will instead print the "no console" message, which is expected — see the gotcha below)

`console.readLine("Enter your name: ")` shows the prompt and reads a line in a single call. `console.printf(...)` is `Console`'s own formatted-output method, functionally similar to `System.out.printf`.

### Level 2 — Intermediate

```java
import java.io.Console;
import java.util.Arrays;

public class ConsolePassword {
    public static void main(String[] args) {
        Console console = System.console();
        if (console == null) {
            System.out.println("No console available (not running in an interactive terminal) -- see Level 3 for a fallback.");
            return;
        }
        String username = console.readLine("Username: ");
        char[] password = console.readPassword("Password: "); // input is NOT echoed to the screen

        System.out.println("Read a password of length: " + password.length);
        Arrays.fill(password, ' '); // clear the sensitive data from memory once no longer needed
    }
}
```

**How to run:** `java ConsolePassword.java` (from a real terminal)

`readPassword` suppresses the terminal echo entirely — whatever the user types for the password is invisible on screen — and returns a `char[]` rather than a `String`, specifically so it can be explicitly wiped (`Arrays.fill`) the moment it's no longer needed, rather than lingering indefinitely as an immutable `String` might.

### Level 3 — Advanced

```java
import java.io.Console;
import java.util.Arrays;
import java.util.Scanner;

public class ConsoleWithFallback {
    static final String VALID_USER = "alice";
    static final String VALID_PASS = "hunter2";

    public static void main(String[] args) {
        Console console = System.console();
        String username;
        char[] password;

        if (console != null) {
            username = console.readLine("Username: ");
            password = console.readPassword("Password: ");
        } else {
            // Fallback for non-interactive environments (redirected input, many IDE run windows, CI):
            // input will be echoed to the screen since there's no real terminal to suppress it.
            System.out.println("(no console detected -- falling back to visible input via Scanner)");
            Scanner scanner = new Scanner(System.in);
            System.out.print("Username: ");
            username = scanner.nextLine();
            System.out.print("Password: ");
            password = scanner.nextLine().toCharArray();
        }

        boolean valid = username.equals(VALID_USER) && new String(password).equals(VALID_PASS);
        System.out.println(valid ? "Login successful." : "Login failed.");

        Arrays.fill(password, ' ');
    }
}
```

**How to run:** `echo -e "alice\nhunter2" | java ConsoleWithFallback.java` (piping input means `System.console()` returns `null`, exercising the fallback path deterministically; running it directly from a real terminal instead exercises the `Console` branch interactively)

Checking `console != null` before deciding how to read input is the crucial pattern: this program works correctly whether or not a real terminal is attached, rather than crashing with a `NullPointerException` the moment `System.console()` returns `null` — which, as the next section shows, is extremely common in practice.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example, running via `echo -e "alice\nhunter2" | java ConsoleWithFallback.java`. Because input is being piped in rather than typed at a real interactive terminal, `System.console()` returns `null`.

The `if (console != null)` check is `false`, so execution takes the `else` branch. It prints `"(no console detected -- falling back to visible input via Scanner)"`, then creates a `Scanner` wrapping `System.in`. `System.out.print("Username: ")` prints the prompt (without a newline, so it stays on the same line as whatever comes next); `scanner.nextLine()` reads the first piped line, `"alice"`, assigning it to `username`.

`System.out.print("Password: ")` prints the second prompt; `scanner.nextLine()` reads the second piped line, `"hunter2"`, and `.toCharArray()` converts it into a `char[]`, assigned to `password`. Because this fallback path uses `Scanner` rather than `Console.readPassword`, this input would be **visible** in a real terminal — there's no way to suppress echo without a genuine console attached, which is an inherent limitation of the fallback, not a bug.

`boolean valid = username.equals(VALID_USER) && new String(password).equals(VALID_PASS)` checks both fields: `username.equals("alice")` is `true`; `new String(password).equals("hunter2")` reconstructs a `String` from the `char[]` just long enough to compare it, and is also `true`. `valid` is `true`, so `"Login successful."` is printed.

Finally, `Arrays.fill(password, ' ')` overwrites every character in the `password` array with a space, ensuring the plaintext password no longer sits in that array in memory once the program is done with it.

Expected output:
```
(no console detected -- falling back to visible input via Scanner)
Username: Password: Login successful.
```

## 7. Gotchas & takeaways

> `System.console()` returns **`null`** far more often than newcomers expect: running from many IDEs' built-in run/console panels, any time input or output is redirected or piped (as in the Level 3 example above), and in most CI/automation environments. Code that calls `console.readLine(...)` without a null check will throw `NullPointerException` in exactly these very common situations — always check for `null` and provide a deliberate fallback or a clear error, never assume an interactive terminal is guaranteed.

- `Console.readLine(prompt)` combines showing a prompt and reading a line in one call, functionally similar to a `Scanner`-based prompt-and-read pair.
- `Console.readPassword(prompt)` suppresses terminal echo entirely and returns a `char[]` rather than a `String`, specifically so the sensitive value can be explicitly cleared from memory (`Arrays.fill`) once no longer needed.
- A `char[]` is used instead of `String` for passwords because `String` is immutable in Java — once created, its backing character data can't be reliably wiped, so it may persist in memory (and potentially in memory dumps or swap) for longer than intended.
- Always null-check `System.console()` before use, and design a fallback path (as Level 3 does with `Scanner`) for the very common case where no real console is attached.
- A `Scanner`-based fallback cannot suppress terminal echo the way `Console.readPassword` can — there's no portable, JDK-only way to hide input without a genuine attached console, which is a real limitation to be aware of when designing CLI tools that must run both interactively and non-interactively.
