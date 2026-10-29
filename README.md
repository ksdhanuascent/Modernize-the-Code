<div align="center">
  <h1>⚡ Modernize the Code (MTC)</h1>
  <p><strong>Multi-Agent Cross-Language Modernization & Migration Architecture with Local & Cloud LLMs</strong></p>
  
  [![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
  [![Java](https://img.shields.io/badge/Java-21%20LTS-orange.svg)](https://www.oracle.com/java/)
  [![Streamlit](https://img.shields.io/badge/Streamlit-1.29.0+-red.svg)](https://streamlit.io/)
  [![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-black.svg)](https://ollama.ai/)
  [![Google Gemini](https://img.shields.io/badge/Google_Gemini-Cloud_AI-blue.svg)](https://ai.google.dev/)
</div>

---

## 📖 Overview

**Modernize the Code (MTC)** is an intelligent, multi-agent AI system engineered to automatically analyze, refactor, translate, test, and document code across language boundaries (e.g., Python ➔ Java, Java ➔ Python, Legacy Python ➔ Modern Python 3.11+, Legacy Java ➔ Modern Java 21 LTS). Built around an Agent-to-Agent (A2A) paradigm, it uses specialized AI agents that collaborate sequentially, implementing self-healing workflows backed by native compiler diagnostics (`javac` and `ast`) to guarantee zero-hallucination, syntactically valid, production-grade code.

The system natively operates using local LLMs (via **Ollama**) for data privacy and offline capability, with seamless fallback capabilities to cloud-based models (via **Google Gemini**) for rapid experimentation.

---

## ✨ Three Core Architectural Layers

1. **Dynamic Language Strategy Layer (`core/languages.py`)**:
   - Modular language matrix decoupling language idioms, syntax rules, and anti-hallucination directives from prompts.
   - Enforces 100% implementation completion (zero `// TODO` or `pass` placeholders) and idiomatic target standards.
   - First-class support for **Python (3.11+)** and **Java (21 LTS)**, with simple registry hooks for additional languages.

2. **Pluggable Validator Engine (`core/validators.py`)**:
   - Language-aware validation interface (`BaseSyntaxValidator`).
   - **Python**: Native Abstract Syntax Tree (`ast.parse`) checking with line/column pointers.
   - **Java**: Native JDK `javac` compiler execution (`javac -Xlint:none -d ...`), capturing precise compiler errors and line numbers with zero hallucinations.

3. **Pluggable Execution Engine (`core/executor.py`)**:
   - Sandboxed runtime runner for immediate verification.
   - **Python**: Dynamic execution via `sys.executable`.
   - **Java**: Ephemeral compilation and execution via `javac` & `java`.
   - Returns standardized `ExecutionResult` tuples for both original and modernized code.

---

## 🏗️ Architecture & Workflow

```mermaid
graph TD
    classDef user padding:10px,font-weight:bold,stroke-width:2px;
    classDef core fill:#4CAF50,color:white,stroke:#388E3C,stroke-width:2px;
    classDef agent fill:#2196F3,color:white,stroke:#1976D2,stroke-width:2px;
    classDef llm fill:#FF9800,color:white,stroke:#F57C00,stroke-width:2px;
    classDef validator fill:#E91E63,color:white,stroke:#C2185B,stroke-width:2px;
    classDef executor fill:#9C27B0,color:white,stroke:#7B1FA2,stroke-width:2px;

    User["👤 User (Web Browser)"]:::user -->|Selects Language Pair & Code| UI["🖥️ Streamlit App (app.py)"]:::core
    
    UI -->|Initiates Pipeline| Manager["🧠 Manager Agent"]:::agent
    
    subgraph Multi-Agent System
        Manager -->|1. Request Blueprint| Architect["🏛️ Architect Agent"]:::agent
        Architect -.->|Returns Translation Plan| Manager
        
        Manager -->|2. Modernization Request| Builder["🔨 Builder Agent"]:::agent
        Builder -.->|Returns Modern Code| Manager
        
        Manager -->|3. Validation Request| QA["🛡️ QA Agent"]:::agent
        QA -.->|Returns Test Cases & Review| Manager
        
        Manager -->|4. Documentation Request| Librarian["📚 Librarian Agent"]:::agent
        Librarian -.->|Returns Markdown Docs| Manager
        
        Manager <-->|Compiler Diagnostics & AST| Validator["⚙️ Pluggable Validator Engine"]:::validator
    end
    
    subgraph Hybrid LLM Engine
        Architect --> LLM
        Builder --> LLM
        QA --> LLM
        Librarian --> LLM
        
        LLM["🌐 Hybrid LLM Provider"]:::llm -->|Primary / Offline| Ollama["🦙 Ollama (Local)"]:::llm
        LLM -->|Fallback / Cloud| Gemini["☁️ Google Gemini"]:::llm
    end
    
    Manager -->|Verified Package| UI
    UI <-->|Sandboxed Run| Exec["⚡ Pluggable Execution Engine"]:::executor
    UI -->|Displays Results & Report| User
```

---

## 📁 Project Structure

```text
MTC/
│
├── app.py                  # Streamlit Interactive Dashboard
├── config.py               # Global configuration & dynamic prompt interfaces
├── requirements.txt        # Python package dependencies
│
├── core/                   # Core application architecture
│   ├── languages.py        # Layer 1: Dynamic Language Strategy & Registry
│   ├── validators.py       # Layer 2: Pluggable Validator Engine (AST & Javac)
│   ├── executor.py         # Layer 3: Pluggable Execution Engine (Python & Java)
│   ├── llm_provider.py     # Hybrid LLM fallback provider
│   ├── model_manager.py    # Local model lifecycle manager
│   └── protocol.py         # Standard Pydantic schemas (TaskResult)
│
├── agents/                 # Intelligent AI Agent Definitions
│   ├── manager.py          # Orchestrator & Self-Healing Loop
│   ├── base_agent.py       # Base agent inheritance & resilient JSON parser
│   ├── architect.py        # Polyglot analysis & modernization planner
│   ├── builder.py          # Modernization & cross-language translation engine
│   ├── qa.py               # Test-case generator & logic reviewer
│   └── librarian.py        # Technical documentation generator
│
└── utils/                  # Helper utilities
    └── validators.py       # Facade for ValidatorFactory
```

---

## 🚀 Installation & Setup

### 1. Prerequisites

- Python 3.9+ installed.
- (Optional) Java JDK installed if compiling and executing Java code locally.
- (Optional) [Ollama](https://ollama.com/) if running in Local AI Mode.

### 2. Set Up Virtual Environment

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🎮 Usage

Launch the MTC toolkit by running:

```bash
streamlit run app.py
```

1. **Select Mode:** Choose between Local (Ollama) or Cloud (Gemini) on the sidebar.
2. **Select Language Pair:** Choose Source Language (e.g. Python) and Target Language (e.g. Java).
3. **Submit Code:** Paste your legacy script.
4. **Execute:** Click "Execute Modernization Pipeline".
5. **Inspect & Execute:** Run original and modernized code side-by-side using the live execution engine, run auto-generated tests, and download the full Markdown migration report.
