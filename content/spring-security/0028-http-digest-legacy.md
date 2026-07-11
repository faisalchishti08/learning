---
card: spring-security
gi: 28
slug: http-digest-legacy
title: "HTTP Digest (legacy)"
---

## 1. What it is

HTTP Digest authentication (RFC 2617/7616) is an older scheme designed to improve on Basic's biggest weakness — sending a plaintext-recoverable password on every request — by having the client hash the password together with a server-supplied `nonce` (a one-time random value) and other request details, so the actual password is never transmitted at all, only a digest that's useless to a network eavesdropper without also knowing the password. Spring Security's Digest support (`DigestAuthenticationFilter`) is deprecated and has been removed from current versions, kept here only as historical context for why it existed and why it was abandoned in favor of TLS-protected Basic or Bearer tokens.

```
 (conceptual, no longer implemented in current Spring Security)
 client computes: HA1 = MD5(username:realm:password)
                  HA2 = MD5(method:requestURI)
                  response = MD5(HA1:nonce:nonceCount:clientNonce:qop:HA2)
 Authorization: Digest username="alice", realm="MyApp", nonce="...", uri="/api", response="...", qop=auth, nc=..., cnonce="..."
```

## 2. Why & when

Digest's core motivation — avoid transmitting the password itself, even in a form recoverable by a passive network observer — mattered enormously in an era where much web traffic ran over plain, unencrypted HTTP. Once TLS became the default expectation for any application handling credentials, Digest's advantage over Basic largely evaporated: with a TLS-encrypted connection, Basic's plaintext-recoverable header is already protected in transit, and Digest's added complexity (managing nonces, replay-attack windows, weaker password-hashing choices like MD5 that are no longer considered strong) stopped paying for itself. Spring Security deprecated and eventually removed Digest support for exactly this reason — modern guidance is to use HTTP Basic (only ever over TLS) or, more commonly today, bearer tokens (OAuth2/JWT) instead.

Reach for understanding HTTP Digest (historically) when:

- Encountering legacy systems, documentation, or exam material that still reference it, to understand why it existed and its relationship to Basic authentication.
- Explaining to a colleague why "just use Digest, it's more secure than Basic" is outdated advice — the answer is that TLS obsoleted its main advantage, while its own weaknesses (MD5-based hashing, nonce management complexity) never disappeared.
- Never reach for it when building a *new* system — it is removed from current Spring Security, and even where technically available via other stacks, current guidance uniformly prefers TLS-protected Basic or bearer-token schemes.

## 3. Core concept

```
 HTTP BASIC:              password sent (base64-encoded, NOT encrypted) on every request
                          relies ENTIRELY on TLS to protect it in transit

 HTTP DIGEST:             password NEVER sent -- only a hash involving a server nonce is sent
                          designed to be safe-ish even WITHOUT TLS

 with TLS universally assumed today:
   Basic's "weakness" (password sent) is already mitigated by the TLS tunnel itself
   Digest's "advantage" no longer matters, while its OWN weaknesses (MD5, nonce complexity) remain
   -> industry and Spring Security moved on to Basic (over TLS) or bearer tokens instead
```

Digest solved a problem (protecting credentials without TLS) that the industry ultimately solved a different, more general way (making TLS ubiquitous instead).

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A timeline showing HTTP Digest's design goal of protecting passwords without TLS becoming obsolete once TLS became the universal default leading Spring Security to deprecate and remove Digest support in favor of TLS protected Basic authentication or bearer tokens">
  <rect x="15" y="60" width="180" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="105" y="80" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">HTTP Digest designed</text>
  <text x="105" y="93" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">(protect password w/o TLS)</text>

  <rect x="230" y="60" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="320" y="80" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">TLS becomes universal</text>
  <text x="320" y="93" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">Digest's advantage evaporates</text>

  <rect x="445" y="60" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="535" y="80" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">Digest deprecated/removed</text>
  <text x="535" y="93" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">Basic (TLS) or tokens instead</text>

  <defs><marker id="a28" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="195" y1="85" x2="230" y2="85" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a28)"/>
  <line x1="410" y1="85" x2="445" y2="85" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a28)"/>
</svg>

Not a technical failure of Digest itself so much as the surrounding ecosystem changing enough to make its trade-offs no longer worthwhile.

## 5. Runnable example

The scenario: model Digest's core hash-based verification (without ever transmitting the raw password) purely to make the mechanism concrete, then show why a replayed request with a reused nonce must be rejected, then contrast the equivalent security outcome achieved simply by running Basic over a "TLS-protected" channel — the actual, modern resolution to the problem Digest was trying to solve.

