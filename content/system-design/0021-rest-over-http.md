---
card: system-design
gi: 21
slug: rest-over-http
title: REST over HTTP
---

## 1. What it is

**Representational State Transfer (REST)** is a style for designing APIs that models everything as a **resource** — a noun, like a user or an order — identified by a URL, and manipulated using standard HTTP verbs (`GET`, `POST`, `PUT`, `DELETE`). **REST over HTTP** means building that API on top of HTTP directly, using its existing verbs, status codes, and headers, rather than inventing a custom protocol.

## 2. Why & when

REST is the most common way to expose a service's functionality to clients — browsers, mobile apps, or other services — because it reuses HTTP's existing, well-understood conventions instead of requiring a custom protocol on both ends. You choose it as your default API style in a design unless a specific requirement points elsewhere (like needing a strict typed contract across many internal services, where gRPC may fit better, or needing real-time push, where WebSocket fits better).

## 3. Core concept

**Resources and verbs — the core mapping:**

| HTTP verb | Meaning | Example |
|---|---|---|
| `GET` | Read a resource | `GET /users/42` — fetch user 42 |
| `POST` | Create a new resource | `POST /users` — create a new user |
| `PUT` | Replace a resource entirely | `PUT /users/42` — overwrite user 42 |
| `PATCH` | Partially update a resource | `PATCH /users/42` — update one field |
| `DELETE` | Remove a resource | `DELETE /users/42` — delete user 42 |

**Key REST principles:**
- **Resources are nouns, in URLs**, not verbs: `GET /users/42` is RESTful; `GET /getUser?id=42` is not.
- **Statelessness:** each request carries everything the server needs to process it (like an auth token); the server does not rely on remembered state from a previous request.
- **Standard status codes** communicate outcome: `200 OK` (success), `201 Created` (resource created), `404 Not Found` (resource does not exist), `400 Bad Request` (client sent invalid data), `500 Internal Server Error` (server-side failure).
- **Idempotency matters for retries:** `GET`, `PUT`, and `DELETE` are expected to be **idempotent** — calling them multiple times with the same input produces the same result as calling them once. `POST` is usually not idempotent — calling it twice can create two resources. This distinction decides which requests are safe to automatically retry after a network failure.

## 4. Diagram

```
 Client                                       Server
   |--GET /users/42-------------------------->|
   |<--200 OK  {"id":42,"name":"Ada"}----------|

   |--POST /users  {"name":"Grace"}----------->|
   |<--201 Created {"id":43,"name":"Grace"}-----|

   |--DELETE /users/43------------------------>|
   |<--204 No Content--------------------------|
```
*Caption: each request names a resource with a URL and a verb; the response uses a standard status code to signal the outcome.*

## 5. Runnable example

### Artifact: a minimal Java in-memory REST-style resource handler (no framework, models the verb → action mapping directly)

```java
import java.util.*;

public class RestResourceSim {

    static final Map<Integer, String> users = new HashMap<>();
    static int nextId = 1;

    static String get(int id) {
        String user = users.get(id);
        return user != null ? "200 OK -> " + user : "404 Not Found";
    }

    static String post(String name) {
        int id = nextId++;
        users.put(id, name);
        return "201 Created -> {id:" + id + ", name:" + name + "}";
    }

    static String delete(int id) {
        if (users.remove(id) != null) {
            return "204 No Content";
        }
        return "404 Not Found";
    }

    public static void main(String[] args) {
        System.out.println("POST /users {name: Ada}   -> " + post("Ada"));
        System.out.println("POST /users {name: Grace} -> " + post("Grace"));
        System.out.println("GET /users/1              -> " + get(1));
        System.out.println("GET /users/99             -> " + get(99));
        System.out.println("DELETE /users/1           -> " + delete(1));
        System.out.println("GET /users/1              -> " + get(1)); // gone now
    }
}
```

**How to run:** save as `RestResourceSim.java`, run `java RestResourceSim.java` (JDK 17+).

## 6. Walkthrough

1. `users` is an in-memory map standing in for a database table, keyed by user ID, holding the resource's data.
2. `get`, `post`, and `delete` each mirror the effect of the matching HTTP verb: `get` reads and returns a status code reflecting whether the resource exists; `post` creates a new resource and returns `201 Created`; `delete` removes a resource, returning `204 No Content` on success or `404 Not Found` if it never existed.
3. `main` runs a realistic sequence: create two users, read one, attempt to read one that does not exist, delete one, then confirm it is really gone.
4. Output:
```
POST /users {name: Ada}   -> 201 Created -> {id:1, name:Ada}
POST /users {name: Grace} -> 201 Created -> {id:2, name:Grace}
GET /users/1              -> 200 OK -> Ada
GET /users/99             -> 404 Not Found
DELETE /users/1           -> 204 No Content
GET /users/1              -> 404 Not Found
```
5. The final `GET /users/1` returning `404 Not Found` after the delete demonstrates why `DELETE` is idempotent: calling it again on the same ID would still return `404 Not Found` (or a defined "already gone" response), never an error from trying to delete something twice — the end state is the same either way.

## 7. Gotchas & takeaways

> **Gotcha:** designing endpoints as verbs in the URL, like `POST /createUser` or `GET /deleteUser?id=42`. This defeats REST's core idea — resources should be nouns identified by URL, with the HTTP verb carrying the action — and it also breaks the idempotency guarantees clients and infrastructure (like retry logic) rely on.

- Model resources as nouns in the URL; let the HTTP verb express the action.
- Use standard status codes consistently, so clients can handle responses generically without parsing custom error formats.
- Know which verbs are idempotent (`GET`, `PUT`, `DELETE`) versus not (`POST`) — it decides what is safe to retry automatically after a failure.
