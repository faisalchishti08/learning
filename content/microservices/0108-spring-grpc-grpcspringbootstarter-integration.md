---
card: microservices
gi: 108
slug: spring-grpc-grpc-spring-boot-starter-integration
title: "Spring gRPC / grpc-spring-boot-starter integration"
---

## 1. What it is

Spring gRPC (and the community-maintained `grpc-spring-boot-starter` that preceded it) brings Spring Boot's familiar dependency-injection and auto-configuration conventions to [gRPC](0089-grpc-and-http-2.md) services: instead of manually wiring a `Server` object and registering service implementations, you annotate a class implementing your generated gRPC service interface with `@GrpcService`, and Spring Boot auto-configures and starts the gRPC server for you, alongside (or instead of) any HTTP server, using the same dependency-injection container as the rest of your Spring beans.

## 2. Why & when

Plain gRPC server setup — building a `Server` via `ServerBuilder`, registering service implementations, starting and gracefully shutting it down — is boilerplate every gRPC-based Spring Boot service would otherwise duplicate, and it doesn't naturally participate in Spring's own bean lifecycle (dependency injection into your service implementation, configuration properties, health checks). `@GrpcService`-based integration removes that gap: a gRPC service implementation becomes a normal Spring bean, can `@Autowired` other Spring beans, and its server lifecycle is managed automatically alongside the rest of the application context.

Use Spring's gRPC integration whenever a Spring Boot service both implements gRPC endpoints (server-side) and needs those endpoints wired into the same dependency-injection and configuration conventions as its REST endpoints and other Spring beans — which is the common case for any Spring Boot microservice adopting gRPC internally.

## 3. Core concept

`@GrpcService` marks a class as a gRPC service implementation; Spring Boot's auto-configuration discovers it, registers it with an automatically-managed gRPC server, and injects any of that class's own Spring dependencies normally.

```java
@GrpcService
class OrderGrpcService extends OrderServiceGrpc.OrderServiceImplBase {

    private final OrderRepository repository;  // ordinary Spring dependency injection

    OrderGrpcService(OrderRepository repository) { this.repository = repository; }

    @Override
    public void getOrder(GetOrderRequest request, StreamObserver<Order> responseObserver) {
        Order order = repository.findById(request.getId());
        responseObserver.onNext(order);
        responseObserver.onCompleted();
    }
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring Boot's application context discovers a GrpcService-annotated bean at startup and auto-configures a gRPC server that registers it, alongside ordinary dependency injection into the bean">
  <rect x="20" y="55" width="200" height="60" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="120" y="80" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Spring ApplicationContext</text>
  <text x="120" y="98" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">discovers @GrpcService beans</text>

  <rect x="270" y="20" width="180" height="50" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="360" y="42" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Auto-configured</text>
  <text x="360" y="58" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">gRPC Server</text>

  <rect x="270" y="100" width="180" height="50" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="360" y="122" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">OrderGrpcService bean</text>
  <text x="360" y="138" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">@Autowired dependencies</text>

  <line x1="220" y1="85" x2="270" y2="45" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="220" y1="85" x2="270" y2="125" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="450" y1="45" x2="450" y2="100" stroke="#6db33f" stroke-width="1.5"/>
  <text x="470" y="75" fill="#6db33f" font-size="7" font-family="sans-serif">registers</text>
</svg>

The gRPC server and the service bean are both managed by the same application context.

## 5. Runnable example

Scenario: a gRPC-style `OrderService` implementation, first wired manually (constructing the server, registering the implementation, managing its lifecycle by hand), then refactored to Spring-style annotation-driven discovery where an auto-configuration process finds and registers `@GrpcService`-annotated beans automatically, then extended to show that annotated service implementation using ordinary constructor-injected dependency, exactly like any other Spring bean.

### Level 1 — Basic

```java
// File: ManualGrpcServerSetup.java -- construct the "server" and
// register the service implementation BY HAND -- the boilerplate
// @GrpcService-based auto-configuration eliminates.
import java.util.*;

public class ManualGrpcServerSetup {
    record Order(int id, String status) {}

    interface OrderServiceImplBase {
        Order getOrder(int id);
    }

    static class OrderGrpcService implements OrderServiceImplBase {
        Map<Integer, Order> orders = new HashMap<>(Map.of(42, new Order(42, "PLACED")));
        public Order getOrder(int id) { return orders.get(id); }
    }

