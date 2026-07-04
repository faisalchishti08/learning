---
card: spring-framework
gi: 295
slug: processing-pipeline-request-flow
title: "Processing Pipeline: Request Flow"
---

## 1. What it is

The **Spring MVC processing pipeline** is the sequence of steps `DispatcherServlet` executes for every HTTP request — from raw bytes arriving at the container to a fully written HTTP response:

```
HTTP Request
  1.  Servlet container decodes request → HttpServletRequest
  2.  DispatcherServlet.doDispatch()
  3.    LocaleResolver.resolveLocale()
  4.    HandlerMapping.getHandler()      → HandlerExecutionChain
  5.    HandlerInterceptor.preHandle()   (may abort)
  6.    HandlerAdapter.handle()          → ModelAndView (or writes body directly)
        a. Argument resolution (@PathVariable, @RequestBody, @RequestParam, …)
        b. Data binding + @Valid validation
        c. Method invocation
        d. Return value handling (@ResponseBody writes body; String → view name)
  7.    HandlerInterceptor.postHandle()
  8.    HandlerExceptionResolver          (if exception thrown in steps 4-7)
  9.    ViewResolver + View.render()     (if ModelAndView returned)
  10.   HandlerInterceptor.afterCompletion()
  11. HttpServletResponse → container → HTTP Response
```

## 2. Why & when

Understanding the pipeline is required for:
- Diagnosing where in the pipeline a request is failing.
- Writing `HandlerInterceptor` that runs before/after specific steps.
- Writing `HandlerExceptionResolver` that intercepts specific exception types.
- Configuring argument resolvers for custom method parameter types.
- Understanding why `@RequestBody` and `@ModelAttribute` behave differently (different step 6a paths).

Every Spring MVC application runs this pipeline on every request. The pipeline is deterministic and ordered — knowing the order prevents confusion about when security, logging, CORS, transaction, and business logic run.

## 3. Core concept

Condensed `DispatcherServlet.doDispatch()` with error handling:

```java
try {
    // 3. Locale resolution (for i18n — used by views/messages)
    Locale locale = localeResolver.resolveLocale(request);

    // 4. Find handler
    HandlerExecutionChain chain = handlerMapping.getHandler(request);
    //    chain.handler = HandlerMethod (your @RequestMapping method)
    //    chain.interceptors = [Interceptor1, Interceptor2, ...]

    HandlerAdapter adapter = getHandlerAdapter(chain.getHandler());

    // 5. PreHandle — runs ALL interceptors in order; if any returns false, stop
    if (!chain.applyPreHandle(request, response)) return;

    // 6. Invoke handler
    ModelAndView mv = adapter.handle(request, response, chain.getHandler());
    //    6a. RequestMappingHandlerAdapter resolves arguments:
    //        @PathVariable → PathVariableMethodArgumentResolver
    //        @RequestBody  → RequestResponseBodyMethodProcessor (uses MessageConverters)
    //        @RequestParam → RequestParamMethodArgumentResolver (uses ConversionService)
    //        @Valid        → runs Validator, populates BindingResult
    //    6b. Invokes your controller method
    //    6c. Processes return value:
    //        @ResponseBody → MessageConverter.write() → response body directly
    //        String        → view name → ViewResolver
    //        ResponseEntity → status + headers + body

    // 7. PostHandle
    chain.applyPostHandle(request, response, mv);

    // 9. Resolve view (if mv != null and mv has a view name)
    processDispatchResult(request, response, chain, mv, null);
    //    viewResolver.resolveViewName(mv.getViewName()) → View
    //    view.render(mv.getModel(), request, response)

} catch (Exception ex) {
    // 8. Exception resolution
    mv = processHandlerException(request, response, handler, ex);
    //    ExceptionHandlerExceptionResolver → @ExceptionHandler
    //    ResponseStatusExceptionResolver   → @ResponseStatus
    //    DefaultHandlerExceptionResolver   → standard Spring MVC exceptions
} finally {
    // 10. AfterCompletion — always runs
    chain.triggerAfterCompletion(request, response, ex);
}
```

