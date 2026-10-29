from agents.base_agent import BaseAgent
from config import Config
from core.languages import LanguageRegistry

class LibrarianAgent(BaseAgent):
    def get_effective_system_prompt(self, payload: dict) -> str:
        target_lang = payload.get("target_language", "python")
        return Config.get_librarian_prompt(target_lang)

    def get_task_prompt(self, payload: dict) -> str:
        code = payload.get("code", "")
        source_lang = payload.get("source_language", "python")
        target_lang = payload.get("target_language", "python")

        t_strat = LanguageRegistry.get(target_lang)
        s_strat = LanguageRegistry.get(source_lang)

        return (
            f"TASK: Generate production-ready technical Markdown documentation for the modernized {t_strat.name} code.\n"
            f"TRANSITION: {s_strat.name} -> {t_strat.name} ({t_strat.modern_standard})\n\n"
            "REQUIREMENTS:\n"
            "1. Architectural overview and design principles.\n"
            "2. Detailed API reference: classes, methods, parameters, return types, exceptions.\n"
            f"3. Full runnable usage snippet in {t_strat.name}.\n"
            "4. Key modernization and cross-language translation highlights.\n\n"
            f"--- CODE ({t_strat.name}) ---\n"
            f"{code}\n"
            f"--- END CODE ---"
        )