    static class ManualGrpcServer { // stands in for grpc's ServerBuilder-based server
        List<OrderServiceImplBase> registeredServices = new ArrayList<>();
        void registerService(OrderServiceImplBase service) { registeredServices.add(service); } // MANUAL registration
        void start() { System.out.println("Server started with " + registeredServices.size() + " manually registered service(s)"); }
    }

    public static void main(String[] args) {
        OrderGrpcService serviceImpl = new OrderGrpcService(); // constructed by hand
        ManualGrpcServer server = new ManualGrpcServer();       // constructed by hand
        server.registerService(serviceImpl);                    // registered by hand
        server.start();
        System.out.println(server.registeredServices.get(0).getOrder(42));
    }
}
```

**How to run:** `javac ManualGrpcServerSetup.java && java ManualGrpcServerSetup` (JDK 17+).

Expected output:
```
Server started with 1 manually registered service(s)
Order[id=42, status=PLACED]
```

### Level 2 — Intermediate

```java
// File: AnnotationDrivenDiscovery.java -- mark the service with a
// @GrpcService-style annotation; a SCANNER discovers and registers it
// automatically -- no manual registration call anywhere.
import java.lang.annotation.*;
import java.lang.reflect.*;
import java.util.*;

public class AnnotationDrivenDiscovery {
    @Retention(RetentionPolicy.RUNTIME) @interface GrpcService {} // stands in for Spring gRPC's real annotation

    record Order(int id, String status) {}

    @GrpcService // just marked -- NOT manually registered anywhere
    static class OrderGrpcService {
        Map<Integer, Order> orders = new HashMap<>(Map.of(42, new Order(42, "PLACED")));
        Order getOrder(int id) { return orders.get(id); }
    }

    static class AutoConfiguringServer { // stands in for Spring Boot's gRPC auto-configuration
        List<Object> discoveredServices = new ArrayList<>();

        void scanAndRegister(Class<?>... candidateClasses) throws Exception {
            for (Class<?> c : candidateClasses) {
                if (c.isAnnotationPresent(GrpcService.class)) { // DISCOVERED automatically, not manually wired
                    discoveredServices.add(c.getDeclaredConstructor().newInstance());
                }
            }
        }

        void start() { System.out.println("Server auto-started with " + discoveredServices.size() + " auto-discovered service(s)"); }
    }

    public static void main(String[] args) throws Exception {
        AutoConfiguringServer server = new AutoConfiguringServer();
        server.scanAndRegister(OrderGrpcService.class); // simulates Spring's component scan
        server.start();
    }
}
```

**How to run:** `javac AnnotationDrivenDiscovery.java && java AnnotationDrivenDiscovery` (JDK 17+).

Expected output:
```
Server auto-started with 1 auto-discovered service(s)
```

### Level 3 — Advanced

```java
// File: WithDependencyInjection.java -- the @GrpcService bean uses
// ORDINARY constructor-injected dependencies, exactly like any other
// Spring bean -- the auto-configuration wires those in too.
import java.lang.annotation.*;
import java.lang.reflect.*;
import java.util.*;

public class WithDependencyInjection {
    @Retention(RetentionPolicy.RUNTIME) @interface GrpcService {}

    record Order(int id, String status) {}

    static class OrderRepository { // an ORDINARY Spring bean, unrelated to gRPC itself
        Map<Integer, Order> orders = new HashMap<>(Map.of(42, new Order(42, "PLACED")));
        Order findById(int id) { return orders.get(id); }
    }

    @GrpcService
    static class OrderGrpcService {
        OrderRepository repository; // CONSTRUCTOR-INJECTED, just like an ordinary Spring bean
        OrderGrpcService(OrderRepository repository) { this.repository = repository; }
        Order getOrder(int id) { return repository.findById(id); }
    }

    static class SimpleDiContainer { // stands in for Spring's ApplicationContext
        Map<Class<?>, Object> beans = new HashMap<>();

        void registerBean(Class<?> type, Object instance) { beans.put(type, instance); }

        Object instantiateWithInjection(Class<?> type) throws Exception {
            Constructor<?> ctor = type.getDeclaredConstructors()[0];
            Object[] args = new Object[ctor.getParameterCount()];
            Class<?>[] paramTypes = ctor.getParameterTypes();
            for (int i = 0; i < paramTypes.length; i++) args[i] = beans.get(paramTypes[i]); // WIRE dependencies
            Object instance = ctor.newInstance(args);
            beans.put(type, instance);
            return instance;
        }
    }