## 4. Diagram

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
    <marker id="err" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#79c0ff"/>
    </marker>
  </defs>

  <!-- Steps horizontal pipeline -->
  <text x="10" y="30" fill="#6db33f" font-size="9" font-family="monospace">HTTP Request</text>

  <rect x="10" y="38" width="65" height="28" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="42" y="56" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">Container</text>

  <line x1="77" y1="52" x2="95" y2="52" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <rect x="97" y="38" width="60" height="28" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="127" y="56" fill="#6db33f" font-size="7" text-anchor="middle" font-family="monospace">Handler</text>
  <text x="127" y="65" fill="#8b949e" font-size="6" text-anchor="middle" font-family="monospace">Mapping</text>

  <line x1="159" y1="52" x2="177" y2="52" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <rect x="179" y="38" width="60" height="28" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="209" y="56" fill="#6db33f" font-size="7" text-anchor="middle" font-family="monospace">pre</text>
  <text x="209" y="65" fill="#8b949e" font-size="6" text-anchor="middle" font-family="monospace">Handle()</text>

  <line x1="241" y1="52" x2="259" y2="52" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <rect x="261" y="30" width="90" height="46" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="306" y="50" fill="#6db33f" font-size="8" text-anchor="middle" font-family="monospace">Handler</text>
  <text x="306" y="62" fill="#8b949e" font-size="6" text-anchor="middle" font-family="monospace">Adapter.handle()</text>
  <text x="306" y="72" fill="#8b949e" font-size="6" text-anchor="middle" font-family="monospace">args, invoke, return</text>

  <line x1="353" y1="52" x2="371" y2="52" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <rect x="373" y="38" width="60" height="28" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="403" y="56" fill="#6db33f" font-size="7" text-anchor="middle" font-family="monospace">post</text>
  <text x="403" y="65" fill="#8b949e" font-size="6" text-anchor="middle" font-family="monospace">Handle()</text>

  <line x1="435" y1="52" x2="453" y2="52" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <rect x="455" y="38" width="65" height="28" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="487" y="56" fill="#6db33f" font-size="7" text-anchor="middle" font-family="monospace">View</text>
  <text x="487" y="65" fill="#8b949e" font-size="6" text-anchor="middle" font-family="monospace">Resolver</text>

  <line x1="522" y1="52" x2="540" y2="52" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <rect x="542" y="38" width="65" height="28" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="574" y="56" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="monospace">Container</text>
  <text x="574" y="65" fill="#8b949e" font-size="6" text-anchor="middle" font-family="monospace">Response</text>

  <!-- Exception path -->
  <line x1="306" y1="78" x2="306" y2="105" stroke="#79c0ff" stroke-width="1.5" stroke-dasharray="3,2" marker-end="url(#err)"/>
  <rect x="180" y="107" width="250" height="35" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="305" y="123" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">HandlerExceptionResolver</text>
  <text x="305" y="136" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">@ExceptionHandler → error ModelAndView / body</text>

  <!-- afterCompletion -->
  <rect x="10" y="155" width="670" height="28" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="345" y="173" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">HandlerInterceptor.afterCompletion()  — always runs (success or exception)</text>

  <text x="10" y="200" fill="#8b949e" font-size="7" font-family="sans-serif">Blue dashed = exception path; afterCompletion always executes last</text>
</svg>

## 5. Runnable example

Scenario: a **shipping tracker** — instrument the full pipeline at three levels.

### Level 1 — Basic

Trace the pipeline through a REST endpoint.

```java
// RequestFlowDemo.java
import jakarta.servlet.http.*;
import org.springframework.context.annotation.*;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.*;
import org.springframework.web.servlet.config.annotation.*;
import java.util.*;

record Shipment(String id, String status, String destination) {}

class PipelineTracer implements HandlerInterceptor {
    @Override
    public boolean preHandle(HttpServletRequest req, HttpServletResponse res, Object h) {
        System.out.println("[5] preHandle   → " + req.getMethod() + " " + req.getRequestURI());
        req.setAttribute("start", System.currentTimeMillis());
        return true;
    }
    @Override
    public void postHandle(HttpServletRequest req, HttpServletResponse res, Object h, ModelAndView mv) {
        System.out.println("[7] postHandle  → mv=" + mv);
    }
    @Override
    public void afterCompletion(HttpServletRequest req, HttpServletResponse res, Object h, Exception ex) {
        long ms = System.currentTimeMillis() - (long)req.getAttribute("start");
        System.out.println("[10] afterCompletion → " + ms + "ms ex=" + ex);
    }
}

@RestController @RequestMapping("/shipments")
class ShipmentController {
    private final Map<String,Shipment> db = Map.of(
        "SHP-001", new Shipment("SHP-001","DELIVERED","Berlin"),
        "SHP-002", new Shipment("SHP-002","IN_TRANSIT","Paris")
    );
    @GetMapping("/{id}")
    public ResponseEntity<Shipment> get(@PathVariable String id) {
        System.out.println("[6] handler invoked for id=" + id);
        Shipment s = db.get(id);
        return s != null ? ResponseEntity.ok(s) : ResponseEntity.notFound().build();
    }
}

@Configuration @EnableWebMvc @ComponentScan
class WebConfig implements WebMvcConfigurer {
    @Override public void addInterceptors(InterceptorRegistry reg) {
        reg.addInterceptor(new PipelineTracer());
    }
}

public class RequestFlowDemo {
    public static void main(String[] args) {
        System.out.println("Request flow steps:");
        System.out.println("  Container receives HTTP → creates HttpServletRequest/Response");
        System.out.println("  [4] HandlerMapping → finds ShipmentController.get()");
        System.out.println("  [5] PipelineTracer.preHandle()");
        System.out.println("  [6] RequestMappingHandlerAdapter: resolves @PathVariable id,");
        System.out.println("      invokes get(), @ResponseBody writes JSON");
        System.out.println("  [7] postHandle()");
        System.out.println("  [10] afterCompletion()");
        System.out.println("Deploy to Servlet container and call GET /shipments/SHP-001 to observe.");
    }
}
```

