# Applied Databases Project (25-26-8637)

Student: Gustavo Goes

Small console project for Applied Databases module.
It use MySQL + Neo4j.

- MySQL: companies, attendees, sessions, rooms, registrations
- Neo4j: attendee connections

Main file: [project/main.py](project/main.py)

## Quick run

1. Import [project/sql/appdbproj.sql](project/sql/appdbproj.sql) in MySQL.
2. Run [project/neo4j/attendeeNetwork.cypher](project/neo4j/attendeeNetwork.cypher) in Neo4j (attendeeNetwork db).
3. Run:

```powershell
python project/main.py
```

The app will ask credentials when it starts.

## What is included in repo

- [project/main.py](project/main.py)
- [project/sql/appdbproj.sql](project/sql/appdbproj.sql)
- [project/neo4j/attendeeNetwork.cypher](project/neo4j/attendeeNetwork.cypher)
- [project/innovation.txt](project/innovation.txt)
- [project/innovation.pdf](project/innovation.pdf)
- [GitLink.txt](GitLink.txt)

## Note

This is a student exercise, so maybe some parts are basic and not production level.
