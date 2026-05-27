from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

import httpx

from src.core.models import ItemScoreResult, ScoreResult, Task
from src.core.ports import Scorer
from src.infra.scoring.answer_key import score_from_answer_key
from src.infra.scoring.personality_quiz import score_personality_quiz
from src.infra.scoring.prompt_templates import build_scoring_prompt

logger = logging.getLogger(__name__)

# ---------------- LangChain imports ----------------
try:
    from langchain.agents import AgentExecutor, create_openai_tools_agent
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.tools import tool
    from langchain_openai import ChatOpenAI

    LANGCHAIN_AVAILABLE = True
except Exception as exc:  # noqa
    LANGCHAIN_AVAILABLE = False
    logger.error("LangChain unavailable, agent disabled: %r", exc)


# ===================================================
#                   SCORER
# ===================================================
class LLMScorer(Scorer):
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://api.deepseek.com/v1/chat/completions",
        timeout: float = 30.0,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout = timeout
        self._debug = os.getenv("LLM_DEBUG", "false").lower() == "true"

        # IMPORTANT: normalize base_url for LangChain
        self._api_base = self._normalize_base_url(base_url)

        logger.warning(
            "LLMScorer init | debug=%s | langchain=%s | api_base=%s | model=%s",
            self._debug,
            LANGCHAIN_AVAILABLE,
            self._api_base,
            self._model,
        )

        self._agent: AgentExecutor | None = None
        if LANGCHAIN_AVAILABLE:
            self._agent = self._build_agent()

        logger.warning("LLMScorer agent_enabled=%s", self._agent is not None)

    # ---------------- Public API ----------------
    def score(self, task: Task, user_answers: list[str]) -> ScoreResult:
        logger.warning("SCORE CALLED | task_id=%s", task.task_id)

        personality_quiz_result = score_personality_quiz(task, user_answers)
        if personality_quiz_result is not None:
            return personality_quiz_result

        answer_key_result = score_from_answer_key(task, user_answers)
        if answer_key_result is not None:
            return answer_key_result

        payload = task.to_prompt_payload()
        prompt = build_scoring_prompt(payload, user_answers)

        try:
            content = self._call_llm(prompt)
            data = _parse_json_response(content)
            return _to_score_result(data, mode="llm")
        except Exception as exc:  # noqa
            fallback = _score_from_answer_key(task, user_answers)
            if fallback is not None:
                logger.warning("LLM scoring failed; using answer-key fallback: %s", exc)
                return ScoreResult(
                    score=fallback.score,
                    feedback=(
                        f"{fallback.feedback}\n\n"
                        "LLM scoring failed; checked against answer key instead."
                    ),
                    items=fallback.items,
                    mode=fallback.mode,
                )
            logger.exception("LLM scoring failed")
            return ScoreResult(
                score=0.0,
                feedback=f"LLM scoring failed: {exc}",
                items=[],
                mode="llm",
            )

    def score_item(self, text: str, question: str, user_answer: str) -> ItemScoreResult:
        task = Task("single", "single", [text], [question])
        result = self.score(task, [user_answer])
        return result.items[0] if result.items else ItemScoreResult(0.0, result.feedback)

    # ---------------- Core call ----------------
    def _call_llm(self, prompt: str) -> str:
        logger.warning("_call_llm | using_agent=%s", self._agent is not None)

        if self._agent:
            try:
                result = self._agent.invoke({"input": prompt})
            except Exception:
                logger.exception("Agent call failed; falling back to plain call")
                return self._call_llm_plain(prompt)
            content = _extract_agent_content(result)
            try:
                _parse_json_response(content)
            except json.JSONDecodeError:
                logger.warning(
                    "Agent returned non-JSON output; falling back to plain call | output=%r",
                    content[:500],
                )
                return self._call_llm_plain(prompt)
            return content

        return self._call_llm_plain(prompt)

    # ---------------- Agent ----------------
    def _build_agent(self) -> AgentExecutor:
        logger.warning("Building LangChain agent...")

        llm = ChatOpenAI(
            model=self._model,
            temperature=0,
            timeout=self._timeout,
            openai_api_key=self._api_key,
            base_url=self._api_base,
        )

        # -------- Tool 1 --------
        @tool("draft_reasoning")
        def draft_reasoning(input_prompt: str) -> str:
            """
            Analyze student's English answers.
            Return examiner-style reasoning text only.
            """
            logger.warning("[TOOL] draft_reasoning CALLED")

            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "You are an ESL examiner. Analyze answers:\n"
                        "- correctness\n"
                        "- grammar errors\n"
                        "- vocabulary issues\n"
                        "- spelling\n"
                        "- improved version\n"
                        "- preliminary score (0..1)\n"
                        "Return TEXT ONLY.",
                    ),
                    ("user", "{input}"),
                ]
            )

            out = llm.invoke(prompt.format_messages(input=input_prompt)).content
            logger.warning(
                "[TOOL] draft_reasoning DONE | response_chars=%s",
                len(str(out)),
            )
            return str(out)

        # -------- Tool 2 --------
        @tool("verify_and_format")
        def verify_and_format(input_prompt: str, reasoning: str) -> str:
            """
            Convert reasoning into strict JSON ScoreResult.
            """
            logger.warning("[TOOL] verify_and_format CALLED")

            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "Return STRICT JSON only:\n"
                        "{{"
                        "\"score\": number,"
                        "\"feedback\": string,"
                        "\"items\": [{{\"score\": number, \"feedback\": string}}]"
                        "}}\n"
                        "Overall score = average of items.\n"
                        "Use the Expected answer from the prompt as the answer key when present.",
                    ),
                    (
                        "user",
                        "PROMPT:\n{input}\n\nREASONING:\n{reasoning}",
                    ),
                ]
            )

            out = llm.invoke(
                prompt.format_messages(input=input_prompt, reasoning=reasoning)
            ).content

            logger.warning(
                "[TOOL] verify_and_format DONE | response_chars=%s",
                len(str(out)),
            )
            return str(out)

        tools = [draft_reasoning, verify_and_format]

        agent_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You MUST:\n"
                    "1) call draft_reasoning\n"
                    "2) call verify_and_format\n"
                    "3) return verify_and_format output ONLY",
                ),
                ("user", "{input}"),
                MessagesPlaceholder("agent_scratchpad"),
            ]
        )

        agent = create_openai_tools_agent(llm, tools, agent_prompt)

        logger.warning("Agent built successfully")
        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=self._debug,
            max_iterations=4,
            return_intermediate_steps=True,
        )

    # ---------------- Plain fallback ----------------
    def _call_llm_plain(self, prompt: str) -> str:
        headers = {"Authorization": f"Bearer {self._api_key}"}
        payload = {
            "model": self._model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": "You are a strict JSON generator."},
                {"role": "user", "content": prompt},
            ],
        }

        url = f"{self._api_base}/chat/completions"
        with httpx.Client(timeout=self._timeout) as client:
            r = client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]

    # ---------------- Utils ----------------
    @staticmethod
    def _normalize_base_url(url: str) -> str:
        url = url.rstrip("/")
        return re.sub(r"/chat/completions$", "", url)


