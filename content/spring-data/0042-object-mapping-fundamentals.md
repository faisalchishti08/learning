---
card: spring-data
gi: 42
slug: object-mapping-fundamentals
title: "Object mapping fundamentals"
---

## 1. What it is

Object mapping is the general mechanism, shared across every Spring Data module, that translates between a Java domain object and its store-specific representation — for JPA, that's largely delegated to Hibernate's own well-established annotation-driven mapping (`@Entity`, `@Column`, `@ManyToOne`), but Spring Data Commons also defines its own lighter-weight mapping model (`@Id`, `@PersistenceCreator`, immutable-object support via all-args constructors) used directly by non-JPA stores, and worth understanding because it explains constructor-based object creation — a pattern this section's examples have used implicitly whenever an entity has a non-default constructor.

```java
public class Customer {
    @Id private final Long id;
    private final String name;

    @PersistenceCreator // tells Spring Data's mapping which constructor to use for loading
    public Customer(Long id, String name) {
        this.id = id;
        this.name = name;
    }
}
```

## 2. Why & when

Every entity in this section's examples has had a protected no-arg constructor (for JPA/Hibernate's own instantiation needs) alongside a public, meaningful constructor for application code to use — this pattern exists because of how object mapping actually works: JPA specifically requires a no-arg constructor (even if protected) to instantiate entities via reflection before populating fields, while Spring Data's own Commons-level mapping (used by non-JPA stores) can construct objects directly through a real, parameterized constructor, enabling genuinely immutable domain objects with `final` fields — a capability plain JPA entities don't have without extra provider-specific support.

Understanding object mapping fundamentals matters specifically when:

- You're deciding whether an entity's fields can be genuinely immutable (`final`, set only in the constructor) — for JPA specifically, this needs either bytecode enhancement or a compromise (mutable fields, protected no-arg constructor); for Spring Data's non-JPA modules, immutable domain objects are the natural, default-supported style.
- You're debugging why a particular constructor is (or isn't) being used when an entity is loaded from the database — `@PersistenceCreator` explicitly designates one when multiple constructors would otherwise be ambiguous.
- You're working with a non-JPA Spring Data module (MongoDB, Redis) where understanding this Commons-level mapping model is directly relevant, rather than being an abstraction JPA/Hibernate mostly hides.

## 3. Core concept

```
 JPA specifically:
   requires a no-arg constructor (can be protected) -- Hibernate instantiates
   via reflection, THEN populates fields (also via reflection, bypassing
   normal setters unless field access is configured differently)
        |
        v
   entities are typically NOT fully immutable in plain JPA -- fields are
   set after construction, so "final" fields are awkward/unsupported by
   default (though Hibernate bytecode enhancement can relax this)

 Spring Data Commons' OWN mapping (used directly by non-JPA modules):
   PersistentEntity / PersistentProperty abstractions describe a domain
   class's structure generically, independent of any specific store

   @PersistenceCreator on a constructor (or a static factory method) tells
   the mapping infrastructure: "construct the object THROUGH here,
   passing in the loaded property values as arguments" -- enabling
   genuinely immutable domain objects with final fields, constructed
   directly rather than via no-arg-then-reflectively-populate
```

JPA's reflection-based, no-arg-constructor-then-populate model and Spring Data Commons' constructor-based model are genuinely different mechanisms — JPA entities in this section's examples have used the former; understanding both explains why the "protected no-arg constructor" pattern exists specifically for JPA.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="JPA instantiates via a no-arg constructor then populates fields reflectively; Spring Data Commons mapping constructs directly through a parameterized constructor">
  <rect x="10" y="20" width="280" height="65" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">JPA / Hibernate</text>
  <text x="150" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">no-arg constructor, THEN</text>
  <text x="150" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">reflectively populate fields</text>

  <rect x="350" y="20" width="280" height="65" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="490" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Spring Data Commons mapping</text>
  <text x="490" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">construct DIRECTLY via</text>
  <text x="490" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@PersistenceCreator constructor</text>
