---
card: spring-framework
gi: 293
slug: web-mvc-config-defaults
title: "Web MVC Config: Defaults"
---

## 1. What it is

`@EnableWebMvc` activates Spring MVC's **full default configuration** — the same bean definitions that `<mvc:annotation-driven/>` provides in XML. It registers a comprehensive set of `HandlerMapping`, `HandlerAdapter`, `ViewResolver`, `HttpMessageConverter`, and argument-resolver beans so you can write `@Controller`/`@RestController` without any boilerplate.

```java
@Configuration
@EnableWebMvc                // activates the full MVC default stack
@ComponentScan
public class WebConfig implements WebMvcConfigurer {

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**").allowedOrigins("https://example.com");
    }

    @Override
    public void configureMessageConverters(List<HttpMessageConverter<?>> converters) {
        converters.add(new MappingJackson2HttpMessageConverter());
    }
}
```

`WebMvcConfigurer` is the extension point — implement its methods to augment the defaults without replacing them.

## 2. Why & when

Without `@EnableWebMvc`, `DispatcherServlet` falls back to the `DispatcherServlet.properties` default beans — simpler but less capable (no data binding, no `@RequestBody`, no `@Valid`, no content negotiation).

`@EnableWebMvc` registers:
- `RequestMappingHandlerMapping` + `RequestMappingHandlerAdapter` — full annotation processing.
- `ExceptionHandlerExceptionResolver` — `@ControllerAdvice` support.
- `MappingJackson2HttpMessageConverter` (if Jackson on classpath) — JSON I/O.
- `ByteArrayHttpMessageConverter`, `StringHttpMessageConverter`, etc. — standard types.
- `PathVariableMethodArgumentResolver`, `RequestParamMethodArgumentResolver`, etc. — argument binding.
- `ConversionService` — type conversion for `@RequestParam`.
- `Validator` (JSR-303) — `@Valid` support.

Do NOT use `@EnableWebMvc` in Spring Boot — Boot's `WebMvcAutoConfiguration` does the same job; adding `@EnableWebMvc` disables the autoconfiguration.

## 3. Core concept

`@EnableWebMvc` imports `DelegatingWebMvcConfiguration` which:

```java
@Configuration
public class DelegatingWebMvcConfiguration extends WebMvcConfigurationSupport {
    @Autowired(required=false)
    public void setConfigurers(List<WebMvcConfigurer> configurers) {
        // collects all WebMvcConfigurer beans from the ApplicationContext
        // delegates each configuration method to them
    }
}
```

`WebMvcConfigurationSupport` defines all the `@Bean` methods (e.g., `requestMappingHandlerMapping()`, `requestMappingHandlerAdapter()`). `WebMvcConfigurer` methods override specific parts via the delegate pattern — they add converters/interceptors/resolvers rather than replacing the whole bean.

Key `WebMvcConfigurer` hooks:

```java
void addInterceptors(InterceptorRegistry)           // HandlerInterceptors
void addCorsMappings(CorsRegistry)                  // CORS rules
void addViewControllers(ViewControllerRegistry)     // URL → view shortcut
void addResourceHandlers(ResourceHandlerRegistry)   // static resources
void configureMessageConverters(List<HttpMessageConverter<?>>)  // replace ALL converters
void extendMessageConverters(List<HttpMessageConverter<?>>)     // add to default converters
void configureDefaultServletHandling(DefaultServletHandlerConfigurer)  // forward to container's default servlet
void configureViewResolvers(ViewResolverRegistry)   // view resolvers
void addFormatters(FormatterRegistry)               // type converters/formatters
```

## 4. Diagram

