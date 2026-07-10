---
card: spring-framework
gi: 432
slug: mockmvc-request-builders-result-matchers
title: "MockMvc request builders & result matchers"
---

## 1. What it is

`MockMvcRequestBuilders` and `MockMvcResultMatchers` are the two static-method factory classes providing `MockMvc`'s full request-construction and response-assertion vocabulary — beyond the basic `get`/`post`/`status`/`jsonPath` seen in earlier cards, they cover multipart file uploads, cookies, headers, XML/XPath assertions, and content-type-aware matching, giving you a complete toolkit for expressing exactly what a request looks like and exactly what a response must satisfy.

```java
mockMvc.perform(multipart("/upload").file("file", fileBytes))
        .andExpect(status().isCreated())
        .andExpect(header().string("Location", containsString("/files/")))
        .andExpect(cookie().value("session", notNullValue()));
```

## 2. Why & when

A real HTTP API surface is more than JSON GET/POST bodies — file uploads, cookies, custom headers, content negotiation, and sometimes XML responses are all common, and a test suite needs to construct requests exercising each of these and assert on the corresponding response details precisely. `MockMvcRequestBuilders`/`MockMvcResultMatchers` cover this full surface so you're not limited to testing the simplest JSON-over-HTTP case.

Reach for the broader request-builder/result-matcher vocabulary when:

- Testing file upload endpoints (`multipart(...)`) — a common and easy-to-get-wrong area (content type, field names, multiple files) worth testing explicitly rather than assuming it works.
- Verifying response headers or cookies your API contract depends on (a `Location` header on `201 Created`, a session cookie, a caching header).
- Testing XML responses via `xpath(...)` matchers, when an API supports XML content negotiation alongside or instead of JSON.
- Composing multiple result matchers to verify a response thoroughly in one assertion chain, rather than checking only the status code and calling it done.

## 3. Core concept

```
 MockMvcRequestBuilders:
   get/post/put/delete/patch(url)   <- standard HTTP methods
   multipart(url)                    <- file upload requests
   .param(name, value)                <- query/form parameters
   .content(body).contentType(type)    <- request body + content type
   .cookie(...)                         <- attach cookies
   .header(name, value)                  <- attach headers

 MockMvcResultMatchers:
   status().isXxx()                 <- HTTP status assertions
   header().string(name, matcher)    <- response header assertions
   cookie().value(name, matcher)      <- response cookie assertions
   content().contentType(type)         <- Content-Type assertion
   jsonPath("$.field").value(...)       <- JSON body field assertions
   xpath("//element").string(...)        <- XML body assertions
```

Both classes are pure factories — every method returns an object representing "how to build this part of the request" or "what to check on this part of the response," composed together via `mockMvc.perform(builder).andExpect(matcher).andExpect(matcher)...`.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Request builders construct the request, result matchers verify multiple aspects of the response">
  <rect x="10" y="70" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="100" y="92" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">multipart("/upload")</text>
  <text x="100" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">.file(...)</text>

  <rect x="240" y="70" width="150" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="315" y="99" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">perform(...)</text>

  <rect x="440" y="20" width="180" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="530" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">status().isCreated()</text>

  <rect x="440" y="60" width="180" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="530" y="82" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">header().string(...)</text>

  <rect x="440" y="100" width="180" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="530" y="122" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">cookie().value(...)</text>

  <line x1="190" y1="95" x2="235" y2="95" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="390" y1="90" x2="435" y2="40" stroke="#8b949e" stroke-width="1.2"/>
  <line x1="390" y1="95" x2="435" y2="78" stroke="#8b949e" stroke-width="1.2"/>
  <line x1="390" y1="100" x2="435" y2="115" stroke="#8b949e" stroke-width="1.2"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

One request can be checked against several independent matchers, each verifying a different facet of the response.

## 5. Runnable example

### Level 1 — Basic

`multipart(...)` for a file-upload endpoint, plus `header()` and `content()` matchers checking the response's `Location` header and content type together.

```java
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.bind.annotation.*;

import java.nio.charset.StandardCharsets;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.multipart;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

public class MockMvcMatchersBasic {

    @RestController
    static class UploadController {
        @PostMapping("/upload")
        org.springframework.http.ResponseEntity<String> upload(
                @org.springframework.web.bind.annotation.RequestParam("file")
                org.springframework.web.multipart.MultipartFile file) {
            String location = "/files/" + file.getOriginalFilename();
            return org.springframework.http.ResponseEntity.created(java.net.URI.create(location))
                    .body("Uploaded " + file.getSize() + " bytes");
        }
    }

    public static void main(String[] args) throws Exception {
        MockMvc mockMvc = MockMvcBuilders.standaloneSetup(new UploadController()).build();

        byte[] fileBytes = "hello world".getBytes(StandardCharsets.UTF_8);
        MockMultipartFile mockFile = new MockMultipartFile(
                "file", "greeting.txt", "text/plain", fileBytes);

        mockMvc.perform(multipart("/upload").file(mockFile))
                .andExpect(status().isCreated())
                .andExpect(header().string("Location", "/files/greeting.txt"))
                .andExpect(content().string("Uploaded 11 bytes"));

        System.out.println("multipart upload test -- PASS");
    }
}
```

