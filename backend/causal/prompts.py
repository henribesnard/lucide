"""
Prompt templates for causal analysis.
"""

from enum import Enum
from typing import Any

from backend.llm.client import LLMClient
from .context import get_causal_context


class QuestionType(Enum):
    FACTUAL = "factual"
    CAUSAL_WHY = "causal_why"
    CAUSAL_WHAT_IF = "causal_what_if"
    CAUSAL_COMPARE = "causal_compare"
    HYBRID = "hybrid"


QUESTION_CLASSIFIER_PROMPT = """
Classify this football question.

Question: "{question}"

Possible types:
- FACTUAL: facts only (score, date, stats)
- CAUSAL_WHY: why did it happen
- CAUSAL_WHAT_IF: counterfactual or hypothetical
- CAUSAL_COMPARE: causal comparison between groups
- HYBRID: facts + causal explanation

Reply with ONE word: FACTUAL, CAUSAL_WHY, CAUSAL_WHAT_IF, CAUSAL_COMPARE, HYBRID
"""


async def classify_question(question: str, llm_client: LLMClient) -> QuestionType:
    """Classify the question using the LLM."""
    messages = [
        {"role": "system", "content": "You are a strict classifier."},
        {"role": "user", "content": QUESTION_CLASSIFIER_PROMPT.format(question=question)},
    ]
    response = await llm_client.chat_completion(messages=messages, temperature=0.0, max_tokens=20)
    content = (response.choices[0].message.content or "").strip().upper()
    try:
        return QuestionType(content.lower())
    except ValueError:
        return QuestionType.HYBRID


TEMPLATES: dict[QuestionType, str] = {
    QuestionType.FACTUAL: """
Answer factually using only the provided data.

Data:
{data}

Question:
{question}
""",
    QuestionType.CAUSAL_WHY: """
{causal_context}

## Causal analysis requested

Question: {question}

Match data:
{match_data}

Stats:
{stats}

Rule findings and metrics:
{enriched_context}
""",
    QuestionType.CAUSAL_WHAT_IF: """
{causal_context}

## Counterfactual analysis requested

Question: {question}

Actual scenario:
{actual_scenario}

Historical data:
{historical_data}

Rule findings and metrics:
{enriched_context}

Return:
1) What happened
2) What would likely change
3) Causal mechanism
4) Confidence
""",
    QuestionType.CAUSAL_COMPARE: """
{causal_context}

## Causal comparison requested

Question: {question}

Group A data:
{group_a_data}

Group B data:
{group_b_data}

Confounders to control:
- Home vs away
- Opponent strength
- Squad availability
- Competition context

Rule findings and metrics:
{enriched_context}
""",
    QuestionType.HYBRID: """
{causal_context}

## Hybrid analysis (facts + causes)

Question: {question}

Factual data:
{factual_data}

Match data:
{match_data}

Rule findings and metrics:
{enriched_context}

Answer in two parts:
1) Facts
2) Causal explanation
""",
}


def get_prompt_for_question(question_type: QuestionType, question: str, **kwargs: Any) -> str:
    """Build the prompt for the given question type."""
    template = TEMPLATES.get(question_type, TEMPLATES[QuestionType.HYBRID])
    if question_type != QuestionType.FACTUAL:
        kwargs["causal_context"] = get_causal_context()
    kwargs["question"] = question
    return template.format(**_fill_missing(template, kwargs))


def _fill_missing(template: str, kwargs: dict[str, Any]) -> dict[str, Any]:
    """Fill missing keys with placeholders to avoid KeyError."""
    import re

    keys = re.findall(r"{(\w+)}", template)
    for key in keys:
        if key not in kwargs:
            kwargs[key] = f"[Missing {key}]"
    return kwargs
