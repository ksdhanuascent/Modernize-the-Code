from typing import Tuple, List
from core.validators import ValidatorFactory, PythonSyntaxValidator

def validate_python_syntax(code: str) -> Tuple[bool, List[str]]:
    """Backward-compatible helper to validate Python syntax."""
    return PythonSyntaxValidator().validate(code)

def validate_syntax(code: str, language: str = "python") -> Tuple[bool, List[str]]:
    """Pluggable syntax validator entrypoint."""
    validator = ValidatorFactory.get_validator(language)
    return validator.validate(code)
