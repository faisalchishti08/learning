---
card: webdev
gi: 79
slug: character-encoding-meta-charset-utf-8
title: Character encoding (meta charset utf-8)
---

## 1. What it is

**Character encoding** is the mapping between bytes on disk (or in a network response) and the characters your eyes see on screen. A browser needs to know which encoding a file uses before it can decode it correctly.

The declaration:

```html
<meta charset="UTF-8">
```

tells the browser: "this file's bytes are encoded as UTF-8." It must appear within the first 1 024 bytes of the `<head>`. Without it, the browser guesses — and guesses wrong often enough to corrupt text.

**UTF-8** is the dominant encoding of the web: it can represent every character in the Unicode standard (over 140 000 characters) — letters, digits, accented characters, Arabic, Chinese, emojis — while keeping ASCII characters (A–Z, 0–9, common punctuation) as single bytes for efficiency.

## 2. Why & when

Before Unicode, web pages used dozens of incompatible encodings: ISO-8859-1 for Western European languages, Shift-JIS for Japanese, Windows-1252 for Windows Latin, and so on. A page written in one encoding but decoded in another displayed as garbage (`Ã©` instead of `é`, `æ¼¢å­—` instead of `漢字`). This is called **mojibake** (文字化け).

UTF-8 solved this: one universal encoding, no mojibake. Today over 98% of all web pages are UTF-8.

You need `<meta charset="UTF-8">` on every HTML page you write. Skipping it means:
- Browsers fall back to a locale-dependent default (often `windows-1252` on Windows).
- Any non-ASCII characters (accents, currencies, emojis) may display incorrectly.
- Security vulnerabilities can arise — some multi-byte sequences in non-UTF-8 encodings include bytes that look like `<`, `"`, `\`, enabling XSS in poorly written parsers.

## 3. Core concept

Think of encoding like a codebook. The bytes `0x48 0x65 0x6C 0x6C 0x6F` mean "Hello" in ASCII/UTF-8 — but the same bytes mean something entirely different if the codebook is Shift-JIS. The `<meta charset>` tag hands the browser the right codebook before it reads the file.

**How UTF-8 works (simplified):**

UTF-8 is a variable-width encoding:
- Code points 0–127 (ASCII: A-Z, 0-9, punctuation) = 1 byte.
- Code points 128–2 047 (Latin accents, Arabic, etc.) = 2 bytes.
- Code points 2 048–65 535 (most of CJK, symbols) = 3 bytes.
- Code points 65 536–1 114 111 (emoji, rare scripts) = 4 bytes.

Because ASCII bytes are unchanged, a UTF-8 file containing only ASCII is byte-for-byte identical to an ASCII file. That backward compatibility is why UTF-8 won.

**Where the encoding is specified:**

1. `Content-Type` HTTP header from the server: `Content-Type: text/html; charset=utf-8` — highest priority.
2. `<meta charset="UTF-8">` in the HTML file — for files opened from disk or when the server doesn't send the header.
3. Browser default (locale-dependent) — worst fallback; avoid relying on it.

The `<meta charset>` and the actual file encoding must agree. Saving a file as UTF-8 but declaring `charset=ISO-8859-1` is just as wrong as the reverse.

**HTML entities** are an alternative for individual characters — `&amp;` = `&`, `&lt;` = `<`, `&copy;` = `©` — but with UTF-8 you can type the characters directly. You only need entities for the four characters that have special meaning in HTML: `<`, `>`, `&`, and `"` (inside attribute values).

## 4. Diagram

<svg viewBox="0 0 620 250" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Flow from file bytes through charset declaration to correct characters on screen, vs corrupted output without declaration">
  <defs>
    <marker id="arr79g" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L5,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="arr79r" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L5,3 L0,6 Z" fill="#f85149"/></marker>
  </defs>

  <!-- Bytes box -->
  <rect x="10" y="40" width="140" height="80" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="80" y="65" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">File bytes</text>
  <text x="80" y="83" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">C3 A9 = é</text>
  <text x="80" y="99" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">E4 B8 AD = 中</text>

  <!-- With charset -->
  <rect x="200" y="20" width="160" height="60" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.2"/>
  <text x="280" y="44" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">meta charset=UTF-8</text>
  <text x="280" y="62" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">correct codebook</text>

  <line x1="152" y1="60" x2="198" y2="50" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr79g)"/>

  <rect x="400" y="20" width="200" height="60" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="500" y="44" fill="#6db33f" font-size="13" text-anchor="middle" font-family="sans-serif">é  中  😀</text>
  <text x="500" y="62" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">✓ correct characters</text>
  <line x1="362" y1="50" x2="398" y2="50" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr79g)"/>

  <!-- Without charset -->
  <rect x="200" y="115" width="160" height="60" rx="5" fill="#1c2430" stroke="#f85149" stroke-width="1.2"/>
  <text x="280" y="139" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">no charset declared</text>
  <text x="280" y="157" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">browser guesses (win-1252)</text>

  <line x1="152" y1="100" x2="198" y2="145" stroke="#f85149" stroke-width="1.5" marker-end="url(#arr79r)"/>

  <rect x="400" y="115" width="200" height="60" rx="5" fill="#0d1117" stroke="#f85149" stroke-width="1.5"/>
  <text x="500" y="139" fill="#f85149" font-size="13" text-anchor="middle" font-family="sans-serif">Ã©  ä¸­  ð</text>
  <text x="500" y="157" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">✗ mojibake (garbled text)</text>
  <line x1="362" y1="145" x2="398" y2="145" stroke="#f85149" stroke-width="1.5" marker-end="url(#arr79r)"/>

  <text x="310" y="220" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Same bytes, different codebook → different characters</text>
