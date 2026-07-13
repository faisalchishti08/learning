---
card: microservices
gi: 399
slug: confused-deputy-ssrf-concerns-at-gateway
title: "Confused deputy / SSRF concerns at the gateway"
---

## 1. What it is

A **confused deputy** is a program that has more privilege than the party asking it to act, and can be tricked into misusing that privilege on the attacker's behalf. **Server-Side Request Forgery (SSRF)** is the most common concrete instance of this in web APIs: a server-side component makes an outbound HTTP request to a URL that's fully or partially controlled by the caller, and an attacker supplies a URL pointing at something the *server* can reach but the *attacker* couldn't reach directly — an internal admin panel, a cloud metadata endpoint, or a service with no external exposure at all. The [API gateway](0382-edge-authentication-at-the-gateway.md), sitting at the trust boundary between the public internet and the internal network, is a particularly high-value confused-deputy target, because it typically *does* have network access to everything behind it.

## 2. Why & when

This matters specifically because of what makes a gateway powerful in the first place: it's trusted, network-privileged, and reachable from outside — exactly the combination a confused-deputy attack needs.

- **Any feature that fetches a URL supplied by the caller is a potential SSRF vector** — webhook registration, "import from URL," avatar-by-URL, PDF-generation-from-URL, and proxy or gateway routing features are the classic culprits.
- **The gateway's network position makes it uniquely dangerous to trick.** A public user has no direct route to an internal-only service; but if the gateway can be convinced to make a request *for* them, the gateway's own network access becomes theirs — this is the "deputy" being confused into acting beyond the caller's actual privilege.
- **Cloud environments add a specific, severe instance:** cloud provider metadata endpoints (commonly `169.254.169.254`) often serve instance credentials with no authentication required *from the instance itself* — an SSRF vulnerability that lets an attacker point a server at this address can exfiltrate the server's own cloud credentials.
- **This is explicitly item API7 on the [OWASP API Security Top 10](0398-owasp-api-security-top-10.md)** precisely because it's common, severe, and easy to introduce accidentally in any feature involving "fetch this URL for me."

You need to think about this any time a service — especially the gateway — makes an outbound network call whose destination is influenced, directly or indirectly, by data from an external caller.

## 3. Core concept

Think of a hotel concierge (the deputy) who has a master key and will fetch anything from any room in the building on a guest's behalf, as a courtesy. A legitimate guest asks the concierge to bring something from the gift shop — fine, that's within the intended use. But if the concierge doesn't check *where* it's fetching from, an attacker can ask "please bring me whatever is in the manager's office safe" — a room the guest could never have entered themselves, but the concierge, using its own privileged master key, walks right in and hands it over. The concierge was tricked into using *its own* privilege on the guest's behalf, for a request the guest was never authorized to make directly. That's the confused deputy problem, and SSRF is exactly this pattern applied to network requests.

The defense has several layers, each closing a different gap:

