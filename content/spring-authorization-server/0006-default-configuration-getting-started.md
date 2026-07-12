---
card: spring-authorization-server
gi: 6
slug: default-configuration-getting-started
title: "Default configuration & getting started"
---

## 1. What it is

`OAuth2AuthorizationServerConfigurer.authorizationServer()` combined with `Customizer.withDefaults()` is Spring Authorization Server's minimal-configuration entry point: calling it registers every core OAuth2/OIDC endpoint (`/oauth2/authorize`, `/oauth2/token`, `/oauth2/jwks`, `/oauth2/introspect`, `/oauth2/revoke`, `/.well-known/openid-configuration`, `/.well-known/oauth-authorization-server`) with sensible, spec-conformant defaults — enough to have a genuinely functional, if minimal, authorization server running from just a handful of bean declarations, before any custom behavior is layered on top.

```java
@Bean
@Order(Ordered.HIGHEST_PRECEDENCE)
public SecurityFilterChain authorizationServerSecurityFilterChain(HttpSecurity http) throws Exception {
    OAuth2AuthorizationServerConfigurer authorizationServerConfigurer =
            OAuth2AuthorizationServerConfigurer.authorizationServer();

    http.securityMatcher(authorizationServerConfigurer.getEndpointsMatcher())
        .with(authorizationServerConfigurer, (authorizationServer) -> authorizationServer.oidc(Customizer.withDefaults()))
        .authorizeHttpRequests(auth -> auth.anyRequest().authenticated())
        .exceptionHandling(exceptions -> exceptions.defaultAuthenticationEntryPointFor(
                new LoginUrlAuthenticationEntryPoint("/login"), new MediaTypeRequestMatcher(MediaType.TEXT_HTML)));

    return http.build();
}
```

## 2. Why & when

