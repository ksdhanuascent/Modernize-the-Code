from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class LanguageStrategy:
    id: str
    name: str
    extension: str
    syntax_label: str
    modern_standard: str
    entrypoint_template: str
    code_guidelines: List[str]
    test_guidelines: str

    def get_architect_prompt(self, source_lang: "LanguageStrategy") -> str:
        if source_lang.id == self.id:
            task_desc = f"Analyze the following legacy {source_lang.name} code for modernization to {self.modern_standard}."
        else:
            task_desc = (
                f"Analyze the following {source_lang.name} code to plan a high-fidelity translation and modernization "
                f"into {self.name} ({self.modern_standard})."
            )
        return (
            f"You are a Principal Software Architect specializing in {source_lang.name} and {self.name}.\n"
            f"{task_desc}\n\n"
            "CRITICAL ARCHITECTURAL DIRECTIVES:\n"
            "1. Preserve 100% of the underlying business logic, mathematical computations, edge cases, and data transformations.\n"
            f"2. Map {source_lang.name} paradigms to idiomatic {self.name} patterns ({self.modern_standard}).\n"
            "3. Identify obsolete libraries, unsafe concurrency, unhandled exceptions, and untyped variables.\n"
            "4. Provide a concrete, step-by-step modernization/translation specification.\n"
            "5. Do NOT output pseudo-code. Provide exact architectural specifications.\n"
            "You MUST respond ONLY with a valid JSON object using DOUBLE QUOTES (\").\n"
            "Format: {\"success\": true, \"data\": {\"plan\": \"Detailed architectural plan...\"}}"
        )

    def get_builder_prompt(self, source_lang: "LanguageStrategy") -> str:
        if source_lang.id == self.id:
            goal_desc = f"Refactor and modernize the legacy {source_lang.name} code to {self.modern_standard}."
        else:
            goal_desc = (
                f"Translate and modernize the {source_lang.name} source code into production-grade {self.name} ({self.modern_standard})."
            )

        guidelines_str = "\n".join(f"- {g}" for g in self.code_guidelines)

        return (
            f"You are an Elite Polyglot Software Engineer specializing in {self.name}.\n"
            f"GOAL: {goal_desc}\n\n"
            "CRITICAL IMPLEMENTATION DIRECTIVES (ZERO-HALLUCINATION POLICY):\n"
            "1. COMPLETE CODE ONLY: Never omit implementation details, never use comments like '// ... rest of code', '/* TODO */', or 'pass'. Output the COMPLETE, fully compilable/runnable code.\n"
            "2. LOGIC FIDELITY: Maintain exact behavioral equivalence with the original code.\n"
            f"3. MODERN IDIOMS ({self.modern_standard}):\n{guidelines_str}\n"
            f"4. RUNNABLE ENTRYPOINT: The output must include an entrypoint so it can execute out of the box.\n{self.entrypoint_template}\n"
            "5. NO MARKDOWN: Output valid JSON containing the code string. Ensure proper escaping for quotes, backslashes, and newlines.\n"
            "Format: {\"success\": true, \"data\": {\"code\": \"full source code string\"}}"
        )

    def get_qa_prompt(self) -> str:
        return (
            f"You are a Lead QA Engineer specializing in {self.name}.\n"
            f"Review the provided {self.name} code for syntax correctness, logical edge cases, boundary conditions, and performance.\n\n"
            "REQUIREMENTS:\n"
            "1. Generate a comprehensive review summary.\n"
            "2. Generate at least 3 distinct, self-contained, and fully executable test cases written in "
            f"{self.name} that directly verify the functions/classes.\n"
            f"3. {self.test_guidelines}\n"
            "4. Each test case MUST be standalone, compilable, and executable, printing output or throwing assertion errors on failure.\n"
            "CRITICAL: Respond ONLY with a valid JSON object using DOUBLE QUOTES (\").\n"
            "Format: {\"success\": true, \"data\": {\"review\": \"Summary of audit\", \"test_cases\": [{\"name\": \"Test Name\", \"code\": \"complete executable test code\"}]}}"
        )

    def get_librarian_prompt(self) -> str:
        return (
            f"You are a Senior Technical Documentation Writer specializing in {self.name}.\n"
            f"Produce comprehensive, production-grade technical Markdown documentation for the provided {self.name} code.\n\n"
            "REQUIREMENTS:\n"
            "1. Executive Overview and architectural description.\n"
            "2. Method/Class API specifications with parameter types, return values, and exception signatures.\n"
            f"3. Complete idiomatic {self.name} usage examples with expected output.\n"
            "4. Migration notes detailing modernizations or translation choices made.\n"
            "CRITICAL: Respond ONLY with a valid JSON object using DOUBLE QUOTES (\").\n"
            "Format: {\"success\": true, \"data\": {\"documentation\": \"# Markdown Documentation...\"}}"
        )


