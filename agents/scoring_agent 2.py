"""
agents/scoring_agent.py
Scoring agent: sends question + answer + context + ontology + marking guide
to a local OLLAMA model and parses the structured score response.
"""

import json
import re
import requests
from typing import Dict, List, Optional

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma3:4b"  # Default model — auto-detected at runtime from installed models

# ── Marking guides (criteria + max marks) ─────────────────────────────────────

MARKING_GUIDES: Dict[int, Dict] = {
    1: {
        "question_en": "Describe the role of Buddhism in the Anuradhapura period.",
        "question_si": "අනුරාධපුර යුගයේ බෞද්ධ ආගමේ භූමිකාව සවිස්තරව විස්තර කරන්න.",
        "criteria": [
            {"id": "C1", "description": "Buddhism's arrival - Mahinda Thero's mission (247 BCE), King Devanampiya Tissa's conversion", "max_marks": 4},
            {"id": "C2", "description": "Religious monuments built - Thuparamaya, Ruwanwelisaya, Jetavanaramaya, Abhayagiri", "max_marks": 4},
            {"id": "C3", "description": "Role of monasteries and Sangha in education, culture, social welfare", "max_marks": 4},
            {"id": "C4", "description": "Writing of Pali Canon (Aluvihara) and Mahavamsa chronicle", "max_marks": 4},
            {"id": "C5", "description": "Buddhism's influence on kingship, state policy, national identity", "max_marks": 4},
        ]
    },
    2: {
        "question_en": "Describe the irrigation civilization of the Anuradhapura kingdom.",
        "question_si": "අනුරාධපුර රාජධානියේ වාරිමාර්ග ශිෂ්ටාචාරය ගැන ඔබ දන්නා දේ විස්තර කරන්න.",
        "criteria": [
            {"id": "C1", "description": "Importance of irrigation for rice cultivation and population support", "max_marks": 4},
            {"id": "C2", "description": "Key tanks and builders (Tissa Wewa, Minneriya, Abhaya Wewa, Kalawewa)", "max_marks": 4},
            {"id": "C3", "description": "Bisokotuwa (sluice) technology - unique engineering achievement", "max_marks": 4},
            {"id": "C4", "description": "Interconnected tank systems, canals, and distribution networks", "max_marks": 4},
            {"id": "C5", "description": "Irrigation as religious duty, royal responsibility, merit-making", "max_marks": 4},
        ]
    },
    3: {
        "question_en": "Describe the contributions of King Dutugamunu to Sri Lankan history.",
        "question_si": "රජ දුටුගැමුණු ශ්‍රී ලංකා ඉතිහාසයට කළ දායකත්වය විස්තර කරන්න.",
        "criteria": [
            {"id": "C1", "description": "Military campaign - unification of Sri Lanka, defeating King Elara", "max_marks": 4},
            {"id": "C2", "description": "Religious monuments - Ruwanwelisaya, Mirisawetiya, Lohaprasada", "max_marks": 4},
            {"id": "C3", "description": "Significance of defeating Elara for Sinhala Buddhist national identity", "max_marks": 4},
            {"id": "C4", "description": "Role in establishing Buddhist state and patronage of religion", "max_marks": 4},
            {"id": "C5", "description": "Legacy recorded in Mahavamsa", "max_marks": 4},
        ]
    },
    4: {
        "question_en": "Describe the administrative system of the Anuradhapura kingdom.",
        "question_si": "අනුරාධපුර රාජධානියේ පාලන ක්‍රමය පිළිබඳව විස්තර කරන්න.",
        "criteria": [
            {"id": "C1", "description": "King as supreme ruler - role, duties, divine status", "max_marks": 4},
            {"id": "C2", "description": "Council of ministers (Amatyas) and advisory roles", "max_marks": 4},
            {"id": "C3", "description": "City organization - planned capital, founded by Pandukabhaya", "max_marks": 4},
            {"id": "C4", "description": "Provincial administration - regional governors", "max_marks": 4},
            {"id": "C5", "description": "Justice system and social order", "max_marks": 4},
        ]
    },
    5: {
        "question_en": "Write about the causes of decline of the Anuradhapura kingdom and its legacy.",
        "question_si": "අනුරාධපුර රාජධානිය පරිහානියට පත් වීමට හේතු සහ ඒ රාජධානියේ උරුමය ගැන ලියන්න.",
        "criteria": [
            {"id": "C1", "description": "South Indian (Chola) invasions - repeated attacks", "max_marks": 4},
            {"id": "C2", "description": "Internal power struggles and succession conflicts", "max_marks": 4},
            {"id": "C3", "description": "Vijayabahu I's resistance and capital transfer to Polonnaruwa (1017 CE)", "max_marks": 4},
            {"id": "C4", "description": "Architectural and cultural legacy - monuments still standing", "max_marks": 4},
            {"id": "C5", "description": "Hydraulic civilization legacy influencing later kingdoms", "max_marks": 4},
        ]
    }
}


