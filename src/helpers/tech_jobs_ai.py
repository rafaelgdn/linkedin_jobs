from langchain.schema import StrOutputParser
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate


def is_tech_job_ai(title):
    llm = OllamaLLM(model="llama3.1")
    prompt = PromptTemplate(input_variables=["prompt"], template="{prompt}")
    chain = prompt | llm | StrOutputParser()

    prompt = f"""
    Analyze this job title: "{title}"

    Instructions:
    1. First, check for non-tech keywords. If ANY of these are present (case-insensitive), return "False":
        Sales, Marketing, Finance, Accountant, HR, Investment, Operations, Supply, Logistics, Customer, Retail, Hospitality, Healthcare, Education, Legal, "Real Estate", Construction, Accelerator, Lead, Responder, Account

    2. If step 1 doesn't apply, check for tech keywords. If ANY of these are present (case-insensitive), return "True":
        Software, Data, IT, "Machine Learning", AI, Cybersecurity, Cloud, DevOps, Database, Developer, Programmer, Coder, Designer, "Tech Manager", "Support Engineer", "Systems Engineer", "Network Engineer", "UI/UX", "Front-end", "Back-end", "Full-stack", "QA", "Test Engineer", "Automation Engineer", "Embedded Systems", "Firmware Engineer", "Hardware Engineer", "Systems Administrator", "Network Administrator", "Security Analyst", "Penetration Tester", "Ethical Hacker", "Cloud Engineer", "Data Engineer", "Data Architect", "Data Analyst", "Data Scientist", "Data Engineer", "Data Analyst", "Data Scientist", "Big Data", "Data Warehouse", "Data Mining", "Data Visualization", "Data Modeling", "Data Governance", "Data Privacy", "Data Protection", "Data Security", "Data Compliance", "Data Governance", "Data Privacy", "Data Protection", "Data Security", "Data Compliance", "Software Engineer", "Software Developer", "Software Architect", "Software Quality Assurance", "Software Test Engineer", "Software Project Manager", "Software Product Manager", "Software Consultant", "Software Analyst", "Software Tester", "Software Developer in Test", "Software Quality Assurance Engineer", "Software Quality Assurance Analyst", "Software Quality Assurance Tester", "Software Quality Assurance Specialist", "Software Quality Assurance Manager", "Software Quality Assurance Lead", "Software Quality Assurance Engineer in Test", "Software Quality Assurance Analyst in Test", "Software Quality Assurance Tester in Test", "Software Quality Assurance Specialist in Test", "Software Quality Assurance Manager in Test", "Software Quality Assurance Lead in Test"

    3. If neither step 1 nor 2 applies, return "False".

    Respond ONLY with "True" or "False". No other text.
    """

    response = chain.invoke(prompt)
    return response.strip().lower() == "true"
