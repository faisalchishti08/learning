---
card: spring-boot
gi: 141
slug: jersey-jax-rs-support
title: Jersey (JAX-RS) support
---

## 1. What it is

**Jersey** is the reference implementation of **JAX-RS** (Jakarta RESTful Web Services), the standard Java API for building REST endpoints using annotations like `@GET`, `@POST`, `@Path`, and `@Produces`. Spring Boot supports Jersey as an alternative to Spring MVC for REST APIs via `spring-boot-starter-jersey`. When Jersey is on the classpath, Spring Boot auto-configures it as a Servlet registered with the embedded container, so Jersey's `ResourceConfig` handles JAX-RS resources while Spring still manages beans, data access, and everything else.

## 2. Why & when

Most Spring Boot apps use Spring MVC (`@RestController`) and never need Jersey. Use Jersey when:

- You're migrating an existing JAX-RS application to Spring Boot and want to keep JAX-RS annotations.
- Your team has strong JAX-RS expertise and prefers the standard API over Spring-specific annotations.
- You use JAX-RS libraries (Bean Validation via `@Valid`, client API, interceptors) that integrate more naturally with Jersey.

If starting a new project with Spring Boot, Spring MVC or Spring WebFlux are the idiomatic choice — deeper Spring integration, more auto-configuration, better documentation.

## 3. Core concept

Jersey runs as a Servlet inside the embedded container. Spring Boot registers it via `JerseyAutoConfiguration`, which creates a `ServletRegistrationBean` for Jersey's `ServletContainer`. Your JAX-RS resources are Spring beans annotated with `@Component` and registered into a `ResourceConfig` subclass.

Key players:

| Component | Role |
|---|---|
| `ResourceConfig` | Jersey's application class; registers resources and providers |
| `@Path` | Maps a class or method to a URL path |
| `@GET`/`@POST`/… | HTTP method binding |
| `@Produces`/`@Consumes` | Content-type negotiation |
| `@Component` | Makes the resource a Spring bean (injectable) |

Jersey and Spring MVC **cannot** both handle the same paths. Jersey takes over the paths registered in `ResourceConfig`; everything else falls through to Spring MVC (or the 404 handler).

## 4. Diagram

