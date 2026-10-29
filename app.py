import streamlit as st
import sys
import os
import time
import json
import socket
from datetime import datetime

# Add the root directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Architecture Core Imports
from core.llm_provider import HybridLLMProvider
from core.model_manager import ModelManager
from core.protocol import TaskResult
from core.languages import LanguageRegistry
from core.executor import execute_code
from agents.manager import ManagerAgent
from agents.architect import ArchitectAgent
from agents.builder import BuilderAgent
from agents.qa import QAAgent
from agents.librarian import LibrarianAgent
from config import Config

# --- Page Config ---
st.set_page_config(
    page_title="Modernize the Code (MTC)",
    page_icon="⚡",
    layout="wide"
)

# --- CSS Styling ---
st.markdown("""
<style>
    .stButton>button { color: white; background-color: #2E7D32; border-radius: 6px; font-weight: 600; width: 100%; }
    .stButton>button[kind="secondary"] { background-color: #C62828; width: 100%; }
    .badge-pill {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 8px;
    }
</style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
defaults = {
    'mode': None,
    'ollama_running': False,
    'qwen_available': False,
    'api_key': "",
    'pipeline_run': False,
    'manager': None,
    'legacy_code': "",
    'source_lang': "python",
    'target_lang': "java",
    'final_result': None
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# --- Helpers ---
def check_ollama_server():
    try:
        sock = socket.create_connection(("127.0.0.1", 11434), timeout=2)
        sock.close()
        return True
    except:
        return False

def generate_report(history, final_result, source_lang: str, target_lang: str):
    s_strat = LanguageRegistry.get(source_lang)
    t_strat = LanguageRegistry.get(target_lang)
    
    report = (
        f"# Cross-Language Modernization & Migration Report\n"
        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"**Source Language:** {s_strat.name}\n"
        f"**Target Language:** {t_strat.name} ({t_strat.modern_standard})\n\n"
    )

    # Architect Plan
    plan_text = "No plan recorded."
    for item in history:
        if item.sender == "Architect" and item.data:
            plan_text = item.data.get("plan") or str(item.data)
            break
    report += f"## 1. Architectural Modernization Plan\n{plan_text}\n\n"

    # Modernized Code
    code = final_result.get("modernized_code", "")
    report += f"## 2. Modernized Source Code ({t_strat.name})\n```{t_strat.syntax_label}\n{code}\n```\n\n"

    # QA Review
    qa_data = final_result.get("qa_report", {})
    review = qa_data.get("review", "No formal review.")
    report += f"## 3. QA Security & Verification Audit\n**Audit Summary:** {review}\n\n"

    tests = qa_data.get("test_cases", [])
    if tests:
        report += f"### Executable Test Suite ({t_strat.name})\n"
        for t in tests:
            report += f"#### {t.get('name', 'Test Case')}\n```{t_strat.syntax_label}\n{t.get('code', '')}\n```\n\n"

    # Documentation
    doc_data = final_result.get('documentation', {})
    if not isinstance(doc_data, dict):
        doc_data = {}
    doc_text = doc_data.get("documentation", "No documentation provided.")
    report += f"## 4. Technical Documentation\n{doc_text}\n"

    return report


# --- Header ---
st.title("⚡ Modernize the Code (MTC)")
st.caption("MTC: Polyglot Multi-Agent Architecture featuring Dynamic Language Strategy, Pluggable Validation & Execution")
st.markdown("---")

# --- Step 1: Mode Selection ---
if st.session_state.mode is None:
    st.subheader("Step 1: Select AI Execution Mode")
    c1, c2 = st.columns(2)
    if c1.button("🖥️ Local AI Engine (Ollama - Qwen2.5-Coder)", use_container_width=True):
        st.session_state.mode = 'local'
        st.rerun()
    if c2.button("☁️ Cloud AI Engine (Google Gemini)", use_container_width=True):
        st.session_state.mode = 'cloud'
        st.rerun()

# --- LOCAL MODE CONFIG ---
elif st.session_state.mode == 'local':
    st.sidebar.header("⚙️ Local AI Engine")
    if not st.session_state.ollama_running:
        st.info("🔍 Probing Ollama runtime on Port 11434...")
        if check_ollama_server():
            st.session_state.ollama_running = True
            st.sidebar.success("✅ Ollama Daemon Connected")
            st.rerun()
        else:
            st.error("❌ Ollama server not detected.")
            st.markdown("1. Open terminal.\n2. Execute: `ollama serve`\n3. Click below to verify.")
            if st.button("🔄 Verify Ollama Connection"):
                st.rerun()
            st.stop()

    if not st.session_state.qwen_available:
        st.sidebar.success("✅ Ollama Daemon Connected")
        if ModelManager.check_model_availability(Config.LOCAL_MODEL_NAME):
            st.session_state.qwen_available = True
            st.success(f"✅ Local Model `{Config.LOCAL_MODEL_NAME}` Ready")
            st.rerun()
        else:
            st.warning(f"⚠️ Model `{Config.LOCAL_MODEL_NAME}` missing from local registry.")
            if st.button(f"⬇️ Download {Config.LOCAL_MODEL_NAME}", type="primary"):
                with st.spinner(f"Pulling {Config.LOCAL_MODEL_NAME}..."):
                    success, msg = ModelManager.pull_model(Config.LOCAL_MODEL_NAME)
                    if success:
                        st.session_state.qwen_available = True
                        st.success("Model downloaded successfully!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(msg)
                        if st.button("🔄 Retry"):
                            st.rerun()
            st.stop()
    st.sidebar.success(f"✅ Engine Ready ({Config.LOCAL_MODEL_NAME})")

# --- CLOUD MODE CONFIG ---
elif st.session_state.mode == 'cloud':
    st.sidebar.header("☁️ Cloud AI Configuration")
    env_key = os.environ.get("GEMINI_API_KEY", "")
    if not st.session_state.api_key and not env_key:
        k = st.text_input("Enter Gemini API Key:", type="password")
        if st.button("Authenticate API"):
            if k.strip():
                st.session_state.api_key = k.strip()
                os.environ["GEMINI_API_KEY"] = k.strip()
                st.success("Authenticated.")
                st.rerun()
            else:
                st.warning("Please supply a valid key.")
        st.stop()
    else:
        if not st.session_state.api_key and env_key:
            st.session_state.api_key = env_key
        st.sidebar.success(f"✅ Gemini Cloud Model Ready ({Config.FALLBACK_MODEL_NAME})")


# --- Step 2: Language Matrix & Source Code Input ---
if (st.session_state.mode == 'local' and st.session_state.qwen_available) or \
   (st.session_state.mode == 'cloud' and st.session_state.api_key):

    st.subheader("Step 2: Dynamic Language Strategy & Input")
    
    # Language Selection Matrix
    supported_langs = LanguageRegistry.list_supported()
    l_col1, l_col2, l_col3 = st.columns([2, 2, 3])
    
    with l_col1:
        source_lang_choice = st.selectbox(
            "Source Language",
            options=supported_langs,
            index=supported_langs.index(st.session_state.source_lang) if st.session_state.source_lang in supported_langs else 0,
            format_func=lambda x: LanguageRegistry.get(x).name
        )
        st.session_state.source_lang = source_lang_choice

    with l_col2:
        target_lang_choice = st.selectbox(
            "Target Language",
            options=supported_langs,
            index=supported_langs.index(st.session_state.target_lang) if st.session_state.target_lang in supported_langs else 1,
            format_func=lambda x: f"{LanguageRegistry.get(x).name} ({LanguageRegistry.get(x).modern_standard})"
        )
        st.session_state.target_lang = target_lang_choice

    with l_col3:
        s_obj = LanguageRegistry.get(source_lang_choice)
        t_obj = LanguageRegistry.get(target_lang_choice)
        if s_obj.id == t_obj.id:
            st.info(f"🔄 **Modernization Mode:** Refactoring legacy `{s_obj.name}` into production-standard `{t_obj.modern_standard}`.")
        else:
            st.info(f"🌐 **Cross-Language Translation:** Migrating `{s_obj.name}` codebase directly into modern `{t_obj.name}` ({t_obj.modern_standard}).")

    # Code Input
    legacy_code = st.text_area(
        f"Paste Source Code ({s_obj.name}):",
        height=220,
        placeholder=f"Paste your legacy or source {s_obj.name} code here..."
    )

    # Launch Pipeline
    if st.button("🚀 Execute Modernization Pipeline", type="primary", use_container_width=True):
        if not legacy_code.strip():
            st.warning("Please supply source code before running the pipeline.")
        else:
            st.session_state.legacy_code = legacy_code
            llm_provider = HybridLLMProvider(force_mode=st.session_state.mode)

            # Initialize Polyglot Agents
            agents = {
                "architect": ArchitectAgent(llm_provider, "Architect"),
                "builder": BuilderAgent(llm_provider, "Builder"),
                "qa": QAAgent(llm_provider, "QA"),
                "librarian": LibrarianAgent(llm_provider, "Librarian")
            }
            manager = ManagerAgent(llm_provider, agents)

            with st.status("Executing Multi-Agent Modernization Pipeline...", expanded=True) as status:
                
                # 1. Architect Agent
                status.update(label=f"🏗️ Architect: Formulating blueprint ({s_obj.name} ➔ {t_obj.name})...", state="running")
                arch_payload = {
                    "legacy_code": legacy_code,
                    "source_language": source_lang_choice,
                    "target_language": target_lang_choice
                }
                arch_result = manager._run_with_self_healing("architect", arch_payload, target_language=target_lang_choice)

                if not arch_result.success:
                    status.update(label="❌ Architect Failed", state="error")
                    st.error("Architectural Analysis Aborted.")
                    st.markdown(f"**Diagnostic Error:** {arch_result.error_message}")
                    if arch_result.data and "raw_response" in arch_result.data:
                        st.text_area("Raw AI Payload", arch_result.data["raw_response"], height=180)
                    st.stop()
                status.update(label="✅ Architect: Roadmap Engineered", state="complete", expanded=False)

                # 2. Builder Agent
                status.update(label=f"🔨 Builder: Synthesizing Modernized {t_obj.name}...", state="running")
                plan = arch_result.data.get("plan", "Modernize code.")
                builder_payload = {
                    "legacy_code": legacy_code,
                    "plan": plan,
                    "source_language": source_lang_choice,
                    "target_language": target_lang_choice
                }
                build_result = manager._run_with_self_healing("builder", builder_payload, target_language=target_lang_choice)

                if not build_result.success:
                    status.update(label="❌ Builder Failed", state="error")
                    st.error("Code Modernization Failed.")
                    st.markdown(f"**Diagnostic Error:** {build_result.error_message}")
                    if build_result.syntax_errors:
                        st.error("Compiler/Syntax Errors:\n" + "\n".join(build_result.syntax_errors))
                    if build_result.data and "raw_response" in build_result.data:
                        st.text_area("Raw AI Output", build_result.data["raw_response"], height=180)
                    st.stop()
                
                modern_code = build_result.data.get("code", "")
                status.update(label=f"✅ Builder: {t_obj.name} Code Verified & Synthesized", state="complete", expanded=False)

                # 3. QA Agent
                status.update(label=f"🛡️ QA: Validating Logic & Compiling Test Suite ({t_obj.name})...", state="running")
                qa_payload = {
                    "code": modern_code,
                    "source_language": source_lang_choice,
                    "target_language": target_lang_choice
                }
                qa_result = manager._run_with_self_healing("qa", qa_payload, target_language=target_lang_choice)
                if not qa_result.success:
                    status.update(label="⚠️ QA: Discrepancies Flagged", state="running")
                else:
                    status.update(label="✅ QA: Verification Passed", state="complete", expanded=False)

                # 4. Librarian Agent
                status.update(label=f"📚 Librarian: Writing {t_obj.name} Documentation...", state="running")
                lib_payload = {
                    "code": modern_code,
                    "source_language": source_lang_choice,
                    "target_language": target_lang_choice
                }
                doc_result = manager._run_with_self_healing("librarian", lib_payload, target_language=target_lang_choice)
                final_doc_data = doc_result.data if isinstance(doc_result.data, dict) else {}
                status.update(label="✅ Librarian: Complete Technical Docs Ready", state="complete")

            # Store in Session State
            st.session_state.final_result = {
                "status": "success",
                "source_language": source_lang_choice,
                "target_language": target_lang_choice,
                "modernized_code": modern_code,
                "documentation": final_doc_data,
                "qa_report": qa_result.data
            }
            st.session_state.manager = manager
            st.session_state.pipeline_run = True
            st.rerun()

    # --- Step 3: Interactive Results Dashboard ---
    if st.session_state.pipeline_run and st.session_state.final_result:
        result = st.session_state.final_result
        source_lang = result.get("source_language", st.session_state.source_lang)
        target_lang = result.get("target_language", st.session_state.target_lang)
        s_strat = LanguageRegistry.get(source_lang)
        t_strat = LanguageRegistry.get(target_lang)

        modern_code = result.get('modernized_code', '')
        original_code = st.session_state.legacy_code

        # 1. Architectural Plan
        st.header("🏗️ Architect's Roadmap")
        plan_text = "No architectural record available."
        if st.session_state.manager:
            for h in st.session_state.manager.history:
                if h.sender == "Architect" and h.data:
                    plan_text = h.data.get("plan") or str(h.data)
                    break
        st.info(plan_text)
        st.markdown("---")

        # 2. Side-by-Side Code Execution & Comparison
        st.header("💻 Code Comparison & Pluggable Execution")
        col1, col2 = st.columns(2)

        with col1:
            st.subheader(f"Original Code ({s_strat.name})")
            st.code(original_code, language=s_strat.syntax_label, line_numbers=True)
            if st.button(f"▶️ Run Original Code ({s_strat.name})", key="run_orig"):
                with st.spinner(f"Executing in {s_strat.name} runtime..."):
                    out, err, exc = execute_code(original_code, language=s_strat.id)
                    if exc:
                        st.error(exc)
                    if err:
                        st.warning("Runtime / Compiler Diagnostics:")
                        st.code(err, language="text")
                    if out:
                        st.success("Execution Output:")
                        st.code(out, language="text")

        with col2:
            st.subheader(f"Modernized Code ({t_strat.name} - {t_strat.modern_standard})")
            st.code(modern_code, language=t_strat.syntax_label, line_numbers=True)
            if st.button(f"▶️ Run Modernized Code ({t_strat.name})", key="run_mod"):
                with st.spinner(f"Compiling & Executing in {t_strat.name} runtime..."):
                    out, err, exc = execute_code(modern_code, language=t_strat.id)
                    if exc:
                        st.error(exc)
                    if err:
                        st.warning("Runtime / Compiler Diagnostics:")
                        st.code(err, language="text")
                    if out:
                        st.success("Execution Output:")
                        st.code(out, language="text")

        st.markdown("---")

        # 3. QA Analysis & Generated Test Suite
        st.header(f"🛡️ QA Analysis & {t_strat.name} Test Suite")
        qa_data = result.get('qa_report', {})
        st.info(f"**Security & Logic Review:** {qa_data.get('review', 'No audit review.')}")

        test_cases = qa_data.get('test_cases', [])
        if test_cases:
            st.markdown(f"### 🧪 Generated Standalone Test Cases ({t_strat.name})")
            for i, t in enumerate(test_cases):
                test_title = t.get('name', f'Test Case {i+1}')
                with st.expander(f"Test {i+1}: {test_title}", expanded=False):
                    code_snippet = t.get('code', '')
                    st.code(code_snippet, language=t_strat.syntax_label)
                    if st.button(f"Run Test {i+1}", key=f"test_run_{i}"):
                        with st.spinner(f"Executing Test {i+1} via {t_strat.name} executor..."):
                            out, err, exc = execute_code(code_snippet, language=t_strat.id)
                            if exc:
                                st.error(exc)
                            if err:
                                st.warning("Test Diagnostics:")
                                st.code(err, language="text")
                            if out:
                                st.success("Test Passed / Output:")
                                st.code(out, language="text")
        else:
            st.warning("No automated test cases returned by QA Agent.")

        st.markdown("---")

        # 4. Documentation
        st.header("📚 Technical Documentation")
        doc_data = result.get('documentation')
        if doc_data and isinstance(doc_data, dict):
            doc_text = doc_data.get('documentation', 'No documentation available.')
            st.markdown(doc_text)
        else:
            st.markdown("*No documentation generated.*")

        st.markdown("---")

        # 5. Export Report & Reset
        st.header("📥 Export & Reset")
        e_col1, e_col2 = st.columns(2)
        with e_col1:
            report_md = generate_report(
                st.session_state.manager.history if st.session_state.manager else [],
                result,
                source_lang,
                target_lang
            )
            st.download_button(
                "⬇️ Download Full Migration Report (.md)",
                report_md,
                file_name=f"migration_report_{source_lang}_to_{target_lang}.md",
                mime="text/markdown",
                use_container_width=True
            )
        with e_col2:
            if st.button("🔄 Modernize Another Script", use_container_width=True):
                st.session_state.pipeline_run = False
                st.session_state.final_result = None
                st.rerun()