How to run: `java -cp spring-webmvc.jar:spring-context.jar:spring-web.jar:jackson-databind.jar:jakarta.servlet-api.jar:. RequestFlowDemo.java`

`PipelineTracer` shows the interceptor positions. `preHandle` runs after `HandlerMapping` but before `HandlerAdapter.handle()`. `postHandle` runs after the handler returns but before view rendering. `afterCompletion` always runs — even if an exception propagates.

---

### Level 2 — Intermediate

Exception path — `HandlerExceptionResolver` intercepts after step 6.

```java
// RequestFlowDemo.java
import jakarta.servlet.http.*;
import org.springframework.context.annotation.*;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.*;
import org.springframework.web.servlet.config.annotation.*;
import java.util.*;

class ShipmentNotFoundException extends RuntimeException {
    ShipmentNotFoundException(String id){ super("Shipment not found: " + id); }
}

@RestControllerAdvice
class GlobalHandler {
    @ExceptionHandler(ShipmentNotFoundException.class)
    public ResponseEntity<Map<String,String>> handleNotFound(ShipmentNotFoundException e) {
        System.out.println("[8] ExceptionHandlerExceptionResolver → " + e.getClass().getSimpleName());
        return ResponseEntity.status(HttpStatus.NOT_FOUND)
            .body(Map.of("error", e.getMessage()));
    }
}

@RestController @RequestMapping("/v2/shipments")
class ShipmentController2 {
    private final Map<String,Shipment> db = Map.of("SHP-001", new Shipment("SHP-001","DELIVERED","Berlin"));

    @GetMapping("/{id}")
    public Shipment get(@PathVariable String id) {
        System.out.println("[6] handler invoked id=" + id);
        Shipment s = db.get(id);
        if (s == null) throw new ShipmentNotFoundException(id);  // exits step 6 abnormally
        return s;  // @ResponseBody → MessageConverter → JSON
    }
}

@Configuration @EnableWebMvc @ComponentScan
class WebConfig2 implements WebMvcConfigurer {
    @Override public void addInterceptors(InterceptorRegistry reg) {
        reg.addInterceptor(new PipelineTracer());
    }
}

public class RequestFlowDemo {
    public static void main(String[] args) {
        System.out.println("Exception path for GET /v2/shipments/MISSING:");
        System.out.println("  [5] preHandle() → logs");
        System.out.println("  [6] handler throws ShipmentNotFoundException");
        System.out.println("  [7] postHandle() is NOT called (exception path skips it)");
        System.out.println("  [8] ExceptionHandlerExceptionResolver → @ExceptionHandler");
        System.out.println("      returns 404 JSON body");
        System.out.println("  [10] afterCompletion(ex=ShipmentNotFoundException) — still runs!");
    }
}
```

How to run: same classpath + deploy

When an exception exits the handler at step 6, step 7 (`postHandle`) is **skipped**. `DispatcherServlet` jumps to step 8 (`HandlerExceptionResolver`). `afterCompletion` at step 10 still runs with the exception as argument.

---

### Level 3 — Advanced

`@Valid` validation + `BindingResult` — pipeline step 6a in detail.

