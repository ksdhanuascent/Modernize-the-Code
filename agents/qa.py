from agents.base_agent import BaseAgent
from config import Config
from core.languages import LanguageRegistry

class QAAgent(BaseAgent):
    def get_effective_system_prompt(self, payload: dict) -> str:
        target_lang = payload.get("target_language", "python")
        return Config.get_qa_prompt(target_lang)

    def get_task_prompt(self, payload: dict) -> str:
        code = payload.get("code", "")
        target_lang = payload.get("target_language", "python")
        t_strat = LanguageRegistry.get(target_lang)

        return (
            f"TASK: Perform rigorous quality assurance and generate executable verification tests in {t_strat.name}.\n"
            f"LANGUAGE: {t_strat.name} ({t_strat.modern_standard})\n\n"
            "REQUIREMENTS:\n"
            "1. Audit the code for syntax, runtime errors, race conditions, type mismatches, and edge-case handling.\n"
            "2. If critical bugs or compile/syntax errors are detected, set 'success': false and specify details in 'error_message'.\n"
            "3. If valid, set 'success': true, provide a 'review' string, and supply at least 3 self-contained, fully executable test cases in 'test_cases'.\n"
            f"4. Each test case must be standalone and directly executable in {t_strat.name} (e.g. self-checking assertions).\n\n"
            f"--- MODERNIZED CODE ({t_strat.name}) ---\n"
            f"{code}\n"
            f"--- END MODERNIZED CODE ---"
        )
