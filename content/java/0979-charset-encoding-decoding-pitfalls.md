---
card: java
gi: 979
slug: charset-encoding-decoding-pitfalls
title: Charset encoding/decoding pitfalls
---

## 1. What it is

A `Charset` defines the mapping between a sequence of bytes and a sequence of characters — encoding converts a Java `String` (internally a sequence of `char`s, representing Unicode code points) into bytes according to some specific charset's rules, and decoding does the reverse, interpreting a sequence of bytes back into characters according to a (hopefully the *same*) charset. The pitfall this entire topic centers on is simple to state and easy to trip over in practice: encoding text with one charset and decoding those same bytes back with a *different* charset produces silently wrong, garbled text (a phenomenon often called "mojibake") — no exception is thrown, since from the decoder's perspective, it's simply following its own charset's rules against whatever bytes it's given, with no way to know those bytes were actually produced under a different charset's rules entirely.

## 2. Why & when

This matters anywhere bytes cross a boundary where the charset isn't automatically, unambiguously known on both sides — reading a text file whose actual encoding wasn't recorded or is only guessed at, receiving an HTTP request body whose declared charset (in a `Content-Type` header) doesn't match what the client actually sent, or — a particularly common and insidious version — relying on a method's *platform default charset* (which several older `String`/`InputStreamReader`/`FileReader` constructors do) rather than an explicitly specified one, meaning the exact same code can behave correctly on a developer's own machine (whose platform default happens to be UTF-8) and silently corrupt non-ASCII text in production on a server configured with a different platform default. The single most important practical guideline: always specify a charset *explicitly* (`StandardCharsets.UTF_8`) at every point where bytes and characters convert into one another, rather than relying on whatever a platform's default charset happens to be at runtime — this single habit eliminates the entire category of "worked on my machine, broke in production" charset bugs.

## 3. Core concept

```java
String text = "café"; // 'é' is a non-ASCII character

byte[] utf8Bytes = text.getBytes(StandardCharsets.UTF_8);       // 5 bytes (é takes 2 bytes in UTF-8)
byte[] latin1Bytes = text.getBytes(StandardCharsets.ISO_8859_1); // 4 bytes (é takes 1 byte in Latin-1)

// MISMATCH: encode as UTF-8, decode as Latin-1 -- WRONG, but NO EXCEPTION:
String garbled = new String(utf8Bytes, StandardCharsets.ISO_8859_1);
// garbled is "cafÃ©" -- silently WRONG, since UTF-8's 2-byte encoding of 'é' is
// misinterpreted as TWO separate Latin-1 characters instead

// CORRECT: decode with the SAME charset used to encode:
String correct = new String(utf8Bytes, StandardCharsets.UTF_8);
// correct is "café" -- exactly right, because encode and decode charsets MATCH
```

The core rule: bytes have no inherent, self-describing charset attached to them — decoding is always a *guess* about which charset the bytes were originally encoded with, and getting that guess wrong produces silently corrupted, but not exception-throwing, output.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A string encoded as UTF-8 bytes, then decoded correctly with UTF-8 producing the original text, versus decoded incorrectly with ISO-8859-1 producing silently garbled text" >
  <rect x="20" y="20" width="140" height="30" fill="#1c2430" stroke="#6db33f"/>
  <text x="90" y="39" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">"café" (String)</text>

  <rect x="240" y="20" width="140" height="30" fill="#1c2430" stroke="#79c0ff"/>
  <text x="310" y="39" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">UTF-8 encode -&gt; bytes</text>
  <line x1="160" y1="35" x2="240" y2="35" stroke="#8b949e" marker-end="url(#a)"/>

  <rect x="440" y="0" width="180" height="30" fill="#1c2430" stroke="#6db33f"/>
  <text x="530" y="19" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">decode UTF-8 -&gt; "café" CORRECT</text>
  <line x1="380" y1="30" x2="440" y2="15" stroke="#6db33f" marker-end="url(#a)"/>

  <rect x="440" y="60" width="180" height="30" fill="#1c2430" stroke="#f0883e"/>
  <text x="530" y="79" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">decode Latin-1 -&gt; "cafÃ©" WRONG</text>
  <line x1="380" y1="40" x2="440" y2="70" stroke="#f0883e" marker-end="url(#a)"/>

  <text x="320" y="125" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Same bytes, different decoding charset -- silently wrong, NO exception thrown</text>
</svg>

*The same encoded bytes produce correct text when decoded with the matching charset, and silently garbled text when decoded with a mismatched one.*

## 5. Runnable example

Scenario: process user-submitted text containing non-ASCII characters, evolving from a basic demonstration of the mismatch pitfall itself, to a realistic file-reading scenario relying on (and then avoiding) platform-default charset behavior, to a more advanced case handling a genuinely malformed byte sequence safely rather than either silently corrupting or crashing.

