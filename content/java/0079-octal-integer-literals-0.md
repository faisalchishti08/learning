---
card: java
gi: 79
slug: octal-integer-literals-0
title: Octal integer literals (0…)
---

## 1. What it is

An octal integer literal is a base-8 integer value written with a leading zero (`0`) followed by one or more octal digits (`0`–`7`). The compiler converts it to its binary representation — exactly the same as any other `int` or `long` literal, but expressed in base 8.

```java
int perm    = 0755;    // octal 755 = decimal 493
int group   = 0644;    // octal 644 = decimal 420
long bigOct = 0777L;   // octal 777 = decimal 511, long literal
```

The octal prefix is a single leading `0`. Any integer literal that starts with `0` followed by more digits is octal — writing `010` in Java source code produces the value `8`, not `10`.

## 2. Why & when

Octal is rarely used in modern Java. Its primary surviving use case is POSIX/Unix file permission modes, where three octal digits each represent three bits (read/write/execute for owner, group, and world). When calling `ProcessBuilder`, `Files.setPosixFilePermissions`, or wrapping native library calls, an octal literal like `0755` directly mirrors how Unix developers think about permissions.

Outside Unix permissions, prefer hexadecimal (which maps cleanly to nibbles and bytes) or binary literals (`0b…`) over octal for any bit-manipulation task. The leading-zero convention is a common trap: refactoring `int port = 0800;` to "make it look like a round number" introduces an octal parse error because `8` and `9` are not valid octal digits.

## 3. Core concept

```java
// ---- Basic octal literals ----
int a = 010;    // 8   (8¹×1 = 8)
int b = 017;    // 15  (8¹×1 + 8⁰×7)
int c = 0777;   // 511 (8²×7 + 8¹×7 + 8⁰×7)

System.out.println(010);    // 8
System.out.println(0755);   // 493  (Unix rwxr-xr-x)
System.out.println(0644);   // 420  (Unix rw-r--r--)

// ---- Octal with L suffix ----
long big = 077777777777L;   // max 10-digit octal fitting in int range
System.out.println(big);    // 2147483647 — Integer.MAX_VALUE!

// ---- Digits 8 and 9 are INVALID in octal ----
// int bad = 09;   // compile error: integer number too large (invalid digit)
// int bad = 08;   // compile error: same reason

// ---- Underscores work in octal too ----
int perm = 07_55;   // same as 0755 = 493
System.out.println(perm);   // 493

// ---- Convert decimal to octal string ----
System.out.println(Integer.toOctalString(493));   // 755
System.out.println(Integer.toOctalString(8));      // 10

// ---- Convert octal string to int ----
int fromString = Integer.parseInt("755", 8);  // 493
System.out.println(fromString);

// ---- Arithmetic with octal literals ----
int sum = 0644 + 0111;   // 420 + 73 = 493  (same as 0755)
System.out.println(Integer.toOctalString(sum));  // 755
System.out.println(sum == 0755);                 // true
```

## 4. Diagram

