---
card: java
gi: 305
slug: inputstreamreader-outputstreamwriter-bridge
title: InputStreamReader / OutputStreamWriter (bridge)
---

## 1. What it is

`InputStreamReader` and `OutputStreamWriter` are the explicit "bridge" classes connecting the byte-stream world (`InputStream`/`OutputStream`) to the character-stream world (`Reader`/`Writer`). `InputStreamReader` decodes bytes into characters using a specified (or default) `Charset`; `OutputStreamWriter` does the reverse, encoding characters into bytes.

```java
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.ByteArrayOutputStream;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;

public class BridgeDemo {
    public static void main(String[] args) throws IOException {
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        OutputStreamWriter writer = new OutputStreamWriter(baos, StandardCharsets.UTF_8);
        writer.write("café");
        writer.flush();

        InputStreamReader reader = new InputStreamReader(
            new ByteArrayInputStream(baos.toByteArray()), StandardCharsets.UTF_8);
        int c;
        StringBuilder sb = new StringBuilder();
        while ((c = reader.read()) != -1) sb.append((char) c);
        System.out.println(sb);
    }
}
```

`OutputStreamWriter` encodes `"café"`'s four characters as UTF-8 bytes (the accented `é` becomes two bytes, the rest one byte each); `InputStreamReader` decodes those bytes back into the original four characters, using the same charset on both ends.

## 2. Why & when

Every character-stream convenience class you've seen — `FileReader`, `FileWriter`, `PrintWriter` wrapping a socket — ultimately needs a byte-to-character (or character-to-byte) conversion somewhere, because the operating system and network only deal in bytes. `InputStreamReader`/`OutputStreamWriter` are where that conversion is made explicit and controllable.

- **Explicit charset control** — when a convenience class like `FileReader` doesn't offer the charset overload you need (or on Java versions before 11, when it offered none at all), wrapping the underlying byte stream directly with `InputStreamReader`/`OutputStreamWriter` and an explicit `Charset` is the fallback.
- **Network and non-file byte sources** — a socket's `InputStream`/`OutputStream` carries raw bytes; wrapping it in `InputStreamReader`/`OutputStreamWriter` is how you read/write text over a network connection.
- **Understanding the whole hierarchy** — recognizing that `FileReader` is essentially `InputStreamReader` plus `FileInputStream` clarifies why encoding concerns apply everywhere text meets bytes, not just for files.

Use `InputStreamReader`/`OutputStreamWriter` directly whenever your byte source isn't a file (sockets, in-memory buffers, compressed streams) but you need to read or write text from it, and always specify an explicit `Charset` rather than relying on the platform default.

## 3. Core concept

```java
import java.io.InputStreamReader;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;

public class BridgeCore {
    public static void main(String[] args) throws IOException {
        byte[] utf8Bytes = "naïve".getBytes(StandardCharsets.UTF_8);
        System.out.println("Byte count: " + utf8Bytes.length); // 6, not 5 -- ï takes 2 bytes

        InputStreamReader reader = new InputStreamReader(
            new ByteArrayInputStream(utf8Bytes), StandardCharsets.UTF_8);
        StringBuilder sb = new StringBuilder();
        int c;
        while ((c = reader.read()) != -1) sb.append((char) c);
        System.out.println("Character count: " + sb.length()); // 5, correctly decoded
    }
}
```

`"naïve".getBytes(StandardCharsets.UTF_8)` produces 6 bytes (because `ï` requires 2 bytes in UTF-8) even though the string has 5 characters; `InputStreamReader` correctly decodes those 6 bytes back into exactly 5 characters, because it understands UTF-8's variable-width encoding rules rather than treating one byte as one character.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A multi byte character is decoded from several bytes into one char by InputStreamReader according to the specified charset">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#8b949e" font-size="10">bytes:  6E 61 C3 AF 76 65   (6 bytes, UTF-8)</text>
  <rect x="20" y="45" width="30" height="30" rx="3" fill="#1c2430" stroke="#8b949e"/>
  <text x="35" y="65" fill="#e6edf3" font-size="10" text-anchor="middle">n</text>
  <rect x="55" y="45" width="30" height="30" rx="3" fill="#1c2430" stroke="#8b949e"/>
  <text x="70" y="65" fill="#e6edf3" font-size="10" text-anchor="middle">a</text>
  <rect x="90" y="45" width="60" height="30" rx="3" fill="#1c2430" stroke="#6db33f"/>
  <text x="120" y="65" fill="#6db33f" font-size="9" text-anchor="middle">C3 AF -&gt; ï</text>
  <rect x="155" y="45" width="30" height="30" rx="3" fill="#1c2430" stroke="#8b949e"/>
  <text x="170" y="65" fill="#e6edf3" font-size="10" text-anchor="middle">v</text>
  <rect x="190" y="45" width="30" height="30" rx="3" fill="#1c2430" stroke="#8b949e"/>
  <text x="205" y="65" fill="#e6edf3" font-size="10" text-anchor="middle">e</text>
  <text x="20" y="105" fill="#79c0ff" font-size="10">InputStreamReader decodes: 6 bytes -&gt; 5 chars: n a ï v e</text>
