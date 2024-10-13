import sqlite3
import json


def get_db_connection():
    conn = sqlite3.connect("founders_linkedin_jobs.db", timeout=20)
    conn.row_factory = sqlite3.Row
    return conn


def create_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS founders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            company TEXT,
            title TEXT,
            website TEXT,
            overview TEXT,
            category TEXT,
            linkedin TEXT,
            email TEXT,
            phone TEXT,
            first_name TEXT,
            last_name TEXT,
            joined TEXT,
            connected TEXT,
            num_employees TEXT,
            linkedin_jobs TEXT,
            tech_jobs TEXT,
            non_tech_jobs TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_to_sqlite(founder):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO founders (
            name, company, title, website, overview, category, linkedin, email, phone,
            first_name, last_name, joined, connected, num_employees, linkedin_jobs, tech_jobs, non_tech_jobs
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            founder["Name"],
            founder["Company"],
            founder["Title"],
            founder["Website"],
            founder["Overview"],
            founder["Category"],
            founder["LinkedIn"],
            founder["Email"],
            founder["Phone"],
            founder["First Name"],
            founder["Last Name"],
            founder["Joined"],
            founder["Connected"],
            founder["# of Employees"],
            json.dumps(founder["Jobs on Linkedin"]),
            json.dumps(founder["Tech Jobs on Linkedin"]),
            json.dumps(founder["Non Tech Jobs on Linkedin"]),
        ),
    )
    conn.commit()
    conn.close()


def get_founders_from_sqlite():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM founders")
    rows = cursor.fetchall()
    founders = []
    for row in rows:
        founder = {
            "Name": row["name"],
            "Company": row["company"],
            "Title": row["title"],
            "Website": row["website"],
            "Overview": row["overview"],
            "Category": row["category"],
            "LinkedIn": row["linkedin"],
            "Email": row["email"],
            "Phone": row["phone"],
            "First Name": row["first_name"],
            "Last Name": row["last_name"],
            "Joined": row["joined"],
            "Connected": row["connected"],
            "# of Employees": row["num_employees"],
            "Jobs on Linkedin": json.loads(row["linkedin_jobs"]),
            "Tech Jobs on Linkedin": json.loads(row["tech_jobs"]),
            "Non Tech Jobs on Linkedin": json.loads(row["non_tech_jobs"]),
        }
        founders.append(founder)
    conn.close()
    return founders