<svg viewBox="0 0 700 185" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Octal literal 0755: leading zero prefix, three octal digits, conversion to decimal 493, and Unix permission interpretation">
  <rect x="8" y="8" width="684" height="169" rx="8" fill="#0d1117"/>

  <!-- Token anatomy -->
  <rect x="16" y="18" width="668" height="58" rx="4" fill="#1c2430"/>
  <text x="350" y="33" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Octal literal anatomy: 0755</text>

  <!-- leading zero -->
  <rect x="80" y="40" width="28" height="26" rx="3" fill="#6db33f" opacity="0.8"/>
  <text x="94" y="57" fill="#0d1117" font-size="14" font-weight="bold" text-anchor="middle" font-family="monospace">0</text>

  <!-- digit 7 -->
  <rect x="112" y="40" width="28" height="26" rx="3" fill="#79c0ff" opacity="0.7"/>
  <text x="126" y="57" fill="#0d1117" font-size="14" font-weight="bold" text-anchor="middle" font-family="monospace">7</text>

  <!-- digit 5 -->
  <rect x="144" y="40" width="28" height="26" rx="3" fill="#79c0ff" opacity="0.5"/>
  <text x="158" y="57" fill="#0d1117" font-size="14" font-weight="bold" text-anchor="middle" font-family="monospace">5</text>

  <!-- digit 5 -->
  <rect x="176" y="40" width="28" height="26" rx="3" fill="#79c0ff" opacity="0.3"/>
  <text x="190" y="57" fill="#e6edf3" font-size="14" font-weight="bold" text-anchor="middle" font-family="monospace">5</text>

  <!-- labels -->
  <text x="94"  y="76" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">octal prefix</text>
  <text x="158" y="76" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">8²×7=448</text>
  <text x="190" y="76" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">…</text>

  <text x="350" y="76" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">= 7×64 + 5×8 + 5×1 = 448 + 40 + 5 = 493</text>

  <!-- Unix perms box -->
  <rect x="16" y="88" width="310" height="72" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="171" y="104" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Unix permission semantics of 0755</text>
  <line x1="26" y1="110" x2="316" y2="110" stroke="#8b949e" stroke-width="0.5"/>
  <text x="26" y="124" fill="#e6edf3" font-size="8" font-family="monospace">7 = rwx (owner: all)</text>
  <text x="26" y="137" fill="#e6edf3" font-size="8" font-family="monospace">5 = r-x (group: read+exec)</text>
  <text x="26" y="150" fill="#e6edf3" font-size="8" font-family="monospace">5 = r-x (world: read+exec)</text>

  <!-- Gotcha box -->
  <rect x="338" y="88" width="346" height="72" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="511" y="104" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Common trap</text>
  <line x1="348" y1="110" x2="674" y2="110" stroke="#8b949e" stroke-width="0.5"/>
  <text x="348" y="124" fill="#8b949e" font-size="8" font-family="monospace">int port = 0800;  // compile ERROR</text>
  <text x="348" y="137" fill="#8b949e" font-size="8" font-family="monospace">// 8 is not a valid octal digit</text>
  <text x="348" y="152" fill="#6db33f" font-size="8" font-family="monospace">int port = 800;   // decimal — correct</text>
</svg>

The leading `0` marks an octal literal; three octal digits directly encode the three owner/group/world permission triplets in Unix; digits `8` and `9` are illegal in octal.

## 5. Runnable example

Scenario: a Unix file-permissions utility — represents, validates, and displays file permission modes using octal literals. The scenario grows from basic mode display, to permission checking using bitwise operations, to generating mode strings and parsing user-provided octal input.

### Level 1 — Basic

```java
public class OctalBasic {

    static String rwx(int bits) {
        return "" + (((bits & 4) != 0) ? 'r' : '-')
                  + (((bits & 2) != 0) ? 'w' : '-')
                  + (((bits & 1) != 0) ? 'x' : '-');
    }

    static String modeLong(int mode) {
        return rwx((mode >> 6) & 7) + rwx((mode >> 3) & 7) + rwx(mode & 7);
    }

    public static void main(String[] args) {
        // Unix file modes expressed as octal literals
        int executableDir  = 0755;   // rwxr-xr-x
        int regularFile    = 0644;   // rw-r--r--
        int privateKey     = 0600;   // rw-------
        int worldWritable  = 0777;   // rwxrwxrwx

        System.out.println("=== File permission modes ===");
        System.out.printf("0755 = %3d decimal : %s%n", executableDir, modeLong(executableDir));
        System.out.printf("0644 = %3d decimal : %s%n", regularFile,   modeLong(regularFile));
        System.out.printf("0600 = %3d decimal : %s%n", privateKey,    modeLong(privateKey));
        System.out.printf("0777 = %3d decimal : %s%n", worldWritable, modeLong(worldWritable));
    }
}
```

**How to run:** `java OctalBasic.java`

`0755` as an octal literal compiles to decimal `493`. The `modeLong` function recovers the three 3-bit groups by right-shifting and masking with `7` (binary `0b111`). Each 3-bit group encodes read (bit 2), write (bit 1), and execute (bit 0) — exactly the structure of Unix file permissions. Using octal literals here makes the source code match how Unix developers write and document permission modes.