</svg>

Two bytes (`C3 AF`) decode to one character (`ï`) — byte count and character count need not match under multi-byte encodings.

## 5. Runnable example

Scenario: reading text sent over a simulated network connection, evolved from a basic byte-to-text decode into a version that reads a length-prefixed message, then into a version that correctly buffers partial multi-byte characters arriving in separate chunks.

### Level 1 — Basic

```java
import java.io.InputStreamReader;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;

public class BridgeBasic {
    public static void main(String[] args) throws IOException {
        byte[] incoming = "Hello from the network!".getBytes(StandardCharsets.UTF_8);

        InputStreamReader reader = new InputStreamReader(new ByteArrayInputStream(incoming), StandardCharsets.UTF_8);
        StringBuilder message = new StringBuilder();
        int c;
        while ((c = reader.read()) != -1) message.append((char) c);

        System.out.println("Received: " + message);
    }
}
```

**How to run:** `java BridgeBasic.java`

Simulates receiving raw bytes (as a network socket would provide) and decoding them into a readable `String` using an explicit UTF-8 charset.

### Level 2 — Intermediate

Same idea, now wrapping the `InputStreamReader` in a `BufferedReader` to read the incoming text line by line, as a real protocol handler often needs to.

```java
import java.io.InputStreamReader;
import java.io.BufferedReader;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;

public class BridgeIntermediate {
    public static void main(String[] args) throws IOException {
        byte[] incoming = "STATUS: ok\nUSER: café_lover\nDONE\n".getBytes(StandardCharsets.UTF_8);

        BufferedReader reader = new BufferedReader(
            new InputStreamReader(new ByteArrayInputStream(incoming), StandardCharsets.UTF_8));

        String line;
        while ((line = reader.readLine()) != null) {
            System.out.println("Line: " + line);
        }
    }
}
```

**How to run:** `java BridgeIntermediate.java`

`InputStreamReader` decodes the raw bytes (including the accented `é` in `"café_lover"`) into a correct character stream, which `BufferedReader` then splits into lines exactly as if the source were a file — the network origin of the bytes is irrelevant to `BufferedReader`, which is the whole point of the character-stream abstraction.

### Level 3 — Advanced

Same simulated protocol, now demonstrating a real subtlety: when bytes arrive in separate chunks (as they genuinely can over a network), a multi-byte character split across two chunks must not be decoded prematurely — handled correctly here by decoding only after all chunks are assembled into one continuous byte stream, rather than decoding each chunk independently.

```java
import java.io.*;
import java.nio.charset.StandardCharsets;

public class BridgeAdvanced {
    public static void main(String[] args) throws IOException {
        String original = "Status update: café is ready";
        byte[] fullMessage = original.getBytes(StandardCharsets.UTF_8);

        // Simulate the message arriving in two network chunks, split in the MIDDLE
        // of the multi-byte 'é' character (byte 17 splits its 2-byte UTF-8 sequence).
        byte[] chunk1 = java.util.Arrays.copyOfRange(fullMessage, 0, 17);
        byte[] chunk2 = java.util.Arrays.copyOfRange(fullMessage, 17, fullMessage.length);

        // WRONG approach (commented out) would decode each chunk separately:
        //   new String(chunk1, StandardCharsets.UTF_8) -- corrupts the split character.
        // CORRECT approach: concatenate raw bytes FIRST, decode the assembled stream once.
        ByteArrayOutputStream assembled = new ByteArrayOutputStream();
        assembled.write(chunk1);
        assembled.write(chunk2);

        InputStreamReader reader = new InputStreamReader(
            new ByteArrayInputStream(assembled.toByteArray()), StandardCharsets.UTF_8);
        StringBuilder result = new StringBuilder();
        int c;
        while ((c = reader.read()) != -1) result.append((char) c);

        System.out.println("Correctly decoded: " + result);
        System.out.println("Matches original: " + original.equals(result.toString()));
    }
}
```

