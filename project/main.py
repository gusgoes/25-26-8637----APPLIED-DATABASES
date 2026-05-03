import mysql.connector
import neo4j

# ─── Configuration ────────────────────────────────────────────────────────────

MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "GGFggf2@2@",
    "database": "appdbproj"
}

NEO4J_URI      = "neo4j://127.0.0.1:7687"
NEO4J_USER     = "neo4j"
NEO4J_PASSWORD = "neo4j123"

# ─── Startup: connect to both databases and cache rooms ───────────────────────

def connect_mysql():
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        print("MySQL connected.")
        return conn
    except mysql.connector.Error as e:
        print(f"MySQL connection failed: {e}")
        raise SystemExit(1)

def connect_neo4j():
    try:
        driver = neo4j.GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        driver.verify_connectivity()
        print("Neo4j connected.")
        return driver
    except Exception as e:
        print(f"Neo4j connection failed: {e}")
        raise SystemExit(1)

def load_rooms(mysql_conn):
    cursor = mysql_conn.cursor()
    cursor.execute("SELECT roomID, roomName, capacity FROM room ORDER BY roomID")
    rooms = cursor.fetchall()
    cursor.close()
    return rooms

# ─── Menu ─────────────────────────────────────────────────────────────────────

def print_menu():
    print("\n" + "=" * 50)
    print("   ConferenceConnect — Main Menu")
    print("=" * 50)
    print("  1. View Speakers & Sessions")
    print("  2. View Attendees by Company")
    print("  3. Add New Attendee")
    print("  4. View Connected Attendees")
    print("  5. Add Attendee Connection")
    print("  6. View Rooms")
    print("  x. Exit")
    print("=" * 50)

# ─── Option 1: View Speakers & Sessions ───────────────────────────────────────

def option1(mysql_conn):
    name = input("Enter speaker name (or part of it): ").strip()
    cursor = mysql_conn.cursor()
    query = """
        SELECT s.sessionID, s.sessionTitle, s.speakerName, s.sessionDate, r.roomName
        FROM session s
        JOIN room r ON s.roomID = r.roomID
        WHERE s.speakerName LIKE %s
        ORDER BY s.sessionDate
    """
    cursor.execute(query, (f"%{name}%",))
    results = cursor.fetchall()
    cursor.close()

    if not results:
        print(f"No sessions found for speaker matching '{name}'.")
        return

    print(f"\n{'ID':<6} {'Title':<35} {'Speaker':<20} {'Date':<12} {'Room'}")
    print("-" * 85)
    for row in results:
        print(f"{row[0]:<6} {row[1]:<35} {row[2]:<20} {str(row[3]):<12} {row[4]}")

# ─── Option 2: View Attendees by Company ──────────────────────────────────────

def option2(mysql_conn):
    company = input("Enter company name: ").strip()
    cursor = mysql_conn.cursor()

    cursor.execute("SELECT companyID FROM company WHERE companyName = %s", (company,))
    row = cursor.fetchone()
    if not row:
        print(f"Company '{company}' not found.")
        cursor.close()
        return

    query = """
        SELECT a.attendeeID, a.attendeeName, s.sessionTitle, s.sessionDate, r.roomName
        FROM attendee a
        JOIN company c ON a.attendeeCompanyID = c.companyID
        JOIN registration reg ON a.attendeeID = reg.attendeeID
        JOIN session s ON reg.sessionID = s.sessionID
        JOIN room r ON s.roomID = r.roomID
        WHERE c.companyName = %s
        ORDER BY a.attendeeName, s.sessionDate
    """
    cursor.execute(query, (company,))
    results = cursor.fetchall()
    cursor.close()

    if not results:
        print(f"No registrations found for attendees from '{company}'.")
        return

    print(f"\n{'ID':<6} {'Attendee':<20} {'Session':<35} {'Date':<12} {'Room'}")
    print("-" * 85)
    for row in results:
        print(f"{row[0]:<6} {row[1]:<20} {row[2]:<35} {str(row[3]):<12} {row[4]}")

# ─── Option 3: Add New Attendee ────────────────────────────────────────────────

def option3(mysql_conn):
    try:
        attendee_id  = int(input("Enter Attendee ID (integer): ").strip())
        name         = input("Enter Attendee Name: ").strip()
        dob          = input("Enter Date of Birth (YYYY-MM-DD): ").strip()
        gender       = input("Enter Gender (Male/Female): ").strip()
        company_id   = int(input("Enter Company ID: ").strip())
    except ValueError:
        print("Invalid input: ID and Company ID must be integers.")
        return

    if gender not in ("Male", "Female"):
        print("Invalid gender. Must be 'Male' or 'Female'.")
        return

    cursor = mysql_conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO attendee (attendeeID, attendeeName, attendeeDOB, attendeeGender, attendeeCompanyID) "
            "VALUES (%s, %s, %s, %s, %s)",
            (attendee_id, name, dob, gender, company_id)
        )
        mysql_conn.commit()
        print(f"Attendee '{name}' added successfully.")
    except mysql.connector.IntegrityError as e:
        err = str(e)
        if "Duplicate entry" in err:
            print(f"Error: Attendee ID {attendee_id} already exists.")
        elif "foreign key" in err.lower():
            print(f"Error: Company ID {company_id} does not exist.")
        else:
            print(f"Database error: {e}")
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
    finally:
        cursor.close()