# ===================================================
#                   HELPERS
# ===================================================
def _extract_agent_content(result: dict[str, Any]) -> str:
    output = str(result.get("output", "")).strip()
    try:
        _parse_json_response(output)
        return output
    except json.JSONDecodeError:
        pass

    for step in reversed(result.get("intermediate_steps", []) or []):
        if not isinstance(step, (tuple, list)) or len(step) < 2:
            continue
        tool_output = str(step[1]).strip()
        if not tool_output:
            continue
        try:
            _parse_json_response(tool_output)
        except json.JSONDecodeError:
            continue
        return tool_output

    return output


def _parse_json_response(content: str) -> dict[str, Any]:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", content, re.DOTALL)
        if not m:
            raise
        return json.loads(m.group(0))


def _to_score_result(data: dict[str, Any], mode: str) -> ScoreResult:
    items = [
        ItemScoreResult(
            score=float(i.get("score", 0)),
            feedback=str(i.get("feedback", "")),
        )
        for i in data.get("items", [])
    ]
    return ScoreResult(
        score=float(data.get("score", 0)),
        feedback=str(data.get("feedback", "")),
        items=items,
        mode=mode,
    )


def _score_from_answer_key(
    task: Task, user_answers: list[str]
) -> ScoreResult | None:
    items = task.pairs()
    if not items:
        return None

    item_scores: list[ItemScoreResult] = []
    for idx, item in enumerate(items):
        if item.answer_schema is None:
            return None
        user_answer = user_answers[idx] if idx < len(user_answers) else ""
        score, feedback = _score_expected_answer(item.answer_schema, user_answer)
        item_scores.append(ItemScoreResult(score=round(score, 2), feedback=feedback))

    total = sum(item.score for item in item_scores) / len(item_scores)
    total = round(total, 2)
    feedback = (
        "Checked against the answer key. Nice work."
        if total >= 80
        else "Checked against the answer key. Review the missed answers and try again."
    )
    return ScoreResult(score=total, feedback=feedback, items=item_scores, mode="answer_key")