### Level 1 — Basic

A simplified Digest-style check: the server never receives the raw password, only a hash combining it with a nonce.

```java
import java.security.MessageDigest;
import java.util.*;

public class HttpDigestLevel1 {
    static String md5(String input) {
        try {
            byte[] digest = MessageDigest.getInstance("MD5").digest(input.getBytes());
            return HexFormat.of().formatHex(digest);
        } catch (Exception e) { throw new RuntimeException(e); }
    }

    static Map<String, String> storedPasswords = Map.of("alice", "hunter2");

    // CLIENT SIDE: computes a response hash, never sends the raw password itself
    static String clientComputeDigestResponse(String username, String rawPassword, String nonce) {
        String ha1 = md5(username + ":MyApp:" + rawPassword);
        return md5(ha1 + ":" + nonce);
    }

    // SERVER SIDE: recomputes the SAME hash using its OWN stored password, compares
    static boolean serverVerify(String username, String claimedResponse, String nonce) {
        String storedPassword = storedPasswords.get(username);
        if (storedPassword == null) return false;
        String expectedHa1 = md5(username + ":MyApp:" + storedPassword);
        String expectedResponse = md5(expectedHa1 + ":" + nonce);
        return expectedResponse.equals(claimedResponse);
    }

    public static void main(String[] args) {
        String nonce = "server-generated-nonce-001";
        String clientResponse = clientComputeDigestResponse("alice", "hunter2", nonce);
        System.out.println("client sends response hash (NOT the password): " + clientResponse);
        System.out.println("server verifies: " + serverVerify("alice", clientResponse, nonce));
    }
}
```

How to run: `java HttpDigestLevel1.java`

`clientComputeDigestResponse` never transmits `"hunter2"` itself — only a hash derived from it and the server's `nonce`; `serverVerify` independently recomputes the identical hash using its own stored password and the same nonce, confirming a match without either side ever sending the plaintext password over the network.

### Level 2 — Intermediate

Add nonce tracking, demonstrating why a captured-and-replayed response hash must be rejected on reuse — the core defense a nonce provides.

```java
import java.security.MessageDigest;
import java.util.*;

public class HttpDigestLevel2 {
    static String md5(String input) {
        try {
            byte[] digest = MessageDigest.getInstance("MD5").digest(input.getBytes());
            return HexFormat.of().formatHex(digest);
        } catch (Exception e) { throw new RuntimeException(e); }
    }

    static Map<String, String> storedPasswords = Map.of("alice", "hunter2");
    static Set<String> usedNonces = new HashSet<>(); // tracks nonces ALREADY consumed

    static String clientComputeDigestResponse(String username, String rawPassword, String nonce) {
        String ha1 = md5(username + ":MyApp:" + rawPassword);
        return md5(ha1 + ":" + nonce);
    }

    static String serverVerify(String username, String claimedResponse, String nonce) {
        if (usedNonces.contains(nonce)) {
            return "REJECTED: nonce already used (likely a replayed request)";
        }
        String storedPassword = storedPasswords.get(username);
        String expectedHa1 = md5(username + ":MyApp:" + storedPassword);
        String expectedResponse = md5(expectedHa1 + ":" + nonce);
        if (!expectedResponse.equals(claimedResponse)) return "REJECTED: response hash mismatch";
        usedNonces.add(nonce); // consumed -- can NEVER be reused
        return "ACCEPTED";
    }

    public static void main(String[] args) {
        String nonce = "server-generated-nonce-001";
        String response = clientComputeDigestResponse("alice", "hunter2", nonce);

        System.out.println("first use of this response+nonce: " + serverVerify("alice", response, nonce));
        System.out.println("attacker REPLAYS the SAME captured response+nonce: " + serverVerify("alice", response, nonce));
    }
}
```

How to run: `java HttpDigestLevel2.java`

The first `serverVerify` call succeeds and marks the `nonce` as used; an attacker who captured that exact request (response hash and nonce together) and replays it verbatim is rejected on the second call, purely because `usedNonces.contains(nonce)` is now `true` — this replay protection is the second major property Digest aimed to provide, beyond simply not transmitting the raw password.

### Level 3 — Advanced

Contrast Digest's approach with the actual modern resolution: Basic authentication running over a channel modeled as TLS-protected, achieving an equivalent confidentiality guarantee with far less mechanism, which is why Spring Security deprecated Digest rather than continuing to maintain it.

