---
card: spring-data
gi: 40
slug: auditoraware
title: "AuditorAware"
---

## 1. What it is

`AuditorAware<T>` is the single-method functional interface (`Optional<T> getCurrentAuditor()`) that supplies "who is currently performing this operation" to `@CreatedBy`/`@LastModifiedBy` — the previous card used a minimal, manually-controlled stub implementation; this card covers a real, production-shaped implementation backed by Spring Security's authentication context, plus what happens when no authenticated user exists (a background job, a system-initiated change).

```java
@Bean
public AuditorAware<String> auditorAware() {
    return () -> Optional.ofNullable(SecurityContextHolder.getContext().getAuthentication())
        .filter(Authentication::isAuthenticated)
        .map(Authentication::getName);
}
```

## 2. Why & when

The previous card deliberately used a fake, manually-toggled "current user" to isolate and demonstrate auditing's field-population mechanics — real applications need `AuditorAware` to reflect the *actual* current user, which in a Spring Security-secured application means reading from `SecurityContextHolder`. Understanding this integration, and how to handle the "no authenticated user" case gracefully, is what makes auditing genuinely production-ready rather than a toy demonstration.

Reach for a proper `AuditorAware` implementation specifically when:

- You're building a Spring Security-secured application and want `@CreatedBy`/`@LastModifiedBy` to reflect the actual logged-in user performing each request, automatically, without threading a "current user" parameter through every service method.
- You need auditing to work correctly for both authenticated (real user) and unauthenticated/system-initiated (a scheduled job, a data migration script) code paths — deciding what identity, if any, to record for the latter.
- You're testing auditing behavior and need a way to control "the current auditor" deterministically in tests, independent of a real security context — a test-specific `AuditorAware` bean is the standard way to do this.

## 3. Core concept

```
 public interface AuditorAware<T> {
     Optional<T> getCurrentAuditor();
 }

 REAL implementation, backed by Spring Security:
   () -> Optional.ofNullable(SecurityContextHolder.getContext().getAuthentication())
       .filter(Authentication::isAuthenticated)
       .filter(auth -> !(auth instanceof AnonymousAuthenticationToken))
       .map(Authentication::getName)

 Called by AuditingEntityListener AT EVERY SAVE that needs @CreatedBy/@LastModifiedBy:
        |
        v
   Optional<String> auditor = auditorAware.getCurrentAuditor();
        |
   present  -> use auditor.get() as the value for @CreatedBy/@LastModifiedBy
   empty    -> leave the field UNCHANGED (null on first save, whatever it
               already was on a subsequent save) -- NOT an error
```

`getCurrentAuditor()` returning `Optional.empty()` is a normal, handled case — auditing simply doesn't populate the identity field for that particular save, rather than failing.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="AuditorAware reads the current Spring Security authentication and supplies it to the auditing listener at each save">
  <rect x="10" y="20" width="200" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">SecurityContextHolder</text>
  <text x="110" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">current Authentication</text>

  <rect x="250" y="20" width="180" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="340" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">AuditorAware&lt;String&gt;</text>
  <text x="340" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">getCurrentAuditor()</text>

  <rect x="470" y="20" width="160" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="550" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">AuditingEntityListener</text>
  <text x="550" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">at each save</text>

  <line x1="210" y1="47" x2="245" y2="47" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="430" y1="47" x2="465" y2="47" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

`AuditorAware` is the adapter between "however your application knows who's acting" and the auditing infrastructure.

## 5. Runnable example

The scenario: an `Order` entity, evolving from a Spring Security-backed `AuditorAware`, to confirming a `null` result (no authenticated user) leaves the field unpopulated rather than failing, to a system/background-job auditor fallback for non-request-driven saves.

### Level 1 — Basic

Implement `AuditorAware<String>` backed by Spring Security's `SecurityContextHolder`, and confirm a real authenticated principal's name is captured.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.EntityListeners;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.data.annotation.CreatedBy;
import org.springframework.data.domain.AuditorAware;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.config.EnableJpaAuditing;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;

import java.util.Optional;

@SpringBootApplication
@EnableJpaAuditing
public class AuditorAwareLevel1 {

