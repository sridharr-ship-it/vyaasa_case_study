# config.py

import os
from dotenv import load_dotenv
# config.py
from langchain_groq import ChatGroq  # fix module name


# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration settings for the interview system"""

    # API Configuration
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

    # Model Configuration
    MODELS = {
        'fast': 'llama-3.1-8b-instant',
        'smart': 'llama-3.3-70b-versatile',
        'conversation': 'llama-3.1-8b-instant',
    }

    # Interview Configuration
    INTERVIEW_DURATION = 1200

    @classmethod
    def validate(cls):
        """Validate configuration"""
        if not cls.GROQ_API_KEY:
            raise ValueError(
                "❌ GROQ_API_KEY not found!\n"
                "Please set it in your .env file or environment variables.\n"
                "Get your API key from: https://console.groq.com/keys"
            )


def get_llm_for_task(task_type: str, temperature: float = 0.7):
    """Get appropriate LLM for the task"""

    # Validate API key before creating LLM
    Config.validate()

    model_map = {
        'mcq': Config.MODELS['fast'],
        'case_generation': Config.MODELS['smart'],
        'conversation': Config.MODELS['conversation'],
        'evaluation': Config.MODELS['smart']
    }

    model_name = model_map.get(task_type, Config.MODELS['fast'])

    return ChatGroq(
        api_key=Config.GROQ_API_KEY,
        model=model_name,
        temperature=temperature
    )
