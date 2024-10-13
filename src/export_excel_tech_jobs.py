import sqlite3
import pandas as pd
import json


def create_jobs_spreadsheet(db_path, output_excel_path):
    # Conectar ao banco de dados
    conn = sqlite3.connect(db_path)

    # Ler os dados da tabela founders
    query = "SELECT linkedin, company, tech_jobs FROM founders"
    df = pd.read_sql_query(query, conn)

    # Função para extrair jobs de uma string JSON
    def extract_jobs(jobs_json):
        try:
            jobs = json.loads(jobs_json)
            return jobs if isinstance(jobs, list) else []
        except json.JSONDecodeError:
            return []

    # Lista para armazenar os dados processados
    processed_data = []

    previous_linkedin = None

    # Processar cada linha do DataFrame
    for _, row in df.iterrows():
        linkedin = row["linkedin"]
        company = row["company"]
        jobs = extract_jobs(row["tech_jobs"])

        if jobs:
            if previous_linkedin is not None and linkedin != previous_linkedin:
                processed_data.append({"LinkedIn": "", "Company": "", "Job Title": "", "Job URL": ""})
                processed_data.append({"LinkedIn": "", "Company": "", "Job Title": "", "Job URL": ""})

            for job in jobs:
                processed_data.append({"LinkedIn": linkedin, "Company": company, "Job Title": job.get("title", ""), "Job URL": job.get("url", "")})

            previous_linkedin = linkedin

    # Criar um novo DataFrame com os dados processados
    new_df = pd.DataFrame(processed_data)

    # Salvar o novo DataFrame como um arquivo Excel
    new_df.to_excel(output_excel_path, index=False)

    print(f"Nova planilha criada em: {output_excel_path}")

    # Fechar a conexão com o banco de dados
    conn.close()


# Exemplo de uso
db_path = "founders_linkedin_jobs.db"
output_excel_path = "founders_tech_jobs.xlsx"
create_jobs_spreadsheet(db_path, output_excel_path)