<svg viewBox="0 0 680 210" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="80" width="130" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="85" y="107" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">HTTP Request</text>
  <text x="85" y="124" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">GET /api/books</text>
  <rect x="230" y="60" width="175" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="317" y="88" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">Jersey Servlet</text>
  <text x="317" y="103" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">ResourceConfig</text>
  <rect x="230" y="130" width="175" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="317" y="155" text-anchor="middle" fill="#8b949e" font-size="12" font-family="sans-serif">Spring MVC</text>
  <text x="317" y="171" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">(non-JAX-RS paths)</text>
  <rect x="480" y="80" width="175" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="567" y="107" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">@Path resource</text>
  <text x="567" y="124" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">Spring @Component</text>
  <line x1="152" y1="110" x2="226" y2="88" stroke="#6db33f" stroke-width="1.5" marker-end="url(#jr)"/>
  <line x1="152" y1="110" x2="226" y2="155" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,3" marker-end="url(#jr2)"/>
  <line x1="407" y1="88" x2="476" y2="108" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#jr3)"/>
  <defs>
    <marker id="jr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="jr2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="jr3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Requests matching JAX-RS paths go to the Jersey Servlet; other paths fall through to Spring MVC. JAX-RS resources are plain Spring `@Component` beans.

## 5. Runnable example

```java
// JerseyApp.java  —  Spring Boot project with spring-boot-starter-jersey
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;
import org.glassfish.jersey.server.ResourceConfig;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.stereotype.Component;

import java.util.List;

@SpringBootApplication
public class JerseyApp {
    public static void main(String[] args) {
        SpringApplication.run(JerseyApp.class, args);
    }
}

// Jersey application config — register resources here
@Component
class JerseyConfig extends ResourceConfig {
    JerseyConfig() {
        // Register the resource class; Spring Boot wires the Spring bean
        register(BookResource.class);
        // Optional: set a URL prefix for all JAX-RS endpoints
        property("jersey.config.servlet.filter.contextPath", "/api");
    }
}

record Book(int id, String title) {}

// JAX-RS resource — also a Spring bean so @Autowired / constructor injection works
@Component
@Path("/books")
@Produces(MediaType.APPLICATION_JSON)
class BookResource {

    @GET
    public List<Book> list() {
        return List.of(
            new Book(1, "Effective Java"),
            new Book(2, "Clean Code")
        );
    }

    @GET
    @Path("/{id}")
    public Book get(@PathParam("id") int id) {
        if (id == 1) return new Book(1, "Effective Java");
        throw new NotFoundException("Book " + id + " not found");
    }

    @POST
    @Consumes(MediaType.APPLICATION_JSON)
    public Book create(Book book) {
        // In a real app: save to DB, return persisted entity
        return new Book(99, book.title());
    }
}
```

**How to run:** add `spring-boot-starter-jersey` to `pom.xml`, start the app, then:
- `curl http://localhost:8080/books` → JSON list of books
- `curl http://localhost:8080/books/1` → single book
- `curl -X POST http://localhost:8080/books -H "Content-Type: application/json" -d '{"id":0,"title":"New Book"}'`

## 6. Walkthrough

- `spring-boot-starter-jersey` brings in `jersey-spring5` (or `jersey-spring6` for Boot 3) which integrates Jersey's DI with Spring's `ApplicationContext`. Resources annotated with `@Component` are fetched from the Spring context — so constructor injection and `@Autowired` work normally inside JAX-RS resources.
- `JerseyConfig extends ResourceConfig` is the JAX-RS application class. `register(BookResource.class)` tells Jersey to route requests to this resource. Spring Boot detects the `ResourceConfig` bean and registers Jersey's `ServletContainer` for it.
- `@Path("/books")` on the class sets the root path. `@Path("/{id}")` on the method adds a path segment with a template variable.
- `@PathParam("id") int id` extracts the `{id}` template variable and converts it to `int` automatically.
- `@Produces(MediaType.APPLICATION_JSON)` tells Jersey to serialise responses as JSON. Jersey uses Jackson (auto-configured by Spring Boot) for serialisation.
- `throw new NotFoundException(...)` is a JAX-RS exception that maps to `404 Not Found` — Jersey's exception mapper handles it automatically.
- `@Consumes(MediaType.APPLICATION_JSON)` on `create(...)` tells Jersey to deserialise the request body as JSON into a `Book` record.

## 7. Gotchas & takeaways

> Jersey's `@Path` resources and Spring MVC's `@RequestMapping` handlers **conflict** if they map the same paths. Jersey runs as a Servlet and takes priority over Spring MVC's `DispatcherServlet` for matching paths. Keep them on separate path prefixes or use only one framework for REST.

> Do NOT use both `spring-boot-starter-web` (Spring MVC) and `spring-boot-starter-jersey` for the same REST paths. They can coexist in the same app but must serve different URL spaces. Actuator endpoints still use Spring MVC regardless.

- Jersey's `ResourceConfig` must extend it (not implement an interface) and be a `@Component` for Spring Boot auto-config to detect it.
- `@Provider` classes (exception mappers, filters, interceptors) must also be registered in `ResourceConfig` via `register(MyExceptionMapper.class)`.
- Jersey does not support Spring MVC's `@ControllerAdvice` — write JAX-RS `ExceptionMapper<T>` implementations instead.
- Bean Validation works with JAX-RS parameters: add `@Valid` to method parameters and Jersey calls the validator automatically (needs `jersey-bean-validation` on the classpath).
- `spring.jersey.type=filter` registers Jersey as a `Filter` instead of a `Servlet` — allows Spring MVC to handle requests Jersey doesn't match.