# ── OLLAMA interface ──────────────────────────────────────────────────────────

def call_ollama(prompt: str, model: str = OLLAMA_MODEL) -> str:
    """Send a prompt to OLLAMA and return the response text."""
    try:
        # Build options — keep tokens low on RAM-constrained machines
        options = {
            "temperature": 0.1,
            "num_predict": 600,   # Enough for JSON score block; was 1500 (caused OOM)
            "num_ctx": 2048,      # Limit context window to save RAM
        }

        # Qwen3 models have a "thinking" mode that uses extra RAM/tokens.
        # Disable it by appending /no_think to the model name if needed.
        run_model = model
        if "qwen3" in model.lower():
            options["think"] = False  # ollama ≥0.6 flag

        payload = {
            "model": run_model,
            "prompt": prompt,
            "stream": False,
            "options": options,
        }
        # CPU-only inference is slow — allow up to 5 minutes per request
        resp = requests.post(OLLAMA_URL, json=payload, timeout=300)
        resp.raise_for_status()
        return resp.json().get("response", "")
    except requests.exceptions.ConnectionError:
        return "__OLLAMA_UNAVAILABLE__"
    except requests.exceptions.Timeout:
        return "__TIMEOUT__"
    except Exception as e:
        return f"__ERROR__: {str(e)}"


def get_available_model() -> str:
    """Check which models are available on the local OLLAMA instance."""
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        models = resp.json().get("models", [])
        if models:
            return models[0]["name"]
    except Exception:
        pass
    return OLLAMA_MODEL


# ── Scoring agent ─────────────────────────────────────────────────────────────

