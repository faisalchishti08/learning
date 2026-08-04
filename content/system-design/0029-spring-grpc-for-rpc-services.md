---
card: system-design
gi: 29
slug: spring-grpc-for-rpc-services
title: Spring gRPC for RPC services
---

## 1. What it is

**Spring gRPC** is Spring's support for building and calling gRPC services using familiar Spring idioms — dependency injection, auto-configuration, and Spring Boot starters — instead of wiring the raw gRPC Java library by hand. It lets you define a service with a `.proto` file (as covered in the earlier gRPC & Protobuf tutorial) and expose or call it using ordinary Spring beans.

## 2. Why & when

You reach for Spring gRPC when your design already uses gRPC for internal, service-to-service communication (typed contracts, high performance, HTTP/2), and your services are built with Spring Boot. It removes the boilerplate of manually managing gRPC servers and channels, letting the gRPC service or client be wired in exactly like any other Spring-managed component.

## 3. Core concept

**On the server side:** you implement the generated gRPC service base class as a Spring-managed `@GrpcService`-annotated bean (or equivalent registration, depending on the Spring gRPC starter version). Spring Boot's auto-configuration starts the underlying gRPC server automatically, using configuration properties (like the port) from `application.properties`, the same way it configures an embedded web server for a REST controller.

**On the client side:** instead of manually creating a gRPC `Channel` and stub, you inject a pre-configured client stub as a Spring bean, with its target address and connection settings managed centrally through Spring's configuration, consistent with how `RestClient` or `WebClient` beans are configured for REST calls.

**How this fits the layered flow:** a gRPC call arriving at a Spring service still flows through a layered structure conceptually similar to a REST controller: the gRPC service implementation receives the typed Protobuf request, delegates to your existing `@Service` business logic layer, which talks to the `@Repository` layer and the database, and the typed Protobuf response flows back out — the same layering you would use for a REST endpoint, with gRPC replacing the transport and serialization details.

## 4. Diagram

```
 gRPC Client (another service)
        |  typed .proto request, over HTTP/2
        v
 @GrpcService bean (generated base class impl)
        |  delegates
        v
 @Service (business logic layer)
        |  delegates
        v
 @Repository (data access layer)
        |
        v
 Database
        (response flows back up the same path, typed by .proto)
```
*Caption: a Spring gRPC service slots into the same layered architecture as a REST controller — only the transport and typed contract differ.*

## 5. Runnable example

### Artifact: a minimal Java sketch of a Spring-managed gRPC service delegating to a business-logic layer

```java
// Generated from a .proto file (shown here as a plain interface for a
// runnable, dependency-free illustration of the layering).
interface UserServiceGrpc {
    UserResponse getUser(GetUserRequest request);
}

record GetUserRequest(int id) {}
record UserResponse(int id, String name) {}

// The business logic layer -- identical in shape to what a REST controller would call.
class UserBusinessService {
    UserResponse findUser(int id) {
        return new UserResponse(id, "Ada"); // stands in for a real repository lookup
    }
}

// The gRPC service implementation, conceptually a Spring-managed @GrpcService bean.
class UserGrpcServiceImpl implements UserServiceGrpc {
    private final UserBusinessService businessService;

    UserGrpcServiceImpl(UserBusinessService businessService) {
        this.businessService = businessService; // constructor injection, Spring-style
    }

    @Override
    public UserResponse getUser(GetUserRequest request) {
        System.out.println("gRPC layer received typed request: " + request);
        UserResponse response = businessService.findUser(request.id());
        System.out.println("gRPC layer returning typed response: " + response);
        return response;
    }
}

public class SpringGrpcDemo {
    public static void main(String[] args) {
        UserBusinessService businessService = new UserBusinessService();
        UserServiceGrpc grpcService = new UserGrpcServiceImpl(businessService);

        UserResponse result = grpcService.getUser(new GetUserRequest(42));
        System.out.println("Client received: " + result);
    }
}
```

**How to run:** save as `SpringGrpcDemo.java`, run `java SpringGrpcDemo.java` (JDK 17+). A real Spring gRPC service uses classes generated from a `.proto` file and the `spring-grpc` starter dependency; this example uses plain interfaces to show the same layering without requiring a build tool and generated code.

## 6. Walkthrough

1. `UserServiceGrpc` stands in for the interface a `.proto` file's compiler would generate, defining the RPC method's typed signature.
2. `UserBusinessService` represents the existing `@Service` layer, unrelated to gRPC itself — the same class a REST controller could also call.
3. `UserGrpcServiceImpl` implements the gRPC service interface and receives `businessService` through constructor injection, exactly how Spring would wire a real `@GrpcService` bean to its dependencies.
4. `main` simulates a call arriving: `getUser` receives the typed request, delegates to the business layer, and returns the typed response — printing each step to show data moving through the layers.
5. Output:
```
gRPC layer received typed request: GetUserRequest[id=42]
gRPC layer returning typed response: UserResponse[id=42, name=Ada]
Client received: UserResponse[id=42, name=Ada]
```
6. This mirrors a real Spring gRPC request end to end: a typed request enters the gRPC layer, flows down to the business logic (and, in a real service, on to a repository and database), and a typed response flows back — the same request/response data-flow shape as a REST controller, just with gRPC's typed contract and transport underneath.

## 7. Gotchas & takeaways

> **Gotcha:** putting business logic directly inside the `@GrpcService` implementation class. This couples your core logic to the gRPC transport, making it hard to reuse the same logic behind a REST endpoint later — keep the gRPC service implementation thin, delegating to a separate business logic layer, just as shown above.

- Spring gRPC lets a gRPC service or client be managed as an ordinary Spring bean, with auto-configuration handling the server/channel setup.
- Keep the same layered architecture (thin transport layer, real logic in `@Service`/`@Repository`) regardless of whether the transport is REST or gRPC.
- Choose Spring gRPC when internal services need a typed contract and gRPC's performance benefits, and you want that wiring to feel like ordinary Spring development.
