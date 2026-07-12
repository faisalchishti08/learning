---
card: spring-authorization-server
gi: 43
slug: custom-consent-page
title: "Custom consent page"
---

## 1. What it is

The consent page is the screen shown to a user mid-authorization-flow (card 0026) listing what a client is requesting and asking for approval. Spring Authorization Server ships a functional default consent page, but production apps almost always replace it with a branded one by setting `.consentPage("/oauth2/consent")` on the authorization endpoint configurer and supplying a matching controller.

## 2. Why & when

The default consent page (a plain, unstyled HTML form) works for development but is the single moment in the entire OAuth2 flow where a user makes an active, informed trust decision — "should this app be allowed to read my tasks?" A generic, unbranded page at this exact moment is both a poor user experience and, from a security-awareness standpoint, actually undesirable: an unfamiliar-looking consent screen trains users to click through without reading, which is precisely the habit phishing pages exploit.

Reach for a custom consent page when:

- Shipping any production authorization server — matching the consent screen's branding to the rest of the login experience (card 0042) builds user trust and recognition.
- Needing to display scope descriptions in human language ("Read your task list" instead of a raw `tasks.read` string) — the default page shows raw scope identifiers.
- Debugging "users are approving things they don't understand" — often traced back to a consent page that doesn't clearly translate scopes into plain-language descriptions of what's being granted.

## 3. Core concept

Think of the default consent page as a generic government form with checkbox codes ("Form 27-B: grant access to subsection 4.2") versus a custom one as a clearly written permission dialog a modern phone shows before an app accesses your camera: "TaskTracker wants to: Read your task list. Allow / Deny." Both convey the same underlying permission grant, but only the second one is actually legible to the person making the decision — and legibility is the entire point of requiring consent in the first place.

```
GET /oauth2/consent
    ?client_id=task-tracker
    &scope=tasks.read tasks.write
    &state=<consent-specific-csrf-state>
```

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Authorization endpoint renders the configured custom consent page, which submits back the user's scope selections">
  <rect x="20" y="70" width="180" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Authorization</text>
  <text x="110" y="110" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Endpoint Filter</text>

  <rect x="280" y="30" width="340" height="150" rx="10" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="450" y="55" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">TaskTracker wants to:</text>
  <text x="450" y="80" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">[x] Read your task list</text>
  <text x="450" y="100" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">[ ] Create and edit tasks</text>
  <rect x="320" y="130" width="90" height="30" rx="6" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="365" y="150" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">Allow</text>
  <rect x="430" y="130" width="90" height="30" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="475" y="150" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">Deny</text>

  <line x1="200" y1="100" x2="275" y2="100" stroke="#8b949e" stroke-width="1.5"/>
</svg>

Individual scopes are selectable, not all-or-nothing — a user can grant a subset of what was requested.

## 5. Runnable example

The scenario: building a branded consent controller, growing to show human-readable scope descriptions instead of raw identifiers, and finally to support partial scope approval where the user deselects individual permissions.

### Level 1 — Basic

```java
// ConsentController.java
import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;

@Controller
public class ConsentController {

    @GetMapping("/oauth2/consent")
    public String consent(Authentication authentication, Model model,
                           @RequestParam("client_id") String clientId,
                           @RequestParam("scope") String scope,
                           @RequestParam("state") String state) {

        model.addAttribute("clientId", clientId);
        model.addAttribute("scopes", scope.split(" "));
        model.addAttribute("state", state);
        model.addAttribute("principalName", authentication.getName());

        return "consent"; // renders templates/consent.html
    }
}
```

**How to run:** register `.authorizationEndpoint(ae -> ae.consentPage("/oauth2/consent"))` on the configurer (card 0026) and add this controller plus a Thymeleaf template. Trigger an authorization request for a client requiring consent: expect this controller's custom page to render instead of the library's default.

### Level 2 — Intermediate

Raw scope strings like `tasks.write` mean nothing to end users — production maps each known scope to a human-readable description before rendering.

```java
import java.util.Map;

public class ScopeDescriptions {

    private static final Map<String, String> DESCRIPTIONS = Map.of(
            "tasks.read", "Read your task list",
            "tasks.write", "Create and edit tasks",
            "profile", "View your basic profile information",
            "email", "View your email address");

    public String describe(String scope) {
        return DESCRIPTIONS.getOrDefault(scope, scope); // fall back to raw scope if undocumented
    }
}
```

**How to run:** call `describe(scope)` for each scope in `ConsentController` before adding it to the model, and render the descriptions instead of raw scope strings in the template. Expected output for scope `tasks.write`: "Create and edit tasks" shown in the UI instead of the literal string `tasks.write`.

What changed: users now see plain-language descriptions of what they're approving instead of internal API identifiers, directly addressing the informed-consent goal this whole page exists for.

### Level 3 — Advanced

