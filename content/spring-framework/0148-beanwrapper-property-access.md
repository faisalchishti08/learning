---
card: spring-framework
gi: 148
slug: beanwrapper-property-access
title: "BeanWrapper & property access"
---

## 1. What it is

`BeanWrapper` is Spring's low-level interface for reading and writing JavaBean properties by name. It handles nested paths (`address.city`), indexed properties (`phones[0]`), and mapped properties (`attributes[key]`). `BeanWrapperImpl` is the standard implementation. `DataBinder` and `BeanUtils` use `BeanWrapper` internally.

```java
BeanWrapper bw = new BeanWrapperImpl(person);
bw.setPropertyValue("address.city", "Portland");
String city = (String) bw.getPropertyValue("address.city");
```

## 2. Why & when

- **Dynamic property access** — read or write arbitrary bean properties at runtime without compile-time coupling (useful in frameworks, tools, and generic form binders).
- **Nested navigation** — `"address.zipCode"` drills into nested beans automatically.
- **Indexed/mapped access** — `"phones[0]"` or `"attributes[color]"` sets List and Map entries.
- **PropertyDescriptor introspection** — `getPropertyDescriptor("name")` returns type information for a property.
- **Rarely used directly** — most Spring apps interact with `DataBinder` or `@Value`, which use `BeanWrapper` under the hood.

## 3. Core concept

`BeanWrapper` property path syntax:

| Path | Accesses |
|---|---|
| `name` | `getName()` / `setName()` |
| `address.city` | `getAddress().setCity()` |
| `phones[0]` | `getPhones().get(0)` |
| `attributes[color]` | `getAttributes().get("color")` |
| `phones[0].number` | `getPhones().get(0).getNumber()` |

`PropertyValue` encapsulates a name-value pair. `PropertyValues` is a collection of them.

Key `BeanWrapper` methods:

| Method | Purpose |
|---|---|
| `setPropertyValue(name, value)` | Set a single property |
| `setPropertyValues(pvs)` | Set multiple at once |
| `getPropertyValue(name)` | Get a property value |
| `getPropertyDescriptor(name)` | Get `PropertyDescriptor` for a property |
| `getPropertyType(name)` | Get the property's `Class` |
| `isReadableProperty(name)` | Check if readable |
| `isWritableProperty(name)` | Check if writable |

Type conversion is performed automatically using registered `PropertyEditor` objects — same mechanism as `DataBinder`.

## 4. Diagram

<svg viewBox="0 0 700 195" xmlns="http://www.w3.org/2000/svg">
  <!-- BeanWrapper -->
  <rect x="10" y="30" width="200" height="130" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="110" y="52" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">BeanWrapper</text>
  <text x="110" y="70" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">setPropertyValue(path, value)</text>
  <text x="110" y="84" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">getPropertyValue(path)</text>
  <text x="110" y="98" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">getPropertyDescriptor(name)</text>
  <text x="110" y="112" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">isReadable / isWritable</text>
  <text x="110" y="130" fill="#6db33f" font-size="9"  text-anchor="middle" font-family="sans-serif">path: name / address.city</text>
  <text x="110" y="144" fill="#6db33f" font-size="9"  text-anchor="middle" font-family="sans-serif">phones[0] / attrs[key]</text>

  <!-- Target Bean -->
  <rect x="275" y="30" width="180" height="130" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="365" y="52" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Target JavaBean</text>
  <text x="365" y="70" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">Person</text>
  <text x="365" y="85" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">  name: "Alice"</text>
  <text x="365" y="100" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">  address:</text>
  <text x="365" y="115" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">    city: "Portland"</text>
  <text x="365" y="130" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">  phones: ["555-0100"]</text>
  <text x="365" y="145" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">  attrs: {color: "blue"}</text>

  <!-- PropertyEditor -->
  <rect x="520" y="50" width="170" height="55" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="605" y="70" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">PropertyEditor</text>
  <text x="605" y="86" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">type conversion</text>
  <text x="605" y="98" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">"42" → int 42</text>

  <defs>
    <marker id="a148" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b148" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
  <line x1="212" y1="95" x2="272" y2="95" stroke="#6db33f" stroke-width="2" marker-end="url(#a148)"/>
  <line x1="457" y1="78" x2="517" y2="78" stroke="#8b949e" stroke-width="1.5" marker-end="url(#b148)"/>

  <text x="350" y="185" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">BeanWrapper navigates nested paths and delegates type conversion to PropertyEditors</text>
