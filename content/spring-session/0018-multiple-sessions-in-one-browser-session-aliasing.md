---
card: spring-session
gi: 18
slug: multiple-sessions-in-one-browser-session-aliasing
title: "Multiple sessions in one browser (session aliasing)"
---

## 1. What it is

Session aliasing (backed by `MultiSessionHttpSessionIdResolver` in Spring Session) lets a single browser hold multiple independent sessions simultaneously — for example, being logged into two different accounts of the same application in two different browser tabs — by encoding an alias alongside the session ID in the cookie, rather than the browser's normal one-cookie-per-domain limitation forcing every tab to share a single session.

## 2. Why & when

A browser's default cookie behavior ties one cookie value to one domain — every tab open to the same site shares the exact same cookie jar, and therefore the exact same session. This is usually exactly what's wanted (a user's tabs should all reflect the same login), but some legitimate use cases need the opposite: a support agent needing to be logged into two different customer-facing accounts simultaneously to compare data side by side, or a personal user wanting to be logged into two different accounts (a work account and a personal account) in separate tabs without using separate browser profiles or incognito windows.

Reach for session aliasing when:

- Building admin or support tooling where staff routinely need multiple authenticated sessions open simultaneously for comparison or investigation purposes.
- Supporting power users who want multi-account access without resorting to separate browser profiles, incognito windows, or a different browser entirely — a real usability improvement for that specific audience.
- Deciding whether this complexity is warranted at all — for the vast majority of applications, the default single-session-per-browser behavior is exactly right, and aliasing should be reached for only when there's a genuine, specific multi-session need, not as a general-purpose feature.

## 3. Core concept

Think of a browser's normal cookie behavior as a single hotel room key that works for every door of a specific hotel chain — walk into any branch, the same key works, because it's tied to you as a guest, not to a specific room. Session aliasing is like the hotel issuing several distinctly-labeled keys, each opening a *different* room under a different guest name, all carried in the same keychain (the same browser) — and requiring you to specify, on each attempt to open a door, which specific labeled key you mean to use, since simply presenting "a key from this keychain" is now ambiguous.

```
Cookie: SESSION_alias1=abc123; SESSION_alias2=def456
   |
Request to /switch-session/alias2 tells the server which aliased session to use for this tab
```

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="One browser holds two independently aliased session cookies, each mapping to a completely separate session and account">
  <rect x="20" y="20" width="600" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="50" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Browser cookie jar: SESSION_0=abc123; SESSION_1=def456</text>

  <rect x="60" y="120" width="220" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="170" y="145" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Tab 1: alias 0</text>
  <text x="170" y="163" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">logged in as support-agent</text>

  <rect x="360" y="120" width="220" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="470" y="145" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Tab 2: alias 1</text>
  <text x="470" y="163" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">logged in as customer-42</text>

  <line x1="170" y1="70" x2="170" y2="115" stroke="#3fb950" stroke-width="1.5"/>
  <line x1="470" y1="70" x2="470" y2="115" stroke="#3fb950" stroke-width="1.5"/>
</svg>

Both aliases live in the same cookie jar; the server distinguishes and routes to the correct underlying session based on which alias a given request targets.

## 5. Runnable example

The scenario: enabling multi-session support for a support tool, growing to build a UI switcher letting staff explicitly pick which aliased session a given tab should act as, and finally to enforce a maximum number of simultaneous aliased sessions per browser to prevent unbounded growth of forgotten, still-active aliases.

### Level 1 — Basic

```java
// MultiSessionConfig.java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.session.web.http.HttpSessionIdResolver;
import org.springframework.session.web.http.CookieHttpSessionIdResolver;

@Configuration
public class MultiSessionConfig {

    // MultiSessionHttpSessionIdResolver wraps a delegate resolver, adding alias-aware
    // cookie parsing so multiple session IDs can coexist under distinctly-named cookies.
    @Bean
    public HttpSessionIdResolver httpSessionIdResolver() {
        return new org.springframework.session.web.http.MultiSessionHttpSessionIdResolver(
                new CookieHttpSessionIdResolver());
    }
}
```

**How to run:** with this resolver active, open the app in one tab and log in as user A. Open a second tab and navigate to a URL requesting a *new* aliased session (typically `/?_s=1` or an equivalent alias-selecting mechanism the resolver exposes), then log in as user B in that tab. Expected result: both tabs remain independently authenticated as their respective users, with `document.cookie` in the browser showing two distinctly-suffixed session cookies rather than one shared cookie being overwritten.

### Level 2 — Intermediate

A real support tool needs an explicit, visible UI for switching between or adding aliased sessions, rather than relying on staff manually constructing alias-selecting URLs.

```java
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;

@RestController
public class SessionSwitcherController {

    @GetMapping("/api/sessions/available")
    public Map<String, Object> listAvailableSessionSlots(HttpServletRequest request) {
        // In a real implementation, this inspects the cookies present and reports which
        // alias slots (0, 1, 2, ...) are currently occupied by an authenticated session,
        // and which principal each one represents, sourced via the indexed repository
        // (findByPrincipalName-style lookups, card 0003) keyed off each alias's session ID.
        return Map.of(
                "slots", List.of(
                        Map.of("alias", "0", "principal", "support-agent-42"),
                        Map.of("alias", "1", "principal", "customer-7"),
                        Map.of("alias", "2", "principal", null) // empty slot, available for a new login
                )
        );
    }
}
```

**How to run:** build a small UI component calling this endpoint and rendering a tab-like switcher showing "Session 0: support-agent-42", "Session 1: customer-7", "+ New session" for the empty slot. Expected behavior: staff can see at a glance which accounts are currently active in which browser "slot" and deliberately choose to add a new one or switch context, rather than needing to remember or guess alias numbers.

What changed: aliasing is no longer a hidden mechanism only reachable via crafted URLs — it's now a real, visible feature staff can operate confidently, which is what makes the underlying capability actually usable in practice rather than a developer-only curiosity.

### Level 3 — Advanced

Without a limit, a support agent could accumulate dozens of forgotten, still-active aliased sessions over a long shift — each one a live, authenticated session consuming store resources and, more importantly, representing a lingering security exposure (an old customer session left open and forgotten). A maximum alias count with explicit eviction addresses this.

```java
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.session.FindByIndexNameSessionRepository;
import org.springframework.session.Session;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class AliasLimitController {

    private static final int MAX_ALIASES_PER_BROWSER = 5;

    private final FindByIndexNameSessionRepository<? extends Session> sessionRepository;

    public AliasLimitController(FindByIndexNameSessionRepository<? extends Session> sessionRepository) {
        this.sessionRepository = sessionRepository;
    }

    @PostMapping("/api/sessions/new-alias")
    public String requestNewAlias(HttpServletRequest request) {
        int currentAliasCount = countActiveAliasesInCookies(request);

        if (currentAliasCount >= MAX_ALIASES_PER_BROWSER) {
            return "Maximum of " + MAX_ALIASES_PER_BROWSER
                    + " simultaneous sessions reached. Close an existing session tab before opening another.";
        }
        return "New alias slot available — proceed to login.";
    }

    private int countActiveAliasesInCookies(HttpServletRequest request) {
        if (request.getCookies() == null) return 0;
        return (int) java.util.Arrays.stream(request.getCookies())
                .filter(c -> c.getName().startsWith("SESSION_"))
                .count();
    }
}
```

**How to run:** simulate a browser accumulating aliased sessions by logging into 5 different accounts across 5 tabs, then attempt a 6th. Expected behavior: the 6th attempt is blocked with a clear message rather than silently allowed, prompting the user to consciously close an existing aliased session (which, paired with an explicit "log out this session" action, actually removes both the cookie and the underlying store entry) before opening another.

What changed and why it's production-flavored: unbounded aliasing accumulation is a real, easy-to-overlook risk in exactly the scenario this feature is built for (a busy support agent, a long shift, many customer accounts touched) — capping it forces a deliberate cleanup habit rather than letting forgotten, still-valid sessions to customer accounts pile up silently in a browser profile that might itself be shared or left unattended.

## 6. Walkthrough

Tracing a support agent opening a second aliased session, in execution order:

1. The agent is already logged in via alias `0`, cookie `SESSION_0=abc123`, working normally in one browser tab.
2. They open a new tab and trigger "New session" via `SessionSwitcherController`'s UI (Level 2), which first calls `AliasLimitController.requestNewAlias(...)` (Level 3) to confirm they haven't hit the 5-session cap.
3. Confirmed available, the new tab is directed to a login flow explicitly requesting alias slot `1`; `MultiSessionHttpSessionIdResolver` recognizes this as a request for a *new*, distinct aliased session rather than reusing whatever session cookie `0` currently points to.
4. The agent logs in as a different account in this tab; the resulting session is created and stored under a new session ID, and the response sets a *new*, distinctly-named cookie, `SESSION_1=def456`, alongside the still-present `SESSION_0=abc123` — the browser now holds both.
5. Requests originating from the first tab continue to be resolved against alias `0`'s session (`abc123`); requests from the second tab resolve against alias `1`'s session (`def456`) — `MultiSessionHttpSessionIdResolver` determines which alias a given request is operating under (typically via a URL parameter or path convention the frontend consistently applies per tab) and reads only that specific cookie's value.
6. Later, the agent explicitly closes out alias `1` (logging out of that specific aliased session); the server invalidates that specific underlying session and the response clears only the `SESSION_1` cookie — alias `0`'s session and cookie remain completely untouched, since the two were always independently tracked.

```
Tab 1 (existing): SESSION_0=abc123 -> session for support-agent-42
   |
Agent opens Tab 2: request new alias
   |
AliasLimitController: current count < MAX -> allowed
   |
Login as customer-7 under alias 1 -> new session created, def456
   |
Response: Set-Cookie SESSION_1=def456  (SESSION_0 cookie untouched)
   |
Tab 1 requests -> resolve against SESSION_0 (abc123)
Tab 2 requests -> resolve against SESSION_1 (def456)
```

## 7. Gotchas & takeaways

> Session aliasing adds real complexity to session resolution logic, and it's a niche capability most applications never need — reach for it only when there's a specific, well-understood multi-session use case (support tooling, power-user multi-account access), not as a general default, since the added complexity in cookie handling and session-switching UI has a genuine ongoing maintenance and testing cost.

- Each aliased session is a fully independent session in every respect — separate expiration timers, separate attribute storage, separate everything covered in cards 0001-0015; aliasing only changes how the *cookie layer* maps multiple sessions into one browser, not anything about session behavior itself.
- A visible, explicit UI for managing aliases (Level 2) is essential for this feature to be usable and safe in practice — a purely URL-parameter-driven mechanism invites both user confusion and the kind of forgotten, lingering session risk that Level 3's cap exists to mitigate.
- Capping the maximum number of simultaneous aliases (Level 3) is a reasonable default safeguard for any aliasing feature exposed to real users, particularly in contexts (support tooling, shared or public-facing workstations) where forgotten authenticated sessions to other accounts represent a genuine security concern.
- Test alias-switching logic carefully against browser tab and window behavior specifically — some alias-selection mechanisms rely on URL state or `sessionStorage` (tab-scoped, unlike cookies) to know which alias a given tab is currently operating under, and this state can behave unexpectedly across tab duplication, bookmarked links, or browser session restoration after a crash.
- When debugging "the wrong account's data is showing up in this tab," check first whether the alias-resolution mechanism correctly identified which session cookie this specific request should use — a bug here manifests as data from the wrong aliased account leaking into the wrong tab, which is a meaningfully more serious class of bug than an ordinary single-session mismatch.
