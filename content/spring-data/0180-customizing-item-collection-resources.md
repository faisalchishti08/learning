---
card: spring-data
gi: 180
slug: customizing-item-collection-resources
title: "Customizing item/collection resources"
---

## 1. What it is

Spring Data REST lets you reshape the generated item resource (a single entity, like `GET /customers/{id}`) and collection resource (a list, like `GET /customers`) beyond simple path renaming — hiding specific fields with `@JsonIgnore`, restricting which HTTP methods are allowed via `RepositoryRestConfiguration`, and controlling pagination defaults for collections.

```java
@Configuration
class RestConfig implements RepositoryRestConfigurer {
    public void configureRepositoryRestConfiguration(RepositoryRestConfiguration config, CorsRegistry cors) {
        config.setDefaultPageSize(20).setMaxPageSize(100);
    }
}
```

## 2. Why & when

The previous cards controlled *whether* and *where* a repository is exposed. This card is about shaping *what the exposed resource actually looks like* once it's reachable — which fields appear in the JSON, which HTTP verbs are allowed, and how large collections are paginated by default. Left entirely on defaults, every entity field is serialized and every CRUD verb is allowed, which is rarely exactly right for a public API.

Reach for item/collection customization when:

- An entity has fields that shouldn't appear in its public JSON representation — an internal audit flag, a computed cache value, a sensitive field.
- Certain operations shouldn't be publicly allowed on a resource — a customer resource that should be read-only via REST, with writes only happening through an internal service.
- Collection endpoints return large datasets that need sensible pagination defaults rather than the framework's out-of-the-box page size.

## 3. Core concept

```
 @Entity
 class Customer {
     @Id String id;
     String name, email;
     @JsonIgnore
     String internalRiskScore;     -- never appears in the JSON response
 }

 config.getExposureConfiguration()
     .forDomainType(Customer.class)
     .withItemExposure((metadata, httpMethods) -> httpMethods.disable(HttpMethod.DELETE));
     -- DELETE /customers/{id} now returns 405, even though the repository could delete internally

 config.setDefaultPageSize(20)
     -- GET /customers returns 20 items per page unless the client requests otherwise
```

Field visibility, verb restrictions, and pagination defaults each shape a different dimension of the same generated resource.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A full entity is filtered down to a public JSON shape with certain fields hidden and certain verbs disabled">
  <rect x="20" y="20" width="250" height="110" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="145" y="42" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Full entity</text>
  <text x="145" y="62" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">name, email,</text>
  <text x="145" y="78" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">internalRiskScore</text>
  <text x="145" y="100" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">GET/POST/PUT/PATCH/DELETE</text>

  <line x1="270" y1="75" x2="330" y2="75" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a13)"/>

  <rect x="340" y="20" width="280" height="110" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Public REST resource</text>
  <text x="480" y="62" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">name, email</text>
  <text x="480" y="78" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">(riskScore hidden)</text>
  <text x="480" y="100" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">GET/POST/PUT/PATCH only</text>

  <defs><marker id="a13" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Customization filters both the fields serialized and the HTTP verbs exposed for the same underlying entity.

## 5. Runnable example

The scenario: shaping a `Customer` resource's public REST surface, evolving from a naive serialization exposing every field, to `@JsonIgnore`-style field hiding, to a full configuration also restricting HTTP verbs and setting pagination defaults for the collection endpoint.

### Level 1 — Basic

Model the unfiltered baseline: every entity field serialized as-is, including one that shouldn't be public.

```java
public class CustomizeResourceLevel1 {
    public static void main(String[] args) {
        Customer amara = new Customer("c1", "Amara", "amara@example.com", 82); // internalRiskScore leaks

        System.out.println("GET /customers/c1 ->");
        System.out.println(toJson(amara)); // EVERY field, including internalRiskScore
    }

    static String toJson(Customer c) {
        return "{ \"name\": \"" + c.name + "\", \"email\": \"" + c.email
            + "\", \"internalRiskScore\": " + c.internalRiskScore + " }";
    }
}

class Customer {
    String id, name, email; int internalRiskScore;
    Customer(String id, String name, String email, int internalRiskScore) {
        this.id = id; this.name = name; this.email = email; this.internalRiskScore = internalRiskScore;
    }
}
```

How to run: `java CustomizeResourceLevel1.java`

`toJson` serializes every field on `Customer`, including `internalRiskScore` — a value that should never reach a public API response, which is exactly what unfiltered default serialization does without any customization.

### Level 2 — Intermediate

Add `@JsonIgnore`-style field filtering, keeping the sensitive field out of the serialized response.

```java
import java.util.*;
import java.lang.reflect.*;
import java.lang.annotation.*;

public class CustomizeResourceLevel2 {
    public static void main(String[] args) {
        Customer amara = new Customer("c1", "Amara", "amara@example.com", 82);

        System.out.println("GET /customers/c1 ->");
        System.out.println(toJson(amara)); // internalRiskScore no longer appears
    }

    @Retention(RetentionPolicy.RUNTIME)
    @interface JsonIgnore {} // stands in for com.fasterxml.jackson.annotation.JsonIgnore

    static String toJson(Object entity) {
        StringBuilder sb = new StringBuilder("{ ");
        boolean first = true;
        for (Field field : entity.getClass().getDeclaredFields()) {
            if (field.isAnnotationPresent(JsonIgnore.class) || field.getName().equals("id")) continue;
            try {
                field.setAccessible(true);
                if (!first) sb.append(", ");
                sb.append("\"").append(field.getName()).append("\": ");
                Object value = field.get(entity);
                sb.append(value instanceof String ? "\"" + value + "\"" : value);
                first = false;
            } catch (IllegalAccessException ignored) {}
        }
        return sb.append(" }").toString();
    }
}

class Customer {
    String id, name, email;
    @CustomizeResourceLevel2.JsonIgnore
    int internalRiskScore; // filtered out of the JSON response entirely
    Customer(String id, String name, String email, int internalRiskScore) {
        this.id = id; this.name = name; this.email = email; this.internalRiskScore = internalRiskScore;
    }
}
```

