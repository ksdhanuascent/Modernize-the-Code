from core.llm_provider import HybridLLMProvider
from core.protocol import TaskResult, AgentMessage
from agents.base_agent import BaseAgent
from utils.validators import validate_syntax, validate_python_syntax
from config import Config

class ManagerAgent:
    def __init__(self, llm_provider: HybridLLMProvider, agents: dict):
        self.llm = llm_provider
        self.agents = agents
        self.history = []

    def _run_with_self_healing(self, agent_name: str, payload: dict, target_language: str = "python") -> TaskResult:
        """
        Executes an agent with a retry loop.
        If the agent returns syntax/compiler errors or invalid JSON, it injects diagnostics
        and commands self-healing until code is verified.
        """
        agent = self.agents[agent_name]
        last_result = None
        retry_count = 0
        lang = payload.get("target_language", target_language)
        
        while retry_count <= Config.MAX_RETRIES:
            # If retrying, construct context with previous errors
            retry_context = None
            if last_result and not last_result.success:
                err_details = []
                if last_result.syntax_errors:
                    err_details.append(f"Syntax/Compiler Diagnostics: {'; '.join(last_result.syntax_errors)}")
                if last_result.error_message:
                    err_details.append(f"Error Message: {last_result.error_message}")
                retry_context = " | ".join(err_details) if err_details else "Previous attempt produced invalid format."

            # Execute Agent
            result = agent.execute(payload, retry_context)
            self.history.append(result)
            
            # --- DEBUGGING: Print detailed error immediately ---
            if not result.success:
                print(f"\n--- ❌ AGENT FAILURE ({agent_name}) - Attempt {retry_count + 1} ---")
                print(f"Error Message: {result.error_message}")
                if result.syntax_errors:
                    print(f"Syntax Errors: {result.syntax_errors}")
                if result.data and 'raw_response' in result.data:
                    print(f"Raw Output Preview: {str(result.data['raw_response'])[:300]}")
                print(f"-------------------------------------------\n")
            
            # --- HEALING CHECK ---
            # 1. Check explicit 'success: false' in agent response
            if not result.success:
                last_result = result
                retry_count += 1
                continue
            
            # 2. Pluggable Syntax & Compiler Verification (if code exists)
            code_to_check = result.data.get("code")
            if code_to_check:
                is_valid, syntax_errors = validate_syntax(code_to_check, language=lang)
                if not is_valid:
                    result.success = False
                    result.syntax_errors = syntax_errors
                    result.error_message = f"Validation failed with {len(syntax_errors)} syntax/compiler error(s)."
                    last_result = result
                    retry_count += 1
                    continue
            
            # Successfully passed validation
            return result

        # Max retries reached
        return TaskResult(
            success=False,
            error_message=f"CRITICAL: Agent {agent_name} failed after {Config.MAX_RETRIES} retries. Last Error: {last_result.error_message if last_result else 'Unknown'}",
            syntax_errors=last_result.syntax_errors if last_result else [],
            data=last_result.data if last_result else {},
            sender="Manager",
            language=lang
        )

    def orchestrate_refactoring(
        self,
        legacy_code: str,
        source_language: str = "python",
        target_language: str = "python"
    ) -> dict:
        """Main pipeline workflow across arbitrary language pairs."""
        
        # Step 1: Architect
        print(f"[Manager] Dispatching Architect ({source_language} -> {target_language})...")
        arch_payload = {
            "legacy_code": legacy_code,
            "source_language": source_language,
            "target_language": target_language
        }
        arch_result = self._run_with_self_healing("architect", arch_payload, target_language=target_language)
        
        if not arch_result.success:
            return {"status": "failed_at_architect", "result": arch_result}
        
        # Step 2: Builder
        print(f"[Manager] Dispatching Builder ({target_language})...")
        builder_payload = {
            "legacy_code": legacy_code,
            "plan": arch_result.data.get("plan", ""),
            "source_language": source_language,
            "target_language": target_language
        }
        build_result = self._run_with_self_healing("builder", builder_payload, target_language=target_language)
        
        if not build_result.success:
            return {"status": "failed_at_builder", "result": build_result}
            
        modernized_code = build_result.data.get("code")

        # Step 3: QA
        print(f"[Manager] Dispatching QA ({target_language})...")
        qa_payload = {
            "code": modernized_code,
            "source_language": source_language,
            "target_language": target_language
        }
        qa_result = self._run_with_self_healing("qa", qa_payload, target_language=target_language)
        
        if not qa_result.success:
            return {"status": "failed_at_qa", "result": qa_result}

        # Step 4: Librarian
        print(f"[Manager] Dispatching Librarian ({target_language})...")
        librarian_payload = {
            "code": modernized_code,
            "source_language": source_language,
            "target_language": target_language
        }
        doc_result = self._run_with_self_healing("librarian", librarian_payload, target_language=target_language)

        return {
            "status": "success",
            "source_language": source_language,
            "target_language": target_language,
            "modernized_code": modernized_code,
            "documentation": doc_result.data,
            "qa_report": qa_result.data
        }
