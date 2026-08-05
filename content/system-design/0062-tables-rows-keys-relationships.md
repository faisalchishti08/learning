---
card: system-design
gi: 62
slug: tables-rows-keys-relationships
title: "Tables, rows, keys & relationships"
---

## 1. What it is

A **relational database** stores data in **tables**, each a grid of **rows** (individual records) and columns (named fields). A **primary key** is one or more columns that uniquely identify each row in a table. A **foreign key** is a column in one table that references a primary key in another table, forming a **relationship** between the two.

## 2. Why & when

Relational structure exists so that data is stored once, in the table it belongs to, and connected to related data by reference rather than by duplicating it everywhere it is needed. This is the foundation everything else in this section builds on: normalization, indexes, joins, and transactions all assume this table-row-key model. Reach for a relational database whenever your data has clear entities with well-defined relationships to each other, and you need strong consistency guarantees on that structure.

## 3. Core concept

**Primary keys guarantee uniqueness:** a table's primary key column (often a numeric `id`) is enforced by the database to never repeat and never be empty — this is what lets other tables reliably point back to exactly one row.

**Foreign keys express relationships:** a column like `orders.user_id` holding the value `42` means "this order belongs to the user whose primary key is `42`" — the relationship is represented as a reference, not by copying the user's full details into every order row.

**Three relationship shapes:**
- **One-to-many:** one user has many orders; `orders.user_id` is a foreign key, `users.id` is the primary key it points to.
- **Many-to-many:** many students enroll in many courses; this needs a third **join table** (e.g. `enrollments`), with foreign keys pointing to both `students` and `courses`, because neither table alone can hold a variable-length list of the other.
- **One-to-one:** one user has exactly one profile; a foreign key on either side, with a uniqueness constraint added to enforce "exactly one," not "many."

**Why references beat duplication:** if a user's name were copied into every one of their orders instead of referenced by `user_id`, changing the user's name would mean updating every order row — a foreign key means it only needs to be updated in one place, the `users` table.

## 4. Diagram

```
users                          orders                       students <-> courses (many-to-many)
+----+-------+                 +----+---------+--------+    students        enrollments          courses
| id | name  |                 | id | user_id | total  |    +----+------+   +------------+       +----+--------+
+----+-------+                 +----+---------+--------+    | id | name |   | student_id |        | id | title  |
| 1  | Alice |  <--- FK -----  | 10 | 1       | 49.99  |    +----+------+   | course_id  |        +----+--------+
| 2  | Bob   |  <--- FK -----  | 11 | 2       | 12.50  |    | 1  | Amy  |   +------------+         | 1  | Math   |
+----+-------+                 | 12 | 1       | 8.00   |    +----+------+   (join table:            | 2  | CS     |
                                +----+---------+--------+                    two FKs, one row       +----+--------+
                                                                              per enrollment pair)
```
*Caption: foreign keys point from the "many" side back to the primary key of the "one" side; many-to-many needs a join table.*

## 5. Runnable example

**Level 1 — Basic.** Model tables as lists of records with a primary key, and a foreign key linking two tables (one-to-many).

**Level 2 — Join.** Resolve a foreign key reference to fetch the related row, simulating what a SQL `JOIN` does.

**Level 3 — Many-to-many via a join table.** Model students and courses connected through an `enrollments` join table.

```java
// TablesRowsKeys.java
import java.util.*;

public class TablesRowsKeys {

    record User(int id, String name) {}
    record Order(int id, int userId, double total) {} // userId is the foreign key

    record Student(int id, String name) {}
    record Course(int id, String title) {}
    record Enrollment(int studentId, int courseId) {} // join table: two foreign keys

    public static void main(String[] args) {
        // Level 1: one-to-many, users <-> orders.
        List<User> users = List.of(new User(1, "Alice"), new User(2, "Bob"));
        List<Order> orders = List.of(
            new Order(10, 1, 49.99),
            new Order(11, 2, 12.50),
            new Order(12, 1, 8.00)
        );

        // Level 2: resolve the foreign key - find the User a given Order belongs to.
        Map<Integer, User> usersById = new HashMap<>();
        for (User u : users) usersById.put(u.id(), u);

        System.out.println("Order-to-user join:");
        for (Order o : orders) {
            User owner = usersById.get(o.userId()); // this is what a JOIN does
            System.out.println("  order " + o.id() + " ($" + o.total() + ") belongs to " + owner.name());
        }

        // Level 3: many-to-many, students <-> courses via an enrollments join table.
        List<Student> students = List.of(new Student(1, "Amy"), new Student(2, "Sam"));
        List<Course> courses = List.of(new Course(1, "Math"), new Course(2, "CS"));
        List<Enrollment> enrollments = List.of(
            new Enrollment(1, 1), // Amy -> Math
            new Enrollment(1, 2), // Amy -> CS
            new Enrollment(2, 2)  // Sam -> CS
        );

        Map<Integer, Course> coursesById = new HashMap<>();
        for (Course c : courses) coursesById.put(c.id(), c);

        System.out.println("Student enrollments (via join table):");
        for (Student s : students) {
            List<String> titles = new ArrayList<>();
            for (Enrollment e : enrollments) {
                if (e.studentId() == s.id()) {
                    titles.add(coursesById.get(e.courseId()).title());
                }
            }
            System.out.println("  " + s.name() + " is enrolled in: " + titles);
        }
    }
}
```

**How to run:** save as `TablesRowsKeys.java`, then run `java TablesRowsKeys.java`.

## 6. Walkthrough

1. `users` and `orders` are modeled as flat lists of records, each `Order` carrying `userId` as its foreign key, matching one `User`'s primary key `id`.
2. `usersById` builds a lookup map from primary key to row, exactly what a database index on `users.id` provides internally for fast lookups.
3. The loop over `orders` resolves each order's `userId` back to its owning `User` via `usersById.get(o.userId())` — this single lookup-and-combine step is what a SQL `JOIN` performs for every matching row pair.
4. For the many-to-many case, `enrollments` holds one row per (student, course) pairing rather than either table trying to hold a list of the other — this is the join-table pattern.
5. For each `Student`, the code scans `enrollments` for rows matching that student's `id`, then resolves each matched `courseId` to its `Course` title — producing "Amy is enrolled in: [Math, CS]" and "Sam is enrolled in: [CS]", the same result a SQL query joining all three tables would produce.

## 7. Gotchas & takeaways

> Gotcha: a foreign key column with no matching row in the referenced table (an "orphaned" reference, e.g. an order pointing to a deleted user) is a real risk if the database is not configured to enforce referential integrity — most relational databases support a `FOREIGN KEY` constraint specifically to reject inserts or deletes that would create this situation.

- Primary keys make rows uniquely addressable; foreign keys turn that addressability into relationships between tables, without duplicating data.
- Many-to-many relationships always need a third join table — neither of the two related tables can directly hold a variable-length list of the other.
- Related concepts: [Normalization (1NF–3NF, BCNF)](0063-normalization-1nf3nf-bcnf.md) (the discipline of organizing tables to avoid duplicating data), [Query planning & the N+1 problem](0067-query-planning-the-n-1-problem.md) (a common performance pitfall when resolving these relationships in application code).