### Level 2 — Intermediate

Same utility: check whether a given mode has specific permission bits set, combine modes with bitwise OR, and strip permissions with AND-NOT.

```java
public class OctalIntermediate {

    static String rwx(int bits) {
        return "" + (((bits & 4) != 0) ? 'r' : '-')
                  + (((bits & 2) != 0) ? 'w' : '-')
                  + (((bits & 1) != 0) ? 'x' : '-');
    }

    static String modeLong(int mode) {
        return rwx((mode >> 6) & 7) + rwx((mode >> 3) & 7) + rwx(mode & 7);
    }

    static boolean ownerCanRead(int mode)  { return (mode & 0400) != 0; }
    static boolean ownerCanWrite(int mode) { return (mode & 0200) != 0; }
    static boolean ownerCanExec(int mode)  { return (mode & 0100) != 0; }

    public static void main(String[] args) {
        int mode = 0644;   // rw-r--r--
        System.out.printf("Mode 0%o (%s)%n", mode, modeLong(mode));
        System.out.println("  owner read  : " + ownerCanRead(mode));
        System.out.println("  owner write : " + ownerCanWrite(mode));
        System.out.println("  owner exec  : " + ownerCanExec(mode));

        // Add group write permission
        int withGroupWrite = mode | 0020;   // set bit: group write
        System.out.printf("%nAfter | 0020 (add group-write): 0%o → %s%n",
            withGroupWrite, modeLong(withGroupWrite));

        // Remove world read
        int noWorldRead = mode & ~0004;    // clear bit: world read
        System.out.printf("After & ~0004 (remove world-read): 0%o → %s%n",
            noWorldRead, modeLong(noWorldRead));

        // Octal string representation
        System.out.printf("%nInteger.toOctalString(%d) = \"%s\"%n",
            mode, Integer.toOctalString(mode));
    }
}
```

**How to run:** `java OctalIntermediate.java`

`0400` isolates the owner-read bit (bit 8, counting from 0). `mode | 0020` sets the group-write bit without changing other bits. `mode & ~0004` clears the world-read bit: `~0004` inverts all bits, turning `0004` (`0b...000000000100`) into a mask where every bit is `1` except bit 2. `%o` in `printf` formats an integer as an octal string without the leading `0` prefix — you must add it manually when displaying modes in the traditional `0755` style.

### Level 3 — Advanced

Same utility: parse octal permission strings provided by the user, validate that all digits are in range `0`–`7`, and produce a detailed permission report for a list of files.

```java
import java.util.List;

public class OctalAdvanced {

    record FileEntry(String name, int mode) {}

    static String rwx(int bits) {
        return "" + (((bits & 4) != 0) ? 'r' : '-')
                  + (((bits & 2) != 0) ? 'w' : '-')
                  + (((bits & 1) != 0) ? 'x' : '-');
    }

    static String modeLong(int mode) {
        return rwx((mode >> 6) & 7) + rwx((mode >> 3) & 7) + rwx(mode & 7);
    }

    // Parse "755" or "0755" → int; throws if any digit outside 0-7
    static int parseOctal(String s) {
        String clean = s.startsWith("0") ? s.substring(1) : s;
        for (char c : clean.toCharArray()) {
            if (c < '0' || c > '7')
                throw new IllegalArgumentException("Invalid octal digit '" + c + "' in: " + s);
        }
        return Integer.parseInt(clean, 8);
    }

    static boolean isSafe(int mode) {
        // World-writable (0002) and setuid/setgid (04000/02000) are considered unsafe
        return (mode & 0002) == 0;
    }

    public static void main(String[] args) {
        // Simulate files with modes stored as octal strings (e.g. from a config file)
        var rawModes = List.of(
            new String[]{"id_rsa",        "0600"},
            new String[]{"deploy.sh",     "755"},
            new String[]{"config.yml",    "0644"},
            new String[]{"public.html",   "0666"},   // world-writable — unsafe
            new String[]{"bad_mode.txt",  "0800"}    // invalid — 8 is not octal
        );

        System.out.printf("%-18s  %-6s  %10s  %s%n", "File", "Mode", "Permission", "Status");
        System.out.println("-".repeat(54));

        for (var row : rawModes) {
            String file = row[0], raw = row[1];
            try {
                int mode = parseOctal(raw);
                String safe = isSafe(mode) ? "OK" : "UNSAFE (world-writable)";
                System.out.printf("%-18s  0%-5s  %10s  %s%n",
                    file, Integer.toOctalString(mode), modeLong(mode), safe);
            } catch (IllegalArgumentException e) {
                System.out.printf("%-18s  %-6s  %10s  ERROR: %s%n",
                    file, raw, "?", e.getMessage());
            }
        }
    }
}
```

