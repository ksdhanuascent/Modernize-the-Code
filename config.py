import os
from dotenv import load_dotenv
from core.languages import LanguageRegistry

load_dotenv()

class Config:
    # --- Project Metadata ---
    PROJECT_NAME = "Modernize the Code"
    PROJECT_ACRONYM = "MTC"

    # --- Model Configuration ---
    LOCAL_MODEL_NAME = "qwen2.5-coder:3b"
    FALLBACK_MODEL_NAME = "gemini-3-flash-preview"
    
    # --- API Keys ---
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # --- Agent System Settings ---
    MAX_RETRIES = 3
    TEMPERATURE = 0.2 
    
    # --- Default System Prompts (Python-to-Python Defaults) ---
    ARCHITECT_SYSTEM_PROMPT = (
        "You are a Senior Software Architect. Analyze the legacy code and modernize it. "
        "You MUST respond with a valid JSON object. "
        "CRITICAL: Use DOUBLE QUOTES (\") for all keys and string values. "
        "Format: {\"success\": true, \"data\": {\"plan\": \"Your detailed text plan here\"}}"
    )
    
    BUILDER_SYSTEM_PROMPT = (
        "You are an Expert Polyglot Developer. Translate or modernize the code into production-ready code. "
        "CRITICAL: Use DOUBLE QUOTES (\") for all keys and strings in your JSON response. "
        "Format: {\"success\": true, \"data\": {\"code\": \"...\"}}"
    )
    
    QA_SYSTEM_PROMPT = (
        "You are a QA Engineer. Review the code and generate tests. "
        "CRITICAL: Use DOUBLE QUOTES (\") for all keys and strings in your JSON response. "
        "Format: {\"success\": true, \"data\": {\"review\": \"...\", \"test_cases\": [{\"name\": \"Test 1\", \"code\": \"...\"}]}}"
    )
    
    LIBRARIAN_SYSTEM_PROMPT = (
        "You are a Technical Writer. Generate markdown documentation. "
        "CRITICAL: Use DOUBLE QUOTES (\") for all keys and strings in your JSON response. "
        "Format: {\"success\": true, \"data\": {\"documentation\": \"# Title\\nContent\"}}"
    )

    @staticmethod
    def get_architect_prompt(source_lang: str = "python", target_lang: str = "python") -> str:
        s_strat = LanguageRegistry.get(source_lang)
        t_strat = LanguageRegistry.get(target_lang)
        return t_strat.get_architect_prompt(s_strat)

    @staticmethod
    def get_builder_prompt(source_lang: str = "python", target_lang: str = "python") -> str:
        s_strat = LanguageRegistry.get(source_lang)
        t_strat = LanguageRegistry.get(target_lang)
        return t_strat.get_builder_prompt(s_strat)

    @staticmethod
    def get_qa_prompt(target_lang: str = "python") -> str:
        t_strat = LanguageRegistry.get(target_lang)
        return t_strat.get_qa_prompt()

    @staticmethod
    def get_librarian_prompt(target_lang: str = "python") -> str:
        t_strat = LanguageRegistry.get(target_lang)
        return t_strat.get_librarian_prompt()