### Level 1 — Basic

```java
import java.nio.charset.StandardCharsets;

public class CharsetMismatchBasic {
    public static void main(String[] args) {
        String original = "café éèê"; // includes accented characters

        byte[] encoded = original.getBytes(StandardCharsets.UTF_8);

        String correctlyDecoded = new String(encoded, StandardCharsets.UTF_8);
        String incorrectlyDecoded = new String(encoded, StandardCharsets.ISO_8859_1);

        System.out.println("original:            " + original);
        System.out.println("correctly decoded:    " + correctlyDecoded);
        System.out.println("incorrectly decoded:  " + incorrectlyDecoded);
    }
}
```

**How to run:** `java CharsetMismatchBasic.java` (JDK 17+).

Expected output:
```
original:            café éèê
correctly decoded:    café éèê
incorrectly decoded:  cafÃ© Ã©Ã¨Ãª
```

Encoding with UTF-8 and decoding with the *same* charset round-trips perfectly, while decoding those exact same bytes with ISO-8859-1 instead produces visibly garbled, but not exception-throwing, output — each multi-byte UTF-8 sequence gets misinterpreted as multiple separate Latin-1 characters, since ISO-8859-1 assigns a character to *every single byte value*, with no concept of multi-byte sequences at all.

### Level 2 — Intermediate

```java
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;

public class CharsetPlatformDefaultPitfall {
    public static void main(String[] args) throws IOException {
        Path path = Files.createTempFile("charset-demo", ".txt");
        String text = "Résumé: naïve café";

        // Write EXPLICITLY as UTF-8 -- unambiguous, regardless of platform.
        Files.writeString(path, text, StandardCharsets.UTF_8);

        // Read back EXPLICITLY as UTF-8 -- matches how it was written, always correct.
        String readCorrectly = Files.readString(path, StandardCharsets.UTF_8);
        System.out.println("read with matching charset: " + readCorrectly);

        // Read back relying on the PLATFORM DEFAULT charset instead of specifying one --
        // this line's correctness now depends entirely on what happens to be running
        // this specific JVM's default charset, which varies by OS, locale, and JVM version.
        String readWithDefault = new String(Files.readAllBytes(path));
        System.out.println("read with platform default: " + readWithDefault);
        System.out.println("platform default charset is: " + java.nio.charset.Charset.defaultCharset());

        Files.delete(path);
    }
}
```

