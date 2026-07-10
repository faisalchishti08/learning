---
card: spring-framework
gi: 440
slug: petclinic-sample-driven-testing-patterns
title: "PetClinic / sample-driven testing patterns"
---

## 1. What it is

Spring PetClinic — the framework team's own long-running reference application (a simple veterinary clinic management system: owners, pets, vets, visits) — is the de facto sample project the Spring community points to for "how should a real Spring application's test suite actually be organized?" This closing card of the testing section distills the testing pyramid pattern PetClinic (and well-organized Spring applications generally) demonstrates: a layered mix of the techniques covered throughout this entire section, each applied to the layer it fits best, rather than one testing style used uniformly everywhere.

```
 PetClinic-style layered test suite:
   OwnerTest              -- pure unit test, no Spring at all (validation logic)
   VisitControllerTests   -- @WebMvcTest / MockMvc (web layer, mocked service)
   OwnerRepositoryTests   -- @DataJpaTest (repository layer, real embedded/containerized DB)
   PetClinicIntegrationTests -- @SpringBootTest (full stack, fewest of these)
```

## 2. Why & when

Every individual technique in this section — plain unit tests, `MockMvc`, `@DataJpaTest`-style repository slices, full `@SpringBootTest` — has its own well-defined scope and trade-off, covered card by card. What PetClinic demonstrates, and what this closing card is about, is how those pieces fit together in one coherent, well-organized test suite: which layer gets which kind of test, roughly how many of each, and why that specific mix produces a suite that's both fast to run and genuinely trustworthy.

The pattern, restated as a decision guide:

- **Domain/validation logic with no Spring dependency** (a `Pet`'s age calculation, a validation rule) → plain unit test, zero Spring context, the fastest and most numerous tier.
- **A single controller's request-handling behavior** (routing, argument binding, view selection) → a narrowly-scoped `MockMvc` test (often Spring Boot's `@WebMvcTest` slice, which loads only web-layer beans, not the whole application) with mocked service dependencies.
- **A repository's actual query behavior against a real schema** → a `@DataJpaTest`-style slice test (loads only JPA-related configuration, backed by an embedded or Testcontainers-provided real database).
- **The whole application wired together and working end-to-end** → a full `@SpringBootTest`, deliberately kept to a small number covering the most critical paths, not attempting to exhaustively re-test everything the narrower, faster layers below it already covered.

## 3. Core concept

```
        Test count (many)                              Test count (few)
             ^                                                ^
             |                                                |
   Unit tests (Owner validation, Pet age calc)       Full @SpringBootTest
   -- no Spring context at all                        -- entire real application
             |                                                |
   @WebMvcTest (OwnerController, VisitController)     covers only the FEW most
   -- web layer slice, mocked service                  critical end-to-end paths
             |                                                |
   @DataJpaTest (OwnerRepository, VetRepository)              |
   -- persistence layer slice, real DB                        |
             |________________________________________________|
                    each layer tested at its OWN natural boundary
```

The shape is the testing pyramid from the very first card of this section, made concrete: PetClinic has many fast unit tests, a healthy number of layer-specific slice tests, and only a handful of full-application integration tests — each layer tested with the cheapest technique that still gives genuine confidence for that layer.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="PetClinic-style layered test suite mapped onto the application's own layers">
  <rect x="220" y="15" width="200" height="40" rx="6" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="320" y="39" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Unit tests -- domain logic</text>

  <rect x="180" y="70" width="280" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="94" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@WebMvcTest -- controllers, MockMvc</text>

  <rect x="180" y="125" width="280" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="149" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@DataJpaTest -- repositories, real DB</text>

  <rect x="220" y="180" width="200" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="201" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">@SpringBootTest -- few, full-stack</text>
</svg>

Fast and numerous at the top and middle, deliberately sparse at the bottom.

## 5. Runnable example

A miniature PetClinic-style domain — `Owner` and `Pet` — demonstrating all four layers of the pattern in one coherent, runnable example set.

### Level 1 — Basic

The fastest, most numerous tier: a plain unit test for domain validation logic, no Spring context, mirroring PetClinic's own `OwnerTest`-style pure-logic tests.

