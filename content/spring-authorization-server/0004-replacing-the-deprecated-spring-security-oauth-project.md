---
card: spring-authorization-server
gi: 4
slug: replacing-the-deprecated-spring-security-oauth-project
title: "Replacing the deprecated Spring Security OAuth project"
---

## 1. What it is

Before Spring Authorization Server existed, the Spring ecosystem's answer to "build your own OAuth2 authorization server" was the `spring-security-oauth2` project (commonly called "Spring Security OAuth") — but that project reached end-of-life years ago, receiving only critical security patches, with the Spring team explicitly recommending new projects avoid it and existing ones migrate away. Spring Authorization Server is the official, actively-maintained, purpose-built replacement, designed from the ground up against the modern OAuth 2.1/OIDC 1.0 baseline (card 0003) rather than inheriting the older project's architecture and gradually-accumulated technical debt.

```xml
<!-- OLD, deprecated (do not use for new projects) -->
<dependency>
    <groupId>org.springframework.security.oauth</groupId>
    <artifactId>spring-security-oauth2</artifactId>
</dependency>

<!-- NEW, official replacement -->
<dependency>
    <groupId>org.springframework.security</groupId>
    <artifactId>spring-security-oauth2-authorization-server</artifactId>
</dependency>
```

## 2. Why & when

An application built years ago on `spring-security-oauth2` faces a real, concrete problem: the project it depends on receives no new features, no OAuth 2.1/OIDC 1.0 conformance updates, and increasingly limited security patching — leaving it stuck on aging protocol support while the broader OAuth2/OIDC ecosystem (and the client libraries integrating with it) continues evolving around it. Spring Authorization Server exists specifically to give such applications, and any new project that would otherwise have reached for the old library out of habit or outdated documentation, a clear, actively-maintained path forward — built by largely the same Spring Security team, but as a genuine rewrite against current specifications rather than an incremental patch to legacy code.

Reach for understanding this migration path when:

