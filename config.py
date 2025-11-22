"""
Configuration file for the Singapore Work Pass Chatbot
"""
import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4o-mini"  # Using mini for cost efficiency, can upgrade to gpt-4 if needed

# Vector Database Configuration
VECTOR_DB_PATH = "./chroma_db"
COLLECTION_NAME = "singapore_work_passes"

# MOM Website URLs - Official sources for work pass information
MOM_BASE_URL = "https://www.mom.gov.sg"
MOM_PASSES_URL = f"{MOM_BASE_URL}/passes-and-permits"

# Work Pass Categories (Reference - used for display/organization, not enforced in categorization)
# The actual categorization will be flexible based on content analysis
WORK_PASS_CATEGORIES = {
    "professionals_executives": {
        "name": "Professionals & Executives",
        "passes": [
            "Employment Pass (EP)",
            "Personalised Employment Pass (PEP)",
            "EntrePass"
        ]
    },
    "skilled_semi_skilled": {
        "name": "Skilled & Semi-Skilled Workers",
        "passes": [
            "S Pass",
            "Work Permit for Foreign Worker"
        ]
    },
    "domestic_specific": {
        "name": "Domestic & Specific Sectors",
        "passes": [
            "Work Permit for Foreign Domestic Worker (FDW)",
            "Work Permit for Performing Artiste",
            "Work Permit for Confinement Nanny"
        ]
    },
    "students_trainees_dependants": {
        "name": "Students, Trainees, Dependants",
        "passes": [
            "Training Employment Pass",
            "Work Holiday Pass",
            "Dependant's Pass",
            "Long-Term Visit Pass (LTVP)"
        ]
    }
}

# Chunking Configuration for RAG
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

