"""
agents/scoring_agent.py
Two-stage scoring to prevent JSON truncation on Sinhala text:
  Stage 1: scores only (numbers) — very short output, never truncates
  Stage 2: Sinhala feedback for each criterion — called separately
Plus: JSON repair logic that recovers partial responses.
"""

import json
import re
import requests
from typing import Dict, List, Optional

OLLAMA_BASE  = "http://localhost:11434"
OLLAMA_URL   = f"{OLLAMA_BASE}/api/generate"
OLLAMA_MODEL = "gemma3:4b"


# ── Marking guides ────────────────────────────────────────────────────────────

MARKING_GUIDES: Dict[int, Dict] = {
    1: {
        "question_en": "Describe the role of Buddhism in the Anuradhapura period.",
        "question_si": "අනුරාධපුර යුගයේ බෞද්ධ ආගමේ භූමිකාව සවිස්තරව විස්තර කරන්න.",
        "criteria": [
            {"id":"C1","max_marks":4,
             "description":   "Buddhism's arrival - Mahinda Thero (247 BCE), Devanampiya Tissa conversion",
             "description_si":"බෞද්ධ ධර්මයේ පැමිණීම — මිහිඳු හිමි (ක්‍රි.පූ. 247), දේවානම්පිය තිස්ස රජු"},
            {"id":"C2","max_marks":4,
             "description":   "Religious monuments - Thuparamaya, Ruwanwelisaya, Jetavanaramaya, Abhayagiri",
             "description_si":"ආගමික ස්මාරක — ථූපාරාමය, රුවන්වැලිසාය, ජේතවනාරාමය, අභයගිරිය"},
            {"id":"C3","max_marks":4,
             "description":   "Monasteries and Sangha in education, culture, social welfare",
             "description_si":"විහාරස්ථාන හා සංඝ ශාසනය — අධ්‍යාපනය, සංස්කෘතිය, සමාජ සේවය"},
            {"id":"C4","max_marks":4,
             "description":   "Writing of Pali Canon (Aluvihara) and Mahavamsa chronicle",
             "description_si":"පාලි ත්‍රිපිටකය (අළුවිහාර) සහ මහාවංශ ක්‍රෝනිකලය"},
            {"id":"C5","max_marks":4,
             "description":   "Buddhism's influence on kingship, state policy, national identity",
             "description_si":"රාජ්‍ය පාලනය හා ජාතික අනන්‍යතාව කෙරෙහි බෞද්ධ ආගමේ බලපෑම"},
        ]
    },
    2: {
        "question_en": "Describe the irrigation civilization of the Anuradhapura kingdom.",
        "question_si": "අනුරාධපුර රාජධානියේ වාරිමාර්ග ශිෂ්ටාචාරය ගැන ඔබ දන්නා දේ විස්තර කරන්න.",
        "criteria": [
            {"id":"C1","max_marks":4,
             "description":   "Importance of irrigation for rice cultivation and population support",
             "description_si":"වී ගොවිතැන හා ජනගහනය සඳහා වාරිමාර්ගයේ වැදගත්කම"},
            {"id":"C2","max_marks":4,
             "description":   "Key tanks and builders (Tissa Wewa, Minneriya, Abhaya Wewa, Kalawewa)",
             "description_si":"ප්‍රධාන ජලාශ හා ඉදිකළ රජවරු — තිස්සවැව, මිනේරිය, අභයවැව, කලාවැව"},
            {"id":"C3","max_marks":4,
             "description":   "Bisokotuwa sluice technology - unique engineering achievement",
             "description_si":"බිසොකොටුව තාක්‍ෂණය — අද්විතීය ඉංජිනේරු ජයග්‍රහණය"},
            {"id":"C4","max_marks":4,
             "description":   "Interconnected tank systems, canals and distribution networks",
             "description_si":"අන්තර් සම්බන්ධිත ජලාශ, ඇළ මාර්ග හා ජල බෙදාහැරීමේ ජාලය"},
            {"id":"C5","max_marks":4,
             "description":   "Irrigation as religious duty, royal responsibility, merit-making",
             "description_si":"වාරිමාර්ගය ආගමික යුතුකමක් හා රාජකීය වගකීමකි"},
        ]
    },
    3: {
        "question_en": "Describe the contributions of King Dutugamunu to Sri Lankan history.",
        "question_si": "රජ දුටුගැමුණු ශ්‍රී ලංකා ඉතිහාසයට කළ දායකත්වය විස්තර කරන්න.",
        "criteria": [
            {"id":"C1","max_marks":4,
             "description":   "Military campaign - unification of Sri Lanka, defeating King Elara",
             "description_si":"යුද්ධ ව්‍යාපාරය — ශ්‍රී ලංකාව ඒකීය කිරීම, ඉලාරා රජු පරාජය"},
            {"id":"C2","max_marks":4,
             "description":   "Religious monuments - Ruwanwelisaya, Mirisawetiya, Lohaprasada",
             "description_si":"ආගමික ස්මාරක — රුවන්වැලිසාය, මිරිසවැටිය, ලෝහාපාසාද"},
            {"id":"C3","max_marks":4,
             "description":   "Significance of defeating Elara for Sinhala Buddhist national identity",
             "description_si":"ඉලාරා පරාජයේ වැදගත්කම — සිංහල බෞද්ධ ජාතික අනන්‍යතාව"},
            {"id":"C4","max_marks":4,
             "description":   "Role in establishing Buddhist state and patronage of religion",
             "description_si":"බෞද්ධ රාජ්‍යය ස්ථාපිත කිරීම හා ආගමට ආරාධනය"},
            {"id":"C5","max_marks":4,
             "description":   "Legacy recorded in Mahavamsa",
             "description_si":"මහාවංශ ග්‍රන්ථයෙහි සටහන් කළ උරුමය"},
        ]
    },
    4: {
        "question_en": "Describe the administrative system of the Anuradhapura kingdom.",
        "question_si": "අනුරාධපුර රාජධානියේ පාලන ක්‍රමය පිළිබඳව විස්තර කරන්න.",
        "criteria": [
            {"id":"C1","max_marks":4,
             "description":   "King as supreme ruler - role, duties, divine status",
             "description_si":"රජු ශ්‍රේෂ්ඨ පාලකයා ලෙස — භූමිකාව, යුතුකම්, දිව්‍ය තත්ත්වය"},
            {"id":"C2","max_marks":4,
             "description":   "Council of ministers (Amatyas) and advisory roles",
             "description_si":"අමාත්‍ය මණ්ඩලය (අමාත්‍යවරු) හා උපදේශක භූමිකාව"},
            {"id":"C3","max_marks":4,
             "description":   "City organization - planned capital, founded by Pandukabhaya",
             "description_si":"නගර සංවිධානය — පණ්ඩුකාභය රජු විසින් සැලසුම් සහිත අගනගරය"},
            {"id":"C4","max_marks":4,
             "description":   "Provincial administration - regional governors",
             "description_si":"පළාත් පාලනය — ප්‍රාදේශීය ආණ්ඩුකාරවරු"},
            {"id":"C5","max_marks":4,
             "description":   "Justice system and social order",
             "description_si":"යුක්ති ක්‍රමය හා සමාජ සාමය"},
        ]
    },
    5: {
        "question_en": "Write about the causes of decline of the Anuradhapura kingdom and its legacy.",
        "question_si": "අනුරාධපුර රාජධානිය පරිහානියට පත් වීමට හේතු සහ ඒ රාජධානියේ උරුමය ගැන ලියන්න.",
        "criteria": [
            {"id":"C1","max_marks":4,
             "description":   "South Indian (Chola) invasions - repeated attacks",
             "description_si":"දකුණු ඉන්දීය (චෝල) ආක්‍රමණ — නිතර නිතර සිදු වූ ප්‍රහාර"},
            {"id":"C2","max_marks":4,
             "description":   "Internal power struggles and succession conflicts",
             "description_si":"අභ්‍යන්තර බලතරඟ හා අනුක්‍රමික ගැටලු"},
            {"id":"C3","max_marks":4,
             "description":   "Vijayabahu I's resistance and capital transfer to Polonnaruwa (1017 CE)",
             "description_si":"විජයබාහු I ගේ ප්‍රතිරෝධය හා ක්‍රි.ව. 1017 දී පොළොන්නරු"},
            {"id":"C4","max_marks":4,
             "description":   "Architectural and cultural legacy - monuments still standing",
             "description_si":"ගෘහනිර්මාණ හා සාංස්කෘතික උරුමය — අදටත් පවතින ස්මාරක"},
            {"id":"C5","max_marks":4,
             "description":   "Hydraulic civilization legacy influencing later kingdoms",
             "description_si":"ජල ශිෂ්ටාචාරයේ උරුමය — පසුකාලීන රාජධානිවලට බලපෑම"},
        ]
    }
}