- Maintaining an existing application built on the old `spring-security-oauth2` project — this is a strong signal to plan a migration, given the old project's end-of-life status and lack of ongoing security patching for anything beyond critical issues.
- Evaluating which library to use for a brand-new authorization server project — `spring-security-oauth2-authorization-server` is unambiguously the correct current choice; the old artifact should never be a first choice for new work.
- Encountering outdated tutorials, Stack Overflow answers, or blog posts referencing `@EnableAuthorizationServer` or `AuthorizationServerConfigurerAdapter` (the old project's configuration style) — these are strong signals the content predates Spring Authorization Server and should be treated with caution, since the configuration model changed substantially.
- Planning the migration itself — understanding what changed (configuration style, `RegisteredClient` replacing the old `ClientDetails`, the `OAuth2AuthorizationServerConfigurer` DSL) is necessary before attempting to port an existing configuration.

## 3. Core concept

```
OLD: spring-security-oauth2 (deprecated, EOL)         NEW: Spring Authorization Server
------------------------------------------------      ------------------------------------------------
@EnableAuthorizationServer                             @EnableWebSecurity + OAuth2AuthorizationServerConfigurer
AuthorizationServerConfigurerAdapter                   OAuth2AuthorizationServerConfigurer.authorizationServer()
ClientDetailsService / ClientDetails                    RegisteredClientRepository / RegisteredClient
InMemoryTokenStore / JdbcTokenStore                     OAuth2AuthorizationService (in-memory or JDBC-backed)
custom UserApprovalHandler                             built-in consent page + customizable OAuth2AuthorizationConsentService
implicit + password grants: SUPPORTED                  implicit + password grants: NOT SUPPORTED (card 0003)
maintenance status: END OF LIFE, security patches only maintenance status: ACTIVELY MAINTAINED, new features

Migration is a REWRITE of the security configuration, not an incremental upgrade --
the configuration MODEL itself changed (annotation-driven adapter classes ->
SecurityFilterChain + configurer DSL, matching every other Spring Security feature
covered throughout this course), not just a version bump.
```

Treating this as "just update the dependency version" will not work — the configuration classes and extension points are genuinely different, requiring an actual migration effort proportional to how deeply the old project's specific APIs were used.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram showing the deprecated end of life spring security oauth2 project on one side receiving only critical patches versus the actively maintained spring authorization server on the other side receiving new features and current specification conformance with an arrow indicating the recommended migration direction">
  <rect x="20" y="20" width="280" height="130" rx="8" fill="#1c2430" stroke="#f85149" stroke-width="1.4"/>
  <text x="160" y="42" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">spring-security-oauth2</text>
  <text x="160" y="60" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">END OF LIFE</text>
  <text x="160" y="80" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">critical security patches ONLY</text>
  <text x="160" y="98" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">no OAuth 2.1 conformance</text>
  <text x="160" y="118" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">supports Implicit + Password grants</text>

  <line x1="300" y1="85" x2="345" y2="85" stroke="#3fb950" stroke-width="2" marker-end="url(#rep4)"/>
  <text x="322" y="75" fill="#3fb950" font-size="8.5" text-anchor="middle" font-family="sans-serif">MIGRATE</text>

  <rect x="350" y="20" width="290" height="130" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.6"/>
  <text x="495" y="42" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Spring Authorization Server</text>
  <text x="495" y="60" fill="#3fb950" font-size="8.5" text-anchor="middle" font-family="sans-serif">ACTIVELY MAINTAINED</text>
  <text x="495" y="80" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">new features, ongoing patches</text>
  <text x="495" y="98" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">OAuth 2.1 / OIDC 1.0 conformant</text>
  <text x="495" y="118" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Implicit + Password grants REMOVED</text>

  <defs><marker id="rep4" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker></defs>
</svg>

The old project's end-of-life status and the new one's active development make the migration direction unambiguous.

## 5. Runnable example

The scenario: model the two configuration styles side by side — an old-style, adapter-based client registration versus the new `RegisteredClient` builder — growing from a bare structural comparison into a small migration checklist runner that verifies an old configuration's key pieces all have a corresponding new-style equivalent.

### Level 1 — Basic

Old-style client configuration versus new-style, side by side.

```java
import java.util.*;

public class ReplacingOldProjectLevel1 {
    // mirrors the OLD project's ClientDetails-style configuration
    record OldStyleClientDetails(String clientId, String clientSecret, List<String> authorizedGrantTypes,
                                  List<String> scopes) {}

    // mirrors the NEW project's RegisteredClient
    record NewRegisteredClient(String clientId, String clientSecret, List<String> authorizationGrantTypes,
                                List<String> scopes) {}

    static NewRegisteredClient migrate(OldStyleClientDetails old) {
        // filter out grant types no longer supported -- IMPLICIT and PASSWORD are dropped (card 0003)
        List<String> supportedGrants = old.authorizedGrantTypes().stream()
                .filter(g -> !g.equals("implicit") && !g.equals("password"))
                .toList();
        return new NewRegisteredClient(old.clientId(), old.clientSecret(), supportedGrants, old.scopes());
    }

    public static void main(String[] args) {
        OldStyleClientDetails oldClient = new OldStyleClientDetails(
                "my-app", "secret", List.of("authorization_code", "implicit", "refresh_token"), List.of("read", "write"));

        NewRegisteredClient migrated = migrate(oldClient);
        System.out.println("migrated grant types (implicit dropped): " + migrated.authorizationGrantTypes());
    }
}
```

**How to run:** save as `ReplacingOldProjectLevel1.java`, run `java ReplacingOldProjectLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
migrated grant types (implicit dropped): [authorization_code, refresh_token]
```

`migrate` mirrors the structural translation a real migration requires: mapping the old `ClientDetails` shape onto the new `RegisteredClient` shape, while dropping grant types no longer supported under the new project's stricter conformance — this is not a mechanical field rename, but a genuine reconciliation with the new baseline's rules.

### Level 2 — Intermediate

A migration checklist verifying every old-style configuration concept has been addressed in the new configuration — catching a configuration gap before it becomes a production surprise.

```java
import java.util.*;

public class ReplacingOldProjectLevel2 {
    record MigrationItem(String oldConcept, String newConcept, boolean addressed) {}

    static class MigrationChecklist {
        private final List<MigrationItem> items = new ArrayList<>();
        void add(String oldConcept, String newConcept, boolean addressed) {
            items.add(new MigrationItem(oldConcept, newConcept, addressed));
        }

        void report() {
            long incomplete = items.stream().filter(i -> !i.addressed()).count();
            for (MigrationItem item : items) {
                System.out.println((item.addressed() ? "[DONE] " : "[PENDING] ")
                        + item.oldConcept() + " -> " + item.newConcept());
            }
            System.out.println(incomplete == 0 ? "migration checklist COMPLETE" : incomplete + " item(s) still incomplete");
        }
    }

    public static void main(String[] args) {
        MigrationChecklist checklist = new MigrationChecklist();
        checklist.add("@EnableAuthorizationServer", "OAuth2AuthorizationServerConfigurer", true);
        checklist.add("ClientDetailsService", "RegisteredClientRepository", true);
        checklist.add("InMemoryTokenStore", "OAuth2AuthorizationService", true);
        checklist.add("custom UserApprovalHandler", "OAuth2AuthorizationConsentService customization", false);

        checklist.report();
    }
}
```

**How to run:** save as `ReplacingOldProjectLevel2.java`, run `java ReplacingOldProjectLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
[DONE] @EnableAuthorizationServer -> OAuth2AuthorizationServerConfigurer
[DONE] ClientDetailsService -> RegisteredClientRepository
[DONE] InMemoryTokenStore -> OAuth2AuthorizationService
[PENDING] custom UserApprovalHandler -> OAuth2AuthorizationConsentService customization
1 item(s) still incomplete
```

What changed: `MigrationChecklist` now tracks whether each old-project concept has a corresponding new-project equivalent actually implemented — surfacing exactly one incomplete item (the consent-handling customization) before the migration is declared finished, mirroring the kind of systematic audit a real migration effort benefits from, rather than assuming a configuration is complete simply because the application compiles and starts.

### Level 3 — Advanced

Model the actual behavioral consequence of an incomplete migration — a grant type the old configuration supported silently failing under the new project, and how to detect this proactively via a compatibility check rather than discovering it from a client's runtime failure.

```java
import java.util.*;

public class ReplacingOldProjectLevel3 {
    record OldStyleClientDetails(String clientId, List<String> authorizedGrantTypes) {}

    static class UnsupportedGrantTypeException extends RuntimeException {
        UnsupportedGrantTypeException(String message) { super(message); }
    }

    static final Set<String> NEW_PROJECT_SUPPORTED_GRANTS = Set.of(
            "authorization_code", "client_credentials", "refresh_token");

    // a PROACTIVE compatibility check, run BEFORE deploying the migrated configuration
    static List<String> findUnsupportedGrants(OldStyleClientDetails oldClient) {
        return oldClient.authorizedGrantTypes().stream()
                .filter(g -> !NEW_PROJECT_SUPPORTED_GRANTS.contains(g))
                .toList();
    }

    static void validateMigration(List<OldStyleClientDetails> oldClients) {
        List<String> allProblems = new ArrayList<>();
        for (OldStyleClientDetails client : oldClients) {
            List<String> unsupported = findUnsupportedGrants(client);
            if (!unsupported.isEmpty()) {
                allProblems.add(client.clientId() + " relies on unsupported grant(s): " + unsupported);
            }
        }
        if (!allProblems.isEmpty()) {
            throw new UnsupportedGrantTypeException(
                    "migration BLOCKED -- the following clients need updating before migrating:\n  "
                            + String.join("\n  ", allProblems));
        }
    }

    public static void main(String[] args) {
        List<OldStyleClientDetails> oldClients = List.of(
                new OldStyleClientDetails("web-app", List.of("authorization_code", "refresh_token")),
                new OldStyleClientDetails("legacy-mobile-app", List.of("password", "refresh_token")), // WILL be a problem
                new OldStyleClientDetails("service-account", List.of("client_credentials")));

        try {
            validateMigration(oldClients);
            System.out.println("all clients are migration-ready");
        } catch (UnsupportedGrantTypeException e) {
            System.out.println(e.getMessage());
        }
    }
}
```

**How to run:** save as `ReplacingOldProjectLevel3.java`, run `java ReplacingOldProjectLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
migration BLOCKED -- the following clients need updating before migrating:
  legacy-mobile-app relies on unsupported grant(s): [password]
```

What changed: `validateMigration` proactively scans every registered client's grant type usage against the new project's supported set *before* the migration is declared complete — catching `legacy-mobile-app`'s reliance on the removed Password grant as a concrete, actionable blocker, rather than discovering it only when that specific mobile app's users start experiencing authentication failures after a production cutover.

## 6. Walkthrough

Trace the discovery and resolution of `legacy-mobile-app`'s incompatibility from Level 3.

**Step 1 — the migration team runs a compatibility audit** across every client registered in the old `spring-security-oauth2`-based configuration, before writing a single line of new configuration — corresponding to `validateMigration(oldClients)` being called as an early, deliberate step.

**Step 2 — `findUnsupportedGrants` checks each client's grant types against the new project's supported set.** For `legacy-mobile-app`, `authorizedGrantTypes()` is `["password", "refresh_token"]`; `"password"` is not in `NEW_PROJECT_SUPPORTED_GRANTS`, so it's flagged.

**Step 3 — the audit surfaces this as a blocking issue**, corresponding to `UnsupportedGrantTypeException` being thrown with a specific, actionable message identifying exactly which client and which grant type are the problem.

**Step 4 — the team must resolve this before migrating**, typically by updating `legacy-mobile-app` itself to use the Authorization Code grant with PKCE (card 0003's mandatory replacement for the Password grant's use case) rather than attempting to preserve Password grant support in the new configuration, since that option simply doesn't exist there.

**Step 5 — once every client is confirmed compatible**, the actual configuration migration proceeds — rewriting `@EnableAuthorizationServer`-style configuration into `OAuth2AuthorizationServerConfigurer` beans, `ClientDetailsService` implementations into `RegisteredClientRepository` ones, and so on, following the mapping this card's core concept section lays out.

```
old project's registered clients
        |
        v
compatibility audit: does EVERY client's grant type usage have a NEW-project equivalent?
        |
   +----+----+
   |         |
 YES        NO -- legacy-mobile-app uses "password"
   |         |
   v         v
proceed   BLOCKED: update legacy-mobile-app to use Authorization Code + PKCE FIRST
with          |
migration     v
           re-run audit -> proceed with migration
```

## 7. Gotchas & takeaways

> **Gotcha:** a client relying on the Password grant (common in older mobile app integrations that predated widespread PKCE support) has no direct configuration-level replacement in Spring Authorization Server — the fix is an actual client-side change (adopting the Authorization Code grant with PKCE), not a server-side setting to preserve old behavior. Migrations blocked on this specific grant type require coordinating a client update alongside the server migration, not just a server-side reconfiguration.

- `spring-security-oauth2` reached end-of-life and receives only critical security patches — Spring Authorization Server is its official, actively-maintained, purpose-built replacement.
- Migration is a genuine rewrite of the security configuration, not an incremental dependency bump — annotation-driven adapter classes give way to the `SecurityFilterChain`/configurer DSL every other Spring Security feature already uses.
- `ClientDetailsService`/`ClientDetails` map onto `RegisteredClientRepository`/`RegisteredClient`; `InMemoryTokenStore`/`JdbcTokenStore` map onto `OAuth2AuthorizationService` implementations — but these are conceptual analogues requiring actual reconfiguration, not drop-in renames.
- Clients relying on the removed Implicit or Password grants need an actual protocol-level change (typically to Authorization Code with PKCE) before migration can complete — there is no server-side configuration path to preserve those grant types.
- A proactive compatibility audit across every registered client's grant type usage, run before attempting the configuration rewrite, catches blocking issues early rather than discovering them as production authentication failures after cutover.
