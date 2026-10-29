import ast
import os
import re
import shutil
import subprocess
import tempfile
from abc import ABC, abstractmethod
from typing import List, Tuple

class BaseSyntaxValidator(ABC):
    """Abstract Base Class for language-specific syntax validation."""

    @abstractmethod
    def validate(self, code: str) -> Tuple[bool, List[str]]:
        """
        Validates code syntax.
        Returns:
            Tuple[bool, List[str]]: (is_valid, list_of_error_messages)
        """
        pass


class PythonSyntaxValidator(BaseSyntaxValidator):
    """Validates Python code using Python's native AST parser."""

    def validate(self, code: str) -> Tuple[bool, List[str]]:
        if not code or not code.strip():
            return False, ["Empty code payload provided."]
        try:
            ast.parse(code)
            return True, []
        except SyntaxError as e:
            line = e.lineno if e.lineno is not None else "?"
            col = f", Col {e.offset}" if e.offset is not None else ""
            msg = e.msg or "Syntax error"
            return False, [f"Python SyntaxError [Line {line}{col}]: {msg}"]
        except IndentationError as e:
            line = e.lineno if e.lineno is not None else "?"
            msg = e.msg or "Indentation error"
            return False, [f"Python IndentationError [Line {line}]: {msg}"]
        except Exception as e:
            return False, [f"Python Parsing Exception: {str(e)}"]


class JavaSyntaxValidator(BaseSyntaxValidator):
    """
    Validates Java code using the JDK's `javac` compiler for 100% precision.
    Falls back to a structural validator if javac is not installed in the environment.
    """

    def __init__(self):
        self.javac_path = self._locate_javac()

    def _locate_javac(self) -> str | None:
        which_javac = shutil.which("javac")
        if which_javac:
            return which_javac
        common_path = r"C:\Program Files\Common Files\Oracle\Java\javapath\javac.exe"
        if os.path.exists(common_path):
            return common_path
        return None

    def _extract_primary_class_name(self, code: str) -> str:
        # Match 'public class ClassName' or 'public record ClassName'
        match = re.search(r"public\s+(?:class|record|interface|enum)\s+([A-Za-z0-9_$]+)", code)
        if match:
            return match.group(1)
        # Match non-public class
        match_any = re.search(r"(?:class|record|interface|enum)\s+([A-Za-z0-9_$]+)", code)
        if match_any:
            return match_any.group(1)
        return "Main"

    def _validate_with_javac(self, code: str, javac_bin: str) -> Tuple[bool, List[str]]:
        class_name = self._extract_primary_class_name(code)
        temp_dir = tempfile.mkdtemp(prefix="java_val_")
        source_path = os.path.join(temp_dir, f"{class_name}.java")
        try:
            with open(source_path, "w", encoding="utf-8") as f:
                f.write(code)

            result = subprocess.run(
                [javac_bin, "-Xlint:none", "-d", temp_dir, source_path],
                capture_output=True,
                text=True,
                timeout=15
            )

            if result.returncode == 0:
                return True, []

            # Parse javac errors
            raw_err = result.stderr or result.stdout or "Compilation failed."
            errors = []
            for line in raw_err.strip().splitlines():
                clean_line = line.strip()
                if clean_line and (source_path in clean_line or "error:" in clean_line or "^" in clean_line):
                    # Strip verbose temp file paths from output for clean LLM prompt feedback
                    clean_line = clean_line.replace(source_path, f"{class_name}.java")
                    errors.append(clean_line)

            if not errors:
                errors = [raw_err.strip()[:400]]

            return False, errors[:10]  # Cap to first 10 most relevant errors

        except subprocess.TimeoutExpired:
            return False, ["Compilation timed out during Java verification."]
        except Exception as e:
            return False, [f"Java compilation execution error: {str(e)}"]
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _validate_heuristics(self, code: str) -> Tuple[bool, List[str]]:
        """Structural fallback when javac is not available."""
        errors = []
        # Check balanced braces
        brace_count = 0
        paren_count = 0
        for i, char in enumerate(code):
            if char == '{': brace_count += 1
            elif char == '}': brace_count -= 1
            elif char == '(': paren_count += 1
            elif char == ')': paren_count -= 1

            if brace_count < 0:
                errors.append(f"Unmatched closing brace '}}' detected around character {i}.")
                break
            if paren_count < 0:
                errors.append(f"Unmatched closing parenthesis ')' detected around character {i}.")
                break

        if brace_count > 0:
            errors.append(f"Unclosed open brace '{{' count: {brace_count}.")
        if paren_count > 0:
            errors.append(f"Unclosed open parenthesis '(' count: {paren_count}.")

        if not re.search(r"(class|record|interface|enum)\s+[A-Za-z0-9_$]+", code):
            errors.append("No valid Java class, record, or interface declaration found.")

        if not errors:
            return True, []
        return False, errors

    def validate(self, code: str) -> Tuple[bool, List[str]]:
        if not code or not code.strip():
            return False, ["Empty Java code payload provided."]

        if self.javac_path:
            return self._validate_with_javac(code, self.javac_path)
        return self._validate_heuristics(code)


class ValidatorFactory:
    _validators = {
        "python": PythonSyntaxValidator(),
        "java": JavaSyntaxValidator(),
    }

    @classmethod
    def get_validator(cls, language: str) -> BaseSyntaxValidator:
        clean_lang = (language or "python").strip().lower()
        if clean_lang not in cls._validators:
            # Default to Python if unrecognized
            return cls._validators["python"]
        return cls._validators[clean_lang]
