---
card: spring-cloud
gi: 65
slug: request-response-compression
title: "Request/response compression"
---

## 1. What it is

Feign can compress outgoing request bodies and accept compressed response bodies, reducing bytes transferred over the network for calls carrying non-trivial payloads — configured via `feign.compression.request.enabled` and `feign.compression.response.enabled`, with tunable minimum size thresholds and MIME types.

```properties
feign.compression.request.enabled=true
feign.compression.request.mime-types=application/json,application/xml
feign.compression.request.min-request-size=2048

feign.compression.response.enabled=true
```

## 2. Why & when

Compression trades CPU time (compressing and decompressing) for reduced network transfer time and bandwidth — a good trade when payloads are large enough that the transfer savings outweigh the compression overhead, and a bad trade for small payloads where the compression overhead itself dominates. The `min-request-size` threshold exists specifically to avoid compressing tiny requests where doing so would add CPU cost for negligible (or even negative) network benefit.

Reach for compression when:

- Feign calls regularly carry large JSON/XML payloads (bulk data exports, large object graphs) where the byte-size reduction from compression is substantial.
- Network bandwidth between services is a genuine, measured constraint — cross-region calls, or calls over a link with real bandwidth limits — where reducing transferred bytes measurably improves latency or cost.
- CPU headroom exists on both ends to absorb the compression/decompression cost — on CPU-constrained services, compression can shift the bottleneck from network to CPU rather than genuinely improving overall performance.

## 3. Core concept

```
 request.size < min-request-size  -> sent uncompressed (compression overhead not worth it)
 request.size >= min-request-size -> compressed before sending, IF mime-type matches configured list

 response: if the server sends a compressed body (Content-Encoding: gzip),
           Feign decompresses it transparently before handing it to the Decoder
```

Compression is applied selectively — by size threshold and MIME type — not blanket-applied to every request regardless of its characteristics.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A small request below the size threshold is sent uncompressed while a large request above the threshold is compressed before sending, trading CPU time for reduced network bytes">
  <rect x="20" y="20" width="270" height="70" rx="10" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="155" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">small request (&lt; min-request-size)</text>
  <text x="155" y="60" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">sent uncompressed</text>
  <text x="155" y="74" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">compression overhead not worth it</text>

  <rect x="340" y="20" width="280" height="70" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="42" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">large request (&gt;= min-request-size)</text>
  <text x="480" y="60" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">compressed before sending</text>
  <text x="480" y="74" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">fewer bytes over the wire</text>

  <text x="320" y="130" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">the size threshold decides which tradeoff applies to each individual request</text>

  <defs><marker id="a65" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The threshold is what makes compression a net win overall — applying it unconditionally to every request would waste CPU on payloads too small to benefit.

## 5. Runnable example

The scenario: decide whether to compress outgoing Feign requests to `billing-service` based on payload size. Start with unconditional (always-on) compression, then add the size-threshold decision, then measure the actual net effect across a batch of requests with mixed sizes.

### Level 1 — Basic

Unconditional compression — the naive baseline this feature improves on.

```java
public class CompressionLevel1 {
    static int compress(String payload) {
        // stands in for real gzip compression -- roughly models compression ratio and per-call overhead
        int compressedSize = Math.max(20, payload.length() / 3); // ~3:1 ratio for typical JSON, plus fixed overhead
        return compressedSize;
    }

    public static void main(String[] args) {
        String tinyPayload = "{}"; // 2 bytes
        int compressed = compress(tinyPayload);
        System.out.println("original: " + tinyPayload.length() + " bytes, compressed: " + compressed + " bytes");
        // compressed is LARGER than original for tiny payloads -- pure overhead, no benefit
    }
}
```

How to run: `java CompressionLevel1.java`

For a tiny 2-byte payload, the simulated compressed size (with its fixed overhead) ends up larger than the original — unconditionally compressing everything can genuinely make small requests worse, not better.

### Level 2 — Intermediate

Add the size-threshold decision: only compress when the payload is large enough for compression to plausibly help.

```java
public class CompressionLevel2 {
    static int minRequestSize = 2048;

    static int compress(String payload) {
        return Math.max(20, payload.length() / 3);
    }

    static String sendRequest(String payload) {
        if (payload.length() >= minRequestSize) {
            int compressedSize = compress(payload);
            return "sent COMPRESSED: " + payload.length() + " -> " + compressedSize + " bytes";
        }
        return "sent UNCOMPRESSED: " + payload.length() + " bytes";
    }

    public static void main(String[] args) {
        String tinyPayload = "{\"id\":\"42\"}"; // small
        String largePayload = "{\"items\":[" + "\"item\",".repeat(500) + "]}"; // large, repetitive JSON

        System.out.println(sendRequest(tinyPayload));
        System.out.println(sendRequest(largePayload));
    }
}
```

How to run: `java CompressionLevel2.java`