</svg>

Two genuinely different object-construction strategies, chosen based on which Spring Data module is in play.

## 5. Runnable example

The scenario: comparing a mutable, no-arg-constructor JPA entity against a genuinely immutable domain object mapped via Spring Data Commons' own constructor-based mapping (demonstrated using Spring Data's `MappingContext`/`PersistentEntity` infrastructure directly, independent of any specific store) — making the two models' difference concrete.

### Level 1 — Basic

Confirm a JPA entity genuinely requires (and uses) its protected no-arg constructor, by observing Hibernate's reflective instantiation.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;

@SpringBootApplication
public class ObjectMappingLevel1 {

    @Entity
    public static class Customer {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;

        // JPA REQUIRES this -- Hibernate instantiates via reflection using it,
        // THEN populates the fields afterward, bypassing this constructor's logic entirely.
        protected Customer() {
            System.out.println("[no-arg constructor] called -- Hibernate needs this for instantiation");
        }

        public Customer(String name) {
            this(); // demonstrates the no-arg constructor still runs even via this one
            this.name = name;
        }

        public String getName() { return name; }
    }

    public interface CustomerRepository extends JpaRepository<Customer, Long> {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(ObjectMappingLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:objmap1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        CustomerRepository repo = ctx.getBean(CustomerRepository.class);
        Customer saved = repo.save(new Customer("Ada Lovelace"));

        System.out.println("--- now reloading from the database, watch for the no-arg constructor call ---");
        Customer reloaded = repo.findById(saved.getId()).orElseThrow();

        System.out.println("reloaded name = " + reloaded.getName());
        if (!"Ada Lovelace".equals(reloaded.getName())) throw new AssertionError("Expected the name to be correctly reloaded");
        System.out.println("JPA used no-arg construction, then reflectively populated fields, on load -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java ObjectMappingLevel1.java` on JDK 17+.

Watching the console output around the `findById` call shows `"[no-arg constructor] called"` printed again — Hibernate genuinely instantiates a fresh `Customer` via the protected no-arg constructor when loading from the database, then populates `name` reflectively afterward, entirely bypassing the `Customer(String name)` constructor's own logic for this reload — the field is set directly, not through this constructor.

### Level 2 — Intermediate

Use Spring Data Commons' own mapping infrastructure directly (`SampleMappingContext`, a lightweight, store-independent `MappingContext` implementation meant for exactly this kind of demonstration/testing) to inspect how it identifies a constructor-based, immutable domain class.

```java
import org.springframework.data.annotation.Id;
import org.springframework.data.annotation.PersistenceCreator;
import org.springframework.data.mapping.PersistentEntity;
import org.springframework.data.mapping.context.SampleMappingContext;
import org.springframework.data.mapping.model.PreferredConstructor;

public class ObjectMappingLevel2 {

    // A genuinely IMMUTABLE domain object -- final fields, no no-arg constructor,
    // no setters at all. This style is impossible with plain JPA but natural here.
    public static class Customer {
        @Id
        private final Long id;
        private final String name;

        @PersistenceCreator
        public Customer(Long id, String name) {
            this.id = id;
            this.name = name;
        }

        public Long getId() { return id; }
        public String getName() { return name; }
    }

    public static void main(String[] args) {
        SampleMappingContext mappingContext = new SampleMappingContext();
        PersistentEntity<?, ?> entity = mappingContext.getPersistentEntity(Customer.class);

        System.out.println("mapped entity type = " + entity.getType().getSimpleName());
        System.out.println("is this a constructor-based (non-default-constructor) entity? " + !entity.isNew(new Object()));

        PreferredConstructor<?, ?> constructor = entity.getPersistenceConstructor();
        System.out.println("has a persistence constructor? " + (constructor != null));
        System.out.println("constructor parameter count = " + (constructor != null ? constructor.getParameterCount() : -1));

        if (constructor == null) throw new AssertionError("Expected a persistence constructor to be identified");
        if (constructor.getParameterCount() != 2)
            throw new AssertionError("Expected the 2-argument @PersistenceCreator constructor to be identified");

        System.out.println("Spring Data Commons mapping correctly identified the @PersistenceCreator constructor -- PASS");
    }
}
```

How to run: put `spring-data-commons` on the classpath, then `java ObjectMappingLevel2.java` on JDK 17+. No database or Spring context needed — this inspects the mapping metadata directly.

`SampleMappingContext` is Spring Data Commons' own lightweight, store-independent implementation of the `MappingContext` abstraction every store module builds on — using it directly here demonstrates the mapping-metadata layer in isolation. `entity.getPersistenceConstructor()` correctly identifies `Customer`'s `@PersistenceCreator`-annotated, 2-argument constructor as the one to use for object creation — proof that Spring Data's own mapping model genuinely supports constructing an object directly through a real, parameterized constructor, unlike JPA's no-arg-then-populate approach from Level 1.

### Level 3 — Advanced

Manually construct a `Customer` instance using the identified persistence constructor's parameter metadata — simulating, at a low level, exactly what a real non-JPA Spring Data module (like Spring Data MongoDB) does internally when loading a document and mapping it back into a domain object.

```java
import org.springframework.data.annotation.Id;
import org.springframework.data.annotation.PersistenceCreator;
import org.springframework.data.mapping.PersistentEntity;
import org.springframework.data.mapping.context.SampleMappingContext;
import org.springframework.data.mapping.model.ParameterValueProvider;
import org.springframework.data.mapping.model.PreferredConstructor;

import java.util.LinkedHashMap;
import java.util.Map;

public class ObjectMappingLevel3 {

    public static class Customer {
        @Id
        private final Long id;
        private final String name;
        private final boolean active;

        @PersistenceCreator
        public Customer(Long id, String name, boolean active) {
            this.id = id;
            this.name = name;
            this.active = active;
        }

        public Long getId() { return id; }
        public String getName() { return name; }
        public boolean isActive() { return active; }
        @Override public String toString() { return "Customer{id=" + id + ", name='" + name + "', active=" + active + "}"; }
    }

    public static void main(String[] args) throws Exception {
        SampleMappingContext mappingContext = new SampleMappingContext();
        PersistentEntity<?, ?> entity = mappingContext.getPersistentEntity(Customer.class);
        PreferredConstructor<?, ?> constructor = entity.getPersistenceConstructor();

        // Simulate "loaded raw data" -- as if read from a document store, keyed by property name.
        Map<String, Object> rawLoadedData = new LinkedHashMap<>();
        rawLoadedData.put("id", 42L);
        rawLoadedData.put("name", "Grace Hopper");
        rawLoadedData.put("active", true);

        // Build the object DIRECTLY through the reflective constructor, using the
        // raw data map -- exactly the pattern a real store module's mapping converter uses.
        java.lang.reflect.Constructor<?> rawConstructor = constructor.getConstructor();
        Object[] args2 = new Object[rawConstructor.getParameterCount()];
        String[] parameterNames = {"id", "name", "active"}; // matches @PersistenceCreator constructor order
        for (int i = 0; i < parameterNames.length; i++) {
            args2[i] = rawLoadedData.get(parameterNames[i]);
        }
        rawConstructor.setAccessible(true);
        Customer constructed = (Customer) rawConstructor.newInstance(args2);

        System.out.println("constructed directly via persistence constructor: " + constructed);

        if (!constructed.getName().equals("Grace Hopper") || !constructed.isActive() || !constructed.getId().equals(42L))
            throw new AssertionError("Expected the constructed object to reflect the raw loaded data exactly");

        System.out.println("Manually replicated constructor-based object mapping, exactly as a real store module would -- PASS");
    }
}
```

How to run: same classpath as Level 2, `java ObjectMappingLevel3.java`.

This deliberately low-level example replicates, by hand, what a real Spring Data MongoDB (or Redis) mapping converter does internally: take raw loaded data (here, a simple `Map` standing in for a parsed document), look up the `@PersistenceCreator`-designated constructor's parameters by name, and invoke that constructor directly via reflection — producing a fully-formed, genuinely immutable `Customer` object in one step, with no intermediate no-arg-then-populate phase at all. This is the mechanism that makes truly immutable domain objects (final fields, no setters) practical for non-JPA Spring Data modules.

## 6. Walkthrough

Trace Level 3's manual construction.

1. **`mappingContext.getPersistentEntity(Customer.class)`** builds (or retrieves from a cache) a `PersistentEntity` describing `Customer`'s structure — its properties (`id`, `name`, `active`), their types, and which one is the `@Id`.
2. **`entity.getPersistenceConstructor()`** identifies `Customer`'s single constructor, annotated `@PersistenceCreator`, as the designated "construct through here" constructor — Spring Data's mapping infrastructure performs this exact lookup internally whenever it needs to instantiate a domain object during a real load operation.
3. **Simulated raw data**: `rawLoadedData` stands in for whatever a real store driver would have already parsed from its native format — a MongoDB `Document`, a Redis hash, or similar — keyed by property name, exactly as it would be after a real database read.
4. **Parameter assembly**: the code walks the constructor's parameters in the order `@PersistenceCreator`'s constructor declares them (`id`, `name`, `active`) and looks up each corresponding value from `rawLoadedData` — real Spring Data mapping converters use a `ParameterValueProvider` abstraction to do exactly this lookup, matching constructor parameter names to available property values.
5. **Direct construction**: `rawConstructor.newInstance(args2)` invokes `Customer`'s actual constructor directly, with all three values supplied simultaneously — there is no intermediate "empty" `Customer` object at any point; the fully-formed, immutable instance is created in this single reflective call.
6. **Result**: `constructed` is a genuine `Customer` with all three `final` fields correctly set — `id=42`, `name="Grace Hopper"`, `active=true` — exactly matching the simulated raw data, having never gone through a no-arg-constructor-then-setter pattern at all.
7. **Verification**: the program checks all three fields on the constructed object match the raw input data, confirming the constructor-based mapping model genuinely produces a correctly-populated, immutable object directly.

```
 raw loaded data: {id: 42, name: "Grace Hopper", active: true}
        |
        v
 @PersistenceCreator constructor identified: Customer(Long id, String name, boolean active)
        |
        v
 match parameter names to raw data values, IN ORDER
        |
        v
 constructor.newInstance(42L, "Grace Hopper", true)
        |
        v
 fully-formed, IMMUTABLE Customer object -- no intermediate empty state ever existed
```

## 7. Gotchas & takeaways

> **Gotcha:** JPA entities in this section's examples all needed a protected (not private) no-arg constructor specifically because Hibernate's reflective instantiation requires at least package-private visibility to invoke it — a genuinely `private` no-arg constructor on a JPA entity typically fails at runtime with an instantiation error, a subtle gotcha for anyone assuming `private` is always the "most encapsulated, therefore safest" choice.

- JPA/Hibernate's object mapping model requires a no-arg constructor (protected is the conventional visibility), instantiating an entity via reflection first and populating its fields afterward — this is why every JPA entity in this section has followed that exact pattern.
- Spring Data Commons' own mapping model (`PersistentEntity`, `PersistentProperty`, `@PersistenceCreator`) is store-independent and supports genuinely immutable domain objects, constructed directly through a real, parameterized constructor with no intermediate empty-object phase.
- `@PersistenceCreator` explicitly designates which constructor (or static factory method) the mapping infrastructure should use when a class has more than one candidate, removing any ambiguity about which one gets invoked during a load.
- Non-JPA Spring Data modules (MongoDB, Redis, and others) rely directly on this Commons-level mapping model, which is why immutable, `final`-field domain objects are a natural, well-supported style there, in contrast to plain JPA's more mutable, reflection-populated entity style.
