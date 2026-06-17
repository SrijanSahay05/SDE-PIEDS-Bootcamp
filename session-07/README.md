# Session 07: Docker, Databases, and Authentication (Supplementary Material)

Welcome to Session 7! In our live sessions, time is limited, so we often cover concepts at a high level. This document serves as supplementary material to dive deeper into the theoretical and practical foundations of Docker, Databases, and Authentication.

---

## 1. Introduction to Databases

A database is a structured system designed to store, manage, and retrieve data efficiently. As your application grows beyond simple Python dictionaries, you need robust data storage. We generally categorize databases into a few main paradigms:

### Relational (SQL) vs. Non-Relational (NoSQL)
- **Relational Databases (SQL):** These store data in highly structured tables (rows and columns). They use SQL (Structured Query Language) for querying and are fantastic at maintaining strict relationships between different entities (e.g., linking a "User" to their "Search History"). Examples include PostgreSQL, MySQL, and SQLite.
- **Non-Relational Databases (NoSQL):** These store data in flexible formats, often as JSON-like documents, key-value pairs, or graphs. Examples include MongoDB and DynamoDB. They are useful for unstructured data or systems with rapidly changing data requirements.

### In-Memory Databases (e.g., Redis)
- **How they work:** Unlike traditional databases that save data to a physical hard drive (disk), in-memory databases store data directly in RAM (Random Access Memory).
- **Pros:** Because RAM is much faster than physical disks, read and write speeds are incredibly fast. 
- **Cons:** RAM is volatile. If the server crashes or loses power, the data is lost (unless specific, slower persistence mechanisms are configured).
- **Use Case:** We typically use tools like Redis for **caching**. For instance, if many users ask our backend the exact same question, we can temporarily store the LLM's response in Redis. The next time the question is asked, we retrieve the answer instantly from RAM instead of querying the slower primary database or paying for another LLM API call.

---

## 2. Containerization with Docker

When building software, a classic problem is "it works on my machine, but it breaks in production." Docker solves this issue.

Docker allows us to package our application along with everything it needs to run (libraries, dependencies, database engines) into a **container**. Containers are isolated environments that run identically regardless of the host operating system (Mac, Windows, or Linux).

### Spinning up PostgreSQL using Docker Compose
Instead of manually installing PostgreSQL directly onto your computer, we use a `docker-compose.yml` file. This file acts as a blueprint to spin up a pre-configured database container. 

In our project, we are spinning up a **PostgreSQL 17** container. We configure it by passing Environment Variables (`ENV`) directly to the container in the compose file:
- `POSTGRES_USER`: Sets the database username.
- `POSTGRES_PASSWORD`: Sets the password.
- `POSTGRES_DB`: Sets the initial database name.

These variables are subsequently used to construct a **Connection URL String**, which our FastAPI backend will use to connect to the database.

---

## 3. Database Mental Model: The Excel Analogy

To visualize how a relational database is structured—without getting bogged down in code—it helps to compare it to a Microsoft Excel workbook.

| Database Concept (PostgreSQL) | Microsoft Excel Equivalent |
| ----------------------------- | -------------------------- |
| **Database Instance**         | The Excel File (`.xlsx`)   |
| **Table**                     | A specific Sheet (e.g., "Users", "Chats") |
| **Schema Definition**         | The Column Headers (e.g., "ID", "Name", "Email") |
| **Records / Data**            | The Rows populated underneath the headers |

### What is a Schema and Why is it Important?
A schema acts as the "template" or blueprint for your data. In Excel, you could accidentally type a word into a column meant for dates, or leave a crucial cell blank. In a database, a **Schema** strictly enforces data types and constraints (e.g., this column must be an Integer, this one must be Text, this one cannot be empty). This guarantees data integrity.

In PostgreSQL, tables are grouped into namespaces (also called schemas). The default namespace is called the `public` schema. When you create a table without specifying a namespace, it lives in `public`.

### Connecting via Python (`asyncpg`)
In Python, we can connect to our database using asynchronous libraries like `asyncpg`. 
```python
import asyncpg

async def fetch_data():
    # The URL string is built using our Docker environment variables
    url = "postgresql://user:password@localhost:5432/dbname"
    
    # Establish a connection
    conn = await asyncpg.connect(url)
    
    # Run a raw SQL query and fetch a single value
    value = await conn.fetchval('SELECT version();')
    print(value)
```

---

## 4. Object Relational Mapping (ORM)

While writing raw SQL strings (like `SELECT * FROM users`) works, it becomes cumbersome, error-prone, and risky as an application grows. 

**The Solution: ORMs**
An Object Relational Mapper (ORM) is a library that allows you to interact with your database using standard Python.
- **Pythonic Code:** Instead of writing raw SQL strings, you define your database tables as Python Classes.
- **Security:** ORMs automatically sanitize inputs, protecting your application against SQL Injection attacks.
- **Maintainability:** Refactoring is easier. Changing a column name is just renaming a class attribute.

Instead of manually crafting SQL `CREATE TABLE` commands, we will define our models in Python, and the ORM will seamlessly translate them into SQL queries for us.

---

## 5. Authentication

With a database ready, we can start securely storing user credentials. For our API, we discussed designing two primary endpoints:

1. **Register Endpoint:** Accepts an HTTP request containing a Username/Email and a Password. The backend hashes the password (passwords should never be stored in plain text!) and saves the new user record to our database.
2. **Login Endpoint:** Accepts user credentials, verifies them against the hashed password in the database, and if successful, returns a secure session token (like a JWT) to the client.

### Moving Forward
In the upcoming sessions, we will transition from theory to hands-on code implementation:
1. **Define a User Schema:** We will use an ORM to define our User database table.
2. **Implement Auth Routes:** We will write the Python logic for our Register and Login functions.
3. **Secure the Application:** We will add authentication dependencies to our existing `/ask` endpoint, ensuring that only users with a valid token can ask questions to the LLM.
