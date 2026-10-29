import ollama
from typing import List, Tuple

# Define the host
OLLAMA_HOST = 'http://127.0.0.1:11434'

# Initialize the Client ONCE with the host.
# This fixes the "unexpected keyword argument" error.
client = ollama.Client(host=OLLAMA_HOST)

class ModelManager:
    @staticmethod
    def check_model_availability(model_name: str) -> bool:
        """Checks if a specific model is available in the local Ollama registry."""
        try:
            # Use the initialized client
            response = client.list()
            available_models = [m['name'] for m in response.get('models', [])]
            
            # Debugging: Print what we found to terminal
            print(f"Available models: {available_models}")
            
            # Check if model_name exists
            return any(model_name in m for m in available_models)
        except Exception as e:
            print(f"Error checking Ollama models: {e}")
            return False

    @staticmethod
    def get_coding_models() -> List[str]:
        """Scans for coding-related models."""
        coding_keywords = ['coder', 'code', 'instruct', 'python']
        found_models = []
        try:
            response = client.list()
            for m in response.get('models', []):
                name = m['name']
                if any(k in name.lower() for k in coding_keywords):
                    found_models.append(name)
        except Exception as e:
            print(f"Error listing models: {e}")
        return found_models

    @staticmethod
    def pull_model(model_name: str) -> Tuple[bool, str]:
        """Attempts to download a model. Returns (Success, StatusMessage)."""
        try:
            print(f"Attempting to download {model_name} from {OLLAMA_HOST}...")
            
            # Use the initialized client's pull method
            progress = client.pull(model_name)
            
            # Consume the generator to wait for download
            for _ in progress:
                pass 
                
            return True, f"Successfully downloaded {model_name}"
        except Exception as e:
            return False, f"Failed to download {model_name}: {str(e)}"