---
card: spring-boot
gi: 140
slug: graphql-support
title: GraphQL support
---

## 1. What it is

**Spring for GraphQL** (available since Spring Boot 2.7 via `spring-boot-starter-graphql`) integrates the GraphQL Java engine into Spring Boot. It auto-configures a `GraphQlSource` from schema files found in `classpath:graphql/**/*.graphqls`, registers a `/graphql` HTTP endpoint (and an optional `/graphiql` browser IDE), and maps `@QueryMapping`, `@MutationMapping`, and `@SchemaMapping` annotations to resolver methods. The result is a type-safe, schema-first GraphQL API with Spring Boot's familiar annotation style.

## 2. Why & when

REST forces clients to make multiple requests for nested data or over-fetches by returning full objects when only a few fields are needed. GraphQL lets the client request exactly the shape of data it needs in a single query — ideal for:

- Mobile apps where bandwidth matters and each screen needs a custom data shape.
- Aggregation APIs that pull from multiple services in one request.
- Frontend teams who want to evolve queries independently of backend changes.

Stick with REST when your API is simple (CRUD), consumed by many heterogeneous clients that benefit from cacheability, or you need HTTP-level caching (GraphQL POSTs are not cacheable by default).

## 3. Core concept

Spring for GraphQL is **schema-first**: you define types and operations in `.graphqls` files; Spring wires annotated Java methods as resolvers.

```
schema.graphqls
  ↓ GraphQlSource (parsed + wired)
  ↓ /graphql endpoint (HTTP POST)
  ↓ DataFetcher (your @QueryMapping method)
  ↓ JSON response with exactly the requested fields
```

Key annotations:

| Annotation | Maps to |
|---|---|
| `@QueryMapping` | A `Query` type field |
| `@MutationMapping` | A `Mutation` type field |
| `@SchemaMapping` | Any field on any type (nested resolvers) |
| `@Argument` | Binds a GraphQL argument to a method parameter |
| `@SubscriptionMapping` | A `Subscription` field (WebSocket) |

`@Controller` classes hold the resolvers; Spring Boot scans them automatically.

## 4. Diagram

<svg viewBox="0 0 680 220" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="80" width="130" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="85" y="107" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">Client Query</text>
  <text x="85" y="124" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">POST /graphql</text>
  <rect x="225" y="60" width="170" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="310" y="88" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">GraphQlSource</text>
  <text x="310" y="103" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">schema + DataFetchers</text>
  <rect x="225" y="130" width="170" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="310" y="152" text-anchor="middle" fill="#8b949e" font-size="12" font-family="sans-serif">@QueryMapping</text>
  <text x="310" y="169" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">resolver method</text>
  <rect x="475" y="80" width="180" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="565" y="107" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">JSON response</text>
  <text x="565" y="124" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">only requested fields</text>
  <line x1="152" y1="110" x2="221" y2="88" stroke="#6db33f" stroke-width="1.5" marker-end="url(#gq)"/>
  <line x1="310" y1="112" x2="310" y2="128" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#gq2)"/>
  <line x1="397" y1="155" x2="471" y2="118" stroke="#8b949e" stroke-width="1.5" marker-end="url(#gq3)"/>
  <defs>
    <marker id="gq" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="gq2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="gq3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Client POSTs a query → `GraphQlSource` resolves fields via `@QueryMapping` methods → JSON response contains only requested fields.

## 5. Runnable example

```java
// GraphQLApp.java  —  Spring Boot project
// pom.xml: spring-boot-starter-web, spring-boot-starter-graphql
// src/main/resources/graphql/schema.graphqls:
//
//   type Query {
//     book(id: ID!): Book
//     books: [Book]
//   }
//   type Book {
//     id: ID!
//     title: String!
//     author: String!
//   }

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.graphql.data.method.annotation.Argument;
import org.springframework.graphql.data.method.annotation.QueryMapping;
import org.springframework.stereotype.Controller;

import java.util.List;
import java.util.Map;

@SpringBootApplication
public class GraphQLApp {
    public static void main(String[] args) {
        SpringApplication.run(GraphQLApp.class, args);
    }
}

record Book(String id, String title, String author) {}

@Controller
class BookController {

    private static final Map<String, Book> BOOKS = Map.of(
        "1", new Book("1", "Effective Java", "Joshua Bloch"),
        "2", new Book("2", "Clean Code", "Robert Martin")
    );

    @QueryMapping
    public Book book(@Argument String id) {
        return BOOKS.get(id);
    }

    @QueryMapping
    public List<Book> books() {
        return List.copyOf(BOOKS.values());
    }
}
```

**How to run:**

1. Create `src/main/resources/graphql/schema.graphqls` with the schema shown in comments.
2. Add `spring.graphql.graphiql.enabled=true` to `application.properties`.
3. Start the app and open `http://localhost:8080/graphiql`.
4. Run this query:
   ```graphql
   query {
     book(id: "1") { title author }
   }
   ```
   Or via curl: `curl -X POST http://localhost:8080/graphql -H "Content-Type: application/json" -d '{"query":"{ books { title } }"}'`

## 6. Walkthrough

- Spring Boot scans `classpath:graphql/**/*.graphqls` and parses the schema into a `GraphQLSchema`. This happens inside `GraphQlSourceBuilderCustomizer` auto-configuration.
- `@Controller` on `BookController` makes it a Spring-managed bean. `@QueryMapping` on `book(...)` tells Spring for GraphQL: "when the `book` field on the `Query` type is requested, call this method."
- `@Argument String id` binds the GraphQL argument `id` to the Java parameter — type coercion (String → Int, etc.) is handled automatically.
- `@QueryMapping public List<Book> books()` resolves the `books` field — returns all books. The client can request `{ books { title } }` and only `title` is included in the response; `author` and `id` are stripped.
- `spring.graphql.graphiql.enabled=true` serves the GraphiQL browser IDE at `/graphiql` — invaluable for development. Disable in production.
- For nested resolvers (e.g. a `Book` has an `Author` object with its own resolver), use `@SchemaMapping(typeName = "Book", field = "author")` on a method that receives the parent `Book` and returns an `Author`.

## 7. Gotchas & takeaways

> GraphQL errors do **not** return HTTP 4xx/5xx by default — they return `200 OK` with an `errors` array in the JSON body. Don't check HTTP status for GraphQL error detection; inspect the `errors` field.

> N+1 queries are the classic GraphQL pitfall. If `books` returns 100 books and each triggers a separate DB call to fetch the author, you get 101 queries. Use `@BatchMapping` (Spring for GraphQL's batch loader) or DataLoader to coalesce them into one query.

- Schema files must be in `src/main/resources/graphql/` (or subdirectories); the extension must be `.graphqls` or `.gql`.
- `spring.graphql.path=/graphql` (default); change if `/graphql` conflicts with an existing REST endpoint.
- `@MutationMapping` follows the same pattern as `@QueryMapping` but maps to `Mutation` type fields.
- Spring Security integrates with Spring for GraphQL — annotate resolver methods with `@PreAuthorize` as you would REST controllers.
- `GraphQlTester` is the test utility for integration-testing GraphQL endpoints without HTTP round-trips.
