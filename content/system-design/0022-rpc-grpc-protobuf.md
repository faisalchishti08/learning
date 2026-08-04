---
card: system-design
gi: 22
slug: rpc-grpc-protobuf
title: "RPC & gRPC (Protobuf)"
---

## 1. What it is

**Remote Procedure Call (RPC)** is a style of communication where a client calls a function that appears to run locally, but the call actually executes on a remote server over the network — the networking is hidden behind a normal-looking function call. **gRPC** is a modern, widely used RPC framework built by Google, running over HTTP/2, that uses **Protocol Buffers (Protobuf)** — a compact, strongly typed binary format — to define the calls and encode the data.

## 2. Why & when

You choose gRPC over REST when two conditions both matter: internal service-to-service communication (not a public, browser-facing API) and a need for high performance with a strict, typed contract between services. gRPC is very common inside a microservices architecture, where many internal services call each other frequently and both sides are controlled by your own team, so you can afford a shared `.proto` contract file.

## 3. Core concept

**How gRPC differs from REST:**

| | REST (typically JSON over HTTP/1.1) | gRPC (Protobuf over HTTP/2) |
|---|---|---|
| Data format | JSON — text, human-readable, larger | Protobuf — binary, compact, faster to parse |
| Contract | Often informal (OpenAPI docs, loosely enforced) | A `.proto` file — a strict, generated contract both sides must match |
| Transport | Usually HTTP/1.1 (one request per connection turn) | HTTP/2 (multiplexed streams over one connection) |
| Streaming | Awkward, needs workarounds (SSE, WebSocket) | Built-in: client, server, or bidirectional streaming |
| Browser support | Native, universal | Needs a proxy (gRPC-Web) for browser clients |

**The `.proto` contract:** a `.proto` file defines a service's methods and the exact shape of its request and response messages, with typed fields. Both the client and server generate code from the *same* `.proto` file, so a field type or name mismatch is caught at compile time, not discovered at runtime like a malformed JSON field often is.

```protobuf
service UserService {
  rpc GetUser (GetUserRequest) returns (UserResponse);
}
message GetUserRequest { int32 id = 1; }
message UserResponse { int32 id = 1; string name = 2; }
```

**Why Protobuf is faster and smaller than JSON:** JSON repeats field names as text in every single message (`{"id":42,"name":"Ada"}`); Protobuf encodes the same data as compact binary, using the field's defined position number instead of repeating its name, and using binary number encoding instead of decimal text. This typically produces messages several times smaller, and faster to parse, than the equivalent JSON.

## 4. Diagram

```
    .proto file (shared contract)
           |
   +-------+--------+
   v                 v
 generated CLIENT   generated SERVER
 stub code           stub code
   |                     |
   |--GetUser(id=42)---->|   (looks like a normal function call)
   |                      |   (actually: Protobuf-encoded over HTTP/2)
   |<--UserResponse-------|
```
*Caption: both sides generate code from the same .proto contract, so a call that looks local is really a typed, binary-encoded network request.*

## 5. Runnable example

### Artifact: a Java simulation of an RPC-style call using a typed request/response, contrasted with the equivalent JSON payload size

```java
public class RpcSim {

    record GetUserRequest(int id) {}
    record UserResponse(int id, String name) {}

    // Simulated "server" method, called as if it were local.
    static UserResponse getUser(GetUserRequest request) {
        // In a real gRPC call, this line would actually be a network call
        // encoded with Protobuf and sent over an HTTP/2 stream.
        return new UserResponse(request.id(), "Ada");
    }

    public static void main(String[] args) {
        GetUserRequest request = new GetUserRequest(42);
        UserResponse response = getUser(request); // looks local, is actually remote

        System.out.println("Called getUser(42), got: " + response);

        // Rough size comparison: Protobuf binary vs. equivalent JSON text.
        String equivalentJson = "{\"id\":42,\"name\":\"Ada\"}";
        int protobufApproxBytes = 2 + 1 + 1 + 3; // field tags + varint id + string len + "Ada"
        System.out.println("Equivalent JSON: " + equivalentJson + " (" + equivalentJson.length() + " bytes)");
        System.out.println("Approx. Protobuf size: " + protobufApproxBytes + " bytes");
    }
}
```

**How to run:** save as `RpcSim.java`, run `java RpcSim.java` (JDK 17+).

## 6. Walkthrough

1. `GetUserRequest` and `UserResponse` are Java `record`s standing in for messages generated from a `.proto` file — typed, fixed-shape data structures.
2. `getUser` is called exactly like a normal local method — this is RPC's defining property: the network call is hidden behind an ordinary function call syntax.
3. `main` calls `getUser` with a request for user 42 and prints the typed response.
4. It then compares the JSON text representation of the same data against a rough estimate of Protobuf's binary size, to make the size difference concrete.
5. Output:
```
Called getUser(42), got: UserResponse[id=42, name=Ada]
Equivalent JSON: {"id":42,"name":"Ada"} (23 bytes)
Approx. Protobuf size: 7 bytes
```
6. The size gap (23 bytes vs roughly 7) is the core reason gRPC/Protobuf outperforms JSON REST for high-volume internal service calls: less data to serialize, transmit, and parse, on every single call, adds up significantly at scale.

## 7. Gotchas & takeaways

> **Gotcha:** choosing gRPC for a public, browser-facing API. Browsers cannot make native gRPC calls without an extra proxy layer (gRPC-Web), and gRPC's binary format is not human-readable in browser dev tools, making REST/JSON a better fit for public or browser-facing APIs.

- gRPC's typed `.proto` contract catches mismatches at compile time; REST/JSON typically catches them only at runtime.
- Protobuf's binary encoding is smaller and faster to parse than JSON, which matters at high internal call volume.
- Default to gRPC for internal, service-to-service calls where you control both ends; default to REST/JSON for public or browser-facing APIs.
