import os
import re
import shutil
import subprocess
import sys
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Tuple

@dataclass
class ExecutionResult:
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    error: Optional[str] = None
    success: bool = True

    def as_tuple(self) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Provides compatibility with legacy (stdout, stderr, error) tuples."""
        return self.stdout, self.stderr, self.error


class BaseExecutor(ABC):
    """Abstract Base Class for executing language code snippets."""

    @abstractmethod
    def execute(self, code: str, timeout: int = 10) -> ExecutionResult:
        pass


class PythonExecutor(BaseExecutor):
    """Executes Python code using the active Python runtime."""

    def execute(self, code: str, timeout: int = 10) -> ExecutionResult:
        if not code or not code.strip():
            return ExecutionResult(error="No Python code provided to execute.", success=False)

        temp_dir = tempfile.mkdtemp(prefix="py_exec_")
        temp_file = os.path.join(temp_dir, "script.py")
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(code)

            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return ExecutionResult(
                stdout=result.stdout if result.stdout else None,
                stderr=result.stderr if result.stderr else None,
                error=None,
                success=(result.returncode == 0)
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(error=f"Execution timed out after {timeout} seconds.", success=False)
        except Exception as e:
            return ExecutionResult(error=f"Execution failed: {str(e)}", success=False)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class JavaExecutor(BaseExecutor):
    """Compiles and executes Java code using javac and java."""

    def __init__(self):
        self.javac_path = self._locate_tool("javac")
        self.java_path = self._locate_tool("java")

    def _locate_tool(self, tool_name: str) -> Optional[str]:
        which_path = shutil.which(tool_name)
        if which_path:
            return which_path
        common_path = rf"C:\Program Files\Common Files\Oracle\Java\javapath\{tool_name}.exe"
        if os.path.exists(common_path):
            return common_path
        return None

    def _extract_primary_class_name(self, code: str) -> str:
        match = re.search(r"public\s+(?:class|record|interface|enum)\s+([A-Za-z0-9_$]+)", code)
        if match:
            return match.group(1)
        match_any = re.search(r"(?:class|record|interface|enum)\s+([A-Za-z0-9_$]+)", code)
        if match_any:
            return match_any.group(1)
        return "Main"

    def execute(self, code: str, timeout: int = 12) -> ExecutionResult:
        if not code or not code.strip():
            return ExecutionResult(error="No Java code provided to execute.", success=False)

        if not self.javac_path or not self.java_path:
            return ExecutionResult(
                error="Java Development Kit (javac/java) is not configured in PATH. Live execution unavailable.",
                success=False
            )

        class_name = self._extract_primary_class_name(code)
        temp_dir = tempfile.mkdtemp(prefix="java_exec_")
        source_file = os.path.join(temp_dir, f"{class_name}.java")

        try:
            with open(source_file, "w", encoding="utf-8") as f:
                f.write(code)

            # Step 1: Compile
            compile_proc = subprocess.run(
                [self.javac_path, "-Xlint:none", "-d", temp_dir, source_file],
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if compile_proc.returncode != 0:
                raw_err = compile_proc.stderr or compile_proc.stdout
                clean_err = raw_err.replace(source_file, f"{class_name}.java")
                return ExecutionResult(
                    stderr=clean_err,
                    error="Compilation Error",
                    success=False
                )

            # Step 2: Run Bytecode
            run_proc = subprocess.run(
                [self.java_path, "-cp", temp_dir, class_name],
                capture_output=True,
                text=True,
                timeout=timeout
            )

            return ExecutionResult(
                stdout=run_proc.stdout if run_proc.stdout else None,
                stderr=run_proc.stderr if run_proc.stderr else None,
                error=None,
                success=(run_proc.returncode == 0)
            )

        except subprocess.TimeoutExpired:
            return ExecutionResult(error=f"Java process timed out after {timeout} seconds.", success=False)
        except Exception as e:
            return ExecutionResult(error=f"Java execution error: {str(e)}", success=False)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class ExecutorFactory:
    _executors = {
        "python": PythonExecutor(),
        "java": JavaExecutor(),
    }

    @classmethod
    def get_executor(cls, language: str) -> BaseExecutor:
        clean_lang = (language or "python").strip().lower()
        if clean_lang not in cls._executors:
            return cls._executors["python"]
        return cls._executors[clean_lang]


def execute_code(code: str, language: str = "python", timeout: int = 10) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Universal execution helper returning (stdout, stderr, error)."""
    executor = ExecutorFactory.get_executor(language)
    result = executor.execute(code, timeout=timeout)
    return result.as_tuple()
