# --- IMPORTS & WARNINGS ---
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

import ollama
import google.generativeai as genai
import os
from config import Config
from typing import Optional

class HybridLLMProvider:
    def __init__(self, force_mode=None):
        """
        force_mode: 'local', 'cloud', or None (defaults to local-first fallback)
        """
        self.force_mode = force_mode
        self.model_type = "local" 

    def _run_local(self, prompt: str, system_prompt: str) -> str:
        print(f"[*] [LOCAL] Generating with {Config.LOCAL_MODEL_NAME}...")
        response = ollama.generate(
            model=Config.LOCAL_MODEL_NAME,
            system=system_prompt,
            prompt=prompt,
            options={'temperature': Config.TEMPERATURE, 'num_ctx': 4096, 'num_predict': 1024}
        )
        return response.get('response', '')

    def _run_cloud(self, prompt: str, system_prompt: str) -> str:
        print(f"[*] [CLOUD] Generating with {Config.FALLBACK_MODEL_NAME}...")
        
        # Read API key dynamically
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Gemini API Key is missing in environment variables.")
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(Config.FALLBACK_MODEL_NAME)
        
        full_prompt = f"System Instruction: {system_prompt}\n\nUser Prompt: {prompt}"
        response = model.generate_content(full_prompt)
        
        if not response.text:
            raise ValueError("Gemini returned an empty response.")
        return response.text

    def generate(self, prompt: str, system_prompt: str) -> str:
        # 1. EXPLICIT CLOUD MODE
        if self.force_mode == 'cloud':
            try:
                self.model_type = "cloud"
                return self._run_cloud(prompt, system_prompt)
            except Exception as e:
                raise Exception(f"Cloud generation failed: {str(e)}")

        # 2. EXPLICIT LOCAL MODE (or Default Hybrid)
        else: 
            try:
                self.model_type = "local"
                return self._run_local(prompt, system_prompt)
            except Exception as e:
                print(f"[!] Local model failed: {e}. Fallback to Cloud...")
                try:
                    self.model_type = "cloud"
                    return self._run_cloud(prompt, system_prompt)
                except Exception as cloud_e:
                    raise Exception(f"Both Local and Cloud LLM providers failed. Cloud Error: {cloud_e}")

    def get_current_provider(self) -> str:
        return self.model_type