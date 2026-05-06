import mysql.connector
import neo4j
import getpass

# ─── Configuration ────────────────────────────────────────────────────────────

MYSQL_DATABASE = "appdbproj"
NEO4J_URI      = "bolt://127.0.0.1:7687"

def prompt_credentials():
    print("\n" + "=" * 50)
    print(" DATABASE CREDENTIALS SETUP")
    print("=" * 50)
    print(" Enter your local MySQL and Neo4j credentials.")
    print(" (These are the credentials you set when")
    print("  installing MySQL and Neo4j on your machine.)")
    print("=" * 50)

    print("\n--- MySQL ---")
    mysql_user     = input("  MySQL username [default: root]: ").strip() or "root"
    mysql_password = getpass.getpass("  MySQL password: ")

    print("\n--- Neo4j ---")
    neo4j_user     = input("  Neo4j username [default: neo4j]: ").strip() or "neo4j"
    neo4j_password = getpass.getpass("  Neo4j password: ")

    mysql_config = {
        "host":     "localhost",
        "user":     mysql_user,
        "password": mysql_password,
        "database": MYSQL_DATABASE
    }
    return mysql_config, neo4j_user, neo4j_password

# ─── Startup: connect to both databases and cache rooms ───────────────────────

def connect_mysql(mysql_config):
    try:
        conn = mysql.connector.connect(**mysql_config)
        print("MySQL connected.")
        return conn
    except mysql.connector.Error as e:
        print(f"MySQL connection failed: {e}")
        raise SystemExit(1)

def connect_neo4j(neo4j_user, neo4j_password):
    try:
        driver = neo4j.GraphDatabase.driver(NEO4J_URI, auth=(neo4j_user, neo4j_password))
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

# ─── Helpers: show reference data ────────────────────────────────────────────

def show_companies(mysql_conn):
    cursor = mysql_conn.cursor()
    cursor.execute("SELECT companyID, companyName, industry FROM company ORDER BY companyID")
    rows = cursor.fetchall()
    cursor.close()
    print(f"\n  {'ID':<6} {'Company':<20} {'Industry'}")
    print("  " + "-" * 45)
    for row in rows:
        print(f"  {row[0]:<6} {row[1]:<20} {row[2]}")

def show_attendees(mysql_conn):
    cursor = mysql_conn.cursor()
    cursor.execute("SELECT attendeeID, attendeeName, attendeeCompanyID FROM attendee ORDER BY attendeeID")
    rows = cursor.fetchall()
    cursor.close()
    print(f"\n  {'ID':<6} {'Name':<25} {'CompanyID'}")
    print("  " + "-" * 40)
    for row in rows:
        print(f"  {row[0]:<6} {row[1]:<25} {row[2]}")

