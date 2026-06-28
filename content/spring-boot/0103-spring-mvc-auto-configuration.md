---
card: spring-boot
gi: 103
slug: spring-mvc-auto-configuration
title: Spring MVC auto-configuration
---

## 1. What it is

Spring Boot's **Spring MVC auto-configuration** automatically sets up the full web stack when it finds `spring-webmvc` on the classpath. You get a production-ready MVC setup with zero XML and zero `@Configuration` boilerplate — just add `spring-boot-starter-web` and write your `@RestController`.

What auto-configuration provides out of the box:
- A `DispatcherServlet` mapped to `"/"`.
- `ContentNegotiatingViewResolver` and `BeanNameViewResolver`.
- Support for serving static resources from `/static`, `/public`, `/resources`, `/META-INF/resources`.
- `HttpMessageConverter` beans (Jackson for JSON, XML for JAXB if present).
- `MessageCodesResolver` for form validation error codes.
- `WebBindingInitializer` with a shared `ConversionService`.
- `PathMatchingContentNegotiationStrategy`.
- Automatic registration of `Converter`, `GenericConverter`, `Formatter` beans.

The auto-configuration class is `WebMvcAutoConfiguration` inside `spring-boot-autoconfigure.jar`.

## 2. Why & when

Before Spring Boot, setting up Spring MVC required: a `DispatcherServlet` in `web.xml`, a `@Configuration` with `@EnableWebMvc`, message converter beans, static resource handlers, and view resolver configuration — typically 50–100 lines of boilerplate.

Auto-configuration eliminates all of it. The trade-off is that you must understand what auto-configuration does when you need to extend or override it, so you don't accidentally disable the defaults.

**Extend (recommended):** add your own `@Configuration` class that **does not** annotate `@EnableWebMvc`. Spring Boot detects the absence of `@EnableWebMvc` and applies its own MVC configuration while honouring your additions via `WebMvcConfigurer`.

**Replace:** annotate a `@Configuration` class with `@EnableWebMvc`. This switches off `WebMvcAutoConfiguration` entirely. Now you own 100% of the configuration. Only do this if you need complete control.

## 3. Core concept

`WebMvcAutoConfiguration` is conditionally activated:
```
@ConditionalOnWebApplication(type = SERVLET)
@ConditionalOnClass({ Servlet.class, DispatcherServlet.class, WebMvcConfigurer.class })
@ConditionalOnMissingBean(WebMvcConfigurationSupport.class)
```

The last condition is the key: if you add `@EnableWebMvc` (which imports `DelegatingWebMvcConfiguration extends WebMvcConfigurationSupport`), `WebMvcAutoConfiguration` backs off. This is the "missing bean" pattern.

To add to the auto-configuration without replacing it:
```java
@Configuration
public class MyMvcConfig implements WebMvcConfigurer {
    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(new LoggingInterceptor());
    }
    @Override
    public void addFormatters(FormatterRegistry registry) {
        registry.addConverter(new OrderIdConverter());
    }
}
```

Spring Boot merges all `WebMvcConfigurer` implementations (including its own auto-configured one) via `WebMvcConfigurerComposite`.

## 4. Diagram

<svg viewBox="0 0 680 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring MVC auto-configuration: extends vs replaces path, showing WebMvcAutoConfiguration conditions">
  <rect x="8" y="8" width="664" height="264" rx="12" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="340" y="33" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="sans-serif" font-weight="bold">WebMvcAutoConfiguration — Extend vs. Replace</text>

  <!-- Left: extend -->
  <rect x="30" y="55" width="290" height="100" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="175" y="74" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Extend (recommended)</text>
  <text x="50" y="92" fill="#e6edf3" font-size="10" font-family="monospace">@Configuration</text>
  <text x="50" y="107" fill="#e6edf3" font-size="10" font-family="monospace">public class MyMvc</text>
  <text x="50" y="122" fill="#e6edf3" font-size="10" font-family="monospace">    implements WebMvcConfigurer {</text>
  <text x="50" y="137" fill="#8b949e" font-size="10" font-family="monospace">  // add interceptors, formatters…</text>
  <text x="175" y="153" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">✓ WebMvcAutoConfiguration stays active</text>

  <!-- Right: replace -->
  <rect x="360" y="55" width="290" height="100" rx="7" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="505" y="74" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Replace (rarely needed)</text>
  <text x="380" y="92" fill="#e6edf3" font-size="10" font-family="monospace">@Configuration</text>
  <text x="380" y="107" fill="#f85149" font-size="10" font-family="monospace">@EnableWebMvc</text>
  <text x="380" y="122" fill="#e6edf3" font-size="10" font-family="monospace">public class MyMvc { … }</text>
  <text x="505" y="153" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">✗ WebMvcAutoConfiguration backs off</text>

  <!-- Auto-config box -->
  <rect x="150" y="186" width="380" height="60" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="340" y="206" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">WebMvcAutoConfiguration</text>
  <text x="340" y="224" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">DispatcherServlet, MessageConverters, ViewResolvers, Static Resources</text>
  <text x="340" y="238" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@ConditionalOnMissingBean(WebMvcConfigurationSupport.class)</text>

  <defs><marker id="ma" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L5,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="175" y1="156" x2="260" y2="184" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ma)"/>
  <line x1="505" y1="156" x2="420" y2="184" stroke="#f85149" stroke-width="1.5" stroke-dasharray="4 3" marker-end="url(#ma)"/>
</svg>

Implement `WebMvcConfigurer` to add to auto-config; use `@EnableWebMvc` only when you want full ownership.

## 5. Runnable example