**How to run:** `java OctalAdvanced.java`

`Integer.parseInt(clean, 8)` parses a decimal-digit string as base 8. The explicit digit-range check before parsing gives a clear error message instead of a generic `NumberFormatException`. The `isSafe` check tests whether the world-write bit (`0002`) is set — a common security gate before deploying files to a server. The `0800` entry demonstrates how `8` and `9` are invalid octal digits; in Java source code this would be a compile error, but when received as a runtime string it must be caught explicitly.

## 6. Walkthrough

Execution trace through `OctalAdvanced.main` for the entry `{"id_rsa", "0600"}`:

**`parseOctal("0600")`.** The string starts with `0`, so `clean = "600"`. Each character is checked: `6`, `0`, `0` — all in range `'0'`–`'7'`. `Integer.parseInt("600", 8)` evaluates `6×64 + 0×8 + 0×1 = 384`.

**`modeLong(384)`.** The mode `384` in binary is `0000_0001_1000_0000`. The owner triplet is extracted as `(384 >> 6) & 7 = 6 & 7 = 6` (`110` binary = `rw-`). The group triplet: `(384 >> 3) & 7 = 48 & 7 = 0` (`000` = `---`). The world triplet: `384 & 7 = 0` (`000` = `---`). Result: `rw-------`.

**`isSafe(384)`.** `384 & 0002` = `384 & 2`. Binary `384` has no bit 1 set, so the result is `0` — not world-writable, status `OK`.

**Error path for `"0800"`.** `clean = "800"`. On the first character `'8'`: `'8' > '7'` is true, so `IllegalArgumentException` is thrown with the message `"Invalid octal digit '8' in: 0800"`. The `catch` block prints the `ERROR:` line.

```
Request  : parseOctal("0600")
           └─ strip leading 0 → "600"
           └─ validate digits: 6✓ 0✓ 0✓
           └─ parseInt("600", 8) → 6×64 + 0×8 + 0 = 384

modeLong(384):
  owner  : (384>>6)&7 = 6 → rwx(6) → "rw-"
  group  : (384>>3)&7 = 0 → rwx(0) → "---"
  world  :  384    &7 = 0 → rwx(0) → "---"
  result : "rw-------"
```

## 7. Gotchas & takeaways

> **A leading `0` makes any integer literal octal.** `int port = 0800;` is a compile error because `8` is not a valid octal digit. Likewise, `0080` fails for the same reason. Always write port numbers, IDs, and similar values without a leading zero.

> **`08` and `09` are compile errors, not decimal 8 and 9.** The leading `0` commits the literal to octal, where only `0`–`7` are valid. If you accidentally write `int x = 09;` you get `"integer number too large"` — a confusing error for what looks like a valid number.

- Octal literals start with `0` followed by digits `0`–`7`.
- The primary use case in Java is Unix file permission modes (`0755`, `0644`, `0600`).
- Use `Integer.toOctalString(int)` to convert a value to its octal string representation.
- Use `Integer.parseInt(s, 8)` to parse an octal string at runtime.
- Digits `8` and `9` are invalid in octal literals — the compiler reports a compile error.
- Underscores work in octal literals too: `07_55` is the same as `0755`.
- For bit manipulation unrelated to Unix permissions, prefer hex (`0x…`) or binary (`0b…`) literals — they are more commonly understood.
