---
card: spring-authorization-server
gi: 41
slug: token-exchange-grant
title: "Token exchange grant"
---

## 1. What it is

The token exchange grant (`grant_type=urn:ietf:params:oauth:grant-type:token-exchange`, RFC 8693) lets a client trade one security token for another — typically, a downstream service swaps a token it received from an upstream caller for a new, differently-scoped token to use when calling a *further* downstream service. It's the mechanism behind "on-behalf-of" delegation in service-to-service chains.

## 2. Why & when

In a microservice chain — gateway calls Service A, Service A calls Service B — simply forwarding the original user's access token from A to B is tempting but wrong: Service B now holds a token scoped for whatever the *original* caller (the gateway or the user's client) was allowed to do, not what Service A specifically needs, and B has no way to tell whether A is legitimately relaying the call or something else entirely. Token exchange fixes this by having Service A present the incoming token to the authorization server and receive back a *new* token — one that can be scoped down, marked as "acting on behalf of user X," and explicitly identify Service A as the actor, giving Service B precise, auditable information about who's really calling and why.

Reach for token exchange when:

- Building a microservice chain where an intermediate service needs to call a further downstream service without either over-privileging the downstream call or losing track of the original caller's identity.
- Implementing delegation — "Service A acting on behalf of User X" needs to be distinguishable, in the token itself, from "Service A acting as itself."
- Deciding whether to just forward the original token unchanged — do that only when the receiving service trusts the exact same audience and scope as the original; the moment scope should narrow or the actor should be recorded, exchange it instead.

## 3. Core concept

Think of token exchange like a corporate relay of a signed authorization letter. A manager (the user) signs a letter authorizing broad purchasing (the original access token). Purchasing (Service A) doesn't hand that same broad letter to a specific vendor (Service B) — instead, purchasing goes to legal (the token endpoint) and exchanges it for a narrower, vendor-specific purchase order that says "Purchasing, acting on behalf of the manager, authorizes up to $500 with this vendor specifically" — a new document, scoped down, with both the delegate (Purchasing) and the original principal (the manager) clearly recorded on it.

```
POST /oauth2/token
    grant_type=urn:ietf:params:oauth:grant-type:token-exchange
    subject_token=<token received from upstream caller>
    subject_token_type=urn:ietf:params:oauth:token-type:access_token
    requested_token_type=urn:ietf:params:oauth:token-type:access_token
    audience=service-b
    scope=orders.read
```

## 4. Diagram

<svg viewBox="0 0 700 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Service A exchanges the incoming token for a new, narrower token scoped to Service B before calling it">
  <rect x="10" y="20" width="140" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="80" y="50" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Gateway / User</text>

  <rect x="260" y="20" width="140" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="50" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Service A</text>

  <line x1="150" y1="45" x2="255" y2="45" stroke="#8b949e" stroke-width="1.5"/>
  <text x="205" y="35" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">broad token</text>

  <rect x="260" y="120" width="140" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="145" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Token Endpoint</text>
  <text x="330" y="162" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">token-exchange</text>

  <line x1="330" y1="70" x2="330" y2="115" stroke="#8b949e" stroke-width="1.5"/>
  <text x="380" y="95" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">subject_token=broad token</text>

  <rect x="510" y="120" width="150" height="60" rx="8" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="585" y="145" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">New token</text>
  <text x="585" y="162" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">act=A, aud=service-b</text>

  <line x1="400" y1="150" x2="505" y2="150" stroke="#3fb950" stroke-width="1.5"/>

  <rect x="510" y="220" width="150" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="585" y="240" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Service B</text>
  <line x1="585" y1="180" x2="585" y2="215" stroke="#79c0ff" stroke-width="1.5"/>
</svg>

The new token carries an `act` claim identifying Service A as the actor, distinct from `sub`, which still identifies the original principal.

## 5. Runnable example

The scenario: Service A exchanging an incoming user token for a scoped-down token to call Service B, growing to inspect the delegation chain (`act` claim) on the receiving side, and finally to enforce that only specific services are allowed to exchange tokens on behalf of others.

### Level 1 — Basic