</svg>

UTF-8 bytes decoded with the wrong codebook produce mojibake; `<meta charset="UTF-8">` prevents that.

## 5. Runnable example

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Character Encoding</title>
</head>
<body>
  <h1>UTF-8 Characters</h1>

  <!-- All these characters work fine in UTF-8 -->
  <p>Accented: café, naïve, résumé, jalapeño</p>
  <p>Currency: €, £, ¥, ₹, ₿</p>
  <p>CJK: 你好, こんにちは, 안녕하세요</p>
  <p>Emoji: 😀 🎉 🌍 ✅</p>
  <p>Math: π ≈ 3.14159, ∑, √2 ≈ 1.414</p>

  <!-- HTML entities for special HTML characters -->
  <p>Entities: &lt;tag&gt;, &amp;amp;, &copy; 2025, &trade;</p>

  <script>
    // UTF-8 byte lengths in JavaScript (which uses UTF-16 internally)
    const str = "café";
    console.log(str.length);                            // 4 (JS counts UTF-16 code units)
    console.log(new TextEncoder().encode(str).length);  // 5 (UTF-8 bytes: é = 2 bytes)

    // The TextEncoder API encodes strings to UTF-8 bytes
    const encoder = new TextEncoder();
    const bytes = encoder.encode("é");
    console.log([...bytes].map(b => b.toString(16)));  // ["c3", "a9"]

    // TextDecoder decodes UTF-8 bytes back to a string
    const decoder = new TextDecoder("utf-8");
    console.log(decoder.decode(new Uint8Array([0xc3, 0xa9]))); // "é"
  </script>
</body>
</html>
```

**How to run:** save as `charset.html` **in UTF-8 encoding** (most editors do this by default; check your editor's "Save with encoding" option). Open in a browser. All characters should render correctly.

## 6. Walkthrough

- `<meta charset="UTF-8">` — early in `<head>`. The browser reads this before processing the rest of the file. If it's after a large block of content, the browser may have already decoded part of the file with the wrong encoding.
- The accented, CJK, emoji, and math characters in the `<p>` tags are stored as multi-byte UTF-8 sequences in the file. The browser decodes them into the correct Unicode code points using the UTF-8 table.
- `new TextEncoder().encode("café").length` is 5, not 4 — `é` is U+00E9, which in UTF-8 is two bytes (`0xC3 0xA9`). JavaScript's `.length` counts UTF-16 code units (internal format), not UTF-8 bytes.
- `[...bytes].map(b => b.toString(16))` converts the raw byte values to hex to show what's actually stored in the file: `é` → `c3 a9`.
- `TextDecoder("utf-8")` reverses the process. These APIs are useful when working with binary data, file uploads, or WebSockets.

## 7. Gotchas & takeaways

> **The file must actually be saved as UTF-8.** Declaring `charset="UTF-8"` in a file saved as `windows-1252` still breaks non-ASCII characters. The declaration and the file's actual encoding must match. Modern editors (VS Code, Sublime, JetBrains) default to UTF-8; check if you're on a legacy system.

> **The HTTP `Content-Type` header beats the `<meta>` tag.** If the server sends `Content-Type: text/html; charset=iso-8859-1`, the browser ignores your `<meta charset="UTF-8">`. Fix the server response, not just the HTML.

> **JavaScript string `.length` ≠ UTF-8 byte count.** JS uses UTF-16 internally. Emojis are 2 UTF-16 code units (`.length` = 2) but 4 UTF-8 bytes. Use `TextEncoder` for accurate byte counts.

- Every HTML page needs `<meta charset="UTF-8">` in the first 1 024 bytes of `<head>`.
- Save files as UTF-8 (virtually every modern editor does this by default).
- UTF-8 covers every Unicode character — no need for other encodings on the web.
- Entities (`&lt;`, `&amp;`, `&copy;`) are needed only for `<`, `>`, `&`, and `"` in HTML context.
- `TextEncoder`/`TextDecoder` are the JS APIs for converting between strings and UTF-8 bytes.