<svg viewBox="0 0 700 195" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- @EnableWebMvc -->
  <rect x="10" y="70" width="135" height="55" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="77" y="92" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">@EnableWebMvc</text>
  <text x="77" y="107" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">imports Delegating-</text>
  <text x="77" y="119" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">WebMvcConfiguration</text>

  <line x1="147" y1="97" x2="187" y2="97" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- DelegatingWebMvcConfiguration -->
  <rect x="189" y="40" width="220" height="115" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="299" y="62" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">DelegatingWebMvcConfiguration</text>
  <line x1="199" y1="68" x2="399" y2="68" stroke="#8b949e" stroke-width="0.5"/>
  <text x="299" y="86" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">@Bean requestMappingHandlerMapping</text>
  <text x="299" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">@Bean requestMappingHandlerAdapter</text>
  <text x="299" y="114" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">@Bean messageConverters</text>
  <text x="299" y="128" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">@Bean mvcValidator</text>
  <text x="299" y="142" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">@Bean mvcConversionService</text>

  <!-- Arrow from WebMvcConfigurer -->
  <line x1="299" y1="157" x2="299" y2="180" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr)"/>
  <rect x="189" y="181" width="220" height="10" rx="3" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="299" y="190" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">↑ WebMvcConfigurer delegates customise each @Bean</text>

  <line x1="411" y1="97" x2="451" y2="97" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- Result -->
  <rect x="453" y="55" width="230" height="85" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="568" y="78" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">DispatcherServlet discovers</text>
  <line x1="463" y1="84" x2="673" y2="84" stroke="#8b949e" stroke-width="0.5"/>
  <text x="568" y="102" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">HandlerMapping, HandlerAdapter</text>
  <text x="568" y="116" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">MessageConverters, Validators</text>
  <text x="568" y="130" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">ViewResolvers, Interceptors</text>
</svg>

## 5. Runnable example

Scenario: a **product store API** — configure Spring MVC at three levels of customisation.

### Level 1 — Basic

`@EnableWebMvc` with zero-config defaults.

```java
// WebMvcConfigDefaultsDemo.java
import org.springframework.context.annotation.*;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.config.annotation.*;
import java.util.*;

record Product(long id, String name, double price) {}

@RestController @RequestMapping("/products")
class ProductController2 {
    private final Map<Long,Product> db = new LinkedHashMap<>(
        Map.of(1L, new Product(1L,"Widget",49.99), 2L, new Product(2L,"Gadget",99.00))
    );
    @GetMapping           public Collection<Product> list()              { return db.values(); }
    @GetMapping("/{id}")  public ResponseEntity<Product> get(@PathVariable long id) {
        return db.containsKey(id) ? ResponseEntity.ok(db.get(id)) : ResponseEntity.notFound().build();
    }
    @PostMapping          public Product create(@RequestBody Product p) {
        long id = db.size() + 1;
        Product saved = new Product(id, p.name(), p.price()); db.put(id, saved); return saved;
    }
}

@Configuration
@EnableWebMvc      // registers all default MVC beans
@ComponentScan
class WebConfig {
    // No WebMvcConfigurer methods needed for basic JSON REST API
    // @EnableWebMvc auto-configures Jackson, ConversionService, Validator, etc.
}

public class WebMvcConfigDefaultsDemo {
    public static void main(String[] args) throws Exception {
        var ctx = new org.springframework.web.context.support.AnnotationConfigWebApplicationContext();
        ctx.register(WebConfig.class);
        ctx.refresh();

        // Verify default message converters
        var adapter = ctx.getBean(org.springframework.web.servlet.mvc.method.annotation.RequestMappingHandlerAdapter.class);
        System.out.println("Default message converters:");
        adapter.getMessageConverters().forEach(mc ->
            System.out.println("  " + mc.getClass().getSimpleName()));

        ctx.close();
    }
}
```

How to run: `java -cp spring-webmvc.jar:spring-context.jar:spring-web.jar:jackson-databind.jar:jakarta.servlet-api.jar:. WebMvcConfigDefaultsDemo.java`