```java
// TokenExchangeClient.java
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.Base64;

public class TokenExchangeClient {

    private final HttpClient client = HttpClient.newHttpClient();

    public String exchange(String subjectToken, String audience, String clientId, String clientSecret) throws Exception {
        String credentials = Base64.getEncoder().encodeToString((clientId + ":" + clientSecret).getBytes());

        String body = "grant_type=" + java.net.URLEncoder.encode(
                        "urn:ietf:params:oauth:grant-type:token-exchange", "UTF-8")
                + "&subject_token=" + subjectToken
                + "&subject_token_type=" + java.net.URLEncoder.encode(
                        "urn:ietf:params:oauth:token-type:access_token", "UTF-8")
                + "&requested_token_type=" + java.net.URLEncoder.encode(
                        "urn:ietf:params:oauth:token-type:access_token", "UTF-8")
                + "&audience=" + audience;

        HttpRequest request = HttpRequest.newBuilder(URI.create("http://localhost:8080/oauth2/token"))
                .header("Authorization", "Basic " + credentials)
                .header("Content-Type", "application/x-www-form-urlencoded")
                .POST(HttpRequest.BodyPublishers.ofString(body))
                .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        return response.body();
    }
}
```

**How to run:** with a `RegisteredClient` for `service-a` that includes `TOKEN_EXCHANGE` as an allowed grant type, call `exchange(incomingToken, "service-b", "service-a", "secret")` where `incomingToken` was received from the upstream gateway. Expected output: a JSON body with a new `access_token` whose audience is `service-b`.

### Level 2 — Intermediate

Service B needs to see *both* who the original user was and which service is relaying the call — token exchange tokens carry an `act` (actor) claim alongside the usual `sub`, and Service B should log and use both.

```java
import org.springframework.security.oauth2.jwt.Jwt;

public class DelegationChainReader {

    public String describeCaller(Jwt token) {
        String subject = token.getClaimAsString("sub");
        Object actClaim = token.getClaim("act");

        if (actClaim instanceof java.util.Map<?, ?> act) {
            Object actor = act.get("sub");
            return "User '" + subject + "', relayed by service '" + actor + "'";
        }
        return "User '" + subject + "', direct call (no delegation)";
    }
}
```

**How to run:** call `describeCaller(jwt)` in Service B's controller for both a direct call (a token obtained normally) and a delegated call (a token from Level 1's exchange). Expected output for the exchanged token: `User 'alice', relayed by service 'service-a'`; for a direct token: `User 'alice', direct call (no delegation)`.

What changed: Service B can now distinguish a genuine delegated call from a direct one and knows precisely which intermediate service is vouching for it — essential information for audit logs and for any authorization decision that should differ based on how a request arrived.

### Level 3 — Advanced

Not every service should be allowed to exchange tokens on behalf of users — production restricts which `client_id`s are permitted to call the token-exchange grant at all, and further restricts which `audience` values each is allowed to request, preventing a compromised intermediate service from minting itself tokens for arbitrary downstream targets.

```java
import java.util.Map;
import java.util.Set;

public class ExchangePolicy {

    private static final Map<String, Set<String>> ALLOWED_AUDIENCES = Map.of(
            "service-a", Set.of("service-b", "service-c"),
            "service-d", Set.of("service-e"));

    public void enforce(String requestingClientId, String requestedAudience) {
        Set<String> allowed = ALLOWED_AUDIENCES.get(requestingClientId);
        if (allowed == null || !allowed.contains(requestedAudience)) {
            throw new SecurityException(
                    "Client '" + requestingClientId + "' is not permitted to exchange tokens for audience '"
                            + requestedAudience + "'");
        }
    }
}
```

