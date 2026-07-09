---
card: java
gi: 558
slug: java-util-base64
title: java.util.Base64
---

## 1. What it is

`java.util.Base64` is Java 8's built-in encoder/decoder for **Base64**, a scheme that represents arbitrary binary data (bytes) using only 64 printable ASCII characters (`A-Z`, `a-z`, `0-9`, `+`, `/`, and `=` for padding). It gives you `Encoder`/`Decoder` objects via static factory methods, replacing the third-party libraries (Apache Commons Codec, `sun.misc.BASE64Encoder`) that everyone used before this was part of the standard library.

## 2. Why & when

Many systems only safely transport or store *text*: email bodies, URLs, JSON fields, XML attributes, HTTP headers like `Authorization: Basic ...`. Binary data — an image, an encrypted key, a serialized object — can contain byte values that break those text-oriented formats. Base64 encoding maps binary bytes to a safe subset of ASCII so the data can travel through text-only channels intact, at the cost of about 33% size overhead. You reach for `Base64` whenever you need to embed binary in JSON/XML, build HTTP Basic Auth headers, or store binary blobs in a system that only accepts text.

## 3. Core concept

```java
import java.util.Base64;

byte[] original = "Hello, Base64!".getBytes();

String encoded = Base64.getEncoder().encodeToString(original);
System.out.println(encoded); // SGVsbG8sIEJhc2U2NCE=

byte[] decoded = Base64.getDecoder().decode(encoded);
System.out.println(new String(decoded)); // Hello, Base64!
```

`Base64.getEncoder()` and `Base64.getDecoder()` return stateless, thread-safe singletons — no `new Base64()` constructor is used. Three flavors exist: `getEncoder()`/`getDecoder()` (standard Base64), `getUrlEncoder()`/`getUrlDecoder()` (URL-and-filename-safe alphabet, swapping `+`/`/` for `-`/`_`), and `getMimeEncoder()`/`getMimeDecoder()` (inserts line breaks per MIME requirements).

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Base64 maps arbitrary bytes to a safe subset of printable ASCII characters">
  <rect x="8" y="15" width="280" height="50" rx="8" fill="#1c2430" stroke="#f85149"/>
  <text x="148" y="38" fill="#f85149" font-size="12" text-anchor="middle" font-family="sans-serif">binary bytes</text>
  <text x="148" y="55" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">may contain any byte value</text>

  <line x1="300" y1="40" x2="360" y2="40" stroke="#6db33f" stroke-width="2" marker-end="url(#a1)"/>
  <text x="330" y="30" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">encode</text>

  <rect x="360" y="15" width="270" height="50" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="495" y="38" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Base64 text</text>
  <text x="495" y="55" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">only A-Z a-z 0-9 + / =</text>

  <line x1="360" y1="90" x2="300" y2="90" stroke="#79c0ff" stroke-width="2" marker-end="url(#a2)"/>
  <text x="330" y="80" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">decode</text>
  <text x="8" y="120" fill="#8b949e" font-size="10" font-family="sans-serif">Encoded text is ~33% larger than the original bytes but safe for any text-only channel.</text>

  <defs>
    <marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="a2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Encoding and decoding are exact inverses: decoding an encoded string always reproduces the original bytes.

## 5. Runnable example

Scenario: sending a small binary attachment (simulated as raw bytes) inside a JSON-like text payload — starting with basic encode/decode round-tripping, then handling the URL-safe alphabet for use in a query string, then building a self-contained "envelope" that stores a filename and Base64 payload together and validates it round-trips correctly.

### Level 1 — Basic

```java
import java.util.Base64;
import java.nio.charset.StandardCharsets;

public class Base64Basic {
    public static void main(String[] args) {
        byte[] fileBytes = "attachment contents (pretend this is binary)".getBytes(StandardCharsets.UTF_8);

        String encoded = Base64.getEncoder().encodeToString(fileBytes);
        System.out.println("Encoded: " + encoded);

        byte[] decoded = Base64.getDecoder().decode(encoded);
        System.out.println("Decoded: " + new String(decoded, StandardCharsets.UTF_8));
    }
}
```

**How to run:** `java Base64Basic.java`

Expected output:
```
Encoded: YXR0YWNobWVudCBjb250ZW50cyAocHJldGVuZCB0aGlzIGlzIGJpbmFyeSk=
Decoded: attachment contents (pretend this is binary)
```

`Base64.getEncoder().encodeToString(fileBytes)` turns the raw bytes into a printable string using only the standard 64-character alphabet plus `=` padding. `Base64.getDecoder().decode(encoded)` reverses that exactly, returning the original byte array — reconstructing the original text confirms no data was lost in the round trip.

### Level 2 — Intermediate

```java
import java.util.Base64;
import java.nio.charset.StandardCharsets;

public class Base64UrlSafe {
    public static void main(String[] args) {
        byte[] tokenBytes = { (byte) 0xFB, (byte) 0xEF, 0x00, 0x3F, (byte) 0xC1 };

        String standard = Base64.getEncoder().encodeToString(tokenBytes);
        String urlSafe = Base64.getUrlEncoder().withoutPadding().encodeToString(tokenBytes);

        System.out.println("Standard: " + standard);
        System.out.println("URL-safe: " + urlSafe);

        String query = "https://example.com/verify?token=" + urlSafe;
        System.out.println("Query:    " + query);
    }
}
```