class ScoringAgent:
    """
    Agent responsibility: score the student answer using OLLAMA
    with RAG context + ontology enrichment + marking guide.
    """

    def __init__(self):
        self.model = get_available_model()
        print(f"[Scoring Agent] Using OLLAMA model: {self.model}")

    def build_prompt(
        self,
        question_id: int,
        student_answer: str,
        rag_context: str,
        ontology_enrichment: str,
    ) -> str:
        guide = MARKING_GUIDES[question_id]
        criteria_text = "\n".join(
            f"  {c['id']}: {c['description']} [max {c['max_marks']}]"
            for c in guide["criteria"]
        )

        # Trim context to save RAM during inference — 600 chars is enough signal
        short_rag = rag_context[:600] if rag_context else "N/A"
        short_onto = ontology_enrichment[:400] if ontology_enrichment else "N/A"

        prompt = f"""You are a Sri Lankan History examiner. Grade the Sinhala student answer below.

QUESTION: {guide['question_en']}

MARKING CRITERIA (total 20 marks):
{criteria_text}

RELEVANT CONTEXT:
{short_rag}

CONCEPTS IN ANSWER: {short_onto}

STUDENT ANSWER (Sinhala):
{student_answer}

TASK: Award marks for each criterion. Output ONLY this JSON, no other text:
{{"criteria_scores":[{{"id":"C1","awarded":0,"max":4,"justification":""}},{{"id":"C2","awarded":0,"max":4,"justification":""}},{{"id":"C3","awarded":0,"max":4,"justification":""}},{{"id":"C4","awarded":0,"max":4,"justification":""}},{{"id":"C5","awarded":0,"max":4,"justification":""}}],"total_score":0,"overall_feedback":"","strengths":"","improvements":""}}"""
        return prompt

    def score(
        self,
        question_id: int,
        student_answer: str,
        rag_context: str,
        ontology_enrichment: str,
    ) -> Dict:
        """Score an answer and return structured result."""
        prompt = self.build_prompt(question_id, student_answer, rag_context, ontology_enrichment)
        raw_response = call_ollama(prompt, self.model)

        if raw_response in ("__OLLAMA_UNAVAILABLE__", "__TIMEOUT__"):
            return self._fallback_score(question_id, student_answer)

        if raw_response.startswith("__ERROR__"):
            return {"error": raw_response, "total_score": 0}

        return self._parse_response(raw_response, question_id, student_answer)

    def _parse_response(self, raw: str, question_id: int, student_answer: str) -> Dict:
        """Extract JSON from OLLAMA response."""
        # Try to find JSON block
        json_match = re.search(r'\{[\s\S]*\}', raw)
        if json_match:
            try:
                result = json.loads(json_match.group())
                # Validate and clamp scores
                for cs in result.get("criteria_scores", []):
                    cs["awarded"] = max(0, min(cs["awarded"], cs["max"]))
                # Recalculate total to be safe
                result["total_score"] = sum(
                    cs["awarded"] for cs in result.get("criteria_scores", [])
                )
                result["question_id"] = question_id
                result["raw_answer"] = student_answer
                return result
            except json.JSONDecodeError:
                pass

        # Fallback: parse manually
        return self._fallback_score(question_id, student_answer, raw_text=raw)

    def _fallback_score(
        self, question_id: int, student_answer: str, raw_text: str = ""
    ) -> Dict:
        """
        Keyword-based fallback scoring when OLLAMA is unavailable.
        Uses simple heuristics based on answer length and keyword presence.
        """
        guide = MARKING_GUIDES[question_id]
        answer_lower = student_answer.lower()
        answer_len = len(student_answer.split())

        # Keyword sets per question
        keyword_sets = {
            1: [["මිහිඳු", "mahinda", "devanampiya", "දේවානම්පිය"],
                ["ථූපාරාමය", "රුවන්වැලිසාය", "ජේතවනාරාමය", "thuparamaya"],
                ["විහාර", "සංඝ", "sangha", "monastery"],
                ["මහාවංශ", "පාලි", "mahavamsa", "pali"],
                ["රජ", "රාජ්‍ය", "king", "state"]],
            2: [["වාරිමාර්ග", "irrigation", "වැව"],
                ["මිනේරිය", "minneriya", "තිස්සවැව", "tissa"],
                ["බිසොකොටුව", "bisokotuwa", "sluice"],
                ["ඇළ", "canal", "ජල"],
                ["ගොවිතැන", "rice", "agriculture"]],
            3: [["ඉලාරා", "elara", "සටන"],
                ["රුවන්වැලිසාය", "රජ", "රාජ"],
                ["ජාතික", "sinhala", "sinhalese"],
                ["බෞද්ධ", "buddhist", "ආගම"],
                ["මහාවංශ", "mahavamsa"]],
            4: [["රජ", "king", "supreme"],
                ["ඇමති", "minister", "amatya"],
                ["නගරය", "city", "pandukabhaya"],
                ["පළාත", "province", "regional"],
                ["යුක්තිය", "justice", "law"]],
            5: [["චෝල", "chola", "invasion"],
                ["දේශීය", "internal", "ගැටුම"],
                ["විජයබාහු", "vijayabahu", "polonnaruwa"],
                ["ස්මාරක", "monument", "legacy"],
                ["ජල", "hydraulic", "irrigation"]],
        }

        criteria_scores = []
        total = 0
        keywords = keyword_sets.get(question_id, [[] for _ in range(5)])

        for i, c in enumerate(guide["criteria"]):
            kws = keywords[i] if i < len(keywords) else []
            found = any(kw in answer_lower for kw in kws)
            # Award partial marks based on keyword presence and answer length
            if found and answer_len > 20:
                awarded = 3
            elif found:
                awarded = 2
            elif answer_len > 50:
                awarded = 1
            else:
                awarded = 0
            criteria_scores.append({
                "id": c["id"],
                "awarded": awarded,
                "max": c["max_marks"],
                "justification": ("Relevant keywords/concepts found in answer." if found
                                  else "Criterion not clearly addressed in answer.")
            })
            total += awarded

        return {
            "question_id": question_id,
            "criteria_scores": criteria_scores,
            "total_score": total,
            "overall_feedback": (
                "Score based on keyword analysis (OLLAMA unavailable). "
                "Please ensure OLLAMA is running for detailed AI scoring."
            ),
            "strengths": "Answer contains some relevant content.",
            "improvements": "Please run with OLLAMA for detailed feedback.",
            "raw_answer": student_answer,
            "fallback_mode": True,
        }


# ── Singleton ─────────────────────────────────────────────────────────────────
_scoring_agent: Optional[ScoringAgent] = None

def get_scoring_agent() -> ScoringAgent:
    global _scoring_agent
    if _scoring_agent is None:
        _scoring_agent = ScoringAgent()
    return _scoring_agent