</svg>

`BeanWrapper` resolves dotted paths into bean property calls, with type conversion via `PropertyEditor`.

## 5. Runnable example

### Level 1 — Basic

Set and get simple, nested, and indexed properties.

```java
// BeanWrapperBasic.java
import org.springframework.beans.*;
import java.util.*;

class Address {
    private String street;
    private String city;
    private String zipCode;

    public void setStreet(String s)  { this.street = s; }
    public void setCity(String c)    { this.city = c; }
    public void setZipCode(String z) { this.zipCode = z; }
    public String getStreet()  { return street; }
    public String getCity()    { return city; }
    public String getZipCode() { return zipCode; }

    @Override public String toString() {
        return street + ", " + city + " " + zipCode;
    }
}

class Person {
    private String name;
    private int age;
    private Address address;
    private List<String> phones;
    private Map<String, String> attributes;

    Person() {
        this.address    = new Address();
        this.phones     = new ArrayList<>(Arrays.asList("", ""));
        this.attributes = new HashMap<>();
    }

    public void setName(String n)    { this.name = n; }
    public void setAge(int a)        { this.age = a; }
    public void setAddress(Address a){ this.address = a; }
    public void setPhones(List<String> p)          { this.phones = p; }
    public void setAttributes(Map<String,String> m){ this.attributes = m; }

    public String getName()    { return name; }
    public int getAge()        { return age; }
    public Address getAddress(){ return address; }
    public List<String> getPhones()           { return phones; }
    public Map<String, String> getAttributes(){ return attributes; }
}

public class BeanWrapperBasic {
    public static void main(String[] args) {
        Person person = new Person();
        BeanWrapper bw = new BeanWrapperImpl(person);

        // Simple properties
        bw.setPropertyValue("name", "Alice");
        bw.setPropertyValue("age",  "30");    // String → int conversion

        // Nested path
        bw.setPropertyValue("address.street",  "123 Main St");
        bw.setPropertyValue("address.city",    "Portland");
        bw.setPropertyValue("address.zipCode", "97201");

        // Indexed (List)
        bw.setPropertyValue("phones[0]", "503-555-0100");
        bw.setPropertyValue("phones[1]", "503-555-0200");

        // Mapped (Map)
        bw.setPropertyValue("attributes[color]", "blue");
        bw.setPropertyValue("attributes[tier]",  "gold");

        // Read back
        System.out.println("name:          " + bw.getPropertyValue("name"));
        System.out.println("age:           " + bw.getPropertyValue("age"));
        System.out.println("address.city:  " + bw.getPropertyValue("address.city"));
        System.out.println("phones[0]:     " + bw.getPropertyValue("phones[0]"));
        System.out.println("attrs[color]:  " + bw.getPropertyValue("attributes[color]"));

        // PropertyDescriptor introspection
        System.out.println("\nname type:    " + bw.getPropertyType("name"));
        System.out.println("age type:     " + bw.getPropertyType("age"));
        System.out.println("isReadable(name):   " + bw.isReadableProperty("name"));
        System.out.println("isWritable(name):   " + bw.isWritableProperty("name"));

        System.out.println("\nFull person: " + person.getName() + ", " +
            person.getAge() + " | " + person.getAddress() +
            " | phones=" + person.getPhones() +
            " | attrs=" + person.getAttributes());
    }
}
```

How to run: `java BeanWrapperBasic.java`

`"age"` receives the `String "30"` and converts it to `int 30` via the built-in `CustomNumberEditor`. Nested path `"address.city"` calls `person.getAddress().setCity("Portland")`. Indexed access `"phones[0]"` calls `person.getPhones().set(0, ...)`.

### Level 2 — Intermediate

`PropertyValues` bulk set; check `PropertyDescriptor`; `BeanWrapper` for framework-style dynamic binding.

