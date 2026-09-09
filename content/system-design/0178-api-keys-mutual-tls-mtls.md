---
card: system-design
gi: 178
slug: api-keys-mutual-tls-mtls
title: API keys & mutual TLS (mTLS)
---

## 1. What it is

An **API key** is a simple, long-lived secret string a client includes with every request to identify itself to a service — much simpler than [OAuth2](0176-oauth2-openid-connect.md), but with no built-in expiry, scoping, or user context by default. **Mutual TLS (mTLS)** goes further: both the client and the server present X.509 certificates during the TLS handshake itself, so each side cryptographically proves its identity to the other before any application data is exchanged at all — unlike normal TLS, where only the server proves its identity to the client.

## 2. Why & when

API keys are the simplest possible way to identify a calling service or application — easy to generate, easy to check — and are well suited for service-to-service calls where a full OAuth2 flow would be unnecessary overhead. But a leaked API key is fully usable by whoever has it, with no additional proof of possession required. mTLS solves a different, stronger problem: verifying that the caller is not just *someone who has a valid credential*, but a specific, certificate-holding party the server was configured to trust — this matters most for high-security service-to-service communication (internal microservices, payment networks, sensitive B2B integrations) where you want cryptographic proof of identity baked into the connection itself, not a string that could be copied from a log file.

## 3. Core concept

- **API key transmission:** commonly sent as a header (`X-API-Key: abc123`) or a query parameter (avoid query parameters — they end up logged in server access logs and browser history); the server simply checks it against a stored list of valid keys.
- **API key scoping:** a well-designed API-key system associates each key with specific permissions and rate limits, not just "valid or not," so a leaked key's blast radius is limited.
- **Normal TLS is one-directional trust:** in standard HTTPS, the client verifies the server's certificate, but the server has no cryptographic proof of who the client is — that is handled separately, typically by an API key or a token in the request.
- **mTLS adds client certificate verification:** during the TLS handshake, the server also requests and verifies a certificate from the client, checking it was issued by a certificate authority (CA) the server trusts — this happens before the connection is even established, at the transport layer, not the application layer.
- **Certificate rotation:** both API keys and client certificates need a rotation plan — issuing new credentials periodically and revoking old ones — since a credential that never changes only grows riskier the longer it exists.

## 4. Diagram

```
   API KEY:                                    mTLS:
   client -> header: X-API-Key: abc123         client                        server
                |                              (presents cert)    <-------> (presents cert)
                v                                   |    TLS handshake verifies BOTH certs  |
   server: is "abc123" a known, valid key?          |    against a trusted CA               |
           -> yes: proceed, apply that key's        v
              scopes/rate limits                connection established ONLY if both
           -> no: reject                        certificates are valid and trusted
                                                      |
                                              application data flows only after this
```
*Caption: an API key is checked at the application layer on every request; mTLS verifies both parties' identity at the transport layer, before any application data is sent.*

## 5. Runnable example

**Level 1 — Basic.** Validate an API key against a stored, scoped list.

**Level 2 — Per-key scopes and rate limits.** A leaked key's damage is limited by what it was actually issued to do.

**Level 3 — Model mTLS: both sides present and verify a certificate before any data flows.** Contrast with the one-directional trust of an API key alone.