```java
import java.time.LocalDate;
import java.time.Period;

public class PetClinicPatternBasic {

    record Pet(String name, LocalDate birthDate) {
        int ageInYears(LocalDate today) {
            if (birthDate.isAfter(today)) throw new IllegalArgumentException("Birth date cannot be in the future");
            return Period.between(birthDate, today).getYears();
        }
    }

    public static void main(String[] args) {
        Pet pet = new Pet("Rex", LocalDate.of(2020, 3, 15));

        int age = pet.ageInYears(LocalDate.of(2026, 6, 1));
        System.out.println("Rex's age: " + age);
        if (age != 6) throw new AssertionError("Expected age 6, got " + age);
        System.out.println("ageInYears calculation -- PASS");

        try {
            pet.ageInYears(LocalDate.of(2019, 1, 1)); // before birth date
            throw new AssertionError("Expected rejection of a date before birth");
        } catch (IllegalArgumentException e) {
            System.out.println("Correctly rejected an impossible date: " + e.getMessage());
        }

        System.out.println("Layer 1 (pure unit test, no Spring) -- PASS. This is the FASTEST, "
                + "MOST NUMEROUS tier of the pyramid -- domain logic tested in complete isolation.");
    }
}
```

How to run: `java PetClinicPatternBasic.java` — no dependencies beyond the JDK.

Exactly like PetClinic's own domain tests, this verifies business logic (age calculation, validation) with zero Spring involvement — the fastest possible feedback loop, and the tier that should have the most tests in any well-organized Spring application's suite.

### Level 2 — Intermediate

The web-layer slice tier: a `MockMvc` test for a controller, with its service dependency mocked — mirroring PetClinic's `VisitControllerTests`-style pattern of testing request handling in isolation from persistence.

```java
import org.springframework.stereotype.Controller;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

import java.util.List;
import java.util.Optional;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

public class PetClinicPatternIntermediate {

    record Owner(long id, String firstName, String lastName) {}

    interface OwnerRepository { Optional<Owner> findById(long id); }

    @Controller
    static class OwnerController {
        private final OwnerRepository repository;
        OwnerController(OwnerRepository repository) { this.repository = repository; }

        @GetMapping("/owners/{id}")
        String showOwner(@PathVariable long id, Model model) {
            Owner owner = repository.findById(id).orElseThrow();
            model.addAttribute("owner", owner);
            return "ownerDetails";
        }
    }

    public static void main(String[] args) throws Exception {
        // The service/repository dependency is a hand-built test double -- in a real
        // PetClinic-style @WebMvcTest, this would typically be a Mockito @MockitoBean,
        // combining the patterns from this card and the @MockitoBean card earlier in this section.
        OwnerRepository fakeRepository = id -> id == 1
                ? Optional.of(new Owner(1, "George", "Franklin"))
                : Optional.empty();

        MockMvc mockMvc = MockMvcBuilders
                .standaloneSetup(new OwnerController(fakeRepository))
                .setViewResolvers((viewName, locale) -> (model, request, response) -> {
                    response.setContentType("text/html");
                    Owner owner = (Owner) model.get("owner");
                    response.getWriter().write("<html><body>" + owner.firstName() + " " + owner.lastName() + "</body></html>");
                })
                .build();

        mockMvc.perform(get("/owners/1"))
                .andExpect(status().isOk())
                .andExpect(content().string(org.hamcrest.Matchers.containsString("George Franklin")));

        System.out.println("Layer 2 (@WebMvcTest / MockMvc style, mocked repository) -- PASS. "
                + "This tests routing and view rendering WITHOUT touching a real database.");
    }
}
```

How to run: add `spring-test`, `spring-webmvc`, and `jakarta.servlet-api` to the classpath, then `java PetClinicPatternIntermediate.java`.

This is the web-layer slice pattern: the controller's real request-handling logic runs, but its data dependency (`OwnerRepository`) is a fake, not a real database connection — exactly PetClinic's own `@WebMvcTest`-annotated controller tests, which Spring Boot auto-configures to load only web-layer beans plus mocked service/repository dependencies, deliberately excluding the full persistence stack this layer doesn't need to touch.

### Level 3 — Advanced

The persistence-layer slice tier and the full-stack tier together, in one example: a repository test against a real embedded database (the `@DataJpaTest`-style pattern), and a minimal full-stack test demonstrating why PetClinic keeps full-application tests deliberately few — because the layers below already cover most of the actual logic.