How to run: add `spring-test`, `spring-webmvc`, and `jakarta.servlet-api` to the classpath, then `java MockMvcMatchersBasic.java`.

`MockMultipartFile("file", "greeting.txt", "text/plain", fileBytes)` simulates an uploaded file with a field name (`"file"`, matching the controller's `@RequestParam`), an original filename, a content type, and actual bytes — no real HTTP multipart encoding needed, since `MockMvc` handles the whole request in memory. `header().string("Location", "/files/greeting.txt")` checks an exact response header value, confirming the controller's `ResponseEntity.created(...)` call set it correctly.

### Level 2 — Intermediate

`cookie()` matchers for verifying session-related behavior, and composing several matchers (status, header, cookie, JSON body) in one assertion chain to thoroughly verify a login-style endpoint's full response contract.

```java
import jakarta.servlet.http.Cookie;
import org.springframework.http.ResponseEntity;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.bind.annotation.*;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

public class MockMvcMatchersIntermediate {

    record LoginResult(boolean success, String username) {}

    @RestController
    static class AuthController {
        @PostMapping("/login")
        ResponseEntity<LoginResult> login(
                @org.springframework.web.bind.annotation.RequestParam String username,
                jakarta.servlet.http.HttpServletResponse response) {
            Cookie sessionCookie = new Cookie("SESSION", "sess-" + username.hashCode());
            sessionCookie.setHttpOnly(true);
            sessionCookie.setPath("/");
            response.addCookie(sessionCookie);
            return ResponseEntity.ok()
                    .header("X-Auth-Provider", "internal")
                    .body(new LoginResult(true, username));
        }
    }

    public static void main(String[] args) throws Exception {
        MockMvc mockMvc = MockMvcBuilders.standaloneSetup(new AuthController()).build();

        mockMvc.perform(post("/login").param("username", "ada"))
                .andExpect(status().isOk())
                .andExpect(header().string("X-Auth-Provider", "internal"))
                .andExpect(cookie().exists("SESSION"))
                .andExpect(cookie().httpOnly("SESSION", true))
                .andExpect(cookie().path("SESSION", "/"))
                .andExpect(jsonPath("$.success").value(true))
                .andExpect(jsonPath("$.username").value("ada"));

        System.out.println("Full login response contract verified in one chain -- PASS");
    }
}
```

How to run: same dependencies as Level 1, then `java MockMvcMatchersIntermediate.java`.

Six independent matchers chain onto one `perform(...)` call, each checking a different facet of the response: HTTP status, a custom header, cookie presence, cookie flags (`httpOnly`, `path`), and two JSON body fields — a thorough test of a login endpoint's complete response contract in one readable assertion chain, rather than several separate, narrower test methods each checking one thing (which is also a valid style, but this demonstrates the matchers composing cleanly when a single test wants comprehensive coverage).

### Level 3 — Advanced

`xpath(...)` matchers for an XML-producing endpoint, and a custom `ResultMatcher` (the underlying functional interface every built-in matcher implements) for an assertion the built-in matchers don't directly express — showing the extension point available when the standard vocabulary isn't quite enough.

```java
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.ResultMatcher;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.bind.annotation.*;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

public class MockMvcMatchersAdvanced {

    @RestController
    static class ProductXmlController {
        @GetMapping(value = "/products/{id}.xml", produces = MediaType.APPLICATION_XML_VALUE)
        String getProductXml(@PathVariable long id) {
            return "<product><id>" + id + "</id><name>Laptop</name><price>999.99</price></product>";
        }

        @GetMapping("/products/{id}/timing")
        org.springframework.http.ResponseEntity<String> getWithTiming(@PathVariable long id) {
            long start = System.nanoTime();
            try { Thread.sleep(5); } catch (InterruptedException ignored) {}
            long elapsedMs = (System.nanoTime() - start) / 1_000_000;
            return org.springframework.http.ResponseEntity.ok()
                    .header("X-Response-Time-Ms", String.valueOf(elapsedMs))
                    .body("id=" + id);
        }
    }

    // A custom ResultMatcher for an assertion the built-in matchers don't directly express:
    // verifying a numeric header falls within an acceptable range.
    static ResultMatcher responseTimeUnder(long maxMillis) {
        return result -> {
            String header = result.getResponse().getHeader("X-Response-Time-Ms");
            long actualMs = Long.parseLong(header);
            if (actualMs > maxMillis) {
                throw new AssertionError("Response time " + actualMs + "ms exceeded max " + maxMillis + "ms");
            }
        };
    }

    public static void main(String[] args) throws Exception {
        MockMvc mockMvc = MockMvcBuilders.standaloneSetup(new ProductXmlController()).build();

        mockMvc.perform(get("/products/42.xml"))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_XML))
                .andExpect(xpath("/product/id").string("42"))
                .andExpect(xpath("/product/name").string("Laptop"))
                .andExpect(xpath("/product/price").string("999.99"));
        System.out.println("XPath assertions on XML response -- PASS");

        mockMvc.perform(get("/products/42/timing"))
                .andExpect(status().isOk())
                .andExpect(responseTimeUnder(1000)); // custom ResultMatcher, composed like any built-in one
        System.out.println("Custom ResultMatcher assertion -- PASS");
    }
}
```

How to run: same dependencies as Level 1, then `java MockMvcMatchersAdvanced.java`.

`xpath("/product/id").string("42")` navigates the XML response body using an XPath expression, asserting the text content at that path — the XML equivalent of `jsonPath(...)` for JSON responses, useful whenever an endpoint returns XML (via content negotiation or dedicated XML endpoints). `responseTimeUnder(maxMillis)` is a hand-written `ResultMatcher` — the same functional interface (`MvcResult -> void`, throwing on failure) every built-in matcher from `MockMvcResultMatchers` implements — showing that the entire result-matcher system is just this one simple interface, extensible for any assertion the built-in vocabulary doesn't directly cover.

## 6. Walkthrough

Trace `MockMvcMatchersAdvanced.main`'s XML request:

1. **Request built and dispatched.** `mockMvc.perform(get("/products/42.xml"))` builds a mock `GET` request and routes it to `getProductXml(42)` via the real `DispatcherServlet`, exactly as any other `MockMvc` request.
2. **Controller returns XML.** The method returns a hand-built XML string; because the mapping declares `produces = MediaType.APPLICATION_XML_VALUE`, the response's `Content-Type` header is set to `application/xml`, and the string body becomes the response body verbatim (no message converter transformation needed here, since it's already a `String` return type with the content type explicitly declared).
3. **Status and content-type matchers run first.** `status().isOk()` and `content().contentType(MediaType.APPLICATION_XML)` check the coarse-grained response facts before diving into the body's actual structure.
4. **XPath matchers parse and navigate the body.** Each `xpath("/product/...")` call parses the response body as XML (once per matcher, or cached depending on the implementation) and evaluates the given XPath expression against it — `/product/id` navigates to the `<id>` element's text content, compared against the expected string `"42"`; similarly for `/product/name` and `/product/price`.
5. **Second request: custom matcher.** `mockMvc.perform(get("/products/42/timing"))` hits a different endpoint that measures its own internal timing and reports it via a response header.
6. **`responseTimeUnder(1000)` executes.** As a `ResultMatcher`, its lambda receives the completed `MvcResult`, reads the `X-Response-Time-Ms` header, parses it as a `long`, and throws an `AssertionError` only if that value exceeds the given threshold — since the endpoint only sleeps 5ms, this passes comfortably under the 1000ms limit.