```java
// ApiKeyMtlsDemo.java
import java.util.*;

public class ApiKeyMtlsDemo {

    static class ApiKeyRecord {
        final Set<String> scopes;
        final int rateLimitPerMinute;
        ApiKeyRecord(Set<String> scopes, int rateLimitPerMinute) { this.scopes = scopes; this.rateLimitPerMinute = rateLimitPerMinute; }
    }

    // Level 1 & 2: each key maps to specific scopes and a rate limit - not just "valid/invalid".
    static Map<String, ApiKeyRecord> validKeys = Map.of(
        "key-readonly-abc", new ApiKeyRecord(Set.of("read"), 100),
        "key-fullaccess-xyz", new ApiKeyRecord(Set.of("read", "write", "delete"), 1000)
    );

    static boolean callApiWithKey(String apiKey, String requiredScope) {
        ApiKeyRecord record = validKeys.get(apiKey);
        if (record == null) {
            System.out.println("  REJECTED: unknown API key");
            return false;
        }
        if (!record.scopes.contains(requiredScope)) {
            System.out.println("  REJECTED: key lacks scope \"" + requiredScope + "\" (has " + record.scopes + ")");
            return false;
        }
        System.out.println("  ACCEPTED: key has scope \"" + requiredScope + "\", proceeding (rate limit: " + record.rateLimitPerMinute + "/min)");
        return true;
    }

    // Level 3: models mTLS - a certificate on EACH side, both verified against a trusted CA, before any data flows.
    static class Certificate {
        final String subject, issuedByCA;
        Certificate(String subject, String issuedByCA) { this.subject = subject; this.issuedByCA = issuedByCA; }
    }

    static final String TRUSTED_CA = "internal-ca";

    static boolean establishMutualTlsConnection(Certificate clientCert, Certificate serverCert) {
        System.out.println("  TLS handshake: verifying server cert (subject=" + serverCert.subject + ")...");
        if (!TRUSTED_CA.equals(serverCert.issuedByCA)) {
            System.out.println("  REJECTED: server certificate not issued by a trusted CA");
            return false;
        }
        System.out.println("  TLS handshake: verifying CLIENT cert too (subject=" + clientCert.subject + ")...");
        if (!TRUSTED_CA.equals(clientCert.issuedByCA)) {
            System.out.println("  REJECTED: client certificate not issued by a trusted CA - connection refused BEFORE any data flows");
            return false;
        }
        System.out.println("  CONNECTION ESTABLISHED: both parties cryptographically verified");
        return true;
    }

    public static void main(String[] args) {
        System.out.println("-- API key scenarios --");
        System.out.println("read-only key requesting read access:");
        callApiWithKey("key-readonly-abc", "read");
        System.out.println("read-only key requesting write access:");
        callApiWithKey("key-readonly-abc", "write");
        System.out.println("unknown key:");
        callApiWithKey("key-stolen-999", "read");

        System.out.println("-- mTLS scenarios --");
        Certificate trustedServerCert = new Certificate("api.internal.example.com", "internal-ca");
        Certificate trustedClientCert = new Certificate("service-orders", "internal-ca");
        Certificate untrustedClientCert = new Certificate("service-unknown", "some-other-ca");

        System.out.println("legitimate service connecting:");
        establishMutualTlsConnection(trustedClientCert, trustedServerCert);
        System.out.println("an attacker with a self-signed cert (no valid API key equivalent needed to even TRY) trying to connect:");
        establishMutualTlsConnection(untrustedClientCert, trustedServerCert);
    }
}
```

**How to run:** save as `ApiKeyMtlsDemo.java`, then run `java ApiKeyMtlsDemo.java`.

## 6. Walkthrough

1. `callApiWithKey("key-readonly-abc", "read")` finds `validKeys.get("key-readonly-abc")` returns a record with `scopes = {"read"}`; since `record.scopes.contains("read")` is true, the call is accepted.
2. `callApiWithKey("key-readonly-abc", "write")` finds the same key record, but `record.scopes.contains("write")` is false — the key is valid, but scoped too narrowly for this action, so the call is rejected specifically for lacking scope, not for being an invalid key.
3. `callApiWithKey("key-stolen-999", "read")` finds no entry at all in `validKeys`, so `record` is `null`, and the method rejects it immediately as an unknown key — before scope is even considered.
4. `establishMutualTlsConnection(trustedClientCert, trustedServerCert)` first checks the server certificate's `issuedByCA` against `TRUSTED_CA` (matches), then checks the client certificate's `issuedByCA` the same way (also matches) — both checks pass, so the method prints "CONNECTION ESTABLISHED," modeling a successful mTLS handshake where both sides proved their identity.
5. `establishMutualTlsConnection(untrustedClientCert, trustedServerCert)` passes the server-certificate check (still `"internal-ca"`), but fails on the client-certificate check, since `untrustedClientCert.issuedByCA` is `"some-other-ca"`, not the trusted CA — the connection is refused entirely, at the handshake stage, before any application-level check (like an API key) would even get the chance to run.

## 7. Gotchas & takeaways

> Gotcha: an API key sent as a URL query parameter (rather than a header) commonly ends up recorded in server access logs, browser history, and even shared inadvertently when a URL is copy-pasted — always send API keys as a header, never as part of the URL itself.

- API keys are simple to implement and use, but a leaked key is fully usable by anyone who has it, unless scoped and rate-limited per key.
- mTLS verifies both parties' identity cryptographically at the connection level, before any application data (including an API key) is even sent.
- Both mechanisms need a real rotation and revocation plan — a credential that is never rotated only becomes riskier the longer it has existed.
- Related concepts: [OAuth2 & OpenID Connect](0176-oauth2-openid-connect.md) (a richer, scoped, revocable alternative to a plain long-lived API key), [Encryption in transit (TLS) & at rest](0179-encryption-in-transit-tls-at-rest.md) (the underlying TLS mechanism mTLS extends), [Secrets management & rotation](0180-secrets-management-rotation.md) (how API keys and certificates should actually be stored and rotated in practice).