`@EnableWebMvc` auto-detects Jackson on the classpath and registers `MappingJackson2HttpMessageConverter`. `@RequestBody` and `@ResponseBody` work out of the box. `@PathVariable`, `@RequestParam`, type conversion are all handled by the default `RequestMappingHandlerAdapter`.

---

### Level 2 — Intermediate

`WebMvcConfigurer` — interceptors, CORS, resource handlers.

```java
// WebMvcConfigDefaultsDemo.java
import jakarta.servlet.http.*;
import org.springframework.context.annotation.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.*;
import org.springframework.web.servlet.config.annotation.*;
import org.springframework.web.servlet.resource.ResourceHttpRequestHandler;
import java.util.*;

// (Product and ProductController2 same as Level 1)

class RequestIdInterceptor implements HandlerInterceptor {
    @Override
    public boolean preHandle(HttpServletRequest req, HttpServletResponse res, Object h) {
        res.setHeader("X-Request-Id", UUID.randomUUID().toString());
        return true;
    }
}

@Configuration @EnableWebMvc @ComponentScan
class WebConfig2 implements WebMvcConfigurer {
    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(new RequestIdInterceptor())
                .addPathPatterns("/**")
                .excludePathPatterns("/static/**");
    }

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/products/**")
            .allowedOrigins("https://example.com","http://localhost:3000")
            .allowedMethods("GET","POST","PUT","DELETE")
            .maxAge(3600);
    }

    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        registry.addResourceHandler("/static/**")
                .addResourceLocations("classpath:/static/")
                .setCachePeriod(3600);
    }

    @Override
    public void configureDefaultServletHandling(DefaultServletHandlerConfigurer configurer) {
        configurer.enable();  // forward unmatched requests to container's default servlet
    }
}

public class WebMvcConfigDefaultsDemo {
    public static void main(String[] args) {
        System.out.println("WebMvcConfigurer hooks used:");
        System.out.println("  addInterceptors   → adds X-Request-Id header to all (non-static) responses");
        System.out.println("  addCorsMappings   → CORS for /products/** from allowed origins");
        System.out.println("  addResourceHandlers → serves /static/** from classpath:/static/");
        System.out.println("  configureDefaultServletHandling → falls back to container for unmapped URLs");
    }
}
```

How to run: same classpath + deploy

`WebMvcConfigurer` methods ADD to the existing beans — they don't replace them. `addInterceptors()` appends to the interceptor chain; `addCorsMappings()` registers CORS `CorsConfiguration` objects into `DispatcherServlet`'s `CorsInterceptor`. `addResourceHandlers()` registers `ResourceHttpRequestHandler` beans.

---

### Level 3 — Advanced

`extendMessageConverters` + custom `Formatter`.

```java
// WebMvcConfigDefaultsDemo.java
import org.springframework.context.annotation.*;
import org.springframework.format.*;
import org.springframework.http.converter.*;
import org.springframework.http.converter.json.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.config.annotation.*;
import java.util.*;

enum Priority { LOW, MEDIUM, HIGH }

// Formatter: converts "low"/"medium"/"high" request params to Priority enum
class PriorityFormatter implements Formatter<Priority> {
    @Override public Priority parse(String text, Locale locale) {
        return Priority.valueOf(text.toUpperCase());
    }
    @Override public String print(Priority p, Locale locale) { return p.name().toLowerCase(); }
}

@RestController @RequestMapping("/tasks")
class TaskController2 {
    @GetMapping
    public String tasks(@RequestParam(defaultValue="MEDIUM") Priority priority) {
        return "Tasks with priority: " + priority;
    }
}

@Configuration @EnableWebMvc @ComponentScan
class WebConfig3 implements WebMvcConfigurer {
    @Override
    public void extendMessageConverters(List<HttpMessageConverter<?>> converters) {
        // extendMessageConverters: ADD to defaults (not replace)
        // configureMessageConverters: REPLACE defaults
        converters.add(0, new StringHttpMessageConverter());  // highest priority string converter
        // Configure Jackson's ObjectMapper
        converters.stream()
            .filter(c -> c instanceof MappingJackson2HttpMessageConverter)
            .map(c -> (MappingJackson2HttpMessageConverter) c)
            .findFirst()
            .ifPresent(c -> c.getObjectMapper()
                .enable(com.fasterxml.jackson.databind.SerializationFeature.INDENT_OUTPUT));
    }

    @Override
    public void addFormatters(FormatterRegistry registry) {
        registry.addFormatter(new PriorityFormatter());  // enables ?priority=high query param
    }
}

public class WebMvcConfigDefaultsDemo {
    public static void main(String[] args) throws Exception {
        var ctx = new org.springframework.web.context.support.AnnotationConfigWebApplicationContext();
        ctx.register(WebConfig3.class);
        ctx.refresh();

        // Verify formatters registered
        var service = ctx.getBean(org.springframework.format.support.FormattingConversionService.class);
        System.out.println("Can convert 'high' → Priority? " + service.canConvert(String.class, Priority.class));
        Priority p = service.convert("high", Priority.class);
        System.out.println("Converted: " + p);

        ctx.close();
    }
}
```