`sendRequest` only compresses when `payload.length() >= minRequestSize` — the tiny payload is sent as-is, avoiding pointless overhead, while the large, repetitive payload (which compresses well, being highly repetitive JSON) is compressed, genuinely reducing the bytes actually sent over the network.

### Level 3 — Advanced

Measure the actual net effect across a batch of requests with mixed sizes, confirming the threshold-based approach outperforms both "never compress" and "always compress" in total bytes transferred.

```java
import java.util.*;

public class CompressionLevel3 {
    static int minRequestSize = 2048;

    static int compressedSize(String payload) {
        return Math.max(20, payload.length() / 3);
    }

    static int neverCompress(List<String> payloads) {
        return payloads.stream().mapToInt(String::length).sum();
    }

    static int alwaysCompress(List<String> payloads) {
        return payloads.stream().mapToInt(CompressionLevel3::compressedSize).sum();
    }

    static int thresholdCompress(List<String> payloads) {
        return payloads.stream().mapToInt(p ->
                p.length() >= minRequestSize ? compressedSize(p) : p.length()
        ).sum();
    }

    public static void main(String[] args) {
        List<String> payloads = List.of(
                "{}",                                    // tiny
                "{\"id\":\"42\"}",                        // small
                "{\"items\":[" + "\"x\",".repeat(1000) + "]}" // large
        );

        System.out.println("never compress:     " + neverCompress(payloads) + " bytes total");
        System.out.println("always compress:    " + alwaysCompress(payloads) + " bytes total");
        System.out.println("threshold compress:  " + thresholdCompress(payloads) + " bytes total");
    }
}
```

How to run: `java CompressionLevel3.java`

`neverCompress` sends every payload at full size, including the large one, which wastes the most bandwidth. `alwaysCompress` compresses everything, including the two tiny payloads, adding needless overhead to them even though the large payload benefits substantially. `thresholdCompress` gets the best of both: it leaves the two small payloads uncompressed (avoiding their overhead) while still compressing the large one (capturing its real savings) — producing the lowest total byte count of the three strategies.

## 6. Walkthrough

Trace `thresholdCompress`'s computation in Level 3.

1. For `"{}"` (length `2`), `p.length() >= minRequestSize` evaluates `2 >= 2048`, which is `false` — the ternary returns `p.length()` directly, contributing `2` bytes uncompressed to the running sum.
2. For `"{\"id\":\"42\"}"` (length `12`), the same check `12 >= 2048` is `false` — again sent uncompressed, contributing `12` bytes.
3. For the large payload (roughly `5000+` characters, built from `"x",` repeated 1000 times plus wrapping), the check `length >= 2048` is `true` — the ternary calls `compressedSize(p)`, which computes `Math.max(20, length / 3)`, contributing roughly a third of the original size instead of the full amount.
4. The `mapToInt(...).sum()` call adds these three contributions together — the two tiny payloads contribute their full, uncompressed size (since compressing them wasn't worth it), while the large payload contributes only its much-reduced compressed size.
5. Comparing all three totals: `neverCompress` pays the large payload's full size; `alwaysCompress` pays a small, wasted overhead penalty on the two tiny payloads on top of correctly compressing the large one; `thresholdCompress` achieves the same large-payload savings as `alwaysCompress` without paying the small-payload penalty, landing on the lowest total.

```
payload sizes:  tiny(2) + small(12) + large(~5000+)

neverCompress:      2 + 12 + 5000   = ~5014 bytes  (large payload sent uncompressed -- worst case)
alwaysCompress:      ~20 + ~20 + ~1667 = ~1707 bytes (tiny payloads pay overhead, but small anyway)
thresholdCompress:   2 + 12 + ~1667  = ~1681 bytes  (best of both: no waste on tiny, full savings on large)
```

## 7. Gotchas & takeaways

> **Gotcha:** compression only helps for payloads that actually compress well — highly repetitive text (JSON with repeated field names/values) compresses very effectively, but already-compressed or high-entropy binary data (images, encrypted blobs, pre-compressed archives) barely shrinks at all and can even grow slightly from compression overhead, regardless of size. The `mime-types` configuration exists specifically to exclude content types that wouldn't benefit, alongside the size threshold.

- Compression is a CPU-for-bandwidth tradeoff, and it's only a net win above some payload size where the transfer savings exceed the compression overhead — that's exactly what `min-request-size` is tuned to approximate.
- Response compression (server sends `Content-Encoding: gzip`, Feign decompresses transparently) is a separate, independent setting from request compression — a client can enable one without the other, depending on which direction of traffic actually carries the larger payloads.
- Compression is most valuable for calls carrying large, text-based, repetitive payloads (JSON, XML) — it's much less relevant for calls that are mostly small, tightly-shaped requests (most typical CRUD operations), where the size threshold correctly means compression rarely even activates.
- When network bandwidth genuinely isn't a bottleneck (same-datacenter, high-bandwidth internal links), the CPU cost of compression may not be worth paying at all — this is a workload-specific tuning decision, not a default that's automatically beneficial everywhere.