Production consent pages let users approve a *subset* of requested scopes, not just all-or-nothing — the submitted form posts back only the checked scopes, and the server must record exactly that subset as the approved consent, not silently grant everything originally requested.

```java
import org.springframework.security.oauth2.server.authorization.OAuth2AuthorizationConsent;
import org.springframework.security.oauth2.server.authorization.OAuth2AuthorizationConsentService;
import org.springframework.security.oauth2.server.authorization.client.RegisteredClient;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;

import java.util.List;

@Controller
public class ConsentSubmissionController {

    private final OAuth2AuthorizationConsentService consentService;

    public ConsentSubmissionController(OAuth2AuthorizationConsentService consentService) {
        this.consentService = consentService;
    }

    @PostMapping("/oauth2/consent")
    public String submitConsent(RegisteredClient client, String principalName,
                                 @RequestParam(value = "scope", required = false) List<String> approvedScopes,
                                 @RequestParam("state") String state) {

        OAuth2AuthorizationConsent.Builder builder = OAuth2AuthorizationConsent.withId(
                client.getId(), principalName);

        if (approvedScopes != null) {
            approvedScopes.forEach(builder::scope); // only the scopes the user actually checked
        }

        consentService.save(builder.build());

        return "redirect:/oauth2/authorize?client_id=" + client.getClientId()
                + "&state=" + state; // resume the original request; unapproved scopes are simply absent
    }
}
```

**How to run:** submit the consent form with only `tasks.read` checked, even though the original request asked for `tasks.read tasks.write`. Expected behavior: the saved `OAuth2AuthorizationConsent` (card 0018) contains only `tasks.read`; the subsequently issued access token's `scope` claim is `tasks.read` alone, and any call the client makes requiring `tasks.write` fails with `insufficient_scope`.

What changed and why it's production-flavored: users get genuine, granular control rather than a binary "trust everything or nothing" choice, which is both better UX and a real security improvement — a client that later gets compromised has a narrower blast radius if the user never approved its most sensitive requested scope in the first place.

## 6. Walkthrough

Tracing a consent interaction with partial approval, in execution order:

1. The authorization endpoint filter (card 0026) determines consent is required — either first-time consent, or a scope beyond what was previously approved — and redirects to `/oauth2/consent` with the client, requested scopes, and a consent-flow `state` in the query string.
2. `ConsentController.consent(...)` (Level 1) loads the request parameters and, via `ScopeDescriptions` (Level 2), maps each raw scope to a human-readable label before rendering the page.
3. The user sees a checkbox per scope, unchecks `tasks.write`, and submits.
4. `ConsentSubmissionController.submitConsent(...)` (Level 3) receives only the scopes present in the submitted form (`approvedScopes` — here, just `tasks.read`) and builds an `OAuth2AuthorizationConsent` containing exactly that subset.
5. The consent is saved via `OAuth2AuthorizationConsentService` (card 0018), and the browser is redirected back to `/oauth2/authorize?...` with the original `state`.
6. This time, the authorization endpoint filter finds an existing consent covering the (now-reduced) approved scope set and proceeds straight to code issuance — no further consent prompt.
7. The eventual access token (card 0027) carries `scope=tasks.read` only; any client call requiring `tasks.write` is rejected downstream with `403 insufficient_scope`.

```
GET /oauth2/authorize (scope=tasks.read tasks.write)
   |  consent required
redirect /oauth2/consent (Level 1: render with human-readable descriptions)
   |
user unchecks tasks.write, submits
   |
POST /oauth2/consent  -> save OAuth2AuthorizationConsent(scope=[tasks.read])
   |
redirect back to /oauth2/authorize -> consent found, matches -> issue code
   |
POST /oauth2/token -> access_token{scope: "tasks.read"}
```

## 7. Gotchas & takeaways

> A consent page that submits *all originally requested scopes back* regardless of which checkboxes the user actually selected silently defeats the purpose of asking at all — always read the approved set from the submitted form, never from the original request parameters, when building the `OAuth2AuthorizationConsent`.

- Scope descriptions (Level 2) should be maintained alongside the scopes themselves — an undocumented scope silently falling back to its raw identifier in the UI is a sign the descriptions map has drifted out of sync with what the server actually issues.
- Consent, once granted, is remembered (card 0018) — a returning user who previously approved `tasks.read` won't see the consent page again for that same scope, only for *new* scopes a client starts requesting later.
- The consent page must be reachable while authenticated but before full authorization completes — it sits in the same "chain #2" territory as the login page (card 0042), not inside the protocol endpoint chain.
- Never render raw, unescaped client-supplied values (like `client_id` or a client-provided display name) directly into the consent page's HTML without proper templating escaping — this page is a prime target for reflected content injection given how much trust users place in it.
- If testing shows the consent page appearing on every single login even for previously approved scopes, check that the consent service lookup (card 0018) is actually being hit with a matching `registeredClientId` and `principalName` — a mismatch there causes every request to look like first-time consent.