```java
// BeanWrapperBulk.java
import org.springframework.beans.*;
import java.beans.*;
import java.util.*;

class Server {
    private String host;
    private int port;
    private boolean ssl;
    private int maxConnections;
    private String protocol;

    public void setHost(String h)           { this.host = h; }
    public void setPort(int p)              { this.port = p; }
    public void setSsl(boolean s)           { this.ssl = s; }
    public void setMaxConnections(int m)    { this.maxConnections = m; }
    public void setProtocol(String p)       { this.protocol = p; }

    public String getHost()        { return host; }
    public int getPort()           { return port; }
    public boolean isSsl()         { return ssl; }
    public int getMaxConnections() { return maxConnections; }
    public String getProtocol()    { return protocol; }

    @Override
    public String toString() {
        return (ssl ? "https" : "http") + "://" + host + ":" + port +
            " (" + protocol + ") max=" + maxConnections;
    }
}

public class BeanWrapperBulk {
    public static void main(String[] args) {
        Server server = new Server();
        BeanWrapper bw = new BeanWrapperImpl(server);

        // Bulk set via PropertyValues
        MutablePropertyValues pvs = new MutablePropertyValues();
        pvs.add("host",           "api.acme.com");
        pvs.add("port",           "443");
        pvs.add("ssl",            "true");
        pvs.add("maxConnections", "200");
        pvs.add("protocol",       "HTTP/2");

        bw.setPropertyValues(pvs);
        System.out.println("Server: " + server);

        // Introspect all writable properties
        System.out.println("\nAll properties:");
        PropertyDescriptor[] descriptors = bw.getPropertyDescriptors();
        for (PropertyDescriptor pd : descriptors) {
            if (pd.getWriteMethod() == null) continue;
            String name = pd.getName();
            if (name.equals("class")) continue;
            System.out.printf("  %-20s type=%-10s value=%s%n",
                name,
                pd.getPropertyType().getSimpleName(),
                bw.getPropertyValue(name));
        }

        // Partial update — only override what changed
        System.out.println("\nAfter port update:");
        bw.setPropertyValue("port", "8443");
        System.out.println("Server: " + server);

        // Check property type without instantiating
        System.out.println("\nProperty type checks:");
        System.out.println("  port type:  " + bw.getPropertyType("port"));
        System.out.println("  ssl type:   " + bw.getPropertyType("ssl"));
        System.out.println("  host readable: " + bw.isReadableProperty("host"));
        System.out.println("  missing prop:  " + bw.isReadableProperty("nonExistent"));
    }
}
```

How to run: `java BeanWrapperBulk.java`

`setPropertyValues(pvs)` applies all values in bulk. `getPropertyDescriptors()` returns all Java bean descriptors. `isReadableProperty("nonExistent")` returns `false` without throwing.

### Level 3 — Advanced

Deep nested graph navigation; `BeanWrapper` auto-growing nested properties; type conversion via `setAutoGrowNestedPaths`.

