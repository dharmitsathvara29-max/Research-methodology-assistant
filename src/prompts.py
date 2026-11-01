"""Prompt loading, templating, and version management."""

import os
from typing import Dict, Any, List

PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompts")


PROMPT_DESCRIPTIONS = {
    "v1_basic": "Baseline instruction prompt with flat JSON key requirements.",
    "v2_structured": "Structured prompt with persona, academic requirements, and explicit JSON schema.",
    "v3_decomposed": "Cognitive decomposition chain-of-thought, few-shot gold standard example, and anti-hallucination guardrails (Default)."
}


def get_available_prompt_versions() -> List[str]:
    """Return available prompt version identifiers."""
    return ["v3_decomposed", "v2_structured", "v1_basic"]


def get_prompt_text(version: str) -> str:
    """Read the raw prompt template file from prompts directory."""
    filename = f"{version}.txt"
    filepath = os.path.join(PROMPTS_DIR, filename)
    if not os.path.exists(filepath):
        # Fallback to master template if version file not found
        master_path = os.path.join(PROMPTS_DIR, "master_template.md")
        if os.path.exists(master_path):
            with open(master_path, "r", encoding="utf-8") as f:
                return f.read()
        raise FileNotFoundError(f"Prompt file not found for version: {version}")
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def format_constraints_summary(constraints: Dict[str, Any]) -> str:
    """Format user constraint dictionary into clear text bullets."""
    if not constraints:
        return "Standard academic constraints (typical graduate/postgraduate research timeline and budget)."

    parts = []
    if constraints.get("time"):
        parts.append(f"Timeframe: {constraints['time']}")
    if constraints.get("budget"):
        parts.append(f"Budget: {constraints['budget']}")
    if constraints.get("sample_access"):
        parts.append(f"Sample Access: {constraints['sample_access']}")
    if constraints.get("ethical_sensitivity"):
        parts.append(f"Ethical Sensitivity: {constraints['ethical_sensitivity']}")
    if constraints.get("data_availability"):
        parts.append(f"Data Availability: {constraints['data_availability']}")
    if constraints.get("skill_level"):
        parts.append(f"Researcher Skill Level: {constraints['skill_level']}")

    return "; ".join(parts) if parts else "Standard academic constraints."


def format_methodology_prompt(
    version: str,
    research_question: str,
    discipline: str,
    parsed_json: Dict[str, Any],
    constraints: Dict[str, Any]
) -> str:
    """Format the chosen version prompt template with dynamic inputs."""
    template = get_prompt_text(version)
    constraints_summary = format_constraints_summary(constraints)

    import json
    parsed_json_str = json.dumps(parsed_json, indent=2)

    formatted = template.replace("{research_question}", research_question)
    formatted = formatted.replace("{discipline}", discipline)
    formatted = formatted.replace("{parsed_json}", parsed_json_str)
    formatted = formatted.replace("{constraints_summary}", constraints_summary)

    # In case constraints were individually templated (e.g. in master template)
    formatted = formatted.replace("{constraint_time}", str(constraints.get("time", "Standard")))
    formatted = formatted.replace("{constraint_budget}", str(constraints.get("budget", "Standard")))
    formatted = formatted.replace("{constraint_sample_access}", str(constraints.get("sample_access", "Standard")))
    formatted = formatted.replace("{constraint_ethical_sensitivity}", str(constraints.get("ethical_sensitivity", "Standard")))
    formatted = formatted.replace("{constraint_data_availability}", str(constraints.get("data_availability", "Standard")))
    formatted = formatted.replace("{constraint_skill_level}", str(constraints.get("skill_level", "Standard")))

    return formatted