How to run: `java CustomizeResourceLevel2.java`

Reflecting over `Customer`'s fields and skipping any annotated `@JsonIgnore` mirrors exactly how Jackson (which Spring Data REST uses for serialization) filters fields — `internalRiskScore` is stored on the entity and used internally, but never appears in a client-facing JSON response.

### Level 3 — Advanced

Add HTTP verb restriction and pagination defaults — a full item/collection customization covering field visibility, allowed operations, and default page size together.

```java
import java.util.*;

public class CustomizeResourceLevel3 {
    public static void main(String[] args) {
        RestConfig config = new RestConfig();
        config.disableMethod("Customer", "DELETE"); // customers are read-only via REST
        config.setDefaultPageSize(2);

        List<Customer> allCustomers = List.of(
            new Customer("c1", "Amara"), new Customer("c2", "Bilal"),
            new Customer("c3", "Chidi"), new Customer("c4", "Dara")
        );

        System.out.println("GET /customers -> " + config.paginate(allCustomers, 0).size() + " item(s) on page 0");
        System.out.println("DELETE /customers/c1 -> " + (config.isAllowed("Customer", "DELETE") ? "200 OK" : "405 Method Not Allowed"));
        System.out.println("GET /customers/c1 -> " + (config.isAllowed("Customer", "GET") ? "200 OK" : "405 Method Not Allowed"));
    }
}

class Customer { String id, name; Customer(String id, String name) { this.id = id; this.name = name; } }

class RestConfig {
    private final Map<String, Set<String>> disabledMethods = new HashMap<>();
    private int defaultPageSize = 20;

    void disableMethod(String entityName, String httpMethod) {
        disabledMethods.computeIfAbsent(entityName, k -> new HashSet<>()).add(httpMethod);
    }
    void setDefaultPageSize(int size) { this.defaultPageSize = size; }

    boolean isAllowed(String entityName, String httpMethod) {
        return !disabledMethods.getOrDefault(entityName, Set.of()).contains(httpMethod);
    }
    <T> List<T> paginate(List<T> items, int page) {
        int from = page * defaultPageSize;
        int to = Math.min(from + defaultPageSize, items.size());
        return from >= items.size() ? List.of() : items.subList(from, to);
    }
}
```

How to run: `java CustomizeResourceLevel3.java`

`config.disableMethod("Customer", "DELETE")` mirrors restricting the item resource's allowed HTTP methods, and `setDefaultPageSize(2)` mirrors configuring the collection resource's pagination — the collection endpoint now returns only 2 of the 4 customers on the first page, and any `DELETE` request against a customer resource is rejected before it ever reaches the repository.

## 6. Walkthrough

Execution starts in `main` for Level 3. `config.disableMethod("Customer", "DELETE")` records that `DELETE` is disallowed for `Customer` resources; `config.setDefaultPageSize(2)` sets the collection page size to 2.

`config.paginate(allCustomers, 0)` slices the 4-customer list down to just the first 2, mirroring `GET /customers?page=0` returning a paginated HAL collection rather than every row at once:

```
GET /customers -> 2 item(s) on page 0
```

The two `isAllowed` checks show the effect of the verb restriction concretely: `DELETE /customers/c1` is rejected — in a real Spring Data REST application this would return an HTTP `405 Method Not Allowed`, without the request ever reaching `CustomerRepository.deleteById` — while `GET /customers/c1` remains permitted:

```
DELETE /customers/c1 -> 405 Method Not Allowed
GET /customers/c1 -> 200 OK
```

The layering here matters: field visibility (Level 2), verb restriction, and pagination (both Level 3) are each independent configuration concerns — an application typically applies all three together, one per concern the default generated resource doesn't get right on its own.

## 7. Gotchas & takeaways

> Gotcha: restricting an HTTP verb through `RepositoryRestConfiguration` only affects the *auto-generated* Spring Data REST endpoint — if a custom `@RepositoryRestController` (a later card) is also registered for the same path, it can still perform the "disabled" operation, since the restriction doesn't apply to hand-written controllers.

> Gotcha: `@JsonIgnore` on an entity field hides it from *output* serialization by default, but doesn't necessarily block it from being *accepted* on input (a `POST`/`PUT` body) unless configured for both read and write — a field meant to be fully hidden from clients may still be settable via a request body unless explicitly locked down on both directions.

- Item/collection customization shapes what a generated REST resource actually looks like on the wire — field visibility, allowed HTTP verbs, and pagination — independent of whether or where it's exposed.
- `@JsonIgnore`-style field filtering keeps internal-only entity fields out of public JSON responses.
- Disabling specific HTTP methods per entity type restricts what operations are possible through the generated endpoint, useful for making a resource effectively read-only via REST.
- These per-resource customizations layer independently — an application typically combines several of them to get from "everything exposed as-is" to a deliberately shaped public API.
