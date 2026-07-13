---
card: spring-ldap
gi: 23
slug: spring-boot-ldap-auto-configuration
title: "Spring Boot LDAP auto-configuration"
---

## 1. What it is

Spring Boot's LDAP auto-configuration (`LdapAutoConfiguration`, part of `spring-boot-autoconfigure`) automatically creates and configures a `ContextSource` and `LdapTemplate` bean from simple `spring.ldap.*` properties, without any of the manual `@Bean` configuration shown in earlier cards (0002, 0003). Combined with `spring.ldap.embedded.*` properties, it can also auto-configure and start the embedded UnboundID server from card 0022 automatically for tests or local development, again purely from properties.

## 2. Why & when

Every card so far that needed a `ContextSource`/`LdapTemplate` showed it being manually constructed and wired — reasonable for understanding the mechanics, but exactly the kind of boilerplate Spring Boot's auto-configuration model exists to eliminate for the common case. Auto-configuration exists so that, for the overwhelmingly typical setup (one directory server, standard connection details), an application needs only a handful of property values, not a hand-written `@Configuration` class — Spring Boot detects the relevant properties and the Spring LDAP jars on the classpath, and wires up sensible beans automatically.

Rely on auto-configuration when:

- The application has a single, standard LDAP connection to configure — the common case covered directly by `spring.ldap.urls`, `spring.ldap.base`, `spring.ldap.username`, `spring.ldap.password`.
- Local development or testing wants a zero-code embedded directory (card 0022) purely from `spring.ldap.embedded.*` properties.

Fall back to manual `@Configuration` (as in cards 0002–0003) when multiple distinct `ContextSource`/`LdapTemplate` beans are needed (the split-privilege pattern from card 0002), or when pooling needs the finer-grained control shown in card 0019 that plain properties don't expose.

## 3. Core concept

Think of manually wiring `ContextSource` and `LdapTemplate` as building a piece of furniture entirely from raw lumber, and Spring Boot's LDAP auto-configuration as buying the same furniture flat-packed with clear assembly instructions — for the standard, common configuration, you just provide a few measurements (properties) and Spring Boot assembles the exact same kind of beans you'd have hand-built, correctly wired together, with far less effort. It only stops being the right tool when the furniture needed is genuinely custom (multiple context sources, unusual pooling) beyond what the flat-pack instructions anticipate.

```properties
# application.properties — this alone is enough for a working ContextSource + LdapTemplate
spring.ldap.urls=ldap://localhost:389
spring.ldap.base=dc=example,dc=com
spring.ldap.username=cn=admin,dc=example,dc=com
spring.ldap.password=${LDAP_ADMIN_PASSWORD}
```

```java
@Service
public class UserService {
    private final LdapTemplate ldapTemplate; // auto-configured, just @Autowired — no @Bean needed anywhere

    public UserService(LdapTemplate ldapTemplate) {
        this.ldapTemplate = ldapTemplate;
    }
}
```

For the embedded server (card 0022), auto-configuration goes a step further: with `spring-boot-starter-data-ldap` and the UnboundID SDK on the classpath, and `spring.ldap.embedded.base-dn` set, Spring Boot starts an embedded server automatically and points the auto-configured `ContextSource` at it — genuinely zero manual server lifecycle code.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring Boot reads spring.ldap properties and automatically produces ContextSource and LdapTemplate beans, optionally backed by an auto-started embedded server">
  <rect x="20" y="30" width="200" height="60" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="120" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">spring.ldap.* properties</text>
  <text x="120" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">application.properties</text>

  <rect x="270" y="30" width="200" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="370" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">LdapAutoConfiguration</text>
  <text x="370" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(Spring Boot)</text>

  <rect x="520" y="0" width="110" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="575" y="27" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">ContextSource</text>

  <rect x="520" y="55" width="110" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="575" y="82" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">LdapTemplate</text>

  <rect x="520" y="110" width="110" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="575" y="137" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">embedded server</text>
  <text x="575" y="150" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">(if configured)</text>

  <line x1="220" y1="60" x2="265" y2="60" stroke="#3fb950" stroke-width="2" marker-end="url(#s1)"/>
  <line x1="470" y1="45" x2="515" y2="25" stroke="#3fb950" stroke-width="1.5" marker-end="url(#s2)"/>
  <line x1="470" y1="60" x2="515" y2="78" stroke="#3fb950" stroke-width="1.5" marker-end="url(#s3)"/>
  <line x1="470" y1="75" x2="515" y2="132" stroke="#3fb950" stroke-width="1.5" marker-end="url(#s4)"/>

  <defs>
    <marker id="s1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="s2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="s3" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="s4" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
  </defs>