def show_sessions(mysql_conn):
    cursor = mysql_conn.cursor()
    cursor.execute(
        "SELECT s.sessionID, s.sessionTitle, s.speakerName, s.sessionDate, r.roomName "
        "FROM session s JOIN room r ON s.roomID = r.roomID ORDER BY s.sessionDate"
    )
    rows = cursor.fetchall()
    cursor.close()
    print(f"\n  {'ID':<6} {'Title':<35} {'Speaker':<20} {'Date':<12} {'Room'}")
    print("  " + "-" * 85)
    for row in rows:
        print(f"  {row[0]:<6} {row[1]:<35} {row[2]:<20} {str(row[3]):<12} {row[4]}")

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
    print("  ─── Innovations ───────────────")
    print("  7. Delete Attendee")
    print("  8. Most Connected Attendees")
    print("  9. Search Attendee by Name")
    print("  10. Register Attendee for Session")
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
        LEFT JOIN registration reg ON a.attendeeID = reg.attendeeID
        LEFT JOIN session s ON reg.sessionID = s.sessionID
        LEFT JOIN room r ON s.roomID = r.roomID
        WHERE c.companyName = %s
        ORDER BY a.attendeeName, s.sessionDate
    """
    cursor.execute(query, (company,))
    results = cursor.fetchall()
    cursor.close()

    if not results:
        print(f"No attendees found from '{company}'.")
        return

    print(f"\n{'ID':<6} {'Attendee':<20} {'Session':<35} {'Date':<12} {'Room'}")
    print("-" * 85)
    for row in results:
        session = row[2] if row[2] else "(no registrations)"
        date    = str(row[3]) if row[3] else ""
        room    = row[4] if row[4] else ""
        print(f"{row[0]:<6} {row[1]:<20} {session:<35} {date:<12} {room}")

# ─── Option 3: Add New Attendee ────────────────────────────────────────────────

def option3(mysql_conn):
    print("\nAvailable companies:")
    show_companies(mysql_conn)
    try:
        name         = input("Enter Attendee Name: ").strip()
        dob          = input("Enter Date of Birth (YYYY-MM-DD): ").strip()
        gender       = input("Enter Gender (Male/Female): ").strip()
        company_id   = int(input("Enter Company ID: ").strip())
    except ValueError:
        print("Invalid input: Company ID must be an integer.")
        return

    if gender not in ("Male", "Female"):
        print("Invalid gender. Must be 'Male' or 'Female'.")
        return

    cursor = mysql_conn.cursor()
    try:
        cursor.execute("SELECT MAX(attendeeID) FROM attendee")
        max_id = cursor.fetchone()[0] or 0
        attendee_id = max_id + 1

        cursor.execute(
            "INSERT INTO attendee (attendeeID, attendeeName, attendeeDOB, attendeeGender, attendeeCompanyID) "
            "VALUES (%s, %s, %s, %s, %s)",
            (attendee_id, name, dob, gender, company_id)
        )
        mysql_conn.commit()
        print(f"Attendee '{name}' added successfully with ID {attendee_id}.")
    except mysql.connector.IntegrityError as e:
        err = str(e)
        if "foreign key" in err.lower():
            print(f"Error: Company ID {company_id} does not exist.")
        else:
            print(f"Database error: {e}")
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
    finally:
        cursor.close()

# ─── Option 4: View Connected Attendees ───────────────────────────────────────

def option4(mysql_conn, neo4j_driver):
    print("\nAvailable attendees:")
    show_attendees(mysql_conn)
    try:
        attendee_id = int(input("\nEnter Attendee ID: ").strip())
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
    print("\nAvailable attendees:")
    show_attendees(mysql_conn)
    try:
        id1 = int(input("\nEnter first Attendee ID: ").strip())
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

# ─── Option 7: Delete Attendee ───────────────────────────────────────────────

def option7(mysql_conn, neo4j_driver):
    print("\nAvailable attendees:")
    show_attendees(mysql_conn)
    try:
        attendee_id = int(input("\nEnter Attendee ID to delete: ").strip())
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

    confirm = input(f"Are you sure you want to delete '{row[0]}' (ID {attendee_id})? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Deletion cancelled.")
        cursor.close()
        return

    try:
        cursor.execute("DELETE FROM registration WHERE attendeeID = %s", (attendee_id,))
        cursor.execute("DELETE FROM attendee WHERE attendeeID = %s", (attendee_id,))
        mysql_conn.commit()

        def remove_node(tx, aid):
            tx.run("MATCH (a:Attendee {AttendeeID: $id}) DETACH DELETE a", id=aid)

        with neo4j_driver.session() as session:
            session.execute_write(remove_node, attendee_id)

        print(f"Attendee '{row[0]}' (ID {attendee_id}) deleted from MySQL and Neo4j.")
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
    finally:
        cursor.close()

# ─── Option 8: Most Connected Attendees ───────────────────────────────────────

def option8(mysql_conn, neo4j_driver):
    def get_top_connected(tx):
        result = tx.run(
            "MATCH (a:Attendee)-[:CONNECTED_TO]-(b:Attendee) "
            "RETURN a.AttendeeID AS id, count(b) AS connections "
            "ORDER BY connections DESC LIMIT 10"
        )
        return [(record["id"], record["connections"]) for record in result]

    with neo4j_driver.session() as session:
        top = session.execute_read(get_top_connected)

    if not top:
        print("No connections found in the network.")
        return

    print(f"\n{'Rank':<6} {'ID':<8} {'Name':<25} {'Connections'}")
    print("-" * 55)
    cursor = mysql_conn.cursor()
    for rank, (aid, count) in enumerate(top, start=1):
        cursor.execute("SELECT attendeeName FROM attendee WHERE attendeeID = %s", (aid,))
        name_row = cursor.fetchone()
        name = name_row[0] if name_row else "(unknown)"
        print(f"{rank:<6} {aid:<8} {name:<25} {count}")
    cursor.close()

# ─── Option 9: Search Attendee by Name ────────────────────────────────────────

def option9(mysql_conn):
    name = input("Enter attendee name (or part of it): ").strip()
    cursor = mysql_conn.cursor()
    cursor.execute(
        "SELECT a.attendeeID, a.attendeeName, a.attendeeDOB, a.attendeeGender, c.companyName "
        "FROM attendee a JOIN company c ON a.attendeeCompanyID = c.companyID "
        "WHERE a.attendeeName LIKE %s ORDER BY a.attendeeName",
        (f"%{name}%",)
    )
    results = cursor.fetchall()
    cursor.close()

    if not results:
        print(f"No attendees found matching '{name}'.")
        return

    print(f"\n{'ID':<6} {'Name':<25} {'DOB':<12} {'Gender':<8} {'Company'}")
    print("-" * 70)
    for row in results:
        print(f"{row[0]:<6} {row[1]:<25} {str(row[2]):<12} {row[3]:<8} {row[4]}")

# ─── Option 10: Register Attendee for Session ────────────────────────────────

def option10(mysql_conn):
    show_attendees(mysql_conn)
    try:
        attendee_id = int(input("\nEnter Attendee ID to register: ").strip())
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

    show_sessions(mysql_conn)
    try:
        session_id = int(input("\nEnter Session ID to register for: ").strip())
    except ValueError:
        print("Invalid input: Session ID must be an integer.")
        cursor.close()
        return

    cursor.execute("SELECT sessionTitle FROM session WHERE sessionID = %s", (session_id,))
    row = cursor.fetchone()
    if not row:
        print(f"Session ID {session_id} not found.")
        cursor.close()
        return
    session_title = row[0]

    # Check for duplicate registration
    cursor.execute(
        "SELECT registrationID FROM registration WHERE attendeeID = %s AND sessionID = %s",
        (attendee_id, session_id)
    )
    if cursor.fetchone():
        print(f"'{attendee_name}' is already registered for '{session_title}'.")
        cursor.close()
        return

    # Generate next registrationID
    cursor.execute("SELECT MAX(registrationID) FROM registration")
    max_id = cursor.fetchone()[0] or 0
    new_reg_id = max_id + 1

    try:
        cursor.execute(
            "INSERT INTO registration (registrationID, attendeeID, sessionID, registeredAt) "
            "VALUES (%s, %s, %s, NOW())",
            (new_reg_id, attendee_id, session_id)
        )
        mysql_conn.commit()
        print(f"Success: '{attendee_name}' registered for '{session_title}' (registrationID: {new_reg_id}).")
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
    finally:
        cursor.close()

# ─── Option 6: View Rooms (from cache) ────────────────────────────────────────

def option6(rooms_cache):
    print(f"\n{'ID':<6} {'Room Name':<25} {'Capacity'}")
    print("-" * 40)
    for room in rooms_cache:
        print(f"{room[0]:<6} {room[1]:<25} {room[2]}")

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    mysql_config, neo4j_user, neo4j_password = prompt_credentials()
    mysql_conn   = connect_mysql(mysql_config)
    neo4j_driver = connect_neo4j(neo4j_user, neo4j_password)
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
        elif choice == "7":
            option7(mysql_conn, neo4j_driver)
        elif choice == "8":
            option8(mysql_conn, neo4j_driver)
        elif choice == "9":
            option9(mysql_conn)
        elif choice == "10":
            option10(mysql_conn)
        elif choice == "x":
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please try again.")

    mysql_conn.close()
    neo4j_driver.close()

if __name__ == "__main__":
    main()