PYTHON_STRATEGY = LanguageStrategy(
    id="python",
    name="Python",
    extension=".py",
    syntax_label="python",
    modern_standard="Python 3.11+",
    entrypoint_template="Include a `if __name__ == '__main__':` block that initializes the objects/functions, executes a meaningful demo, and prints results to stdout.",
    code_guidelines=[
        "Use modern type hinting (e.g., list[str], dict[str, Any], int | None, Self from typing).",
        "Adhere strictly to PEP 8 standards (naming, layout, docstrings).",
        "Leverage modern standard library features: dataclasses, match-case, pathlib, contextlib, enum.",
        "Ensure robust error handling with specific exception types and informative error messages.",
        "Ensure syntactically valid code parseable by standard Python `ast`."
    ],
    test_guidelines=(
        "Each test case must be a standalone executable Python script with assertions or unittest/pytest style verification. "
        "Each test must run standalone and print verification results to stdout."
    )
)

JAVA_STRATEGY = LanguageStrategy(
    id="java",
    name="Java",
    extension=".java",
    syntax_label="java",
    modern_standard="Java 21 LTS",
    entrypoint_template=(
        "Create a standalone class named `Main` (or ensure the primary class has `public static void main(String[] args)`). "
        "The class must contain all necessary helper classes/records inside or in package-private scope so it compiles in a single file named Main.java. "
        "The main method must run the modernized logic and print output using System.out.println."
    ),
    code_guidelines=[
        "Use modern Java 21 LTS features where appropriate: records for data transfer, pattern matching for switch, var for local variables, Text Blocks, and Stream API.",
        "Use proper OOP encapsulation (private fields, accessors, immutability where suitable).",
        "Use generic collections (List<T>, Map<K,V>, Set<T>) and java.util.Optional to avoid NullPointerExceptions.",
        "All code must fit in a single self-contained compilation unit with `public class Main` as the entrypoint.",
        "Include all required imports (e.g., java.util.*, java.time.*, java.io.*)."
    ],
    test_guidelines=(
        "Each test case must be a self-contained Java source file with a `public class Main` or test class containing `public static void main(String[] args)` "
        "that executes assertions and prints either 'PASS: <description>' or throws an AssertionError on failure."
    )
)


class LanguageRegistry:
    _strategies: Dict[str, LanguageStrategy] = {
        "python": PYTHON_STRATEGY,
        "java": JAVA_STRATEGY,
    }

    @classmethod
    def get(cls, language_id: str) -> LanguageStrategy:
        clean_id = (language_id or "python").strip().lower()
        if clean_id not in cls._strategies:
            raise ValueError(
                f"Unsupported language: '{language_id}'. Supported languages: {list(cls._strategies.keys())}"
            )
        return cls._strategies[clean_id]

    @classmethod
    def list_supported(cls) -> List[str]:
        return list(cls._strategies.keys())

    @classmethod
    def register(cls, strategy: LanguageStrategy) -> None:
        cls._strategies[strategy.id.lower()] = strategy
