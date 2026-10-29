from agents.base_agent import BaseAgent
from config import Config
from core.languages import LanguageRegistry

class BuilderAgent(BaseAgent):
    def get_effective_system_prompt(self, payload: dict) -> str:
        source_lang = payload.get("source_language", "python")
        target_lang = payload.get("target_language", "python")
        return Config.get_builder_prompt(source_lang, target_lang)

    def get_task_prompt(self, payload: dict) -> str:
        legacy_code = payload.get("legacy_code", "")
        plan = payload.get("plan", "")
        source_lang = payload.get("source_language", "python")
        target_lang = payload.get("target_language", "python")

        t_strat = LanguageRegistry.get(target_lang)
        s_strat = LanguageRegistry.get(source_lang)

        return (
            f"TASK: Generate the complete, modernized source code in {t_strat.name} ({t_strat.modern_standard}).\n"
            f"SOURCE LANGUAGE: {s_strat.name}\n"
            f"TARGET LANGUAGE: {t_strat.name}\n\n"
            f"ARCHITECTURAL MODERNIZATION PLAN:\n{plan}\n\n"
            "STRICT RULES:\n"
            "1. NO OMISSIONS: You must output the entire functional code. Never write '// TODO', '# TODO', '...', or omit bodies.\n"
            "2. RUNNABLE ENTRYPOINT: Ensure the code has a runnable entrypoint so it compiles/runs standalone.\n"
            f"{t_strat.entrypoint_template}\n"
            "3. RETURN JSON: Output ONLY a JSON object with 'success': true, and 'data': {'code': '<full source string>'}.\n\n"
            f"--- ORIGINAL SOURCE CODE ({s_strat.name}) ---\n"
            f"{legacy_code}\n"
            f"--- END ORIGINAL SOURCE CODE ---"
        )