```java
// RequestFlowDemo.java
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import org.springframework.context.annotation.*;
import org.springframework.http.*;
import org.springframework.validation.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.config.annotation.*;
import java.util.*;

class CreateShipmentRequest {
    @NotBlank(message="id is required") public String id;
    @NotBlank(message="destination is required") public String destination;
    @Pattern(regexp="[A-Z]{2}\\d{4}", message="id must be XX9999 format") public String trackingCode;
}

@RestController @RequestMapping("/v3/shipments")
class ShipmentController3 {
    private final List<Shipment> db = new ArrayList<>();

    @PostMapping
    public ResponseEntity<?> create(@Valid @RequestBody CreateShipmentRequest req, BindingResult br) {
        // BindingResult parameter signals: don't throw MethodArgumentNotValidException automatically
        // let the controller handle validation errors
        System.out.println("[6a] @Valid ran: hasErrors=" + br.hasErrors());
        if (br.hasErrors()) {
            Map<String,String> errors = new LinkedHashMap<>();
            br.getFieldErrors().forEach(e -> errors.put(e.getField(), e.getDefaultMessage()));
            return ResponseEntity.badRequest().body(errors);
        }
        db.add(new Shipment(req.id, "REGISTERED", req.destination));
        return ResponseEntity.status(HttpStatus.CREATED).body(Map.of("tracking", req.trackingCode));
    }
}

@Configuration @EnableWebMvc @ComponentScan
class WebConfig3 {}

public class RequestFlowDemo {
    public static void main(String[] args) {
        System.out.println("@Valid in pipeline step 6a:");
        System.out.println("  POST /v3/shipments {\"id\":\"\",\"destination\":\"Berlin\"}");
        System.out.println("  [6a] @RequestBody → MappingJackson2HttpMessageConverter reads JSON");
        System.out.println("       @Valid → runs Hibernate Validator");
        System.out.println("       BindingResult present → errors collected, NOT thrown");
        System.out.println("       Controller receives req with constraint violations in BindingResult");
        System.out.println("       Returns 400 {\"id\":\"id is required\"}");
    }
}
```

How to run: same classpath + deploy

`@Valid @RequestBody` triggers validation **inside** `RequestMappingHandlerAdapter` at step 6a, before the controller method body runs. With `BindingResult` as the next parameter, validation errors are collected into `BindingResult` rather than thrown as `MethodArgumentNotValidException`. Without `BindingResult`, a validation failure throws the exception and jumps to step 8.

## 6. Walkthrough

**Level 2 — `GET /v2/shipments/MISSING` exception path:**

1. `GET /v2/shipments/MISSING` → Tomcat → `DispatcherServlet`.
2. **[4]** `RequestMappingHandlerMapping.getHandler()` → `HandlerExecutionChain(ShipmentController2.get, [PipelineTracer])`.
3. **[5]** `PipelineTracer.preHandle()` → logs, sets `startTime`, returns `true` → continue.
4. **[6]** `RequestMappingHandlerAdapter.handle()`:
   - Resolves `@PathVariable id` → `"MISSING"`.
   - Invokes `ShipmentController2.get("MISSING")`.
   - `db.get("MISSING")` → null → `throw new ShipmentNotFoundException("MISSING")`.
5. **Exception exits step 6** — `postHandle` is SKIPPED.
6. **[8]** `ExceptionHandlerExceptionResolver.resolveException()`:
   - Finds `@ExceptionHandler(ShipmentNotFoundException.class)` in `GlobalHandler`.
   - Invokes `handleNotFound(ex)` → `ResponseEntity(404, {error: "Shipment not found: MISSING"})`.
   - Writes JSON to response.
   - Returns non-null `ModelAndView` — exception handled.
7. **[10]** `PipelineTracer.afterCompletion(req, res, handler, ex=ShipmentNotFoundException)`.
8. Response `404 {"error":"Shipment not found: MISSING"}` committed.

## 7. Gotchas & takeaways

> **`postHandle()` does NOT run on exception.** If step 6 throws, the pipeline skips straight from the exception to step 8 (`HandlerExceptionResolver`). `afterCompletion()` always runs. Write cleanup logic in `afterCompletion`, not `postHandle`, if you need it on the exception path.

> **`@RequestBody` and `@ModelAttribute` use different pipelines.** `@RequestBody` is processed by `HttpMessageConverter` (Jackson reads the body stream). `@ModelAttribute` is processed by data binders and property editors / conversion service. They are separate argument resolvers in step 6a.

> **`@Valid` without `BindingResult` throws `MethodArgumentNotValidException`** at step 6 (before your method body runs). The default handler (`DefaultHandlerExceptionResolver`) returns 400. With `BindingResult`, the exception is suppressed and your method receives the validation errors to handle explicitly.

- Pipeline: HandlerMapping → preHandle → HandlerAdapter(args+invoke+response) → postHandle → ViewResolver → afterCompletion.
- Exception: skips postHandle; goes to HandlerExceptionResolver; afterCompletion still fires.
- `@Valid` without `BindingResult` → throws before method body; with `BindingResult` → errors collected into it.
- `@RequestBody` uses `HttpMessageConverter`; `@ModelAttribute` uses `DataBinder`/`ConversionService`.
- `afterCompletion()` — always runs; use for cleanup/logging regardless of outcome.