How to run: same classpath

`extendMessageConverters()` receives the ALREADY populated default list — you ADD to it. Use `configureMessageConverters()` only if you want to REPLACE all defaults (use with caution — you lose Jackson auto-configuration). `addFormatters()` registers `Formatter<T>` for `@RequestParam` / `@ModelAttribute` conversion. Spring MVC looks up formatters from the `ConversionService` injected into `RequestMappingHandlerAdapter`.

## 6. Walkthrough

**Level 3 — `GET /tasks?priority=high` with custom formatter:**

1. `DispatcherServlet` → `RequestMappingHandlerMapping` → `TaskController2.tasks()`.
2. `RequestMappingHandlerAdapter`:
   - Resolves `@RequestParam(defaultValue="MEDIUM") Priority priority`.
   - Reads raw `"high"` string from query parameter.
   - Looks up converter: `ConversionService.canConvert(String.class, Priority.class)` → true (PriorityFormatter registered).
   - `ConversionService.convert("high", Priority.class)` → `PriorityFormatter.parse("high", locale)` → `Priority.HIGH`.
3. `tasks(Priority.HIGH)` invoked → returns `"Tasks with priority: HIGH"`.
4. `StringHttpMessageConverter` writes `"Tasks with priority: HIGH"` as `text/plain`.

## 7. Gotchas & takeaways

> **`configureMessageConverters()` REPLACES all defaults; `extendMessageConverters()` ADDS to them.** If you override `configureMessageConverters()` and don't add Jackson, `@RequestBody` / `@ResponseBody` stop working for JSON. Always prefer `extendMessageConverters()` unless you deliberately want to replace.

> **`@EnableWebMvc` disables Spring Boot's `WebMvcAutoConfiguration`.** Do NOT add `@EnableWebMvc` in a Spring Boot application — it turns off auto-configuration and you must re-register everything manually. Use `WebMvcConfigurer` beans directly in Spring Boot; they're picked up automatically.

> **`addFormatters()` affects `@RequestParam` and `@ModelAttribute` binding**, not `@RequestBody` (which uses `HttpMessageConverter`). They are separate pipelines: `ConversionService` for form/URL params, `HttpMessageConverter` for request body.

- `@EnableWebMvc` = full MVC default stack; `WebMvcConfigurer` = additive customisation.
- `extendMessageConverters()` adds to defaults; `configureMessageConverters()` replaces all.
- `addFormatters()` → `@RequestParam` type conversion; `HttpMessageConverter` → `@RequestBody`.
- Don't use `@EnableWebMvc` in Spring Boot — disable Boot's auto-config.
- CORS via `addCorsMappings()`; static resources via `addResourceHandlers()`.