# ─── Option 4: View Connected Attendees ───────────────────────────────────────

def option4(mysql_conn, neo4j_driver):
    try:
        attendee_id = int(input("Enter Attendee ID: ").strip())
    except ValueError:
        print("Invalid input: ID must be an integer.")
        return

    cursor = mysql_conn.cursor()
    cursor.execute("SELECT attendeeName FROM attendee WHERE attendeeID = %s", (attendee_id,))
    row = cursor.fetchone()
    if not row:
        print(f"Attendee ID {attendee_id} not found.")
        cursor.close()
        return
    attendee_name = row[0]

    def get_connections(tx, aid):
        result = tx.run(
            "MATCH (a:Attendee {AttendeeID: $id})-[:CONNECTED_TO]-(b:Attendee) RETURN b.AttendeeID AS id",
            id=aid
        )
        return [record["id"] for record in result]

    with neo4j_driver.session() as session:
        connected_ids = session.execute_read(get_connections, attendee_id)

    if not connected_ids:
        print(f"{attendee_name} (ID {attendee_id}) has no connections.")
        return

    print(f"\nConnections for {attendee_name} (ID {attendee_id}):")
    print("-" * 40)
    for cid in connected_ids:
        cursor.execute("SELECT attendeeName FROM attendee WHERE attendeeID = %s", (cid,))
        name_row = cursor.fetchone()
        cname = name_row[0] if name_row else "(unknown)"
        print(f"  ID {cid}: {cname}")

    cursor.close()

# ─── Option 5: Add Attendee Connection ────────────────────────────────────────

def option5(mysql_conn, neo4j_driver):
    try:
        id1 = int(input("Enter first Attendee ID: ").strip())
        id2 = int(input("Enter second Attendee ID: ").strip())
    except ValueError:
        print("Invalid input: IDs must be integers.")
        return

    if id1 == id2:
        print("Error: Cannot connect an attendee to themselves.")
        return

    cursor = mysql_conn.cursor()
    cursor.execute("SELECT attendeeName FROM attendee WHERE attendeeID = %s", (id1,))
    row1 = cursor.fetchone()
    if not row1:
        print(f"Attendee ID {id1} not found.")
        cursor.close()
        return

    cursor.execute("SELECT attendeeName FROM attendee WHERE attendeeID = %s", (id2,))
    row2 = cursor.fetchone()
    if not row2:
        print(f"Attendee ID {id2} not found.")
        cursor.close()
        return
    cursor.close()

    def check_and_create(tx, a, b):
        exists = tx.run(
            "MATCH (x:Attendee {AttendeeID: $a})-[:CONNECTED_TO]-(y:Attendee {AttendeeID: $b}) RETURN x",
            a=a, b=b
        ).single()
        if exists:
            return False
        tx.run("MERGE (:Attendee {AttendeeID: $id})", id=a)
        tx.run("MERGE (:Attendee {AttendeeID: $id})", id=b)
        tx.run(
            "MATCH (x:Attendee {AttendeeID: $a}), (y:Attendee {AttendeeID: $b}) "
            "CREATE (x)-[:CONNECTED_TO]->(y)",
            a=a, b=b
        )
        return True

    with neo4j_driver.session() as session:
        created = session.execute_write(check_and_create, id1, id2)

    if created:
        print(f"Connection created between {row1[0]} (ID {id1}) and {row2[0]} (ID {id2}).")
    else:
        print(f"Connection already exists between ID {id1} and ID {id2}.")

# ─── Option 6: View Rooms (from cache) ────────────────────────────────────────

def option6(rooms_cache):
    print(f"\n{'ID':<6} {'Room Name':<25} {'Capacity'}")
    print("-" * 40)
    for room in rooms_cache:
        print(f"{room[0]:<6} {room[1]:<25} {room[2]}")

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    mysql_conn   = connect_mysql()
    neo4j_driver = connect_neo4j()
    rooms_cache  = load_rooms(mysql_conn)

    while True:
        print_menu()
        choice = input("Select an option: ").strip().lower()

        if choice == "1":
            option1(mysql_conn)
        elif choice == "2":
            option2(mysql_conn)
        elif choice == "3":
            option3(mysql_conn)
        elif choice == "4":
            option4(mysql_conn, neo4j_driver)
        elif choice == "5":
            option5(mysql_conn, neo4j_driver)
        elif choice == "6":
            option6(rooms_cache)
        elif choice == "x":
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please try again.")

    mysql_conn.close()
    neo4j_driver.close()

if __name__ == "__main__":
    main()
