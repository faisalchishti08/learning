---
card: spring-boot
gi: 116
slug: cors-support
title: CORS support
---

## 1. What it is

**CORS (Cross-Origin Resource Sharing)** is a browser security mechanism that blocks JavaScript from calling a server on a different origin (scheme + host + port) unless that server explicitly says it is allowed. Spring Boot / Spring MVC lets you configure which origins, methods, and headers are permitted — at the handler level with `@CrossOrigin`, globally via `WebMvcConfigurer`, or as a `CorsFilter` bean.

## 2. Why & when

Browsers enforce the **same-origin policy**: a script on `https://frontend.example.com` cannot fetch from `https://api.example.com` without CORS headers. Without them, the browser cancels the response before JavaScript ever sees it.

You need CORS configuration whenever:

- Your frontend (React, Vue, Angular) is served from a different origin than your API.
- You expose a public API consumed by third-party web apps.
- You develop locally (frontend on `localhost:3000`, API on `localhost:8080`).

You do *not* need it for server-to-server calls — browsers enforce CORS, not HTTP clients like `RestTemplate` or `curl`.

## 3. Core concept

For "non-simple" requests (anything other than `GET`/`POST` with safe headers), the browser first sends a **preflight** `OPTIONS` request. The server must respond with `Access-Control-Allow-Origin` and related headers before the browser sends the real request.

Spring MVC handles this automatically when you configure CORS — it intercepts the `OPTIONS` preflight and replies correctly. The allowed origins, methods, headers, and credential flags are all expressed via `CorsConfiguration`.

Analogy: CORS is a bouncer checking an advance guest list (`OPTIONS` preflight → "you're on the list") before letting the guest (real request) in.

## 4. Diagram

<svg viewBox="0 0 680 240" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="85" width="140" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="90" y="116" text-anchor="middle" fill="#e6edf3" font-size="13" font-family="sans-serif">Browser</text>
  <text x="90" y="133" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">frontend.com</text>
  <rect x="440" y="65" width="175" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="527" y="95" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">Spring CorsFilter</text>
  <rect x="440" y="135" width="175" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="527" y="165" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">Your Controller</text>
  <line x1="163" y1="103" x2="435" y2="82" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="5,3" marker-end="url(#co)"/>
  <text x="300" y="78" text-anchor="middle" fill="#8b949e" font-size="10" font-family="sans-serif">1. OPTIONS preflight</text>
  <line x1="435" y1="90" x2="163" y2="110" stroke="#79c0ff" stroke-width="1.5" stroke-dasharray="5,3" marker-end="url(#co2)"/>
  <text x="300" y="108" text-anchor="middle" fill="#79c0ff" font-size="10" font-family="sans-serif">2. 204 + Access-Control-Allow-*</text>
  <line x1="163" y1="135" x2="435" y2="152" stroke="#6db33f" stroke-width="1.5" marker-end="url(#co3)"/>
  <text x="300" y="148" text-anchor="middle" fill="#6db33f" font-size="10" font-family="sans-serif">3. Real GET/POST request</text>
  <line x1="527" y1="135" x2="527" y2="136" stroke="#6db33f" stroke-width="1.5"/>
  <defs>
    <marker id="co" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="co2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="co3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

The browser sends a dashed preflight first; only after receiving CORS headers does it send the real request.

## 5. Runnable example

```java
// CorsApp.java  —  run with: java CorsApp.java  (JDK 17+, Spring Boot on classpath)
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@SpringBootApplication
public class CorsApp {
    public static void main(String[] args) {
        SpringApplication.run(CorsApp.class, args);
    }
}

// Option A: annotation on a single controller/method
@RestController
class ProductController {

    @CrossOrigin(origins = "https://shop.example.com")
    @GetMapping("/api/products")
    public String products() {
        return "[{\"id\":1,\"name\":\"Widget\"}]";
    }
}

// Option B: global CORS via WebMvcConfigurer (applies to all endpoints)
@Configuration
class CorsConfig implements WebMvcConfigurer {

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
                .allowedOrigins("https://shop.example.com", "http://localhost:3000")
                .allowedMethods("GET", "POST", "PUT", "DELETE")
                .allowedHeaders("*")
                .allowCredentials(true)
                .maxAge(3600); // cache preflight for 1 hour
    }
}
```

**How to run:** add to a Spring Boot project, start with `./mvnw spring-boot:run`, then from a browser console on a different origin:
```
fetch('http://localhost:8080/api/products').then(r => r.text()).then(console.log)
```

## 6. Walkthrough

- `@CrossOrigin(origins = "https://shop.example.com")` on `ProductController.products()` restricts CORS to that single origin for that one endpoint. Spring generates the required `Access-Control-Allow-Origin` response header automatically.
- `CorsConfig` implements `WebMvcConfigurer.addCorsMappings()` — the global approach. `addMapping("/api/**")` applies the rule to all paths under `/api/`.
- `.allowedOrigins(...)` lists exact origins (no wildcards when `allowCredentials(true)` — security requirement).
- `.allowedMethods(...)` tells the browser which HTTP verbs are permitted; `.allowedHeaders("*")` passes any request header.
- `.allowCredentials(true)` enables cookies / `Authorization` headers in cross-origin requests.
- `.maxAge(3600)` caches the preflight response for 3600 seconds, reducing extra `OPTIONS` round-trips.
- Both options can coexist; the annotation takes precedence for its specific endpoint.

## 7. Gotchas & takeaways

> You cannot use `allowedOrigins("*")` together with `allowCredentials(true)` — the browser (and the spec) forbid it. Use explicit origin lists when credentials are needed.

> CORS headers must be on the response, not a filter that short-circuits before Spring adds them. If you use `spring-security`, configure CORS there too — its filter chain runs before Spring MVC and will block preflights unless `http.cors(...)` is enabled.

- CORS is enforced by **browsers only** — `curl`, Postman, and server-to-server calls are not affected.
- Wrong CORS config causes a silent failure: the browser drops the response without JavaScript seeing any error body.
- For Spring Security apps: call `http.cors(Customizer.withDefaults())` to pick up the `WebMvcConfigurer` bean.
- Wildcards (`*`) work for origins only when credentials are false.
- `maxAge` defaults to 1800 s; raising it reduces preflight traffic on high-frequency APIs.