Every earlier card in this section established the concepts (roles, spec conformance, migration path) — this is the card where those concepts become a runnable application. A minimal configuration matters because it demonstrates that a functioning authorization server doesn't require reimplementing every OAuth2/OIDC endpoint by hand: `OAuth2AuthorizationServerConfigurer` handles the protocol machinery, leaving an application to supply only what's genuinely application-specific — registered clients (card 0007's territory for the surrounding `SecurityFilterChain`), a `UserDetailsService` for resource owner login, and signing keys.

Reach for the default configuration as a starting point when:

- Learning Spring Authorization Server for the first time — starting from the minimal, defaults-based setup and incrementally customizing is far more tractable than assembling every option from scratch.
- Prototyping or demoing an OAuth2 flow locally — a default configuration with an in-memory `RegisteredClientRepository` and a generated signing key gets a working server running in minutes, sufficient for local development and testing.
- Verifying the framework's baseline behavior before layering custom logic — confirming the default configuration works correctly establishes a known-good baseline to diff any subsequent customization against.

## 3. Core concept

```
OAuth2AuthorizationServerConfigurer.authorizationServer() registers, with sensible defaults:

    /oauth2/authorize                    -- authorization endpoint (card 0090's redirect target)
    /oauth2/token                        -- token endpoint (card 0090's code exchange)
    /oauth2/jwks                         -- JWK Set endpoint (card 0101's key source)
    /oauth2/introspect                   -- token introspection (card 0102's validation target)
    /oauth2/revoke                       -- token revocation
    /oauth2/device_authorization         -- device authorization grant (if enabled)
    /connect/register                    -- dynamic client registration (if enabled)
    /.well-known/openid-configuration    -- OIDC discovery metadata (card 0110's metadata source)
    /.well-known/oauth-authorization-server -- OAuth2 authorization server metadata (RFC 8414)
    /userinfo                            -- OIDC UserInfo endpoint (card 0096's territory)

MINIMUM additional beans a working instance still needs:
    RegisteredClientRepository  -- at least one registered client (card 0007's next-door topic)
    a signing key source        -- a JWKSource<SecurityContext>, for signing issued JWTs
    (a UserDetailsService, via the ORDINARY second SecurityFilterChain, for resource owner login -- card 0002)

securityMatcher(authorizationServerConfigurer.getEndpointsMatcher()) SCOPES this chain
to ONLY these OAuth2/OIDC-specific endpoints -- card 0002's two-chain pattern.
```

The defaults produce a spec-conformant server immediately; every customization covered in later cards of this project layers on top of, rather than replaces, this baseline.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram showing OAuth2AuthorizationServerConfigurer dot authorizationServer registering a family of endpoints authorize token jwks introspect revoke and oidc discovery all with sensible defaults from just a few lines of configuration">
  <rect x="20" y="20" width="200" height="50" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="120" y="42" fill="#6db33f" font-size="9.5" text-anchor="middle" font-family="sans-serif">authorizationServer()</text>
  <text x="120" y="58" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">+ Customizer.withDefaults()</text>

  <line x1="220" y1="45" x2="260" y2="45" stroke="#6db33f" stroke-width="1.6" marker-end="url(#dc6)"/>

  <rect x="265" y="15" width="140" height="30" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="335" y="35" fill="#79c0ff" font-size="8.5" text-anchor="middle" font-family="sans-serif">/oauth2/authorize</text>

  <rect x="265" y="50" width="140" height="30" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="335" y="70" fill="#79c0ff" font-size="8.5" text-anchor="middle" font-family="sans-serif">/oauth2/token</text>

  <rect x="415" y="15" width="150" height="30" rx="5" fill="#1c2430" stroke="#f0883e" stroke-width="1.2"/>
  <text x="490" y="35" fill="#f0883e" font-size="8.5" text-anchor="middle" font-family="sans-serif">/oauth2/jwks</text>

  <rect x="415" y="50" width="150" height="30" rx="5" fill="#1c2430" stroke="#f0883e" stroke-width="1.2"/>
  <text x="490" y="70" fill="#f0883e" font-size="8.5" text-anchor="middle" font-family="sans-serif">/.well-known/openid-configuration</text>

  <rect x="40" y="100" width="540" height="30" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="310" y="120" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">/oauth2/introspect, /oauth2/revoke, /userinfo, ... -- all registered automatically</text>

  <text x="320" y="160" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">still needs: a RegisteredClientRepository and a signing key source to be genuinely functional</text>

  <defs><marker id="dc6" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker></defs>
</svg>

One configurer call registers the entire endpoint family; a client repository and signing key are the minimum additional pieces needed for it to actually issue tokens.

## 5. Runnable example

The scenario: model the default configuration's endpoint registration and the minimal additional beans it needs, growing from a bare endpoint-listing check into a functioning minimal token issuance, then into confirming the OIDC discovery metadata correctly reflects every registered endpoint — precisely what a real client library would query first.

### Level 1 — Basic

Register the default endpoint set, confirming it's complete.

```java
import java.util.*;

public class DefaultConfigLevel1 {
    static class AuthorizationServerConfigurer {
        private final Set<String> registeredEndpoints = new LinkedHashSet<>();

        // mirrors OAuth2AuthorizationServerConfigurer.authorizationServer() with defaults
        AuthorizationServerConfigurer withDefaults() {
            registeredEndpoints.addAll(List.of(
                    "/oauth2/authorize", "/oauth2/token", "/oauth2/jwks",
                    "/oauth2/introspect", "/oauth2/revoke",
                    "/.well-known/openid-configuration", "/.well-known/oauth-authorization-server",
                    "/userinfo"));
            return this;
        }

        Set<String> getEndpoints() { return registeredEndpoints; }
    }

    public static void main(String[] args) {
        AuthorizationServerConfigurer configurer = new AuthorizationServerConfigurer().withDefaults();

        System.out.println("registered endpoints: " + configurer.getEndpoints().size());
        System.out.println("includes token endpoint: " + configurer.getEndpoints().contains("/oauth2/token"));
        System.out.println("includes OIDC discovery: " + configurer.getEndpoints().contains("/.well-known/openid-configuration"));
    }
}
```

**How to run:** save as `DefaultConfigLevel1.java`, run `java DefaultConfigLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
registered endpoints: 8
includes token endpoint: true
includes OIDC discovery: true
```

`AuthorizationServerConfigurer.withDefaults` mirrors exactly what `OAuth2AuthorizationServerConfigurer.authorizationServer()` with `Customizer.withDefaults()` provides: the entire family of standard OAuth2/OIDC endpoints, registered from a single call, with no per-endpoint configuration required to get a spec-conformant baseline.

### Level 2 — Intermediate

Add the two minimum additional pieces (a registered client, a signing key) needed for the default configuration to actually issue a token.

```java
import java.util.*;

public class DefaultConfigLevel2 {
    record RegisteredClient(String clientId, String clientSecret) {}
    record SigningKey(String keyId, String keyMaterial) {}
    record IssuedToken(String value, String signedByKeyId) {}

    static class MinimalAuthorizationServer {
        private RegisteredClientRepositoryStub clientRepository;
        private SigningKey signingKey;

        void setClientRepository(RegisteredClientRepositoryStub repo) { this.clientRepository = repo; }
        void setSigningKey(SigningKey key) { this.signingKey = key; }

        IssuedToken issueToken(String clientId, String clientSecret) {
            if (clientRepository == null) throw new IllegalStateException("no RegisteredClientRepository configured");
            if (signingKey == null) throw new IllegalStateException("no signing key source configured");
            RegisteredClient client = clientRepository.findByClientId(clientId);
            if (client == null || !client.clientSecret().equals(clientSecret)) throw new IllegalStateException("invalid_client");
            return new IssuedToken("token-" + UUID.randomUUID().toString().substring(0, 8), signingKey.keyId());
        }
    }

    static class RegisteredClientRepositoryStub {
        private final Map<String, RegisteredClient> clients = new HashMap<>();
        void register(RegisteredClient client) { clients.put(client.clientId(), client); }
        RegisteredClient findByClientId(String clientId) { return clients.get(clientId); }
    }

    public static void main(String[] args) {
        MinimalAuthorizationServer server = new MinimalAuthorizationServer();

        try {
            server.issueToken("my-app", "secret");
        } catch (IllegalStateException e) {
            System.out.println("before configuring beans: " + e.getMessage());
        }

        RegisteredClientRepositoryStub repository = new RegisteredClientRepositoryStub();
        repository.register(new RegisteredClient("my-app", "secret"));
        server.setClientRepository(repository);
        server.setSigningKey(new SigningKey("key-1", "generated-rsa-key-material"));

        IssuedToken token = server.issueToken("my-app", "secret");
        System.out.println("token issued: " + token.value() + " (signed with " + token.signedByKeyId() + ")");
    }
}
```

**How to run:** save as `DefaultConfigLevel2.java`, run `java DefaultConfigLevel2.java` (JDK 17+ runs single files directly).

Expected output (token value varies):
```
before configuring beans: no RegisteredClientRepository configured
token issued: token-a1b2c3d4 (signed with key-1)
```

What changed: `MinimalAuthorizationServer` now models exactly the two additional beans (a `RegisteredClientRepository`, a signing key source) the default endpoint configuration from Level 1 still needs before it can genuinely function — without them, the endpoints exist but have nothing to actually operate against, confirming the core concept's point that the endpoint family alone isn't sufficient for a working instance.

### Level 3 — Advanced

Verify the OIDC discovery document correctly reflects every registered endpoint — exactly what a real OIDC client library queries first, before attempting any actual authorization flow, to learn where each endpoint actually lives.

```java
import java.util.*;

public class DefaultConfigLevel3 {
    record OidcDiscoveryDocument(String issuer, String authorizationEndpoint, String tokenEndpoint,
                                  String jwksUri, String userinfoEndpoint) {}

    static class MinimalAuthorizationServer {
        private final String issuer;
        MinimalAuthorizationServer(String issuer) { this.issuer = issuer; }

        // mirrors GET /.well-known/openid-configuration -- built from the SAME configuration
        // that registered every individual endpoint in Level 1
        OidcDiscoveryDocument buildDiscoveryDocument() {
            return new OidcDiscoveryDocument(
                    issuer,
                    issuer + "/oauth2/authorize",
                    issuer + "/oauth2/token",
                    issuer + "/oauth2/jwks",
                    issuer + "/userinfo");
        }
    }

    // mirrors a REAL OIDC client library's discovery-driven flow
    static void clientDiscoversAndUsesEndpoints(MinimalAuthorizationServer server) {
        OidcDiscoveryDocument discovery = server.buildDiscoveryDocument();
        System.out.println("client discovered issuer: " + discovery.issuer());
        System.out.println("client will redirect users to: " + discovery.authorizationEndpoint());
        System.out.println("client will exchange codes at: " + discovery.tokenEndpoint());
        System.out.println("client will verify JWTs using keys from: " + discovery.jwksUri());
        System.out.println("client will fetch profile data from: " + discovery.userinfoEndpoint());
    }

    public static void main(String[] args) {
        MinimalAuthorizationServer server = new MinimalAuthorizationServer("https://auth.example.com");
        clientDiscoversAndUsesEndpoints(server);
    }
}
```

**How to run:** save as `DefaultConfigLevel3.java`, run `java DefaultConfigLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
client discovered issuer: https://auth.example.com
client will redirect users to: https://auth.example.com/oauth2/authorize
client will exchange codes at: https://auth.example.com/oauth2/token
client will verify JWTs using keys from: https://auth.example.com/oauth2/jwks
client will fetch profile data from: https://auth.example.com/userinfo
```

What changed: `buildDiscoveryDocument` constructs exactly the metadata document a real OIDC client (built with `oauth2Login()`, card 0088; or `RelyingPartyRegistrations.fromMetadataLocation(...)`-style discovery, card 0110) would fetch and parse before ever initiating a login flow — every endpoint URL follows directly from the `issuer` base, demonstrating that the default configuration's endpoints are automatically discoverable, not just individually reachable if you already know their paths.

## 6. Walkthrough

Trace a client application's first interaction with a freshly-configured, default-settings authorization server.

**Step 1 — the client application starts up and needs to know this authorization server's endpoints.** Rather than hard-coding each URL, it fetches the discovery document — corresponding to `server.buildDiscoveryDocument()` in Level 3:
```
GET /.well-known/openid-configuration HTTP/1.1
Host: auth.example.com
```

**Step 2 — the response gives the client everything it needs, derived automatically from the default configuration:**
```
HTTP/1.1 200 OK
Content-Type: application/json

{"issuer":"https://auth.example.com","authorization_endpoint":"https://auth.example.com/oauth2/authorize",
 "token_endpoint":"https://auth.example.com/oauth2/token","jwks_uri":"https://auth.example.com/oauth2/jwks",
 "userinfo_endpoint":"https://auth.example.com/userinfo"}
```

**Step 3 — the client redirects a user's browser to the authorization endpoint**, discovered in step 2, beginning card 0090's Authorization Code grant flow:
```
GET /oauth2/authorize?client_id=my-app&response_type=code&... HTTP/1.1
```
This corresponds to Level 2's `RegisteredClientRepositoryStub.findByClientId("my-app")` needing to find a registered client — confirming this is precisely where the "minimum additional beans" this card discusses become necessary: the endpoint exists (from the default configuration), but it needs a real registered client to operate against.

**Step 4 — after the user authenticates and the code is exchanged**, the token endpoint (also discovered in step 2) issues a token — corresponding to `server.issueToken("my-app", "secret")` in Level 2, requiring both the client repository and the signing key to actually succeed.

**Step 5 — the resource server, elsewhere, validates the issued JWT** by fetching keys from `jwks_uri` (also from the discovery document) — corresponding to card 0101's `JwtDecoder` fetching from exactly this URL, closing the loop from "here is a default-configured authorization server" to "a real client and resource server can interoperate with it using nothing but the discovered metadata."

```
client fetches /.well-known/openid-configuration (default config's discovery endpoint)
        |
        v
client redirects to /oauth2/authorize (default config's authorization endpoint)
        |
        v (requires a REAL RegisteredClientRepository entry)
user authenticates, code issued, exchanged at /oauth2/token (default config's token endpoint)
        |
        v (requires a REAL signing key)
token issued, signed -- resource server validates it via /oauth2/jwks (default config's JWKS endpoint)
```

## 7. Gotchas & takeaways

> **Gotcha:** the default configuration registers every standard endpoint's *routing and protocol handling*, but a genuinely useful authorization server still requires at least one registered client and a signing key configured separately — omitting either produces an application that starts successfully and responds to requests at the correct paths, but fails the moment any real client attempts an actual flow, since there's nothing registered to authenticate against or nothing to sign tokens with.

- `OAuth2AuthorizationServerConfigurer.authorizationServer()` with `Customizer.withDefaults()` registers the complete family of standard OAuth2/OIDC endpoints from a single configuration call, providing a spec-conformant baseline immediately.
- A working instance still requires, at minimum, a `RegisteredClientRepository` (at least one registered client) and a signing key source — the endpoint registration alone isn't sufficient for genuine token issuance.
- The OIDC discovery document (`/.well-known/openid-configuration`) is built automatically from the same configuration that registered each individual endpoint, letting real client libraries discover and use them without any hard-coded URLs.
- Starting from this minimal, defaults-based configuration and incrementally layering customization (custom client registration, custom claims, custom consent handling) is the recommended learning and development path, rather than attempting to configure every option from the outset.
- The `securityMatcher(authorizationServerConfigurer.getEndpointsMatcher())` scoping, from card 0002's two-chain pattern, ensures this configuration applies only to the OAuth2/OIDC-specific endpoints, leaving the rest of the application's security configuration (login pages, ordinary endpoints) entirely separate.