```java
import java.util.*;

public class HttpDigestLevel3 {
    record Channel(String protocol, boolean encrypted) {}

    static Map<String, String> storedPasswords = Map.of("alice", "hunter2");

    // models an eavesdropper's view of the wire -- what they ACTUALLY see, given the channel
    static String whatEavesdropperSees(Channel channel, String rawAuthorizationHeaderValue) {
        if (channel.encrypted()) {
            return "<TLS-encrypted bytes, unreadable without the session key>";
        }
        return rawAuthorizationHeaderValue; // plain HTTP: eavesdropper sees EXACTLY this
    }

    public static void main(String[] args) {
        String basicHeader = "Basic " + Base64.getEncoder().encodeToString("alice:hunter2".getBytes());

        Channel plainHttp = new Channel("HTTP", false);
        Channel tlsHttp = new Channel("HTTPS", true);

        System.out.println("Basic over plain HTTP,  eavesdropper sees: " + whatEavesdropperSees(plainHttp, basicHeader));
        System.out.println("Basic over TLS (HTTPS), eavesdropper sees: " + whatEavesdropperSees(tlsHttp, basicHeader));

        System.out.println();
        System.out.println("conclusion: Digest's password-hiding trick becomes UNNECESSARY once the channel itself");
        System.out.println("is encrypted -- which is why Spring Security deprecated Digest rather than keep maintaining");
        System.out.println("a more complex mechanism (MD5-based, nonce-managed) solving a problem TLS already solves.");
    }
}
```

How to run: `java HttpDigestLevel3.java`

Over plain HTTP, `whatEavesdropperSees` returns the *exact* Basic header, trivially base64-decodable to recover `"alice:hunter2"` — the scenario Digest was designed to prevent; over TLS, the same Basic header is returned as unreadable encrypted bytes, achieving the identical confidentiality outcome Digest aimed for, but via the transport layer rather than via a more complex application-layer hashing scheme.

## 6. Walkthrough

Trace Level 3's two `whatEavesdropperSees` calls in order.

1. `whatEavesdropperSees(plainHttp, basicHeader)` runs first — `plainHttp.encrypted()` is `false`, so the method takes the second branch and returns `rawAuthorizationHeaderValue` completely unchanged: the literal Basic header string, still trivially base64-decodable by anyone who captured it.
2. `whatEavesdropperSees(tlsHttp, basicHeader)` runs next — `tlsHttp.encrypted()` is `true`, so the method takes the first branch, returning the stand-in string representing TLS-encrypted, unreadable bytes — modeling the fact that everything inside a TLS tunnel, including the `Authorization` header, is protected from a passive network observer.
3. The final printed conclusion connects this observation back to Digest's original design goal: Digest existed specifically to prevent step 1's outcome *without* relying on TLS — but once TLS became the assumed baseline for any credential-carrying traffic, step 2 shows that same protection is already achieved for free, at the transport layer, for *any* authentication scheme running over it, Basic included.
4. This is precisely why Spring Security's maintainers chose to deprecate and eventually remove `DigestAuthenticationFilter`: maintaining a more complex, MD5-based, nonce-tracking mechanism stopped being worth it once its core benefit was already subsumed by an assumption (TLS) the ecosystem had independently converged on for unrelated reasons.

```
Basic header over plain HTTP -> eavesdropper reads it directly (base64 is reversible)  <- what Digest fixed
Basic header over TLS        -> eavesdropper sees only encrypted bytes                 <- same fix, different layer
```

## 7. Gotchas & takeaways

> **Gotcha:** encountering `DigestAuthenticationFilter` or related classes referenced in older tutorials, Stack Overflow answers, or certification study material is a strong signal that the material predates current Spring Security versions — attempting to configure Digest authentication in a current Spring Boot/Spring Security application will fail, since the supporting classes have been removed.

- HTTP Digest was designed to avoid transmitting a recoverable password over an unencrypted connection, using a nonce-based hash instead of the raw credential.
- TLS becoming the universal baseline for any credential-carrying traffic made Digest's core advantage redundant — the same confidentiality guarantee is achieved at the transport layer for any scheme, Basic included.
- Digest's own remaining weaknesses (reliance on MD5, the operational complexity of managing nonces and replay windows correctly) never went away, tipping the cost-benefit balance against continuing to maintain it.
- For new applications, use HTTP Basic only over TLS, or — more commonly for modern APIs — bearer tokens via OAuth2/JWT, which sidestep both Basic's and Digest's trade-offs entirely by not being password-based at all on a per-request basis.