1. **Never let user input directly become a raw destination URL/host** for a server-side fetch. If the feature must support user-influenced destinations, resolve against an explicit allow-list of permitted hosts or domains, not a deny-list (deny-lists are trivially bypassed with redirects, alternate IP encodings, or DNS tricks).
2. **Block requests to internal/private IP ranges by default** at the network layer (egress filtering) — `127.0.0.0/8`, `10.0.0.0/8`, `169.254.0.0/16` (cloud metadata), and other RFC 1918 ranges — so even a URL that slips past application-layer validation still can't reach internal infrastructure.
3. **Validate after DNS resolution, not just the string.** A hostname that looks external (`legit-looking-domain.com`) can still resolve to an internal IP via attacker-controlled DNS — checking the *string* is not enough; the *resolved address actually being connected to* must be checked too.
4. **Follow redirects carefully, or not at all.** A URL that passes validation can issue an HTTP redirect to an internal address; either disable following redirects for user-supplied-URL fetches, or re-validate the destination after each hop.
5. **Least-privilege network segmentation** limits the blast radius even if a request does get through — a gateway that genuinely cannot reach a sensitive internal service at the network level is safe from being tricked into reaching it, regardless of any application bug.

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An attacker supplies a webhook URL pointing at an internal admin service; the gateway, which has network access the attacker lacks directly, is tricked into fetching it on the attacker's behalf unless the destination is validated" font-family="sans-serif">
  <rect x="20" y="90" width="120" height="50" rx="8" fill="#1c2430" stroke="#f85149"/>
  <text x="80" y="112" fill="#e6edf3" font-size="10" text-anchor="middle">Attacker</text>
  <text x="80" y="127" fill="#8b949e" font-size="8" text-anchor="middle">no direct network route</text>

  <rect x="220" y="90" width="160" height="60" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="300" y="112" fill="#e6edf3" font-size="10" text-anchor="middle">Gateway (the "deputy")</text>
  <text x="300" y="128" fill="#8b949e" font-size="9" text-anchor="middle">has internal network access</text>
  <text x="300" y="142" fill="#8b949e" font-size="8" text-anchor="middle">webhookUrl=http://10.0.0.5/admin</text>

  <rect x="460" y="30" width="150" height="50" rx="8" fill="#1c2430" stroke="#f85149"/>
  <text x="535" y="50" fill="#f85149" font-size="10" text-anchor="middle">Internal admin service</text>
  <text x="535" y="65" fill="#8b949e" font-size="8" text-anchor="middle">not reachable from internet</text>

  <rect x="460" y="150" width="150" height="60" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="535" y="172" fill="#6db33f" font-size="10" text-anchor="middle">Allow-list check</text>
  <text x="535" y="188" fill="#8b949e" font-size="8" text-anchor="middle">host not on allow-list</text>
  <text x="535" y="202" fill="#6db33f" font-size="8" text-anchor="middle">-&gt; request BLOCKED</text>

  <line x1="140" y1="115" x2="220" y2="115" stroke="#8b949e" marker-end="url(#ssrf)"/>
  <text x="180" y="105" fill="#8b949e" font-size="8" text-anchor="middle">supplies URL</text>
  <line x1="300" y1="90" x2="460" y2="60" stroke="#f85149" stroke-dasharray="3,2" marker-end="url(#ssrf)"/>
  <text x="380" y="65" fill="#f85149" font-size="8">without validation: fetched!</text>
  <line x1="300" y1="150" x2="460" y2="175" stroke="#6db33f" marker-end="url(#ssrf)"/>
  <defs>
    <marker id="ssrf" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

The attacker has no direct route to the internal admin service, but the gateway does — an unvalidated fetch turns the gateway into a confused deputy that reaches it on the attacker's behalf.

## 5. Runnable example

Scenario: a webhook-registration feature where the gateway fetches a URL supplied by the user to verify it's reachable. We start with a completely open fetch, add naive deny-list filtering (and show how it's bypassed), then implement a proper allow-list plus post-DNS-resolution IP validation.

### Level 1 — Basic

```java
// File: OpenSsrfVector.java -- the gateway fetches WHATEVER URL the caller
// supplies, with no validation at all. Any internal address the gateway can
// reach, the caller can now reach too, indirectly.
public class OpenSsrfVector {
    // Simulates an outbound fetch -- in reality an HTTP client call.
    static String fetchUrl(String url) {
        return "Gateway fetched: " + url + " (whatever is there, the caller now effectively sees)";
    }

    static String registerWebhook(String userSuppliedUrl) {
        return fetchUrl(userSuppliedUrl);
    }

    public static void main(String[] args) {
        System.out.println(registerWebhook("https://partner.example.com/webhook-receiver"));
        // An attacker supplies an INTERNAL address instead -- the gateway fetches it just the same.
        System.out.println(registerWebhook("http://10.0.0.5/admin/delete-all-users"));
        System.out.println(registerWebhook("http://169.254.169.254/latest/meta-data/iam/security-credentials/"));
    }
}
```

How to run: `java OpenSsrfVector.java`

`registerWebhook` passes the caller-supplied URL straight to `fetchUrl` with no checks. The legitimate partner URL and the two malicious ones — an internal admin endpoint and the cloud metadata service — are all fetched identically. The gateway has become a confused deputy: it's using its own network access to reach destinations the caller could never reach directly.

### Level 2 — Intermediate

