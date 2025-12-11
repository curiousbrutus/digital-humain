"""LLM provider integrations for local inference."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from loguru import logger
import httpx
import json


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None,
    ) -> str:
        """Generate text completion."""
        pass
    
    @abstractmethod
    def generate_sync(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None,
    ) -> str:
        """Synchronous text generation."""
        pass


class OllamaProvider(LLMProvider):
    """
    Ollama LLM provider for local inference.
    
    Supports running models locally with full data privacy.
    """
    
    def __init__(
        self,
        model: str = "llama2",
        base_url: str = "http://localhost:11434",
        timeout: int = 300,
    ):
        """
        Initialize Ollama provider.
        
        Args:
            model: Model name (e.g., 'llama2', 'mistral', 'codellama')
            base_url: Ollama server URL
            timeout: Request timeout in seconds
        """
        self.model = model
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        logger.info(f"Initialized Ollama provider with model: {model}")
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None,
    ) -> str:
        """Generate text completion asynchronously."""
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        if stop:
            payload["options"]["stop"] = stop
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()
                return result.get("response", "")
        
        except httpx.HTTPError as e:
            logger.error(f"Ollama API error: {e}")
            raise RuntimeError(f"Failed to generate completion: {e}")
    
    def generate_sync(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None,
    ) -> str:
        """Generate text completion synchronously."""
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        if stop:
            payload["options"]["stop"] = stop
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()
                return result.get("response", "")
        
        except httpx.HTTPError as e:
            logger.error(f"Ollama API error: {e}")
            raise RuntimeError(f"Failed to generate completion: {e}")
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List available models."""
        url = f"{self.base_url}/api/tags"
        
        try:
            with httpx.Client(timeout=30) as client:
                response = client.get(url)
                response.raise_for_status()
                result = response.json()
                return result.get("models", [])
        
        except httpx.HTTPError as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    def pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama library."""
        url = f"{self.base_url}/api/pull"
        
        payload = {"name": model_name, "stream": False}
        
        try:
            with httpx.Client(timeout=600) as client:
                logger.info(f"Pulling model: {model_name}")
                response = client.post(url, json=payload)
                response.raise_for_status()
                logger.info(f"Model {model_name} pulled successfully")
                return True
        
        except httpx.HTTPError as e:
            logger.error(f"Failed to pull model: {e}")
            return False


class VLLMProvider(LLMProvider):
    """
    vLLM provider for high-performance local inference.
    
    Supports OpenAI-compatible API endpoint.
    """
    
    def __init__(
        self,
        model: str,
        base_url: str = "http://localhost:8000",
        api_key: str = "EMPTY",
        timeout: int = 300,
    ):
        """
        Initialize vLLM provider.
        
        Args:
            model: Model name
            base_url: vLLM server URL
            api_key: API key (use 'EMPTY' for local)
            timeout: Request timeout in seconds
        """
        self.model = model
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        logger.info(f"Initialized vLLM provider with model: {model}")
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None,
    ) -> str:
        """Generate text completion asynchronously."""
        url = f"{self.base_url}/v1/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "temperature": temperature,
            "max_tokens": max_tokens or 512,
        }
        
        if stop:
            payload["stop"] = stop
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["text"]
        
        except httpx.HTTPError as e:
            logger.error(f"vLLM API error: {e}")
            raise RuntimeError(f"Failed to generate completion: {e}")
    
    def generate_sync(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None,
    ) -> str:
        """Generate text completion synchronously."""
        url = f"{self.base_url}/v1/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "temperature": temperature,
            "max_tokens": max_tokens or 512,
        }
        
        if stop:
            payload["stop"] = stop
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["text"]
        
        except httpx.HTTPError as e:
            logger.error(f"vLLM API error: {e}")
            raise RuntimeError(f"Failed to generate completion: {e}")
