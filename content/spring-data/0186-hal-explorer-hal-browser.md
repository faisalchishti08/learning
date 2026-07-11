---
card: spring-data
gi: 186
slug: hal-explorer-hal-browser
title: "HAL Explorer / HAL Browser"
---

## 1. What it is

The HAL Explorer is a browser-based UI, bundled as an optional dependency (`spring-data-rest-hal-explorer`), that lets a developer click through a Spring Data REST API interactively — following `_links`, viewing resource JSON, and issuing requests — without writing a single line of client code or reaching for a separate tool.

```
Add to pom.xml: org.springframework.data:spring-data-rest-hal-explorer
Then visit: GET /  (the API's root)  in a browser -> HAL Explorer UI loads automatically
```

## 2. Why & when

Every card so far in this section has been about the API's *shape* — what gets exposed, how it's customized, how it validates. HAL Explorer is a *tooling* card: given a working HAL API, how do you actually explore it during development, without hand-writing curl commands or importing it into a separate REST client for every small check?

Reach for the HAL Explorer when:

- Developing or debugging a Spring Data REST API and wanting to click through its resources and links interactively, the same way you'd browse a website.
- Verifying that `_links` (from the exposure and customization cards earlier) actually point where they should, and that excerpt projections render as expected, without writing test code for a purely visual check.
- Onboarding someone new to an API — clicking through the real, live hypermedia links teaches the API's shape faster than reading documentation about it.

## 3. Core concept

```
 GET /                                      -- API root
   -> HAL Explorer renders: links to /customers, /orders, /products, ...

 Click "customers"  -> GET /customers        -- HAL Explorer follows the link, shows the collection
   -> click _links.next -> pagination handled by clicking, not manual query params
   -> click an item's self link -> GET /customers/c1, full item resource shown

 No client code written -- every navigation step IS just following a _links entry that's already in the response.
```

The Explorer doesn't add any new capability to the API — it visualizes and makes clickable the hypermedia links the API was already returning.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A developer clicks through the API root, a collection resource, and an item resource, each reached by following a rendered link">
  <rect x="20" y="45" width="160" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="100" y="72" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">GET / (API root)</text>

  <line x1="180" y1="67" x2="240" y2="67" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a19)"/>
  <text x="210" y="57" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">click</text>

  <rect x="250" y="45" width="160" height="45" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="72" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">GET /customers</text>

  <line x1="410" y1="67" x2="470" y2="67" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a19)"/>
  <text x="440" y="57" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">click</text>

  <rect x="480" y="45" width="140" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="550" y="72" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">GET /customers/c1</text>

  <defs><marker id="a19" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Each step is reached by clicking a link already present in the previous response's body.

## 5. Runnable example

The scenario: modeling what the HAL Explorer does under the hood — parsing a HAL response and turning its `_links` into a navigable menu — evolving from raw HAL JSON a developer would otherwise have to read manually, to a simple link-extraction utility, to a small interactive navigator that follows links step by step, the way clicking through the real HAL Explorer does.

### Level 1 — Basic

Show a raw HAL response as a developer would see it without any tooling — readable, but tedious to navigate by hand.

```java
public class HalExplorerLevel1 {
    public static void main(String[] args) {
        String apiRoot =
            "{ \"_links\": { " +
            "\"customers\": { \"href\": \"/customers\" }, " +
            "\"orders\": { \"href\": \"/orders\" } } }";

        System.out.println("GET / ->");
        System.out.println(apiRoot);
        // A developer has to manually read this JSON, find "customers", copy "/customers",
        // and issue a SEPARATE request by hand to go anywhere.
    }
}
```

How to run: `java HalExplorerLevel1.java`

Reading `_links` out of raw JSON by eye and manually issuing the next request is exactly the tedious loop the HAL Explorer automates away.

### Level 2 — Intermediate

Add a link-extraction utility that parses `_links` out of a HAL body — the core parsing step any HAL-aware tool, including the Explorer, performs.

```java
import java.util.*;
import java.util.regex.*;

public class HalExplorerLevel2 {
    public static void main(String[] args) {
        String apiRoot =
            "{ \"_links\": { " +
            "\"customers\": { \"href\": \"/customers\" }, " +
            "\"orders\": { \"href\": \"/orders\" } } }";

        Map<String, String> links = extractLinks(apiRoot);
        System.out.println("Available links at GET /:");
        for (Map.Entry<String, String> link : links.entrySet()) {
            System.out.println("  " + link.getKey() + " -> " + link.getValue());
        }
    }

    // Parses "_links" relation names and their hrefs out of a HAL JSON body.
    static Map<String, String> extractLinks(String halJson) {
        Map<String, String> links = new LinkedHashMap<>();
        Matcher m = Pattern.compile("\"(\\w+)\":\\s*\\{\\s*\"href\":\\s*\"([^\"]+)\"").matcher(halJson);
        while (m.find()) links.put(m.group(1), m.group(2));
        return links;
    }
}
```

How to run: `java HalExplorerLevel2.java`