# ── OLLAMA helpers ────────────────────────────────────────────────────────────

def is_ollama_running() -> bool:
    try:
        r = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=4)
        return r.status_code == 200
    except Exception:
        return False


def get_available_model() -> str:
    try:
        r = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=5)
        models = r.json().get("models", [])
        if models:
            names = [m["name"] for m in models]
            for preferred in ["gemma3:4b","gemma3:12b","qwen3:4b","qwen3:8b",
                              "mistral","llama3.2","gemma3:1b","qwen2.5:1.5b"]:
                if preferred in names:
                    return preferred
            return names[0]
    except Exception:
        pass
    return OLLAMA_MODEL


def _call_stream(prompt: str, model: str, num_predict: int, num_ctx: int) -> str:
    """Core streaming call — shared by both stages."""
    options = {
        "temperature":    0.1,
        "num_predict":    num_predict,
        "num_ctx":        num_ctx,
        "repeat_penalty": 1.05,
    }
    if "qwen3" in model.lower():
        options["think"] = False

    collected = []
    try:
        with requests.post(
            OLLAMA_URL,
            json={"model": model, "prompt": prompt, "stream": True, "options": options},
            stream=True, timeout=(10, 300)
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                    collected.append(chunk.get("response", ""))
                    if chunk.get("done"):
                        break
                except json.JSONDecodeError:
                    continue
        return "".join(collected)
    except requests.exceptions.ConnectionError:
        return "__OLLAMA_UNAVAILABLE__"
    except requests.exceptions.Timeout:
        partial = "".join(collected)
        return partial if partial.strip() else "__TIMEOUT__"
    except Exception as e:
        return f"__ERROR__: {str(e)}"


# ── JSON repair utilities ─────────────────────────────────────────────────────

def _repair_json(raw: str) -> Optional[Dict]:
    """
    Try multiple strategies to extract valid JSON from a possibly truncated response.
    Strategy 1: direct parse after stripping markdown
    Strategy 2: extract scores with regex if JSON is too broken
    """
    clean = re.sub(r"```(?:json)?|```", "", raw).strip()

    # Strategy 1 — standard parse
    m = re.search(r'\{[\s\S]*\}', clean)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass

    # Strategy 2 — truncated JSON: try to close open braces/brackets
    fragment = m.group() if m else clean
    # Count unclosed braces/brackets and close them
    for _ in range(10):
        try:
            return json.loads(fragment)
        except json.JSONDecodeError as e:
            msg = str(e)
            # If truncated mid-string, close the string then close containers
            if "Unterminated string" in msg or "EOF" in msg or "delimiter" in msg:
                # Close any open string
                if fragment.count('"') % 2 == 1:
                    fragment += '"'
                # Close containers in reverse order
                opens = [c for c in fragment if c in '{[']
                closes = [c for c in fragment if c in '}]']
                pair = {'{':'}', '[':']'}
                for o in reversed(opens[len(closes):]):
                    fragment += pair[o]
            else:
                break

    # Strategy 3 — regex: extract any "awarded": N pairs found (even partial)
    awards = re.findall(r'"awarded"\s*:\s*(\d+)', raw)
    if awards:
        ids = ["C1","C2","C3","C4","C5"]
        scores = []
        for i in range(5):
            val = int(awards[i]) if i < len(awards) else 0
            scores.append({"id": ids[i], "awarded": min(val,4), "max": 4,
                           "justification": "AI ප්‍රතිචාරයෙන් ලකුණු ලබා ගන්නා ලදී."})
        print(f"[JSON repair] Recovered {len(awards)}/5 scores via regex")
        return {
            "criteria_scores":  scores,
            "total_score":      sum(s["awarded"] for s in scores),
            "overall_feedback": "",
            "strengths":        "",
            "improvements":     "",
        }

    return None


# ── Scoring agent ─────────────────────────────────────────────────────────────

class ScoringAgent:

    def __init__(self):
        self.model = get_available_model()
        print(f"[Scoring Agent] Using OLLAMA model: {self.model}")

    # ── Stage 1: scores only (compact, never truncates) ───────────────────────
    def _build_scores_prompt(self, question_id, student_answer, rag_context, ontology_enrichment) -> str:
        guide = MARKING_GUIDES[question_id]
        criteria_lines = "\n".join(
            f"{c['id']}(max {c['max_marks']}): {c['description']}"
            for c in guide["criteria"]
        )
        rag_snip  = (rag_context or "")[:500]
        onto_snip = (ontology_enrichment or "")[:200]

        # Ask ONLY for numbers + very short (10-word) justifications
        # This output is ~250 tokens max — never truncates
        return (
            f"You are a Sri Lankan History examiner grading a Sinhala answer.\n"
            f"QUESTION: {guide['question_en']}\n"
            f"CRITERIA:\n{criteria_lines}\n"
            f"CONTEXT: {rag_snip}\n"
            f"CONCEPTS: {onto_snip}\n"
            f"ANSWER: {student_answer}\n\n"
            f"Output ONLY this JSON. Keep each justification under 10 words. No markdown:\n"
            f'{{"C1":0,"C2":0,"C3":0,"C4":0,"C5":0,'
            f'"j1":"reason","j2":"reason","j3":"reason","j4":"reason","j5":"reason"}}'
        )

    # ── Stage 2: Sinhala feedback only (separate call) ────────────────────────
    def _build_feedback_prompt(self, question_id, student_answer, scores: Dict) -> str:
        guide  = MARKING_GUIDES[question_id]
        s_list = ", ".join(f"{k}:{v}" for k,v in scores.items() if k.startswith("C"))
        return (
            f"You graded a Sinhala answer for: {guide['question_en']}\n"
            f"Scores awarded: {s_list} (out of 4 each, total 20)\n"
            f"Student answer: {student_answer[:400]}\n\n"
            f"Write ONLY this JSON in Sinhala language. Keep each field under 20 words:\n"
            f'{{"overall":"සමස්ත ප්‍රතිඵලය","strengths":"ශක්තිමත් කරුණු","improvements":"වැඩිදියුණු කළ යුතු"}}'
        )

    def score(self, question_id, student_answer, rag_context, ontology_enrichment) -> Dict:
        if not is_ollama_running():
            print("[Scoring Agent] OLLAMA not reachable — keyword fallback")
            return self._fallback_score(question_id, student_answer)

        # ── Stage 1: Get scores (short output) ───────────────────────────────
        prompt1 = self._build_scores_prompt(
            question_id, student_answer, rag_context, ontology_enrichment
        )
        print(f"[Scoring Agent] Stage 1 prompt: {len(prompt1)} chars → {self.model}")
        raw1 = _call_stream(prompt1, self.model, num_predict=300, num_ctx=3000)
        print(f"[Scoring Agent] Stage 1 response: {raw1[:200]}")

        if raw1 in ("__OLLAMA_UNAVAILABLE__", "__TIMEOUT__") or raw1.startswith("__ERROR__"):
            return self._fallback_score(question_id, student_answer)

        scores_dict = _repair_json(raw1)
        if not scores_dict:
            print("[Scoring Agent] Stage 1 JSON parse failed — keyword fallback")
            return self._fallback_score(question_id, student_answer)

        # Normalise stage-1 compact format → standard format
        criteria_scores = self._normalise_scores(scores_dict, question_id)

        # ── Stage 2: Get Sinhala feedback (separate short call) ───────────────
        prompt2 = self._build_feedback_prompt(question_id, student_answer, scores_dict)
        print(f"[Scoring Agent] Stage 2 prompt: {len(prompt2)} chars")
        raw2 = _call_stream(prompt2, self.model, num_predict=200, num_ctx=2048)
        print(f"[Scoring Agent] Stage 2 response: {raw2[:150]}")

        fb = self._parse_feedback(raw2)
        total = sum(cs["awarded"] for cs in criteria_scores)

        if not fb.get("overall"):
            fb["overall"] = self._auto_feedback(total)

        result = {
            "question_id":      question_id,
            "criteria_scores":  criteria_scores,
            "total_score":      total,
            "overall_feedback": fb.get("overall", ""),
            "strengths":        fb.get("strengths", ""),
            "improvements":     fb.get("improvements", ""),
            "raw_answer":       student_answer,
            "fallback_mode":    False,
        }
        print(f"[Scoring Agent] Final score: {total}/20 ✓")
        return result

    def _normalise_scores(self, d: Dict, question_id: int) -> List[Dict]:
        """Convert stage-1 compact dict to standard criteria_scores list."""
        guide = MARKING_GUIDES[question_id]
        result = []
        for i, c in enumerate(guide["criteria"]):
            cid     = c["id"]
            num     = i + 1
            awarded = max(0, min(int(d.get(cid, 0)), c["max_marks"]))
            just_en = str(d.get(f"j{num}", "")).strip()
            # If justification is English, translate via a simple label
            just    = just_en if just_en else "ලකුණු AI ගණනය මත පදනම් වේ."
            result.append({"id": cid, "awarded": awarded,
                           "max": c["max_marks"], "justification": just})
        return result

    def _parse_feedback(self, raw: str) -> Dict:
        cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
        m = re.search(r'\{[\s\S]*\}', cleaned)
        if m:
            try:
                d = json.loads(m.group())
                return {
                    "overall":      d.get("overall", ""),
                    "strengths":    d.get("strengths", ""),
                    "improvements": d.get("improvements", ""),
                }
            except Exception:
                pass
        # Fallback: return raw as overall feedback
        text = cleaned[:200].strip()
        return {"overall": text if text else "", "strengths": "", "improvements": ""}

    def _auto_feedback(self, total: int) -> str:
        if   total >= 18: return "විශිෂ්ට පිළිතුරකි. සියලු නිර්ණායක හොඳින් ආවරණය කර ඇත."
        elif total >= 14: return "හොඳ පිළිතුරකි. ප්‍රධාන නිර්ණායක ආවරණය කර ඇත."
        elif total >= 10: return "සාමාන්‍ය පිළිතුරකි. වැඩිදියුණු කිරීමේ ඉඩ ඇත."
        elif total >= 6:  return "පිළිතුර අසම්පූර්ණයි. වැඩිදුර කරුණු ඇතුළත් කරන්න."
        else:             return "පිළිතුර ඉතා කෙටිය. සවිස්තරාත්මකව ලිවීම අවශ්‍යයි."

    def _generate_feedback(self, result: Dict, question_id: int) -> str:
        return self._auto_feedback(result.get("total_score", 0))

    def _fallback_score(self, question_id, student_answer, raw_text="") -> Dict:
        guide      = MARKING_GUIDES[question_id]
        ans_lower  = student_answer.lower()
        word_count = len(student_answer.split())

        keyword_sets = {
            1:[["මිහිඳු","mahinda","දේවානම්පිය","247"],
               ["ථූපාරාමය","රුවන්වැලිසාය","ජේතවනාරාමය","thuparamaya"],
               ["විහාර","සංඝ","sangha","මහාසංඝ"],
               ["මහාවංශ","පාලි","mahavamsa","අළුවිහාර","ත්‍රිපිටක"],
               ["රාජ්‍ය ආගම","රාජකීය","බෞද්ධ රාජ්‍ය"]],
            2:[["වාරිමාර්ග","ජලාශ","irrigation","වැව","ගොවිතැන"],
               ["මිනේරිය","minneriya","තිස්සවැව","කලාවැව","අභයවැව"],
               ["බිසොකොටුව","bisokotuwa","sluice","ජල ගේට්ටු"],
               ["ඇළ","canal","ජල බෙදා","ජල ජාලය"],
               ["ගොවිතැන","rice","කෘෂිකර්ම","රාජකීය","පිනකම"]],
            3:[["ඉලාරා","elara","සටන","ජය","යුද්ධ"],
               ["රුවන්වැලිසාය","මිරිසවැටිය","ලෝහාපාසාද"],
               ["ජාතික","sinhala","sinhalese","සිංහල"],
               ["බෞද්ධ","ආගම","දහම","ආගමික"],
               ["මහාවංශ","mahavamsa","ඉතිහාස"]],
            4:[["රජ","king","ශ්‍රේෂ්ඨ","supreme"],
               ["ඇමති","minister","අමාත්‍ය","amatya"],
               ["නගරය","city","පණ්ඩුකාභය","pandukabhaya"],
               ["පළාත","province","ප්‍රාදේශීය","regional"],
               ["යුක්තිය","justice","නීතිය","law"]],
            5:[["චෝල","chola","ආක්‍රමණ","invasion"],
               ["ගැටුම","internal","succession","බල ගැටලු"],
               ["විජයබාහු","vijayabahu","පොළොන්නරු","1017"],
               ["ස්මාරක","monument","උරුම","legacy"],
               ["ජල","hydraulic","වාරිමාර්ග","ශිෂ්ටාචාර"]],
        }

        total, cscores = 0, []
        for i, c in enumerate(guide["criteria"]):
            kws   = keyword_sets.get(question_id, [[]])[i] if i < 5 else []
            found = any(kw in ans_lower for kw in kws)
            if   found and word_count > 50: awarded = 3
            elif found and word_count > 20: awarded = 2
            elif found:                     awarded = 1
            elif word_count > 80:           awarded = 1
            else:                           awarded = 0
            cscores.append({
                "id": c["id"], "awarded": awarded, "max": c["max_marks"],
                "justification": (
                    "සම්බන්ධිත මූලපද හඳුනා ගන්නා ලදී." if found
                    else f"මෙම නිර්ණායකය ({c['description_si']}) ස්පර්ශ නොවේ."
                )
            })
            total += awarded

        return {
            "question_id":      question_id,
            "criteria_scores":  cscores,
            "total_score":      total,
            "overall_feedback": self._auto_feedback(total) + " (OLLAMA නොලැබීම — මූලපද ක්‍රමය)",
            "strengths":        "පිළිතුරේ සම්බන්ධිත ඓතිහාසික කරුණු ඇතුළත් වේ.",
            "improvements":     "OLLAMA සමඟ ධාවනය කළ විට සවිස්තරාත්මක ප්‍රතිඵල ලැබේ.",
            "raw_answer":       student_answer,
            "fallback_mode":    True,
        }


# ── Singleton ─────────────────────────────────────────────────────────────────
_scoring_agent: Optional[ScoringAgent] = None

def get_scoring_agent() -> ScoringAgent:
    global _scoring_agent
    if _scoring_agent is None:
        _scoring_agent = ScoringAgent()
    return _scoring_agent