```java
// File: NaiveDenyList.java -- a DENY-LIST blocks a few obviously-bad patterns,
// but deny-lists are inherently incomplete: they only stop what someone
// already thought to block, and are easy to bypass with encoding tricks or
// alternate representations of the same address.
import java.util.*;

public class NaiveDenyList {
    static final List<String> BLOCKED_SUBSTRINGS = List.of("10.0.0", "169.254", "localhost", "127.0.0.1");

    static boolean looksBlocked(String url) {
        return BLOCKED_SUBSTRINGS.stream().anyMatch(url::contains);
    }

    static String registerWebhook(String userSuppliedUrl) {
        if (looksBlocked(userSuppliedUrl)) {
            return "BLOCKED: '" + userSuppliedUrl + "' matches a denied pattern";
        }
        return "Gateway fetched: " + userSuppliedUrl;
    }

    public static void main(String[] args) {
        System.out.println(registerWebhook("http://10.0.0.5/admin")); // correctly blocked
        // Bypass 1: decimal IP notation for 127.0.0.1 -- doesn't contain the blocked STRING "127.0.0.1".
        System.out.println(registerWebhook("http://2130706433/admin"));
        // Bypass 2: a DNS name the attacker controls, resolving to an internal IP -- the STRING looks fine.
        System.out.println(registerWebhook("http://attacker-controlled-dns.example.com/admin"));
    }
}
```

How to run: `java NaiveDenyList.java`

`looksBlocked` only catches URLs whose *text* literally contains one of the blocked substrings. The first call is correctly blocked. But `2130706433` is the decimal representation of `127.0.0.1` — a valid way to encode that IP address that most HTTP clients will happily resolve, and it contains none of the blocked substrings, so it sails through. Worse, a hostname an attacker controls the DNS for can be pointed at any internal IP *after* this string check runs — the string itself never reveals where the name will actually resolve. Deny-lists fail because they check the wrong thing: the surface text, not the actual network destination.

### Level 3 — Advanced

```java
// File: AllowListWithResolvedIpCheck.java -- an ALLOW-LIST of permitted hosts,
// PLUS a check on the ACTUALLY-RESOLVED IP address (not just the hostname
// string) against private/internal ranges -- closing both the deny-list gap
// and the DNS-rebinding-style bypass.
import java.net.*;
import java.util.*;
import java.util.regex.*;

public class AllowListWithResolvedIpCheck {
    static final Set<String> ALLOWED_HOSTS = Set.of("partner.example.com", "webhooks.trusted-vendor.com");

    // Simulates DNS resolution -- in a real system this is an actual lookup.
    static final Map<String, String> SIMULATED_DNS = Map.of(
            "partner.example.com", "203.0.113.10",           // legitimate external IP
            "attacker-controlled-dns.example.com", "10.0.0.5" // attacker's domain resolves INTERNALLY
    );

    static boolean isPrivateOrReservedIp(String ip) {
        // Stand-in for real RFC 1918 / loopback / link-local range checks.
        return ip.startsWith("10.") || ip.startsWith("127.") || ip.startsWith("169.254.")
                || ip.startsWith("172.16.") || ip.startsWith("192.168.");
    }

    static String extractHost(String url) {
        Matcher m = Pattern.compile("https?://([^/]+)").matcher(url);
        return m.find() ? m.group(1) : null;
    }

    static String registerWebhook(String userSuppliedUrl) {
        String host = extractHost(userSuppliedUrl);
        if (host == null) return "REJECTED: could not parse URL";

        // Step 1: allow-list check on the HOSTNAME.
        if (!ALLOWED_HOSTS.contains(host)) {
            return "REJECTED: host '" + host + "' is not on the allow-list";
        }

        // Step 2: resolve DNS and check the ACTUAL IP, not just the name.
        String resolvedIp = SIMULATED_DNS.getOrDefault(host, "0.0.0.0");
        if (isPrivateOrReservedIp(resolvedIp)) {
            return "REJECTED: host '" + host + "' resolved to internal/private IP " + resolvedIp + " -- likely DNS rebinding attempt";
        }

        return "Gateway fetched: " + userSuppliedUrl + " (resolved to " + resolvedIp + ", verified external)";
    }

    public static void main(String[] args) {
        System.out.println(registerWebhook("https://partner.example.com/webhook-receiver")); // allowed + resolves externally
        System.out.println(registerWebhook("http://10.0.0.5/admin"));                         // not on allow-list at all
        // Even though this domain LOOKS like it might not be blocked by name, it's not on the allow-list either --
        // and even if it somehow were, its resolved IP would catch it.
        System.out.println(registerWebhook("http://attacker-controlled-dns.example.com/admin"));
    }
}
```

How to run: `java AllowListWithResolvedIpCheck.java`

