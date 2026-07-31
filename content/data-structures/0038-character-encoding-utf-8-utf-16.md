---
card: data-structures
gi: 38
slug: character-encoding-utf-8-utf-16
title: Character encoding (UTF-8 / UTF-16)
---

## 1. What it is

A **character encoding** is a set of rules mapping abstract characters (like `'A'`, `'€'`, or an emoji) to concrete bytes in memory or on disk. **UTF-16** is the encoding Java uses internally for `String` and `char` — each `char` is 16 bits. **UTF-8** is the dominant encoding for text on the web, in files, and over networks — it uses a variable number of bytes (1 to 4) per character, and is backward-compatible with plain ASCII.

## 2. Why & when

This matters the moment text crosses a boundary — reading a file, sending an HTTP request, or writing to a database — because the bytes on one side must be decoded with the *same* encoding used to write them, or the text comes out corrupted (called "mojibake"). It also explains a Java-specific subtlety: a single Java `char` cannot always hold one visible character, because some characters need more than 16 bits to represent in Unicode.

## 3. Core concept

**UTF-16 in Java: most characters fit in one `char`, some need two.** Characters in the Basic Multilingual Plane (covering the vast majority of everyday text) fit in a single 16-bit `char`. Characters outside that range — many emoji, for example — require a pair of `char`s called a **surrogate pair**. This means `"😀".length()` returns `2`, not `1`, since the emoji is stored as two `char` values.

**UTF-8: variable width, ASCII-compatible.** UTF-8 encodes ASCII characters (English letters, digits, basic punctuation) in exactly 1 byte, identical to plain ASCII — this is why UTF-8 text that only contains ASCII characters looks the same whether or not you know it is UTF-8. Characters outside ASCII use 2, 3, or 4 bytes, with the byte pattern itself signaling how many bytes make up that character.

**Why mismatched encoding corrupts text.** If bytes were written as UTF-8 but read back as a different encoding (e.g. Latin-1), the reader groups the same raw bytes into different characters than the writer intended — the result is garbled text, without any error being raised, since both encodings can technically decode any byte sequence into *something*.

**Java's `getBytes(charset)` and `new String(bytes, charset)` are the boundary points.** Converting a `String` to `byte[]` (to write to a file or send over a network) requires specifying an encoding; converting `byte[]` back to a `String` requires the *same* encoding to reconstruct the original text correctly.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The character A taking 1 byte in UTF-8 and 2 bytes in UTF-16, while an emoji takes 4 bytes in UTF-8 and a surrogate pair (4 bytes as two chars) in UTF-16">
  <g font-family="sans-serif" font-size="11">
    <text x="160" y="16" fill="#8b949e" text-anchor="middle">'A' (ASCII character)</text>
    <rect x="70" y="30" width="60" height="26" fill="#161b22" stroke="#3fb950"/><text x="100" y="47" fill="#e6edf3" text-anchor="middle" font-size="10">UTF-8: 1 byte</text>
    <rect x="150" y="30" width="80" height="26" fill="#161b22" stroke="#79c0ff"/><text x="190" y="47" fill="#e6edf3" text-anchor="middle" font-size="10">UTF-16: 2 bytes</text>

    <text x="480" y="16" fill="#8b949e" text-anchor="middle">'😀' (emoji, outside ASCII)</text>
    <rect x="400" y="30" width="90" height="26" fill="#161b22" stroke="#3fb950"/><text x="445" y="47" fill="#e6edf3" text-anchor="middle" font-size="10">UTF-8: 4 bytes</text>
    <rect x="500" y="30" width="120" height="26" fill="#161b22" stroke="#79c0ff"/><text x="560" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">UTF-16: surrogate pair (2 chars, 4 bytes)</text>
    <text x="320" y="110" fill="#79c0ff" text-anchor="middle">"😀".length() in Java returns 2, not 1 -- it is stored as two chars</text>
  </g>
</svg>

ASCII characters like `'A'` are cheap in both encodings. Characters outside the Basic Multilingual Plane, like many emoji, need extra units in both.

## 5. Runnable example