    @Entity
    @EntityListeners(AuditingEntityListener.class)
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private double total;
        @CreatedBy
        private String createdBy;
        protected Order() {}
        public Order(double total) { this.total = total; }
        public String getCreatedBy() { return createdBy; }
    }

    public interface OrderRepository extends JpaRepository<Order, Long> {}

    @Bean
    public AuditorAware<String> auditorAware() {
        return () -> Optional.ofNullable(SecurityContextHolder.getContext().getAuthentication())
            .map(auth -> auth.getName());
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(AuditorAwareLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:auditoraware1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        // Simulate a real, authenticated request context.
        SecurityContextHolder.getContext().setAuthentication(
            new UsernamePasswordAuthenticationToken("ada.lovelace", null));

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        Order saved = repo.save(new Order(100.0));

        System.out.println("createdBy = " + saved.getCreatedBy());

        if (!"ada.lovelace".equals(saved.getCreatedBy()))
            throw new AssertionError("Expected createdBy to reflect the authenticated principal's name");
        System.out.println("AuditorAware backed by SecurityContextHolder captured the real authenticated user -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa`, `spring-security-core`, and `com.h2database:h2` on the classpath, then `java AuditorAwareLevel1.java` on JDK 17+.

`auditorAware()` reads `SecurityContextHolder.getContext().getAuthentication()` — the standard Spring Security mechanism for accessing the current request's authenticated principal — and maps it to its `getName()`. Setting a real `UsernamePasswordAuthenticationToken` before the save simulates what a genuine authenticated HTTP request's security context would already have in place, and `createdBy` correctly captures `"ada.lovelace"` from it.

### Level 2 — Intermediate

Confirm that when no authentication is present, `getCurrentAuditor()` correctly returns `Optional.empty()`, and the auditing field is simply left unpopulated rather than the save failing.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.EntityListeners;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.data.annotation.CreatedBy;
import org.springframework.data.domain.AuditorAware;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.config.EnableJpaAuditing;
import org.springframework.security.core.context.SecurityContextHolder;

import java.util.Optional;

@SpringBootApplication
@EnableJpaAuditing
public class AuditorAwareLevel2 {

    @Entity
    @EntityListeners(AuditingEntityListener.class)
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private double total;
        @CreatedBy
        private String createdBy;
        protected Order() {}
        public Order(double total) { this.total = total; }
        public String getCreatedBy() { return createdBy; }
    }

    public interface OrderRepository extends JpaRepository<Order, Long> {}

    @Bean
    public AuditorAware<String> auditorAware() {
        return () -> Optional.ofNullable(SecurityContextHolder.getContext().getAuthentication())
            .map(auth -> auth.getName());
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(AuditorAwareLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:auditoraware2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        // NO authentication set -- simulates a background job, a scheduled task,
        // or any code path that runs OUTSIDE an authenticated request.
        SecurityContextHolder.clearContext();

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        Order saved = repo.save(new Order(50.0));

        System.out.println("createdBy (no authentication present) = " + saved.getCreatedBy());
        System.out.println("save succeeded without throwing = true");

        if (saved.getCreatedBy() != null)
            throw new AssertionError("Expected createdBy to remain null when no auditor is available");
        System.out.println("Missing auditor left the field unpopulated instead of failing the save -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java AuditorAwareLevel2.java`.

`SecurityContextHolder.clearContext()` simulates a code path with no authenticated principal at all — `auditorAware().getCurrentAuditor()` correctly returns `Optional.empty()` in this case, and `AuditingEntityListener` treats that as "nothing to populate," leaving `createdBy` at its default (`null`) rather than throwing an exception or failing the save — a background job or scheduled task can still persist entities normally, simply without an associated auditor identity.

### Level 3 — Advanced

Provide a fallback "system" auditor for non-request-driven code paths, distinguishing genuinely anonymous/unauthenticated saves from deliberate, identified system-initiated ones — a realistic production pattern for background jobs that should still be attributable to *something* in an audit trail.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.EntityListeners;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.data.annotation.CreatedBy;
import org.springframework.data.domain.AuditorAware;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.config.EnableJpaAuditing;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;

import java.util.Optional;

@SpringBootApplication
@EnableJpaAuditing
public class AuditorAwareLevel3 {

    @Entity
    @EntityListeners(AuditingEntityListener.class)
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private double total;
        @CreatedBy
        private String createdBy;
        protected Order() {}
        public Order(double total) { this.total = total; }
        public String getCreatedBy() { return createdBy; }
    }

    public interface OrderRepository extends JpaRepository<Order, Long> {}

    // Falls back to a well-known "SYSTEM" identity when no real authentication exists,
    // rather than leaving the field null -- deliberate attribution for background jobs.
    @Bean
    public AuditorAware<String> auditorAware() {
        return () -> {
            var authentication = SecurityContextHolder.getContext().getAuthentication();
            if (authentication != null && authentication.isAuthenticated()) {
                return Optional.of(authentication.getName());
            }
            return Optional.of("SYSTEM");
        };
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(AuditorAwareLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:auditoraware3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        OrderRepository repo = ctx.getBean(OrderRepository.class);

        // Path 1: a real authenticated request.
        SecurityContextHolder.getContext().setAuthentication(
            new UsernamePasswordAuthenticationToken("grace.hopper", null,
                java.util.List.of(() -> "ROLE_USER"))); // authenticated=true when authorities are present
        Order userInitiated = repo.save(new Order(75.0));

        // Path 2: a background job, no authentication.
        SecurityContextHolder.clearContext();
        Order systemInitiated = repo.save(new Order(25.0));

        System.out.println("user-initiated order createdBy = " + userInitiated.getCreatedBy());
        System.out.println("system-initiated order createdBy = " + systemInitiated.getCreatedBy());

        if (!"grace.hopper".equals(userInitiated.getCreatedBy()))
            throw new AssertionError("Expected the real user's name for the authenticated save");
        if (!"SYSTEM".equals(systemInitiated.getCreatedBy()))
            throw new AssertionError("Expected the SYSTEM fallback for the unauthenticated save");

        System.out.println("Real user vs. SYSTEM fallback auditor both correctly attributed -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java AuditorAwareLevel3.java`.

Instead of returning `Optional.empty()` when no authentication is present, this `AuditorAware` deliberately falls back to `Optional.of("SYSTEM")` — every save is now attributed to *something*, distinguishing real users (`"grace.hopper"`, captured from an authenticated `SecurityContext`) from background/system-initiated changes (`"SYSTEM"`), rather than leaving some audit records with no creator information at all. Which approach (leaving the field `null`, as in Level 2, versus a `"SYSTEM"` fallback, as here) is correct depends entirely on what an application's audit trail actually needs to distinguish.

## 6. Walkthrough

Trace the second save in Level 3 (the system-initiated one).

1. **`SecurityContextHolder.clearContext()`** removes any previously-set authentication, simulating code running outside an authenticated request context — a scheduled job, a startup data-seeding routine, or similar.
2. **`repo.save(new Order(25.0))`** triggers the same `@PrePersist` lifecycle event as any other save, and `AuditingEntityListener` calls `auditorAware().getCurrentAuditor()` to populate `@CreatedBy`.
3. **Inside the `AuditorAware` lambda**: `SecurityContextHolder.getContext().getAuthentication()` returns `null` (no authentication set), so the `if (authentication != null && authentication.isAuthenticated())` check fails.
4. **Fallback branch**: the lambda returns `Optional.of("SYSTEM")` instead of `Optional.empty()` — a deliberate design choice to always attribute a save to *some* identity.
5. **`AuditingEntityListener` receives this non-empty `Optional`**: it unwraps it and sets `createdBy = "SYSTEM"` on the `Order` entity, exactly as it would set any real username.
6. **The actual `INSERT`** runs, persisting the order with `createdBy = "SYSTEM"` in the database — a genuinely queryable, filterable value, distinguishable from any real user's name in later audit queries.
7. **Comparison with the first save**: the earlier `userInitiated` order, saved while a real `UsernamePasswordAuthenticationToken` for `"grace.hopper"` was active, correctly captured that name instead of falling back to `"SYSTEM"` — the same `AuditorAware` bean produces different results depending purely on what `SecurityContextHolder` reports at the moment each save occurs.
8. **Verification**: the program checks both saves' `createdBy` values, confirming the fallback logic correctly distinguished the two scenarios.

```
 Path 1: authenticated request           Path 2: background job (no auth)
        |                                          |
 SecurityContextHolder has                 SecurityContextHolder is EMPTY
 Authentication("grace.hopper")                    |
        |                                          v
        v                               AuditorAware fallback: Optional.of("SYSTEM")
 AuditorAware: Optional.of("grace.hopper")          |
        |                                          v
        v                               createdBy = "SYSTEM"
 createdBy = "grace.hopper"
```

## 7. Gotchas & takeaways

> **Gotcha:** `SecurityContextHolder`'s default strategy stores the security context in a `ThreadLocal` — this means `AuditorAware` reading from it works correctly for typical synchronous request handling, but can silently return empty (or stale/incorrect data) for saves that happen on a *different* thread than the one that received the original authenticated request — a common pitfall with `@Async` methods, custom thread pools, or reactive code that hops threads, unless the security context is explicitly propagated to those threads.

- `AuditorAware<T>`'s single method, `getCurrentAuditor()`, returns an `Optional<T>` — a genuinely absent result (no current user) is a normal, expected case that `AuditingEntityListener` handles by simply not populating the identity field, not an error condition.
- Backing `AuditorAware` with `SecurityContextHolder.getContext().getAuthentication()` is the standard way to reflect a real, logged-in user's identity in `@CreatedBy`/`@LastModifiedBy`, for applications secured with Spring Security.
- Deciding between "leave the field null when no auditor exists" (Level 2) and "fall back to a well-known system identity" (Level 3) is an application-level design choice about what an audit trail should distinguish — both are legitimate, depending on whether "who created this" needs to always have a non-null answer.
- Be mindful of `SecurityContextHolder`'s thread-local storage when auditing code runs off the original request thread (`@Async` methods, custom executors) — the security context (and therefore the auditor) may not automatically be available there without explicit propagation.