**How to run:** call `enforce("service-a", "service-b")` (allowed) and `enforce("service-a", "service-e")` (not in `service-a`'s allow-list). Wire this check into a custom `OAuth2TokenExchangeAuthenticationProvider` decorator (or equivalent request-validation hook) ahead of actual token issuance. Expected behavior: the first call passes silently; the second throws `SecurityException`, and that request should be converted into a `400 invalid_target` response rather than issuing a token.

```
HTTP/1.1 400 Bad Request
Content-Type: application/json

{"error":"invalid_target","error_description":"Client 'service-a' is not permitted to exchange tokens for audience 'service-e'"}
```

What changed and why it's production-flavored: without this policy, any service holding valid client credentials could exchange a token for *any* audience in the system, effectively letting it impersonate delegation to services it was never meant to call — a per-client audience allow-list keeps the blast radius of a single compromised service contained to its actual legitimate downstream dependencies.

## 6. Walkthrough

Tracing a token exchange call within a service chain, in execution order:

1. The gateway authenticates the user (via authorization code flow, card 0038) and calls Service A with `Authorization: Bearer <original token>`, whose audience and scope were issued for the gateway's own use.
2. Service A needs to call Service B, but forwarding the original token unchanged would give Service B a token scoped for the gateway, with no record that Service A is the actual caller.
3. Service A sends `POST /oauth2/token` to the authorization server with `grant_type=urn:ietf:params:oauth:grant-type:token-exchange`, `subject_token` set to the original token, and `audience=service-b`, authenticating itself with its own client credentials.
4. The server (Level 3's `ExchangePolicy`) checks Service A is permitted to request tokens for the `service-b` audience — an unpermitted audience is rejected with `400 invalid_target` before any token work happens.
5. Assuming the policy check passes, the server validates the `subject_token` is itself a real, unexpired token, then constructs a new access token: `sub` remains the original user, a new `aud` claim targets `service-b`, scope is narrowed to what's relevant for that call, and an `act` claim records `service-a` as the delegate actor.
6. The server responds `200 OK` with the new token, distinct from and independent of the original `subject_token` (which remains valid and unaffected — exchange doesn't consume or revoke it).
7. Service A calls Service B with this new token; Service B validates it as a normal bearer token, and its `DelegationChainReader` (Level 2) reads both `sub` and `act` to know precisely who the request is really for and who relayed it.

```
Gateway -> Service A: Bearer <original token, aud=gateway>
Service A -> Token Endpoint: POST /token (token-exchange, subject_token=original, audience=service-b)
Token Endpoint: policy check -> validate subject_token -> issue new token (sub=user, aud=service-b, act=service-a)
Token Endpoint -> Service A: 200 OK {access_token: <new token>}
Service A -> Service B: Bearer <new token, aud=service-b, act=service-a>
Service B: reads sub (who) and act (relayed by whom)
```

Concrete request and response:

```
POST /oauth2/token HTTP/1.1
Authorization: Basic c2VydmljZS1hOnNlY3JldA==
Content-Type: application/x-www-form-urlencoded

grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Atoken-exchange&subject_token=eyJhbGciOiJSUzI1NiJ9...&subject_token_type=urn%3Aietf%3Aparams%3Aoauth%3Atoken-type%3Aaccess_token&audience=service-b

HTTP/1.1 200 OK
Content-Type: application/json

{"access_token":"eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJhbGljZSIsImF1ZCI6InNlcnZpY2UtYiIsImFjdCI6eyJzdWIiOiJzZXJ2aWNlLWEifX0...","issued_token_type":"urn:ietf:params:oauth:token-type:access_token","token_type":"Bearer","expires_in":600}
```

## 7. Gotchas & takeaways

> Token exchange does not revoke or consume the original `subject_token` — both the original and the newly exchanged token remain independently valid until their own individual expiries. If a downstream service is compromised and the exchanged token leaks, revoking only the exchanged token (card 0029) is not enough if the original is also exposed; both need review.

- Nested delegation (Service A exchanges for Service B, which itself exchanges again for Service C) produces a chain of `act` claims — always design the receiving side to walk the full chain if depth matters, not just the immediate `act.sub`.
- Token exchange tokens are typically issued with shorter lifetimes than the original (`expires_in: 600` in the example above versus a typical 3600 for user-facing tokens) — this is intentional, since they're meant for a single, narrow downstream call, not long-term client-side storage.
- Never accept a token-exchange request where `audience` is left unconstrained — an authorization server that will mint a token for *any* requested audience effectively lets any client become any other client's caller.
- Distinguish `subject_token` (whose identity the new token represents) from `actor_token` (an optional second token identifying an intermediate actor in a multi-hop delegation chain, distinct from the requesting client's own credentials) — most simple service-to-service cases only need `subject_token`.
- If Service B is seeing unexpectedly broad access from a delegated call, check the exchange request's `scope` parameter first — without explicitly narrowing it, some configurations pass through the original token's full scope unchanged, defeating the purpose of scoping down per hop.
