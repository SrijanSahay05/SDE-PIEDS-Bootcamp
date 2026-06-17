# Session 07: Docker, Databases, and Authentication

In this session, we lay the foundation for persistence and user management by introducing Docker, PostgreSQL, and basic authentication concepts.

---

## 1. Docker and Databases

We started by covering **Docker** and what it means to containerise applications.

### Types of Databases
We discussed the differences between various database types:
- **Relational (SQL) vs Non-Relational (NoSQL):** Structured table-based data vs flexible document-based data.
- **In-Memory Databases (e.g., Redis):** Extremely fast read/writes, commonly used for caching. We discussed the pros (speed) and cons (data volatility if not configured properly).

### Setting up PostgreSQL with Docker Compose
We created a `docker-compose.yml` file to spin up a **PostgreSQL 17** container. The database configuration is handled entirely through environment variables directly in Docker:
- Username
- Password
- Database name (used to construct the connection URL string)

---

## 2. Database Mental Model: The Excel Analogy

To understand database initialization and schemas without immediately diving into code, we mapped database concepts to Microsoft Excel (via Excalidraw):

| Database Concept (PostgreSQL) | Microsoft Excel Equivalent |
| ----------------------------- | -------------------------- |
| **Database Instance**         | The Excel File (`.xlsx`)   |
| **Table**                     | A specific Sheet           |
| **Schema Definition**         | The Column Headers         |
| **Records / Data**            | The Rows under the headers |

We discussed why schemas are critical to enforce data structure and integrity. We also explored the default `public` schema in Postgres and how we can connect to the database in Python using the `asyncpg` library:
```python
import asyncpg

# Example connection setup
conn = await asyncpg.connect(url)
value = await conn.fetchval('SELECT ...')
```
*(Code implementation will be expanded in upcoming sessions.)*

---

## 3. Authentication & ORMs

Next, we looked at how an authentication feature (Register and Login endpoints) should be designed. We reviewed what the HTTP request structure would look like for these endpoints (referenced in `auth.py`).

### Moving Forward: ORMs (Object Relational Mapping)
Writing raw SQL strings in Python can be prone to errors and SQL injection. To solve this, we discussed the need for **ORMs** in FastAPI. An ORM allows us to define database tables as Python classes. 

**Upcoming Tasks:**
1. **Define a User Database Schema** using an ORM.
2. **Create Register and Login functions** to serve our auth endpoints.
3. **Secure the `/ask` endpoint** so it requires authentication before returning answers.