</svg>

Properties alone drive `LdapAutoConfiguration` to produce a `ContextSource`, an `LdapTemplate`, and optionally an embedded server, wired together automatically.

## 5. Runnable example

The scenario: a Spring Boot application reading employee data, starting with pure property-driven configuration, then a profile-specific embedded-server setup for tests, and finally a case where auto-configuration needs to be selectively overridden for one specific customization while keeping the rest automatic.

### Level 1 — Basic

```properties
# application.properties
spring.ldap.urls=ldap://localhost:389
spring.ldap.base=dc=example,dc=com
spring.ldap.username=cn=admin,dc=example,dc=com
spring.ldap.password=${LDAP_ADMIN_PASSWORD}
```

```java
// EmployeeController.java
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.core.AttributesMapper;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class EmployeeController {
    private final LdapTemplate ldapTemplate; // auto-configured entirely from application.properties

    public EmployeeController(LdapTemplate ldapTemplate) {
        this.ldapTemplate = ldapTemplate;
    }

    @GetMapping("/employees/{uid}/email")
    public String email(@PathVariable String uid) {
        return ldapTemplate.lookup("uid=" + uid + ",ou=people",
            (AttributesMapper<String>) attrs -> (String) attrs.get("mail").get());
    }
}
```

**How to run:** with `LDAP_ADMIN_PASSWORD` set and a reachable directory at `localhost:389`, start the Spring Boot application and call `GET /employees/jsmith/email`. Expected response: `jsmith@example.com` — no `@Configuration` class anywhere in the application defines `ContextSource` or `LdapTemplate`; both exist purely because `LdapAutoConfiguration` read the four `spring.ldap.*` properties.

### Level 2 — Intermediate