```java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.embedded.EmbeddedDatabaseBuilder;
import org.springframework.jdbc.datasource.embedded.EmbeddedDatabaseType;

import javax.sql.DataSource;
import java.util.List;
import java.util.Optional;

public class PetClinicPatternAdvanced {

    record Owner(long id, String lastName) {}

    // A minimal repository whose real query logic is exactly what this layer's tests exist to verify.
    static class JdbcOwnerRepository {
        private final JdbcTemplate jdbcTemplate;
        JdbcOwnerRepository(JdbcTemplate jdbcTemplate) { this.jdbcTemplate = jdbcTemplate; }

        List<Owner> findByLastNameStartingWith(String prefix) {
            return jdbcTemplate.query(
                    "SELECT id, last_name FROM owners WHERE last_name LIKE ?",
                    (rs, rowNum) -> new Owner(rs.getLong("id"), rs.getString("last_name")),
                    prefix + "%");
        }
    }

    static class OwnerService {
        private final JdbcOwnerRepository repository;
        OwnerService(JdbcOwnerRepository repository) { this.repository = repository; }
        List<Owner> search(String lastNamePrefix) { return repository.findByLastNameStartingWith(lastNamePrefix); }
    }

    @Configuration
    static class Config {
        @Bean
        DataSource dataSource() {
            return new EmbeddedDatabaseBuilder()
                    .setType(EmbeddedDatabaseType.H2)
                    .addScript("classpath:owners-schema.sql") // CREATE TABLE owners(id BIGINT, last_name VARCHAR(50))
                    .build();
        }
        @Bean JdbcTemplate jdbcTemplate(DataSource ds) { return new JdbcTemplate(ds); }
        @Bean JdbcOwnerRepository ownerRepository(JdbcTemplate jdbcTemplate) { return new JdbcOwnerRepository(jdbcTemplate); }
        @Bean OwnerService ownerService(JdbcOwnerRepository repository) { return new OwnerService(repository); }
    }

    public static void main(String[] args) {
        var context = new AnnotationConfigApplicationContext(Config.class);
        JdbcTemplate jdbcTemplate = context.getBean(JdbcTemplate.class);

        jdbcTemplate.update("INSERT INTO owners VALUES (1, 'Franklin')");
        jdbcTemplate.update("INSERT INTO owners VALUES (2, 'Davis')");
        jdbcTemplate.update("INSERT INTO owners VALUES (3, 'Franklyn')"); // deliberately similar but NOT matching

        // --- Layer 3: repository slice, real (embedded) database, THIS is where query correctness lives ---
        JdbcOwnerRepository repository = context.getBean(JdbcOwnerRepository.class);
        List<Owner> matches = repository.findByLastNameStartingWith("Frank");
        System.out.println("Repository layer found: " + matches);
        if (matches.size() != 1 || !matches.get(0).lastName().equals("Franklin")) {
            throw new AssertionError("Expected exactly one match: Franklin");
        }
        System.out.println("Layer 3 (@DataJpaTest style, real embedded DB) -- PASS. "
                + "This is where SQL/query correctness genuinely gets verified.");

        // --- Layer 4: a minimal full-stack test, deliberately checking only the WIRING, ---
        // --- since the query logic itself was ALREADY thoroughly verified at layer 3 above. ---
        OwnerService service = context.getBean(OwnerService.class);
        List<Owner> serviceResult = service.search("Frank");
        if (serviceResult.size() != 1) throw new AssertionError("Expected the service layer to correctly delegate");
        System.out.println("Layer 4 (full-stack wiring check) -- PASS. Notice this test does NOT "
                + "re-verify the SQL LIKE-prefix logic in detail -- layer 3 already did that job.");

        context.close();
    }
}
```

How to run: add `spring-context`, `spring-jdbc`, `com.h2database:h2` to the classpath, with `owners-schema.sql` on the classpath; then `java PetClinicPatternAdvanced.java`.