def _score_expected_answer(expected: Any, user_answer: str) -> tuple[float, str]:
    expected_pairs = _parse_match_pairs(expected)
    user_pairs = _parse_match_pairs(user_answer)
    if expected_pairs and user_pairs:
        correct_keys = [
            key
            for key, value in expected_pairs.items()
            if user_pairs.get(key) == value
        ]
        wrong_keys = [
            key
            for key in expected_pairs
            if key in user_pairs and user_pairs[key] != expected_pairs[key]
        ]
        missing_keys = [key for key in expected_pairs if key not in user_pairs]
        total = len(expected_pairs)
        score = len(correct_keys) / total * 100 if total else 0.0
        feedback = f"Correct matches: {len(correct_keys)}/{total}."
        review_keys = wrong_keys + missing_keys
        if review_keys:
            feedback += f" Review: {', '.join(review_keys)}."
        return score, feedback

    expected_values = _expected_values(expected)
    if len(expected_values) > 1:
        user_values = _split_answer_values(user_answer)
        correct = 0
        for idx, expected_value in enumerate(expected_values):
            if idx >= len(user_values):
                continue
            if _normalize_answer(user_values[idx]) == _normalize_answer(expected_value):
                correct += 1
        total = len(expected_values)
        score = correct / total * 100 if total else 0.0
        return score, f"Correct answers in order: {correct}/{total}."

    expected_text = expected_values[0] if expected_values else ""
    if _normalize_answer(user_answer) == _normalize_answer(expected_text):
        return 100.0, "Correct."
    return 0.0, f"Expected answer: {expected_text}."


def _expected_values(expected: Any) -> list[str]:
    if isinstance(expected, list):
        return [str(value) for value in expected]
    return [str(expected)]


def _split_answer_values(answer: str) -> list[str]:
    values = [part.strip() for part in re.split(r"[,;\n]+", answer) if part.strip()]
    return values if values else [answer.strip()]


def _parse_match_pairs(value: Any) -> dict[str, str]:
    text = ", ".join(_expected_values(value))
    pairs: dict[str, str] = {}
    for key, match_value in re.findall(
        r"\b([A-Za-z])\s*[-:]\s*([0-9]+|[A-Za-z])\b", text
    ):
        pairs[key.upper()] = match_value.lower()
    return pairs


def _normalize_answer(answer: str) -> str:
    text = answer.lower().strip().replace("’", "'")
    contractions = {
        "i'm": "i am",
        "you're": "you are",
        "he's": "he is",
        "she's": "she is",
        "it's": "it is",
        "we're": "we are",
        "they're": "they are",
    }
    for contraction, expanded in contractions.items():
        text = text.replace(contraction, expanded)
    text = text.replace("-", " ")
    text = re.sub(r"[^a-z0-9\s]", "", text)
    return re.sub(r"\s+", " ", text).strip()