**How to run:** `java CharsetPlatformDefaultPitfall.java` (JDK 17+; on most modern JVMs, `file.encoding` defaults to UTF-8, so this specific example may show matching output — the point is that the *second* read's correctness depends on this default, not on anything guaranteed by the code itself).

Expected output shape (JDK 18+ defaults `file.encoding` to UTF-8 regardless of platform locale, so both lines typically match; older JDKs on certain platforms/locales could show a mismatch):
```
read with matching charset: Résumé: naïve café
read with platform default: Résumé: naïve café
platform default charset is: UTF-8
```

The real-world concern added: the first read explicitly specifies `StandardCharsets.UTF_8`, matching exactly how the file was written, guaranteeing correctness regardless of what machine or JVM version this code runs on; the second read relies on `new String(byte[])`'s platform-default-charset behavior, which — while it happens to be UTF-8 on most current systems — is not something the code itself guarantees, meaning identical code could behave differently on a JVM or environment configured with a different default, which is exactly the kind of environment-dependent bug the explicit-charset habit eliminates entirely.

### Level 3 — Advanced

```java
import java.nio.*;
import java.nio.charset.*;

public class CharsetMalformedSequenceHandling {
    public static void main(String[] args) {
        // Deliberately malformed UTF-8: 0xC3 alone is the START of a 2-byte sequence,
        // but it's not followed by a valid continuation byte here.
        byte[] malformed = {(byte) 'h', (byte) 'i', (byte) 0xC3, (byte) 0x20};

        CharsetDecoder lenientDecoder = StandardCharsets.UTF_8.newDecoder()
            .onMalformedInput(CodingErrorAction.REPLACE)
            .replaceWith("?");

        CharsetDecoder strictDecoder = StandardCharsets.UTF_8.newDecoder()
            .onMalformedInput(CodingErrorAction.REPORT);

        try {
            CharBuffer lenientResult = lenientDecoder.decode(ByteBuffer.wrap(malformed));
            System.out.println("lenient decode result: \"" + lenientResult + "\"");
        } catch (CharacterCodingException e) {
            System.out.println("lenient decode failed unexpectedly");
        }

        try {
            CharBuffer strictResult = strictDecoder.decode(ByteBuffer.wrap(malformed));
            System.out.println("strict decode result: \"" + strictResult + "\"");
        } catch (CharacterCodingException e) {
            System.out.println("strict decode correctly reported: " + e.getClass().getSimpleName());
        }
    }
}
```

**How to run:** `java CharsetMalformedSequenceHandling.java` (JDK 17+).

Expected output:
```
lenient decode result: "hi? "
strict decode correctly reported: MalformedInputException
```

The production-flavored hard case: the plain `new String(bytes, charset)` constructor used in earlier examples silently replaces malformed byte sequences with a default replacement character with no way to detect that this happened at all — using an explicit `CharsetDecoder` with `onMalformedInput` configured lets you choose deliberately between lenient handling (`REPLACE`, substituting a stand-in character, useful for best-effort text recovery) and strict handling (`REPORT`, throwing `CharacterCodingException`, useful when malformed input should be treated as a genuine, actionable error rather than silently tolerated), which matters for any application that needs to distinguish "this data might be slightly imperfect but is fine to process anyway" from "this data is corrupted and must be rejected outright."

## 6. Walkthrough

Tracing `strictDecoder.decode(ByteBuffer.wrap(malformed))` end to end:

1. `malformed` contains four bytes: `'h'`, `'i'`, `0xC3`, and `0x20` (a space) — under UTF-8's encoding rules, a byte in the range `0xC2`–`0xDF` signals the *start* of a two-byte sequence, meaning the decoder expects the very next byte to be a valid UTF-8 continuation byte (specifically in the range `0x80`–`0xBF`).
2. The decoder processes `'h'` and `'i'` normally, as ordinary single-byte ASCII characters, appending them to its output.
3. Upon encountering `0xC3`, the decoder recognizes it as the start of a two-byte sequence and looks at the next byte, `0x20`, to determine how to complete it — but `0x20` (an ordinary space character) does not fall within the valid continuation-byte range at all, meaning this two-byte sequence is genuinely malformed under UTF-8's rules.
4. Because `strictDecoder` was explicitly configured with `.onMalformedInput(CodingErrorAction.REPORT)`, the decoder does not attempt any substitution or silent recovery — instead, it throws `CharacterCodingException` (specifically, a `MalformedInputException`, a subclass) at exactly this point, reporting the malformed sequence as an error rather than continuing to process the remaining input.
5. The surrounding `try`/`catch` block catches this exception and prints `"strict decode correctly reported: MalformedInputException"` — confirming the decoder behaved exactly as configured: treating malformed input as a hard failure rather than silently tolerating or masking it.
6. Contrast this with `lenientDecoder`, configured with `.onMalformedInput(CodingErrorAction.REPLACE).replaceWith("?")` earlier: given the identical malformed byte sequence, it instead substitutes the replacement string `"?"` for the malformed two-byte sequence and continues processing, ultimately producing `"hi? "` — demonstrating that the exact same malformed input can be handled in two deliberately different, explicitly-chosen ways, depending on whether the application's requirements call for best-effort recovery or strict validation, a choice that plain `new String(bytes, charset)` never exposes or lets you control at all.

## 7. Gotchas & takeaways

> **Gotcha:** `new String(bytes)` and `new String(bytes, charset)`'s default malformed-input handling silently substitutes a replacement character for any invalid byte sequence, with absolutely no way to detect from the resulting `String` alone that this substitution occurred — if distinguishing "this data was slightly malformed and something was silently replaced" from "this data was perfectly clean" ever matters for your application (data integrity validation, security-sensitive parsing), you must use an explicit `CharsetDecoder` with `CodingErrorAction.REPORT` rather than the plain `String` constructor.

- A `Charset` defines the mapping between bytes and characters — encoding and decoding must use the *same* charset to round-trip correctly; using different charsets on either side produces silently garbled, but not exception-throwing, output.
- Always specify a charset explicitly (`StandardCharsets.UTF_8`) at every point converting between bytes and characters, rather than relying on a platform's default charset, which can vary across machines, operating systems, and JVM configurations.
- Modern JDKs (18+) default `file.encoding` to UTF-8 regardless of platform locale, substantially reducing (but not eliminating) this class of bug — explicit charset specification remains the safest, most portable habit regardless.
- `new String(bytes, charset)` silently substitutes a replacement character for malformed byte sequences by default, with no way to detect that substitution occurred from the resulting string alone.
- An explicit `CharsetDecoder` with `onMalformedInput` configured to `CodingErrorAction.REPORT` lets you treat malformed input as a genuine, catchable error instead, which matters whenever silently tolerating corrupted data is unacceptable.
- See [serialization vulnerabilities & filters](0980-serialization-vulnerabilities-filters.md) for a different, related class of pitfalls involving untrusted byte streams and how they're interpreted.