```java
// SpringMvcAutoConfig.java — run: java SpringMvcAutoConfig.java  (JDK 17+)
// Shows the conditions WebMvcAutoConfiguration checks and what it registers.

import java.util.*;

public class SpringMvcAutoConfig {

    // Simulates a class on the classpath check
    static boolean onClasspath(String className) {
        return Set.of(
            "jakarta.servlet.Servlet",
            "org.springframework.web.servlet.DispatcherServlet",
            "org.springframework.web.servlet.config.annotation.WebMvcConfigurer"
        ).contains(className);
    }

    // Simulates @ConditionalOnMissingBean(WebMvcConfigurationSupport.class)
    // Returns false (bean present) if user added @EnableWebMvc
    static boolean noWebMvcConfigurationSupport(boolean userAddedEnableWebMvc) {
        return !userAddedEnableWebMvc;
    }

    static void printAutoConfig(boolean servletApp, boolean userEnableWebMvc) {
        System.out.printf("@ConditionalOnWebApplication(SERVLET)          : %s%n", servletApp);
        System.out.printf("@ConditionalOnClass(Servlet, DispatcherServlet): %s%n",
            onClasspath("jakarta.servlet.Servlet") && onClasspath("org.springframework.web.servlet.DispatcherServlet"));
        boolean noSupport = noWebMvcConfigurationSupport(userEnableWebMvc);
        System.out.printf("@ConditionalOnMissingBean(WebMvcConfigSupport) : %s%n", noSupport);
        System.out.printf("  (user added @EnableWebMvc: %s)%n", userEnableWebMvc);

        boolean active = servletApp && noSupport;
        System.out.printf("WebMvcAutoConfiguration ACTIVE: %s%n", active);

        if (active) {
            System.out.println("  → DispatcherServlet registered at '/'");
            System.out.println("  → MappingJackson2HttpMessageConverter registered");
            System.out.println("  → Static resource handlers: /static, /public, /resources, /META-INF/resources");
            System.out.println("  → ContentNegotiatingViewResolver + BeanNameViewResolver");
            System.out.println("  → Conversion service with default converters");
            System.out.println("  → MessageCodesResolver for validation");
        } else if (userEnableWebMvc) {
            System.out.println("  → User owns full MVC configuration via @EnableWebMvc");
            System.out.println("  → Must register all converters, resolvers, and handlers manually");
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Normal Spring Boot web app (recommended) ===");
        printAutoConfig(true, false);

        System.out.println("\n=== User added @EnableWebMvc ===");
        printAutoConfig(true, true);

        System.out.println("\n=== Non-web application (e.g. batch job) ===");
        printAutoConfig(false, false);

        System.out.println("\n=== Extending via WebMvcConfigurer (adds interceptor) ===");
        System.out.println("@Configuration");
        System.out.println("public class MyWebConfig implements WebMvcConfigurer {");
        System.out.println("    @Override");
        System.out.println("    public void addInterceptors(InterceptorRegistry r) {");
        System.out.println("        r.addInterceptor(new TimingInterceptor());");
        System.out.println("    }");
        System.out.println("}");
        System.out.println("→ WebMvcAutoConfiguration merges this with its own config");
    }
}
```

**How to run:** `java SpringMvcAutoConfig.java`

## 6. Walkthrough

- `onClasspath` checks simulate `@ConditionalOnClass`. All three classes (`Servlet`, `DispatcherServlet`, `WebMvcConfigurer`) must be present — adding `spring-boot-starter-web` guarantees they are.
- `noWebMvcConfigurationSupport(false)` — returns `true` (bean absent), so `WebMvcAutoConfiguration` fires. This is the normal path.
- When `userEnableWebMvc = true`, `noWebMvcConfigurationSupport` returns `false` (the bean is present — `@EnableWebMvc` imports it). `WebMvcAutoConfiguration` sees the bean present and backs off. The user is responsible for all MVC setup.
- `active = servletApp && noSupport` — both conditions must be true for auto-configuration to activate. A command-line runner (`SpringApplication.setWebApplicationType(WebApplicationType.NONE)`) sets `servletApp=false`, so no `DispatcherServlet` is created.
- The "extending" block shows the recommended pattern: `@Configuration + WebMvcConfigurer`, no `@EnableWebMvc`. Spring Boot calls all `WebMvcConfigurer` beans in `WebMvcConfigurerComposite.addInterceptors()`, so your interceptor is added alongside Spring Boot's own setup.

## 7. Gotchas & takeaways

> **The single most common Spring MVC mistake in Spring Boot: adding `@EnableWebMvc` when you only want to customise the auto-configuration.** Once `@EnableWebMvc` is present, all auto-configured message converters, resource handlers, and content negotiation are gone. You'll see 406 Not Acceptable errors for JSON endpoints and missing static resources. Remove `@EnableWebMvc` and implement `WebMvcConfigurer` instead.

> **`WebMvcConfigurer` is additive; `WebMvcConfigurationSupport` (extended by `@EnableWebMvc`) is a full replacement.** If you genuinely need `WebMvcConfigurationSupport` for a method not exposed in `WebMvcConfigurer`, extend `WebMvcConfigurationSupport` directly but be aware you must then manually replicate everything auto-configuration would have done.

- Check `spring-boot-autoconfigure.jar!/META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports` for the full list of auto-configuration classes.
- `WebMvcAutoConfiguration` is idempotent — running it multiple times (multiple context refreshes in tests) does not create duplicate beans.
- `@SpringBootTest(webEnvironment = WebEnvironment.MOCK)` activates `WebMvcAutoConfiguration` in tests; `WebEnvironment.NONE` skips it.
- Add `@AutoConfigureMockMvc` to a `@SpringBootTest` to inject a `MockMvc` instance configured exactly as the real MVC stack.
- Inspect what auto-configuration applied with `--debug` flag or `spring.autoconfiguration.report=true` — the conditions evaluation report shows which `@Conditional` checks passed or failed.