For integration tests, pointing at a real external directory is undesirable (card 0022's motivation) — a `test` profile using `spring.ldap.embedded.*` properties gets a fully auto-started embedded server, with zero test-specific `@Bean` code.

```properties
# application-test.properties
spring.ldap.embedded.base-dn=dc=example,dc=com
spring.ldap.embedded.port=0
spring.ldap.embedded.ldif=classpath:test-data.ldif
spring.ldap.base=dc=example,dc=com
```

```java
// EmployeeControllerIntegrationTest.java
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.test.context.ActiveProfiles;

import static org.junit.jupiter.api.Assertions.assertEquals;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
class EmployeeControllerIntegrationTest {

    @Autowired
    private TestRestTemplate restTemplate;

    @Test
    void returnsSeededEmployeeEmail() {
        String email = restTemplate.getForObject("/employees/jsmith/email", String.class);
        assertEquals("jsmith@example.com", email);
    }
}
```

**How to run:** run this test with the `test` profile active and `test-data.ldif` (containing a `jsmith` entry, as in card 0021) on the test classpath. Expected result: the test passes — Spring Boot auto-configuration detected `spring.ldap.embedded.*` properties, started an embedded UnboundID server, seeded it from the LDIF file, and pointed the auto-configured `LdapTemplate` at it, all without a single line of manual server-lifecycle code in the test itself.

### Level 3 — Advanced

Real applications sometimes need one specific customization — say, connection pooling (card 0003, 0019) — that plain `spring.ldap.*` properties don't expose directly. Auto-configuration supports this gracefully: defining a custom `ContextSource` bean explicitly causes Spring Boot to back off from creating its own, while the rest of the auto-configuration (like the `LdapTemplate` bean, built from whatever `ContextSource` bean it finds) continues to work automatically.

```java
// PooledContextSourceOverride.java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.ldap.core.support.LdapContextSource;
import org.springframework.ldap.pool2.factory.PoolConfig;
import org.springframework.ldap.pool2.factory.PooledContextSource;
import org.springframework.beans.factory.annotation.Value;

@Configuration
public class PooledContextSourceOverride {

    @Value("${spring.ldap.urls}")
    private String url;
    @Value("${spring.ldap.base}")
    private String base;
    @Value("${spring.ldap.username}")
    private String username;
    @Value("${spring.ldap.password}")
    private String password;

    @Bean
    public PooledContextSource contextSource() { // this bean name/type causes Boot's own ContextSource to back off
        LdapContextSource cs = new LdapContextSource();
        cs.setUrl(url);
        cs.setBase(base);
        cs.setUserDn(username);
        cs.setPassword(password);
        cs.afterPropertiesSet();

        PoolConfig poolConfig = new PoolConfig();
        poolConfig.setMaxTotalPerKey(25);
        poolConfig.setTestOnBorrow(true);

        PooledContextSource pooled = new PooledContextSource(poolConfig);
        pooled.setContextSource(cs);
        return pooled;
    }
    // No @Bean for LdapTemplate needed — LdapAutoConfiguration still creates one automatically,
    // wired to THIS custom PooledContextSource bean instead of its own default one.
}
```

**How to run:** add this `@Configuration` class to the Level 1 application, keeping the same `application.properties`. Expected result: the application still exposes a working `LdapTemplate` bean (auto-configured, unchanged), but it's now backed by a pooled `ContextSource` with the tuning from card 0019 — one specific piece (connection creation/pooling) was customized explicitly, while everything else (reading the same properties for URL/base/credentials, wiring `LdapTemplate` to whatever `ContextSource` exists) remained fully automatic.

## 6. Walkthrough

Tracing Spring Boot's startup sequence for the Level 3 application, in execution order:

1. During context initialization, Spring Boot's auto-configuration mechanism evaluates `LdapAutoConfiguration`'s conditions — among them, a check for whether a `ContextSource` bean already exists in the application context (a `@ConditionalOnMissingBean` style condition).
2. Because `PooledContextSourceOverride` explicitly defines a `contextSource()` bean (of type `PooledContextSource`, which is itself a `ContextSource`), that condition is satisfied by the user-defined bean, and `LdapAutoConfiguration`'s own default `ContextSource`-creating logic backs off — it does not create a second, competing bean.
3. `LdapAutoConfiguration`'s `LdapTemplate`-creating logic, however, has no corresponding user-defined override in this example, so its own condition (no existing `LdapTemplate` bean) is satisfied, and it proceeds to create one — but it does so by injecting whatever `ContextSource` bean is actually available in the context, which is now the custom `PooledContextSource`, not a default one.
4. The application starts with exactly one `ContextSource` bean (the custom pooled one) and one `LdapTemplate` bean (auto-configured, but wired to the custom `ContextSource`) — a blend of manual and automatic configuration, each piece doing exactly the part it's responsible for.
5. At runtime, `EmployeeController`'s `@Autowired`-equivalent constructor injection receives this same auto-configured `LdapTemplate`, and every `lookup`/`search` call it makes flows through the custom pooled `ContextSource` underneath, exactly as if it had been hand-wired that way from the start.

```
startup:
  PooledContextSourceOverride defines contextSource() bean  -> user-defined ContextSource exists
  LdapAutoConfiguration checks: ContextSource bean already exists? YES -> back off, don't create default
  LdapAutoConfiguration checks: LdapTemplate bean already exists?   NO  -> create one
                                 -> wires it to the ONE ContextSource bean present (the pooled one)
runtime:
  EmployeeController -> auto-configured LdapTemplate -> custom PooledContextSource -> LDAP server
```

## 7. Gotchas & takeaways

> Defining a custom `ContextSource` bean to override just one aspect of auto-configuration (like pooling) is a supported, idiomatic pattern — Spring Boot's auto-configuration is specifically designed to back off when a user-defined bean of the relevant type already exists, rather than creating a conflicting duplicate. But this only works cleanly when exactly one `ContextSource`-family bean is defined; introducing two custom ones without clear `@Primary`/qualifier disambiguation reintroduces the kind of ambiguity auto-configuration is meant to avoid.

- `spring.ldap.urls`, `spring.ldap.base`, `spring.ldap.username`, `spring.ldap.password` alone are enough for a fully working `ContextSource` and `LdapTemplate`, with zero `@Configuration` classes needed for the common single-directory case.
- `spring.ldap.embedded.*` properties auto-start and auto-seed an embedded UnboundID server (card 0022), making integration tests genuinely zero-configuration beyond a properties file and an optional LDIF seed file (card 0021).
- Auto-configuration backs off gracefully when a matching user-defined bean already exists — this is the mechanism that makes selective customization (Level 3's pooling override) possible without losing the rest of the automatic wiring.
- For applications needing multiple distinct `ContextSource`/`LdapTemplate` beans (the split-privilege pattern from card 0002), plain property-driven auto-configuration isn't sufficient on its own — that scenario still calls for explicit `@Bean` definitions, since auto-configuration is designed around the single-connection common case.
- When debugging "why is my custom `ContextSource` bean not being used," check for `@ConditionalOnMissingBean`-style auto-configuration ordering issues — a custom bean defined in a configuration class that isn't scanned or that's overridden by component-scan ordering can silently fail to take effect, leaving the default auto-configured bean in place instead.
