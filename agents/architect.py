from agents.base_agent import BaseAgent
from config import Config
from core.languages import LanguageRegistry

class ArchitectAgent(BaseAgent):
    def get_effective_system_prompt(self, payload: dict) -> str:
        source_lang = payload.get("source_language", "python")
        target_lang = payload.get("target_language", "python")
        return Config.get_architect_prompt(source_lang, target_lang)

    def get_task_prompt(self, payload: dict) -> str:
        code = payload.get("legacy_code", "")
        source_lang = payload.get("source_language", "python")
        target_lang = payload.get("target_language", "python")

        s_name = LanguageRegistry.get(source_lang).name
        t_name = LanguageRegistry.get(target_lang).name

        return (
            f"TASK: Conduct a comprehensive architectural analysis and construct a modernization/translation roadmap.\n"
            f"SOURCE LANGUAGE: {s_name}\n"
            f"TARGET LANGUAGE: {t_name}\n\n"
            "REQUIREMENTS:\n"
            "1. Deconstruct the existing code architecture, classes, functions, and control flow.\n"
            "2. Identify anti-patterns, legacy constructs, performance bottlenecks, and potential bugs.\n"
            f"3. Detail the exact mapping from {s_name} data types and idioms to modern {t_name} idioms.\n"
            "4. Define a clear implementation roadmap for the Builder Agent.\n\n"
            f"--- SOURCE CODE ({s_name}) ---\n"
            f"{code}\n"
            f"--- END SOURCE CODE ---"
        )