```java
// CharacterEncodingUtf8Utf16.java
import java.nio.charset.StandardCharsets;
import java.util.Arrays;

public class CharacterEncodingUtf8Utf16 {

    // Basic: encoding the same text to UTF-8 bytes versus counting Java's UTF-16 chars.
    static void basicLevel() {
        String text = "Café"; // contains one non-ASCII character, 'é'
        byte[] utf8Bytes = text.getBytes(StandardCharsets.UTF_8);
        System.out.println("basic: text -> " + text);
        System.out.println("basic: char count (UTF-16 units) -> " + text.length());       // 4
        System.out.println("basic: UTF-8 byte count -> " + utf8Bytes.length);              // 5 ('é' takes 2 bytes)
    }

    // Intermediate: encoding/decoding round trip -- must use the SAME encoding on both ends.
    static void intermediateLevel() {
        String original = "héllo wörld";
        byte[] encoded = original.getBytes(StandardCharsets.UTF_8);
        String decodedCorrectly = new String(encoded, StandardCharsets.UTF_8);
        String decodedWrongly = new String(encoded, StandardCharsets.ISO_8859_1); // wrong charset on purpose

        System.out.println("intermediate: original -> " + original);
        System.out.println("intermediate: decoded with matching UTF-8 -> " + decodedCorrectly);
        System.out.println("intermediate: decoded with mismatched charset -> " + decodedWrongly); // corrupted
    }

    // Advanced: a surrogate pair -- an emoji needs two Java chars, but is one logical "code point".
    static void advancedLevel() {
        String emoji = "😀";
        System.out.println("advanced: emoji.length() (UTF-16 chars) -> " + emoji.length());              // 2
        System.out.println("advanced: emoji.codePointCount(...) (logical characters) -> "
                + emoji.codePointCount(0, emoji.length()));                                                // 1
        byte[] utf8 = emoji.getBytes(StandardCharsets.UTF_8);
        System.out.println("advanced: UTF-8 byte count -> " + utf8.length);                                // 4
        System.out.println("advanced: raw UTF-8 bytes -> " + Arrays.toString(utf8));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `CharacterEncodingUtf8Utf16.java`, then run `java CharacterEncodingUtf8Utf16.java`.

## 6. Walkthrough

1. `basicLevel()` encodes `"Café"` to UTF-8 bytes. `text.length()` reports `4` (Java's UTF-16 `char` count, one per visible character here), but `utf8Bytes.length` reports `5`, because `'é'` needs 2 bytes in UTF-8 while the three ASCII letters need 1 byte each (`3×1 + 1×2 = 5`).
2. `intermediateLevel()` encodes `original` to UTF-8 bytes, then decodes those same bytes twice: once with the matching `UTF_8` charset (producing the correct original text back), and once with a mismatched `ISO_8859_1` charset (producing corrupted, unreadable output) — the raw bytes are identical in both cases, only the decoding rule differs.
3. `advancedLevel()` examines the emoji `"😀"`. `emoji.length()` returns `2`, because Java represents this one visible character as a UTF-16 surrogate pair — two `char` values working together.
4. `codePointCount` correctly reports `1`, since it counts logical Unicode characters (code points), not raw UTF-16 units — this is the method to use when you need the "real" character count for text that might contain characters outside the Basic Multilingual Plane.
5. Encoding the emoji to UTF-8 gives 4 bytes, since characters that need a surrogate pair in UTF-16 also fall into UTF-8's largest, 4-byte encoding form.

## 7. Gotchas & takeaways

> Gotcha: `String.length()` in Java counts UTF-16 `char` units, not "visible characters" — for text containing emoji or other characters outside the Basic Multilingual Plane, `length()` overcounts. Use `codePointCount()` when you need the true number of logical characters.

- Java's `String`/`char` use UTF-16 internally; most characters fit in one `char`, but some need a two-`char` surrogate pair.
- UTF-8 is variable-width (1 to 4 bytes per character) and is backward-compatible with ASCII, which is why it dominates files and networks.
- Encoding and decoding must use the same charset on both ends, or text corrupts silently, with no exception thrown.
- Related concepts: [String as a character sequence](0032-string-as-a-character-sequence.md), [char\[\] vs String](0035-char-vs-string.md).