`extractLinks` turns the raw `_links` object into a `Map` of relation name to URL — this is exactly the data structure the HAL Explorer's UI renders as a clickable menu, one clickable entry per relation.

### Level 3 — Advanced

Build a small step-by-step navigator that follows links across multiple simulated responses — modeling the click-through experience: API root, to a collection, to a single item, purely by following extracted links.

```java
import java.util.*;
import java.util.regex.*;

public class HalExplorerLevel3 {
    public static void main(String[] args) {
        Map<String, String> fakeApi = new HashMap<>();
        fakeApi.put("/", "{ \"_links\": { \"customers\": { \"href\": \"/customers\" } } }");
        fakeApi.put("/customers", "{ \"_links\": { \"self\": { \"href\": \"/customers\" } }, "
            + "\"_embedded\": { \"customers\": [ { \"name\": \"Amara\", \"_links\": { \"self\": { \"href\": \"/customers/c1\" } } } ] } }");
        fakeApi.put("/customers/c1", "{ \"name\": \"Amara\", \"email\": \"amara@example.com\", "
            + "\"_links\": { \"self\": { \"href\": \"/customers/c1\" } } }");

        // Simulates a developer clicking: root -> "customers" link -> first customer's self link.
        String current = navigate(fakeApi, "/", null);
        current = navigate(fakeApi, current, "customers");
        current = navigate(fakeApi, current, null); // clicking the embedded item's own self link, extracted separately
    }

    static String navigate(Map<String, String> fakeApi, String path, String followRelation) {
        System.out.println("GET " + path + " ->");
        String body = fakeApi.get(path);
        System.out.println(body);

        if (followRelation == null) return path;
        Map<String, String> links = extractLinks(body);
        String next = links.get(followRelation);
        System.out.println("(clicked '" + followRelation + "' -> navigating to " + next + ")\n");
        return next;
    }

    static Map<String, String> extractLinks(String halJson) {
        Map<String, String> links = new LinkedHashMap<>();
        Matcher m = Pattern.compile("\"(\\w+)\":\\s*\\{\\s*\"href\":\\s*\"([^\"]+)\"").matcher(halJson);
        while (m.find()) links.put(m.group(1), m.group(2));
        return links;
    }
}
```

How to run: `java HalExplorerLevel3.java`

`navigate` is called three times, chaining: the API root's `customers` link leads to the collection; from there, the developer would click into the embedded item's own `self` link (extracted the same way) to reach the individual customer resource — every step is driven entirely by links present in the *previous* response, never a URL typed in from prior knowledge.

## 6. Walkthrough

Execution starts in `main` for Level 3. The first `navigate` call prints the API root's body and returns immediately (`followRelation` is `null`, so no link is followed yet — this call is just "load the page"):

```
GET / ->
{ "_links": { "customers": { "href": "/customers" } } }
```

The second call re-fetches `/` conceptually (in a real Explorer, the previous response would already be in hand) and follows the `"customers"` relation, printing the collection response and then announcing the click:

```
GET / ->
{ "_links": { "customers": { "href": "/customers" } } }
(clicked 'customers' -> navigating to /customers)
```

The third call loads `/customers`, printing its body — including the embedded customer's own `_links.self` pointing at `/customers/c1` — and returns without following further, mirroring how a developer using the real HAL Explorer would see the collection rendered, notice the individual customer link, and click it manually for the next step:

```
GET /customers ->
{ "_links": { "self": { "href": "/customers" } }, "_embedded": { "customers": [ { "name": "Amara", "_links": { "self": { "href": "/customers/c1" } } } ] } }
```

The entire "journey" from API root to an individual customer never required knowing the URL pattern `/customers/{id}` in advance — every step's destination came from a link embedded in the previous step's response, exactly the principle the earlier HAL/hypermedia card introduced, now made interactively clickable by the Explorer tool.

## 7. Gotchas & takeaways

> Gotcha: the HAL Explorer is a development and debugging tool, not something to leave enabled and reachable on a production deployment by default — it exposes the same data any authenticated client could reach anyway, but as a browsable UI it's a convenient target for anyone probing the API's shape, so many teams restrict or disable it outside development environments.

> Gotcha: the HAL Explorer reflects exactly what the API returns — if a resource's `_links` are wrong (pointing at a stale path after a `@RepositoryRestResource(path = ...)` rename, say), the Explorer will happily follow the broken link and show whatever error results, rather than catching the misconfiguration itself; it's a window into the API's actual behavior, not a separate validation layer.

- The HAL Explorer is purely a client-side visualization of `_links` an API was already returning — it adds no new server capability, only makes existing hypermedia navigable by clicking.
- It's valuable for development, debugging, and onboarding — quickly verifying that resource shapes and links behave as expected without writing test or client code.
- It reflects the API's actual behavior exactly, including any misconfigured or stale links, rather than validating the API independently.
- Consider restricting or disabling it outside development environments, since a browsable API explorer is a convenient reconnaissance tool if left open.
