---
card: spring-framework
gi: 433
slug: htmlunit-integration
title: "HtmlUnit integration"
---

## 1. What it is

Spring's HtmlUnit integration (`MockMvcWebClientBuilder`, `MockMvcWebConnection`) plugs `MockMvc` in as the network layer behind HtmlUnit, a headless, GUI-less Java browser — meaning tests can click links, submit HTML forms, and inspect rendered page content, driving a real server-rendered web application, all without a real server, real sockets, or a real browser, while still exercising the real `DispatcherServlet` and controller stack underneath.

```java
WebClient webClient = MockMvcWebClientBuilder
        .webAppContextSetup(webApplicationContext)
        .build();

HtmlPage loginPage = webClient.getPage("/login");
HtmlForm form = loginPage.getFormByName("loginForm");
form.getInputByName("username").setValueAttribute("ada");
HtmlPage resultPage = form.getButtonByName("submit").click();
```

## 2. Why & when

Testing a server-rendered web application (one producing HTML views via Thymeleaf, JSP, or similar — not a JSON API) purely through `MockMvc`'s `jsonPath`/`xpath` matchers means manually parsing and asserting on raw HTML strings, which is fragile and doesn't reflect how a real user actually interacts with the page (following links, filling in and submitting forms, following redirects). HtmlUnit integration bridges that gap: it gives you a genuine browser-like API — pages, forms, links, buttons — while `MockMvc` remains the network layer, so the actual page-rendering logic (controllers, view resolution, template rendering) under test is completely real, with only the transport mocked, consistent with `MockMvc`'s whole design philosophy from earlier cards in this section.

Reach for HtmlUnit integration when:

