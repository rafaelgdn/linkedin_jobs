import sqlite3
import json
import pandas as pd


def read_db_and_create_excel(db_path, excel_path):
    conn = sqlite3.connect(db_path)

    df = pd.read_sql_query("SELECT * FROM founders", conn)

    def format_jobs(jobs_json):
        jobs = json.loads(jobs_json)
        return "\n".join([f"{job['title']} - {job['url']}" for job in jobs])

    df["Jobs on Linkedin"] = df["linkedin_jobs"].apply(format_jobs)
    df["Tech Jobs on Linkedin"] = df["tech_jobs"].apply(format_jobs)

    df = df.drop(columns=["linkedin_jobs", "tech_jobs", "non_tech_jobs", "id"])

    df = df.rename(
        columns={
            "name": "Name",
            "company": "Company",
            "title": "Title",
            "website": "Website",
            "overview": "Overview",
            "category": "Category",
            "linkedin": "LinkedIn",
            "email": "Email",
            "phone": "Phone",
            "first_name": "First Name",
            "last_name": "Last Name",
            "joined": "Joined",
            "connected": "Connected",
            "num_employees": "# of Employees",
        }
    )

    df.to_excel(excel_path, index=False, engine="openpyxl")
    print(f"Excel file created successfully at {excel_path}")
    conn.close()


db_path = "founders_linkedin_jobs.db"
excel_path = "founders_all_data.xlsx"
read_db_and_create_excel(db_path, excel_path)