**How to run:** `java BridgeAdvanced.java`

`chunk1` ends mid-way through the 2-byte UTF-8 encoding of `é` (splitting at byte index 17, inside that character's byte pair); decoding `chunk1` alone would produce a decoding error or a replacement character, since it contains an incomplete multi-byte sequence — assembling the raw bytes first, *then* decoding the complete sequence with one `InputStreamReader`, sidesteps the problem entirely because decoding only ever happens once all the relevant bytes are present.

## 6. Walkthrough

Trace `BridgeAdvanced.main` step by step.

**Setup.** `original` contains the accented character `é` (in `"café"`). `fullMessage` is its UTF-8-encoded byte form; the two bytes representing `é` sit at a specific position within this array. `chunk1` takes bytes `[0, 17)`, and `chunk2` takes the rest, `[17, end)` — index 17 falls squarely inside `é`'s 2-byte encoding, so `chunk1`'s final byte is the *first* byte of `é`, and `chunk2`'s first byte is the *second* byte of `é`.

**Why decoding `chunk1` alone would fail.** If you called `new String(chunk1, StandardCharsets.UTF_8)` directly, the decoder would encounter a byte sequence ending in an incomplete multi-byte character — UTF-8 decoders handle this by either throwing, silently dropping the byte, or substituting a replacement character (`�`), depending on the decoder's error-handling mode. Any of those outcomes corrupts the text. This is exactly the trap the comment warns about.

**The correct approach.** `assembled.write(chunk1)` followed by `assembled.write(chunk2)` concatenates the raw bytes back into one continuous, complete byte sequence — identical to `fullMessage` — **before** any decoding happens. `assembled.toByteArray()` yields exactly the original bytes, split point invisible now that they're rejoined.

**Decoding.** `new InputStreamReader(new ByteArrayInputStream(assembled.toByteArray()), StandardCharsets.UTF_8)` decodes this complete, unbroken byte sequence — the 2-byte `é` sequence is now fully present and adjacent, so it decodes correctly into the single character `é`, with no corruption at the former split point.

**Verification.** `result` accumulates every decoded character; `original.equals(result.toString())` compares the reconstructed text to the original character-for-character, confirming the round-trip succeeded despite the byte-level split.

```
fullMessage (UTF-8 bytes):  ... [byte 16] [byte 17: é part 1] | [byte 18: é part 2] [byte 19] ...
                                                                ^ split point

chunk1 = bytes[0..17)   -- ends with é's FIRST byte only (incomplete character!)
chunk2 = bytes[17..end) -- starts with é's SECOND byte

assembled = chunk1 + chunk2  =  fullMessage (byte-for-byte identical, split invisible)

decode(assembled) -> correct text, é intact
```

**Output:**
```
Correctly decoded: Status update: café is ready
Matches original: true
```

## 7. Gotchas & takeaways

> When receiving byte data in chunks (from a network socket, a chunked file read, or similar), never decode each chunk to text independently unless you know each chunk boundary falls on a character boundary — a multi-byte character can legitimately be split across chunk boundaries, and decoding chunks separately can silently corrupt exactly those characters. Buffer raw bytes and decode once the full message (or a known-safe boundary) is assembled, or use a streaming, stateful decoder (`CharsetDecoder`) designed to handle partial input across calls.

> `InputStreamReader`/`OutputStreamWriter` constructed without an explicit `Charset` argument use the JVM's platform-default encoding — exactly the same portability trap discussed for `Reader`/`Writer` and `FileReader`/`FileWriter` in general, since these bridge classes are where that default actually gets applied.

- `InputStreamReader`/`OutputStreamWriter` are the explicit bridge between byte streams and character streams, applying a `Charset` in each direction.
- A single character can be represented by multiple bytes under encodings like UTF-8 — byte count and character count are not the same thing.
- Never decode network or chunked byte data piecemeal unless chunk boundaries are guaranteed to align with character boundaries — assemble first, decode once.
- Always specify an explicit `Charset` rather than relying on the platform default, for portable, correct behavior across environments.