`registerWebhook` now performs two independent checks. First, `ALLOWED_HOSTS.contains(host)` — an allow-list, not a deny-list, so only explicitly-trusted hostnames pass at all, regardless of what other tricks a URL might use. Second, even for an allowed hostname, `SIMULATED_DNS` resolution is checked against `isPrivateOrReservedIp` — verifying the *actual network destination*, not just the string that was typed. The legitimate partner URL passes both checks. The raw internal IP is rejected immediately at the allow-list stage — it was never going to be an allowed host. The attacker-controlled DNS name is also rejected at the allow-list stage (it isn't `partner.example.com` or `webhooks.trusted-vendor.com`), and would be caught by the resolved-IP check even in the hypothetical where an attacker somehow got a lookalike name onto the allow-list, since it resolves to `10.0.0.5`.

## 6. Walkthrough

Trace `AllowListWithResolvedIpCheck.main` for the third call, `registerWebhook("http://attacker-controlled-dns.example.com/admin")`. **First**, `extractHost` runs its regex against the URL and captures `"attacker-controlled-dns.example.com"` as `host`.

**Next**, `ALLOWED_HOSTS.contains("attacker-controlled-dns.example.com")` is checked. `ALLOWED_HOSTS` contains only `"partner.example.com"` and `"webhooks.trusted-vendor.com"` — this hostname is not among them, so the condition is `true` (not on allow-list), and the method returns immediately: `"REJECTED: host 'attacker-controlled-dns.example.com' is not on the allow-list"`. The DNS resolution step never even runs for this call, because the allow-list check already caught it — a cheap check rejecting the request before any network resolution is attempted.

**Then, for contrast**, walk the *first* call, `registerWebhook("https://partner.example.com/webhook-receiver")`. `host` becomes `"partner.example.com"`, which *is* in `ALLOWED_HOSTS`, so the first check passes. `SIMULATED_DNS.getOrDefault("partner.example.com", "0.0.0.0")` returns `"203.0.113.10"` — a public IP address. `isPrivateOrReservedIp("203.0.113.10")` checks the four private-range prefixes; none match, so it returns `false`. Both checks pass, and the fetch proceeds.

**Finally**, consider what would happen if `ALLOWED_HOSTS` had, hypothetically, been misconfigured to include `"attacker-controlled-dns.example.com"` (simulating a case where an allow-list itself is too permissive, or a partner's own domain gets compromised and repointed): the allow-list check would pass, but `SIMULATED_DNS.getOrDefault(...)` would return `"10.0.0.5"`, and `isPrivateOrReservedIp("10.0.0.5")` — matching the `"10."` prefix — would return `true`, causing rejection at the second check instead. This is exactly why both layers matter: the allow-list catches most attacks cheaply, and the resolved-IP check catches the case where a trusted-looking name still points somewhere it shouldn't.

```
Gateway fetched: https://partner.example.com/webhook-receiver (resolved to 203.0.113.10, verified external)
REJECTED: host '10.0.0.5' is not on the allow-list
REJECTED: host 'attacker-controlled-dns.example.com' is not on the allow-list
```

## 7. Gotchas & takeaways

> Checking a URL's hostname string is not the same as checking where a request will actually go. DNS rebinding attacks specifically exploit this gap: a hostname can pass validation at check-time and then resolve to a different (internal) IP by the time the actual connection is made, if the attacker controls the DNS record and changes it between the check and the fetch. Real defenses re-resolve and re-check the IP at connection time, or route outbound fetches through a proxy that enforces network-layer egress rules independent of application logic.

- A confused deputy is any privileged component tricked into using its own access on an unprivileged caller's behalf; SSRF is the network-request instance of this pattern, and the gateway is a prime target because of its network position.
- Deny-lists for SSRF protection are fundamentally incomplete — alternate IP encodings, redirects, and attacker-controlled DNS all bypass string-based blocking; use an allow-list instead.
- Validate the *resolved* destination, not just the URL string — a hostname that looks external can still resolve to an internal address.
- Cloud metadata endpoints are a especially high-value SSRF target, since they often serve credentials with no additional authentication from the requesting instance itself.
- This is [OWASP API Security Top 10](0398-owasp-api-security-top-10.md) item API7, and defense-in-depth here means combining application-layer allow-listing with network-layer egress filtering, consistent with the broader [defense in depth](0379-defense-in-depth.md) principle running through this whole section.
