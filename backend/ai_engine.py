from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env")

client = genai.Client(api_key=api_key)

def generate_summary(project, percent, delayed):

    risk = "Low"
    if percent < 50 or delayed > 5:
        risk = "High"
    elif percent < 75:
        risk = "Medium"

    prompt = f"""
You are a professional project management AI.

Project: {project}
Completion: {percent:.1f}%
Delayed Tasks: {delayed}
Risk Level: {risk}

Write a concise executive summary (3-4 sentences).
Include:
- Overall health
- Risk assessment
- One short recommendation
Do not explain instructions.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return response.text.strip()