    public static void main(String[] args) throws Exception {
        SimpleDiContainer container = new SimpleDiContainer();
        container.registerBean(OrderRepository.class, new OrderRepository()); // register the dependency first

        Object grpcServiceBean = container.instantiateWithInjection(OrderGrpcService.class); // auto-wired
        OrderGrpcService orderGrpcService = (OrderGrpcService) grpcServiceBean;

        System.out.println("gRPC service bean created with injected repository");
        System.out.println(orderGrpcService.getOrder(42));
    }
}
```

**How to run:** `javac WithDependencyInjection.java && java WithDependencyInjection` (JDK 17+).

Expected output:
```
gRPC service bean created with injected repository
Order[id=42, status=PLACED]
```

## 6. Walkthrough

1. **Level 1** — `main` manually constructs `OrderGrpcService`, manually constructs `ManualGrpcServer`, and manually calls `server.registerService(serviceImpl)` to connect the two. This mirrors plain, non-Spring gRPC server setup — every piece is wired together explicitly, in application code.
2. **Level 2 — discovery instead of manual wiring** — `OrderGrpcService` is now marked with the custom `@GrpcService` annotation but is *never* manually registered anywhere. `AutoConfiguringServer.scanAndRegister` iterates a list of candidate classes, checks each for the `@GrpcService` annotation via reflection, and instantiates (and registers) any that have it — exactly the pattern Spring Boot's component scanning follows for any `@Component`-family annotation, gRPC-specific or not. `main` calls `scanAndRegister(OrderGrpcService.class)`, and the server reports one auto-discovered service, despite no explicit `registerService`-style call appearing anywhere in `main`.
3. **Level 3 — dependency injection into the discovered bean** — `OrderRepository` is an ordinary class representing a typical Spring-managed dependency, unrelated to gRPC itself. `OrderGrpcService`'s constructor now takes an `OrderRepository` parameter — exactly how a real `@GrpcService`-annotated class can `@Autowired`-inject any other Spring bean via its constructor. `SimpleDiContainer` stands in for Spring's `ApplicationContext`: `registerBean` manually seeds it with the already-available `OrderRepository` instance (simulating Spring having already created that bean earlier in the startup sequence), and `instantiateWithInjection` uses reflection to inspect `OrderGrpcService`'s constructor parameter types, look each one up in `beans`, and pass them in when constructing the instance.
4. **Tracing `main`'s calls** — `container.registerBean(OrderRepository.class, new OrderRepository())` seeds the container with the repository bean. `container.instantiateWithInjection(OrderGrpcService.class)` inspects `OrderGrpcService`'s single constructor, sees it needs one `OrderRepository` parameter, looks that up in `beans` (finding the one just registered), and calls `new OrderGrpcService(thatRepository)` — producing a fully-wired instance without any hand-written `new OrderGrpcService(repository)` call appearing directly in `main`. `orderGrpcService.getOrder(42)` then delegates to the injected `repository.findById(42)`, returning the expected order.
5. **What this demonstrates about the real integration** — across all three levels, the core progression mirrors exactly what adopting Spring's gRPC integration buys a real Spring Boot service: manual server/registration boilerplate (Level 1) is replaced by annotation-driven discovery (Level 2), and that discovered bean participates fully in the same dependency-injection machinery as every other Spring bean in the application (Level 3) — meaning a gRPC service implementation can inject a repository, a configuration property, or any other Spring-managed dependency exactly as naturally as a `@RestController` can.

## 7. Gotchas & takeaways

> **Gotcha:** running both a gRPC server (typically on its own port, separate from HTTP) and an HTTP server (for REST endpoints or actuator health checks) in the same Spring Boot application means two separate server lifecycles need to start up and shut down together correctly — verify your health-check and graceful-shutdown configuration accounts for both, not just the HTTP side that Spring Boot manages by default.

- `@GrpcService` (or the equivalent from `grpc-spring-boot-starter`) marks a class as a gRPC service implementation for automatic discovery and server registration, eliminating manual `ServerBuilder`/registration boilerplate.
- A `@GrpcService`-annotated bean participates in the same Spring dependency-injection container as every other bean — it can `@Autowired` repositories, other services, or configuration properties normally.
- This integration is specifically about *server-side* gRPC (implementing endpoints); see [gRPC and HTTP/2](0089-grpc-and-http-2.md) for the underlying protocol and [Protocol Buffers IDL](0090-protocol-buffers-protobuf-idl.md) for how the service's contract is actually defined.
- Running a gRPC server alongside an HTTP server in the same application means managing two separate server lifecycles — plan health checks and graceful shutdown for both.
- Adopting this integration is worthwhile specifically when a Spring Boot service both serves gRPC endpoints and wants those endpoints to share the rest of the application's Spring-managed configuration and dependency wiring.