```
GET /products/42.xml
   -> ProductXmlController.getProductXml(42) -> XML string, Content-Type: application/xml
   -> status().isOk() -- check
   -> content().contentType(APPLICATION_XML) -- check
   -> xpath("/product/id").string("42") -- parses XML, navigates, checks
   -> xpath("/product/name").string("Laptop") -- same
   -> xpath("/product/price").string("999.99") -- same

GET /products/42/timing
   -> getWithTiming(42) -> header X-Response-Time-Ms: ~5
   -> responseTimeUnder(1000) -- custom lambda reads header, parses, compares, throws only if too slow
```

## 7. Gotchas & takeaways

> Gotcha: `xpath(...)` matchers require the response body to be well-formed, parseable XML — a common mistake is using them against a JSON response (or an XML response with a subtle encoding issue), which fails with a parsing exception whose message is about XML syntax, not about the actual assertion mismatch you might expect. When an `xpath` assertion fails unexpectedly, checking `content().contentType(...)` first (or printing the raw response body) usually clarifies whether the issue is the XPath expression itself or the response not being valid XML in the first place.

- `MockMvcRequestBuilders`/`MockMvcResultMatchers` cover the full HTTP surface beyond basic JSON GET/POST — multipart uploads, cookies, headers, and XML via XPath — so tests aren't limited to the simplest request/response shapes.
- Compose several result matchers on one `perform(...)` call to thoroughly verify a response's full contract (status, headers, cookies, body) in one readable chain.
- `xpath(...)` is the XML equivalent of `jsonPath(...)`, useful for any endpoint producing XML via content negotiation or a dedicated XML mapping.
- `ResultMatcher` is a simple functional interface (`MvcResult -> void`, throwing to signal failure) — every built-in matcher implements it, and writing your own for a project-specific assertion the standard vocabulary doesn't cover is straightforward.