- Testing a traditional server-rendered web application's user flows (login, form submission, multi-page navigation) at a higher level than raw HTML string assertions.
- You want tests that read like user interactions (fill in a field, click a button, check the resulting page) rather than low-level HTTP request/response assertions.
- Verifying that server-side view rendering (a Thymeleaf template's actual output, given specific model data) produces the HTML structure your application depends on — form field names, link hrefs — without deploying to a real server.

For a JSON-API-only application with no server-rendered HTML views, this integration doesn't apply — stick with the plain `MockMvc` request-builder/result-matcher vocabulary from the previous cards.

## 3. Core concept

```
 WebClient (HtmlUnit's browser API)
        |
        | network calls routed through
        v
 MockMvcWebConnection   (implements HtmlUnit's WebConnection interface)
        |
        | delegates every "network" request to
        v
 MockMvc.perform(...)    <- same MockMvc used throughout this section
        |
        v
 real DispatcherServlet + real controllers + real view rendering
        |
        v
 HTML response bytes returned back up through MockMvcWebConnection to WebClient
        |
        v
 WebClient parses the HTML into an HtmlPage object graph
   (forms, links, buttons all become real, interactive Java objects)
```

HtmlUnit never knows it isn't talking to a real server — `MockMvcWebConnection` is a complete implementation of HtmlUnit's own network abstraction, backed entirely by `MockMvc` underneath.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="HtmlUnit WebClient routes through MockMvcWebConnection to MockMvc, getting back a real rendered HtmlPage">
  <rect x="10" y="70" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="85" y="92" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">WebClient</text>
  <text x="85" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(HtmlUnit)</text>

  <rect x="240" y="70" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="92" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">MockMvcWebConnection</text>
  <text x="330" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">-&gt; MockMvc.perform()</text>

  <rect x="500" y="70" width="130" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="565" y="92" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">HtmlPage</text>
  <text x="565" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">forms, links, buttons</text>

  <line x1="160" y1="95" x2="235" y2="95" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="420" y1="95" x2="495" y2="95" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

HtmlUnit sees a normal server round trip; `MockMvc` does the real work underneath.

## 5. Runnable example

### Level 1 — Basic

Load a simple server-rendered HTML page via a `MockMvc`-backed `WebClient`, and inspect its content through HtmlUnit's page object API rather than raw HTML string matching.

```java
import org.htmlunit.WebClient;
import org.htmlunit.html.HtmlPage;
import org.springframework.stereotype.Controller;
import org.springframework.test.web.servlet.htmlunit.MockMvcWebClientBuilder;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

public class HtmlUnitBasic {

    @Controller
    static class HomeController {
        @GetMapping("/home")
        String home(Model model) {
            model.addAttribute("greeting", "Welcome to the site");
            return "home"; // resolves to a view -- here rendered inline for a self-contained example
        }
    }

    public static void main(String[] args) throws Exception {
        // A minimal View that renders directly, standing in for a real Thymeleaf/JSP template
        // so this example needs no external template files to be fully self-contained.
        var mockMvc = org.springframework.test.web.servlet.setup.MockMvcBuilders
                .standaloneSetup(new HomeController())
                .setViewResolvers((viewName, locale) -> (model, request, response) -> {
                    response.setContentType("text/html");
                    response.getWriter().write(
                            "<html><body><h1>" + model.get("greeting") + "</h1></body></html>");
                })
                .build();

        WebClient webClient = MockMvcWebClientBuilder.mockMvcSetup(mockMvc).build();

        HtmlPage page = webClient.getPage("http://localhost/home");
        System.out.println("Page title area (h1): " + page.getBody().getFirstChild().asNormalizedText());

        if (!page.asNormalizedText().contains("Welcome to the site")) {
            throw new AssertionError("Expected greeting text on the page");
        }
        System.out.println("HtmlUnit correctly rendered and parsed the real server response -- PASS");

        webClient.close();
    }
}
```

How to run: add `spring-test`, `spring-webmvc`, `org.htmlunit:htmlunit`, and `jakarta.servlet-api` to the classpath, then `java HtmlUnitBasic.java`.

`MockMvcWebClientBuilder.mockMvcSetup(mockMvc)` wires an existing `MockMvc` instance in as HtmlUnit's network layer; `webClient.getPage("http://localhost/home")` looks exactly like a real HtmlUnit call to a real server, but it's routed entirely through `MockMvc` — the response comes from the real `HomeController` and the (here, inline) view rendering, and HtmlUnit parses the resulting HTML into a genuine `HtmlPage` object, letting the test navigate it structurally rather than string-searching raw HTML.

### Level 2 — Intermediate

Fill in and submit an HTML form, following the same interaction pattern a real user (or a real browser automation tool) would use — clicking a submit button and inspecting the resulting page.

```java
import org.htmlunit.WebClient;
import org.htmlunit.html.HtmlForm;
import org.htmlunit.html.HtmlPage;
import org.springframework.stereotype.Controller;
import org.springframework.test.web.servlet.htmlunit.MockMvcWebClientBuilder;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;

public class HtmlUnitIntermediate {

    @Controller
    static class LoginController {
        @GetMapping("/login")
        String loginForm() { return "loginForm"; }

        @PostMapping("/login")
        String doLogin(@RequestParam String username, @RequestParam String password, Model model) {
            boolean success = "ada".equals(username) && "secret".equals(password);
            model.addAttribute("message", success ? "Welcome, " + username + "!" : "Login failed");
            return success ? "welcome" : "loginForm";
        }
    }

    public static void main(String[] args) throws Exception {
        var mockMvc = org.springframework.test.web.servlet.setup.MockMvcBuilders
                .standaloneSetup(new LoginController())
                .setViewResolvers((viewName, locale) -> (model, request, response) -> {
                    response.setContentType("text/html");
                    if ("loginForm".equals(viewName)) {
                        String message = model.get("message") != null ? "<p>" + model.get("message") + "</p>" : "";
                        response.getWriter().write("<html><body>" + message
                                + "<form name='loginForm' method='post' action='/login'>"
                                + "<input name='username' type='text'/>"
                                + "<input name='password' type='password'/>"
                                + "<button name='submit' type='submit'>Log in</button>"
                                + "</form></body></html>");
                    } else { // "welcome"
                        response.getWriter().write("<html><body><h1>" + model.get("message") + "</h1></body></html>");
                    }
                })
                .build();

        WebClient webClient = MockMvcWebClientBuilder.mockMvcSetup(mockMvc).build();

        HtmlPage loginPage = webClient.getPage("http://localhost/login");
        HtmlForm form = loginPage.getFormByName("loginForm");
        form.getInputByName("username").setValueAttribute("ada");
        form.getInputByName("password").setValueAttribute("secret");

        HtmlPage resultPage = form.getButtonByName("submit").click(); // real form submission through MockMvc

        System.out.println("Result page text: " + resultPage.asNormalizedText());
        if (!resultPage.asNormalizedText().contains("Welcome, ada!")) {
            throw new AssertionError("Expected successful login welcome message");
        }
        System.out.println("Form submission flow correctly authenticated -- PASS");

        webClient.close();
    }
}
```

How to run: same dependencies as Level 1, then `java HtmlUnitIntermediate.java`.

`loginPage.getFormByName("loginForm")` and `.getInputByName(...)` navigate the parsed HTML page structurally, exactly as a real browser's DOM API would — no manual construction of a `POST` request with form-encoded parameters is needed. `form.getButtonByName("submit").click()` triggers HtmlUnit to build and submit the real form (reading its `method`/`action` attributes from the parsed HTML), routes that submission through `MockMvcWebConnection` into `MockMvc`, and returns the resulting rendered page — testing the entire login flow the way a user would actually experience it, while `LoginController`'s real logic runs underneath.

### Level 3 — Advanced

Follow a redirect and verify cookie-based session behavior across multiple page loads — testing that a server-rendered application's authentication state persists correctly across what HtmlUnit treats as separate "page visits," exactly mirroring real browser session behavior.

```java
import org.htmlunit.WebClient;
import org.htmlunit.html.HtmlForm;
import org.htmlunit.html.HtmlPage;
import jakarta.servlet.http.Cookie;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;
import org.springframework.test.web.servlet.htmlunit.MockMvcWebClientBuilder;

public class HtmlUnitAdvanced {

    @Controller
    static class SessionAwareController {
        @GetMapping("/login")
        String loginForm() { return "loginForm"; }

        @PostMapping("/login")
        String doLogin(@RequestParam String username, jakarta.servlet.http.HttpServletResponse response) {
            Cookie sessionCookie = new Cookie("APP_SESSION", "session-for-" + username);
            sessionCookie.setPath("/");
            response.addCookie(sessionCookie);
            return "redirect:/dashboard"; // real HTTP redirect, HtmlUnit follows it automatically
        }

        @GetMapping("/dashboard")
        String dashboard(@CookieValue(value = "APP_SESSION", required = false) String session, Model model) {
            if (session == null) {
                model.addAttribute("message", "Not logged in");
            } else {
                model.addAttribute("message", "Dashboard for " + session);
            }
            return "dashboard";
        }
    }

    public static void main(String[] args) throws Exception {
        var mockMvc = org.springframework.test.web.servlet.setup.MockMvcBuilders
                .standaloneSetup(new SessionAwareController())
                .setViewResolvers((viewName, locale) -> (model, request, response) -> {
                    response.setContentType("text/html");
                    if ("loginForm".equals(viewName)) {
                        response.getWriter().write("<html><body>"
                                + "<form name='loginForm' method='post' action='/login'>"
                                + "<input name='username' type='text'/>"
                                + "<button name='submit' type='submit'>Log in</button>"
                                + "</form></body></html>");
                    } else { // "dashboard"
                        response.getWriter().write("<html><body><p>" + model.get("message") + "</p></body></html>");
                    }
                })
                .build();

        WebClient webClient = MockMvcWebClientBuilder.mockMvcSetup(mockMvc).build();

        // Step 1: visit dashboard BEFORE logging in -- no session cookie exists yet.
        HtmlPage before = webClient.getPage("http://localhost/dashboard");
        System.out.println("Before login: " + before.asNormalizedText());
        if (!before.asNormalizedText().contains("Not logged in")) throw new AssertionError("Expected not-logged-in state");

        // Step 2: submit the login form -- server sets a cookie and redirects; HtmlUnit follows automatically.
        HtmlPage loginPage = webClient.getPage("http://localhost/login");
        HtmlForm form = loginPage.getFormByName("loginForm");
        form.getInputByName("username").setValueAttribute("ada");
        HtmlPage afterLogin = form.getButtonByName("submit").click();

        System.out.println("After login (redirected to dashboard): " + afterLogin.asNormalizedText());
        if (!afterLogin.asNormalizedText().contains("Dashboard for session-for-ada")) {
            throw new AssertionError("Expected authenticated dashboard content after redirect");
        }
        System.out.println("Redirect-following and session-cookie persistence confirmed -- PASS");

        // Step 3: visit dashboard AGAIN as a separate page load -- cookie should still be attached automatically.
        HtmlPage revisit = webClient.getPage("http://localhost/dashboard");
        System.out.println("Revisiting dashboard: " + revisit.asNormalizedText());
        if (!revisit.asNormalizedText().contains("Dashboard for session-for-ada")) {
            throw new AssertionError("Expected session cookie to persist across separate page loads");
        }
        System.out.println("Session cookie correctly persisted across separate WebClient page loads -- PASS");

        webClient.close();
    }
}
```

How to run: same dependencies as Level 1, then `java HtmlUnitAdvanced.java`.

`return "redirect:/dashboard"` triggers a real `302` HTTP redirect response; HtmlUnit's `WebClient` automatically follows redirects by default, so `form.getButtonByName("submit").click()` returns the *dashboard* page directly, not the raw redirect response — exactly how a real browser behaves. `WebClient` also automatically manages cookies across requests, the same way a real browser's cookie jar does, which is why the third, entirely separate `webClient.getPage("http://localhost/dashboard")` call still carries the `APP_SESSION` cookie set during login, without the test manually re-attaching it.

## 6. Walkthrough

Trace `HtmlUnitAdvanced.main`'s login-and-redirect sequence:

1. **Pre-login dashboard visit.** `webClient.getPage("http://localhost/dashboard")` routes through `MockMvcWebConnection` into `MockMvc`, reaching `dashboard(session=null, ...)` since no cookie has been set yet — `"Not logged in"` renders.
2. **Login page loaded.** `webClient.getPage("http://localhost/login")` similarly renders the login form via `MockMvc`; HtmlUnit parses it into an `HtmlPage` with a navigable `HtmlForm`.
3. **Form filled and submitted.** `form.getInputByName("username").setValueAttribute("ada")` sets the field value on HtmlUnit's in-memory DOM representation; `.click()` on the submit button causes HtmlUnit to construct a real `POST /login` request with `username=ada` form-encoded, sent through the same `MockMvcWebConnection`.
4. **Server processes login.** `doLogin("ada", response)` runs for real — it adds an `APP_SESSION` cookie to the mock response and returns `"redirect:/dashboard"`, which Spring MVC's view resolution translates into an actual `302 Found` response with a `Location: /dashboard` header.
5. **HtmlUnit follows the redirect automatically.** Seeing the `302`, `WebClient` (per its default redirect-following configuration) immediately issues a follow-up `GET /dashboard` request — critically, *with* the `APP_SESSION` cookie just received, since `WebClient` tracks cookies exactly like a real browser.
6. **Dashboard renders authenticated.** This follow-up request reaches `dashboard(session="session-for-ada", ...)`, since the cookie is now present; `"Dashboard for session-for-ada"` renders, and this is the page `form.getButtonByName("submit").click()` ultimately returns to the calling code — the whole redirect chain resolved transparently.
7. **Separate revisit, same session.** The third, entirely independent `webClient.getPage("http://localhost/dashboard")` call still carries the same `APP_SESSION` cookie (persisted in `WebClient`'s cookie manager since step 4), so it again reaches the authenticated branch — proving cookie-based session state genuinely persists across what look like completely separate page navigations, exactly matching real multi-page browsing behavior.

```
GET /dashboard (no cookie)          -> "Not logged in"
GET /login                          -> login form rendered
POST /login (username=ada)          -> sets APP_SESSION cookie -> 302 redirect to /dashboard
   [WebClient auto-follows, cookie auto-attached]
GET /dashboard (APP_SESSION cookie) -> "Dashboard for session-for-ada"   <- returned from click()
GET /dashboard (separate call, same cookie jar) -> "Dashboard for session-for-ada"  <- session persisted
```

## 7. Gotchas & takeaways

> Gotcha: `MockMvc`-backed `WebClient` instances default to real HtmlUnit behavior in several ways that can surprise a test author expecting pure request/response isolation — automatic redirect-following (as shown here) and automatic cookie persistence across calls on the *same* `WebClient` instance mean state can leak between what look like separate `getPage(...)` calls within one test, which is exactly the point for testing realistic multi-page flows, but can cause confusing failures if a test reuses one `WebClient` across scenarios that were meant to be independent. Create a fresh `WebClient` (or explicitly clear its cookies) when a test genuinely needs a clean, unauthenticated starting state.

- HtmlUnit integration lets tests interact with a server-rendered application through a genuine browser-like API (pages, forms, links, buttons) while `MockMvc` remains the real network layer underneath — no real server, real sockets, or real browser required.
- `MockMvcWebClientBuilder` wires an existing `MockMvc` (or a `WebApplicationContext`) in as HtmlUnit's `WebConnection` implementation, making every "network" call route through `MockMvc.perform(...)` transparently.
- `WebClient` automatically follows redirects and manages cookies across requests, exactly like a real browser — essential for testing realistic login/session flows without manually re-implementing that behavior in test code.
- This integration specifically suits traditional server-rendered web applications (Thymeleaf, JSP); for JSON-API-only applications, the plain `MockMvc` request-builder/result-matcher vocabulary from earlier cards remains the right tool.