**How to run:** `java Base64UrlSafe.java`

Expected output:
```
Standard: ++8AP8E=
URL-safe: --8AP8E
Query:    https://example.com/verify?token=--8AP8E
```

The real-world concern this adds: standard Base64 uses `+` and `/`, both of which have special meaning inside a URL query string (`+` means space, `/` is a path separator) and would need percent-encoding. `Base64.getUrlEncoder()` swaps those two characters for `-` and `_`, which are already URL-safe, so the token can be embedded directly. `.withoutPadding()` additionally strips trailing `=` characters, which are unnecessary in many token formats and can also cause issues in some URL contexts.

### Level 3 — Advanced

```java
import java.util.Base64;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;

public class Base64Envelope {
    record Envelope(String filename, String base64Payload) {
        String render() {
            return "{\"filename\":\"" + filename + "\",\"payload\":\"" + base64Payload + "\"}";
        }
    }

    static Envelope wrap(String filename, byte[] contents) {
        String encoded = Base64.getEncoder().encodeToString(contents);
        return new Envelope(filename, encoded);
    }

    static byte[] unwrap(Envelope envelope) {
        return Base64.getDecoder().decode(envelope.base64Payload());
    }

    public static void main(String[] args) {
        byte[] original = "final production payload — could be any bytes".getBytes(StandardCharsets.UTF_8);

        Envelope sent = wrap("report.txt", original);
        System.out.println("Wire format: " + sent.render());

        // Simulate receiving the envelope elsewhere and unwrapping it.
        byte[] received = unwrap(sent);
        boolean matches = Arrays.equals(original, received);

        System.out.println("Round-trip matches original: " + matches);
        System.out.println("Recovered text: " + new String(received, StandardCharsets.UTF_8));
    }
}
```

**How to run:** `java Base64Envelope.java`

Expected output:
```
Wire format: {"filename":"report.txt","payload":"ZmluYWwgcHJvZHVjdGlvbiBwYXlsb2FkIOKAlCBjb3VsZCBiZSBhbnkgYnl0ZXM="}
Round-trip matches original: true
Recovered text: final production payload — could be any bytes
```

This wraps the raw encode/decode calls in a small `Envelope` abstraction that mirrors how binary attachments are actually transmitted inside JSON APIs: pair a filename (or content-type, or any metadata) with a Base64-encoded payload string, and validate the round trip with `Arrays.equals(...)` on the byte arrays — exactly the kind of check a test or a receiving service would perform to confirm no corruption occurred in transit.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `original` is a UTF-8 byte array for the string `"final production payload — could be any bytes"` (the em dash is a multi-byte UTF-8 sequence, exercising non-ASCII content).

`wrap("report.txt", original)` is called. Inside, `Base64.getEncoder().encodeToString(original)` converts every 3 raw bytes into 4 Base64 characters (padding the final group with `=` if needed), producing the long `ZmluYWwg...` string. A new `Envelope` record is constructed holding `filename = "report.txt"` and `base64Payload` set to that encoded string.

```
raw bytes (partial):        "fin" = [0x66, 0x69, 0x6E], "al " = [0x61, 0x6C, 0x20], ...
Base64 groups (3 bytes -> 4 chars each):
  "fin" -> "Zmlu"
  "al " -> "YWwg"
  ...
result so far: "ZmluYWwg..." (matches the start of the full encoded string)
```

`sent.render()` builds a JSON-shaped string embedding `filename` and `base64Payload` as string fields — this is the "wire format" that would actually be sent over HTTP or written to a file; `main` prints it.

Next, `unwrap(sent)` simulates the receiving side: it reads `sent.base64Payload()` and calls `Base64.getDecoder().decode(...)`, which reverses the encoding exactly, reconstructing the original byte array bit-for-bit — this is `received`.

`Arrays.equals(original, received)` compares the two byte arrays element-by-element; since Base64 encode/decode is a lossless, exact inverse pair, this evaluates to `true`. Finally, `new String(received, StandardCharsets.UTF_8)` decodes the bytes back to readable text using the same charset that was used to produce them, printing the original sentence unchanged — including the em dash, proving multi-byte UTF-8 sequences survive the Base64 round trip intact.

## 7. Gotchas & takeaways

> Base64 is **encoding, not encryption**. Anyone can decode a Base64 string back to the original bytes with one line of code (`Base64.getDecoder().decode(...)`) — it provides zero confidentiality. Never use Base64 alone to "hide" passwords, secrets, or sensitive data; use it only to make binary data safe to transmit as text, and encrypt separately if secrecy is required.

- Always specify a charset explicitly (e.g., `StandardCharsets.UTF_8`) when converting between `String` and `byte[]` around Base64 calls — relying on the platform default charset makes behavior environment-dependent.
- Use `getUrlEncoder()`/`getUrlDecoder()` for anything embedded in a URL or filename, since standard Base64's `+` and `/` characters are not URL-safe.
- `.withoutPadding()` on an encoder strips trailing `=` characters — useful for tokens, but only safe if the decoder side doesn't require padding to determine length (Java's decoder handles unpadded input fine).
- Base64-encoded output is always about 33% larger than the original binary data — factor that into size limits (e.g., HTTP header size limits) when embedding large payloads.
- `getMimeEncoder()` inserts CRLF line breaks every 76 characters per the MIME spec — needed for email attachments, but usually wrong for JSON/URL use, where any embedded line break would corrupt the surrounding format.