```java
// BeanWrapperNested.java
import org.springframework.beans.*;
import java.util.*;

class Department {
    private String name;
    private Address location;

    Department() { this.location = new Address(); }

    public void setName(String n)       { this.name = n; }
    public void setLocation(Address a)  { this.location = a; }
    public String getName()     { return name; }
    public Address getLocation(){ return location; }
}

class Employee {
    private String id;
    private String fullName;
    private Department department;
    private List<String> certifications;
    private Map<String, String> metadata;

    Employee() {
        // department and nested paths auto-created by BeanWrapper
    }

    public void setId(String i)          { this.id = i; }
    public void setFullName(String n)    { this.fullName = n; }
    public void setDepartment(Department d) { this.department = d; }
    public void setCertifications(List<String> c) { this.certifications = c; }
    public void setMetadata(Map<String,String> m) { this.metadata = m; }

    public String getId()      { return id; }
    public String getFullName(){ return fullName; }
    public Department getDepartment() { return department; }
    public List<String> getCertifications() { return certifications; }
    public Map<String,String> getMetadata() { return metadata; }
}

// Reuse Address from BeanWrapperBasic (must be accessible)
class Address2 {
    private String city; private String country;
    public void setCity(String c)    { this.city = c; }
    public void setCountry(String c) { this.country = c; }
    public String getCity()    { return city; }
    public String getCountry() { return country; }
}

public class BeanWrapperNested {
    public static void main(String[] args) {
        Employee emp = new Employee();
        emp.setDepartment(new Department());
        emp.setCertifications(new ArrayList<>(Arrays.asList("", "", "")));
        emp.setMetadata(new HashMap<>());

        BeanWrapperImpl bw = new BeanWrapperImpl(emp);
        bw.setAutoGrowNestedPaths(true);  // auto-create null intermediate objects
        bw.setAutoGrowCollectionLimit(10);

        // Set deep nested path
        bw.setPropertyValue("id",                           "EMP-001");
        bw.setPropertyValue("fullName",                     "Alice Johnson");
        bw.setPropertyValue("department.name",              "Engineering");
        bw.setPropertyValue("department.location.street",   "500 Tech Ave");
        bw.setPropertyValue("department.location.city",     "Austin");

        // Indexed list
        bw.setPropertyValue("certifications[0]", "AWS-SAA");
        bw.setPropertyValue("certifications[1]", "CKA");
        bw.setPropertyValue("certifications[2]", "CKAD");

        // Map entries
        bw.setPropertyValue("metadata[startDate]",  "2022-01-15");
        bw.setPropertyValue("metadata[level]",      "senior");

        // Read back via deep paths
        System.out.println("id:            " + bw.getPropertyValue("id"));
        System.out.println("fullName:      " + bw.getPropertyValue("fullName"));
        System.out.println("dept.name:     " + bw.getPropertyValue("department.name"));
        System.out.println("dept.location.city: " + bw.getPropertyValue("department.location.city"));
        System.out.println("certs[1]:      " + bw.getPropertyValue("certifications[1]"));
        System.out.println("meta[level]:   " + bw.getPropertyValue("metadata[level]"));

        // PropertyType for nested path
        System.out.println("\nProperty types:");
        System.out.println("  department.name type:       " +
            bw.getPropertyType("department.name"));
        System.out.println("  certifications[0] type:     " +
            bw.getPropertyType("certifications[0]"));
    }
}
```

How to run: `java BeanWrapperNested.java`

`setAutoGrowNestedPaths(true)` allows Spring to auto-create intermediate objects if they're null — `department.location.city` instantiates `Address` automatically if `department.location` is null. This is the same auto-grow behavior that Spring MVC uses when binding form submissions to nested command objects.

## 6. Walkthrough

Execution for Level 3 `"department.location.city"`:

1. `bw.setPropertyValue("department.location.city", "Austin")`.
2. `BeanWrapperImpl` splits path: `["department", "location", "city"]`.
3. Navigate: `emp.getDepartment()` → `Department` object (not null — we set it).
4. Navigate: `dept.getLocation()` → not null (set in `Department()` constructor).
5. Set: `location.setCity("Austin")`.
6. Read back: `bw.getPropertyValue("department.location.city")` → traverses same path → `"Austin"`.

## 7. Gotchas & takeaways

> Without `setAutoGrowNestedPaths(true)`, accessing `"address.city"` when `address` is `null` throws `NullValueInNestedPathException`. `DataBinder` enables auto-grow by default; raw `BeanWrapperImpl` does not. Always enable it when binding user-provided nested paths.

> `BeanWrapper` uses Java Beans reflection — it requires standard getter/setter naming conventions (`getX()` / `setX()`, `isX()` for boolean). Record accessors (`x()` without `get`) are not supported by `BeanWrapper`. Use `ReflectionUtils` or `@Value` for record fields.

- `BeanWrapper` is primarily a framework-level API. In application code, prefer `DataBinder` (for form binding), `BeanUtils.copyProperties` (for shallow copy), or direct method calls.
- Indexed access `phones[5]` on a `List` with fewer than 6 elements throws `IndexOutOfBoundsException` unless `setAutoGrowCollectionLimit` is set high enough.
- `getPropertyDescriptors()` returns ALL descriptors including `class`, `hashCode`, etc. Filter by `pd.getWriteMethod() != null` to get only settable properties.
- `BeanWrapper` wraps a target at construction time — if you need to rebind to a different object, create a new `BeanWrapperImpl`.