The repository-layer test (`findByLastNameStartingWith`) is where the actual SQL correctness gets verified thoroughly — including the negative case (`"Franklyn"` deliberately doesn't match a `"Frank"` prefix search the way a naive substring match might). The full-stack-style test at the end deliberately does *not* re-verify that same SQL logic in detail — it only confirms `OwnerService` correctly delegates to the repository and gets a sensible result, exactly the PetClinic pattern of "test each concern once, at the layer where testing it is cheapest and most direct," rather than re-testing SQL correctness redundantly at every higher layer.

## 6. Walkthrough

Trace how a bug in `findByLastNameStartingWith`'s SQL — say, a typo using `=` instead of `LIKE ? || '%'` semantics — would be caught (or missed) at each layer, illustrating why the layered approach matters:

1. **Layer 1 (pure unit tests).** `Pet.ageInYears` and similar domain-logic tests have no SQL in them at all — this bug class is entirely outside their scope, by construction. They'd continue passing, uselessly, telling you nothing about the actual bug.
2. **Layer 2 (`@WebMvcTest`/`MockMvc` with mocked repository).** `OwnerController`'s test uses a *fake* `OwnerRepository` (a hand-built lambda, or a Mockito mock) — the real SQL never runs here either. This layer would also continue passing, since it was never testing the real query in the first place.
3. **Layer 3 (`@DataJpaTest`-style repository test).** This is where the bug is actually caught: `repository.findByLastNameStartingWith("Frank")` runs the *real* SQL against a *real* (if embedded) database — a broken `LIKE` clause would return the wrong rows (or throw a SQL error), and the assertion `matches.size() != 1` would fail, pointing precisely at the repository layer as the source of the problem.
4. **Layer 4 (full-stack test).** Even without layer 3 existing, this layer *would* eventually catch the bug too — `service.search("Frank")` ultimately calls the same broken SQL — but the failure here is less precisely diagnostic: is the bug in `OwnerService`'s delegation logic, or in the repository's query, or somewhere in the wiring? Layer 3's narrower scope makes the failure immediately attributable to exactly one place, which is the practical argument for maintaining that middle layer rather than relying solely on full-stack tests to catch everything.

```
SQL bug in findByLastNameStartingWith (real query logic)

Layer 1 (pure unit, no SQL involved)        -> cannot catch (wrong scope entirely)
Layer 2 (MockMvc, mocked repository)         -> cannot catch (fake repository has no real SQL)
Layer 3 (@DataJpaTest, real embedded DB)     -> CATCHES IT, precisely -- "the repository query is wrong"
Layer 4 (full-stack)                          -> would ALSO catch it, but less precisely --
                                                   "something somewhere in owner search is wrong"
```

This is the concrete payoff of PetClinic's layered pattern: each layer is scoped to catch a specific class of bug, at the cheapest possible cost, with the most precise possible diagnostic signal — and the full-stack layer exists as a final safety net, not as the primary mechanism for catching most bugs.

## 7. Gotchas & takeaways

> Gotcha: a test suite that skips the middle layers (repository slices, web-layer slices) and relies almost entirely on full `@SpringBootTest`-style tests for everything technically "covers" the same code paths, but trades away fast, precise failure diagnosis for slow, ambiguous failure diagnosis — and multiplies test-suite runtime, since every test pays full-application-context-startup cost (mitigated somewhat by context caching, per the earlier card, but still substantially more than a narrow slice test) even when testing something as narrow as one repository method's SQL correctness.

- PetClinic's testing pattern is the testing pyramid (from this section's very first card) made concrete: many fast unit tests, a healthy number of layer-specific slice tests (`@WebMvcTest`-style, `@DataJpaTest`-style), and deliberately few full-stack `@SpringBootTest`-style tests.
- Match each test to the layer and concern it's actually meant to verify — domain logic gets plain unit tests, request handling gets a web-layer slice with mocked dependencies, query correctness gets a persistence-layer slice with a real database, and full-stack tests verify wiring across the most critical paths only.
- A bug is caught with maximum diagnostic precision at the narrowest layer that can actually exercise it — testing SQL correctness only at the full-stack level still eventually catches SQL bugs, but with far less precise "which layer is actually broken" information than a dedicated repository-layer test provides.
- This layered pattern, combined with every individual technique covered throughout this testing section (unit testing, `MockMvc`, TestContext Framework fundamentals, transaction management in tests, `@MockitoBean`, Testcontainers, and more), is what produces a Spring test suite that's both fast to run and genuinely trustworthy — the goal the very first "Spring testing philosophy" card in this section set out to achieve.
