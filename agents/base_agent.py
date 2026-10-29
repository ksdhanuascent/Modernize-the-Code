import json
import re
import ast
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from core.llm_provider import HybridLLMProvider
from core.protocol import TaskResult

class BaseAgent(ABC):
    def __init__(self, llm_provider: HybridLLMProvider, name: str, system_prompt: str = ""):
        self.llm_provider = llm_provider
        self.name = name
        self.system_prompt = system_prompt

    @abstractmethod
    def get_task_prompt(self, payload: dict) -> str:
        """Constructs the specific prompt for this agent based on the payload."""
        pass

    def get_effective_system_prompt(self, payload: dict) -> str:
        """Allows agents to supply a dynamic system prompt based on payload."""
        return self.system_prompt

    def _extract_json_substring(self, text: str) -> Optional[str]:
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            return text[first_brace : last_brace + 1]
        return None

    def execute(self, payload: dict, retry_context: str = None) -> TaskResult:
        user_prompt = self.get_task_prompt(payload)
        base_sys = self.get_effective_system_prompt(payload)
        target_lang = payload.get("target_language", "python")

        full_system_prompt = (
            f"{base_sys}\n\n"
            "STRICT RESPONSE INSTRUCTIONS:\n"
            "1. Output ONLY a valid, parseable JSON object.\n"
            "2. Use DOUBLE QUOTES (\") for all keys and strings.\n"
            "3. Do not include markdown wraps (no ```json ... ```). Output the raw JSON text directly.\n"
            "4. Required root keys: 'success' (boolean), 'data' (object). Optional: 'error_message' (string)."
        )

        if retry_context:
            user_prompt = (
                f"{user_prompt}\n\n"
                f"[RETRY CONTEXT - CORRECT THE FOLLOWING VALIDATION ERRORS]\n"
                f"{retry_context}\n"
                "Ensure full compliance with language syntax, zero placeholders, and strict JSON output."
            )

        # 2. Call LLM
        try:
            raw_response = self.llm_provider.generate(user_prompt, full_system_prompt)
        except Exception as e:
            return TaskResult(
                success=False,
                error_message=f"LLM Connection failed: {str(e)}",
                sender=self.name,
                language=target_lang
            )

        # 3. Parse Response
        clean_response = raw_response.strip()
        if "```json" in clean_response:
            clean_response = clean_response.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_response:
            clean_response = clean_response.split("```")[1].split("```")[0].strip()

        data_dict = None
        # Attempt 1: direct json parse
        try:
            data_dict = json.loads(clean_response)
        except json.JSONDecodeError:
            pass

        # Attempt 2: bounded substring json parse
        if not data_dict:
            substr = self._extract_json_substring(clean_response)
            if substr:
                try:
                    data_dict = json.loads(substr)
                except json.JSONDecodeError:
                    pass

        # Attempt 3: AST literal eval fallback (e.g. single quoted dicts)
        if not data_dict:
            candidate = substr if substr else clean_response
            try:
                data_dict = ast.literal_eval(candidate)
            except Exception:
                pass

        if not isinstance(data_dict, dict):
            return TaskResult(
                success=False,
                error_message="Agent output could not be parsed as valid JSON or dictionary structure.",
                data={"raw_response": raw_response},
                sender=self.name,
                language=target_lang
            )

        is_successful = data_dict.get("success", True)
        return TaskResult(
            success=is_successful,
            data=data_dict.get("data", {}),
            error_message=data_dict.get("error_message"),
            syntax_errors=data_dict.get("syntax_errors", []),
            sender=self.name,
            language=target_lang
        )
