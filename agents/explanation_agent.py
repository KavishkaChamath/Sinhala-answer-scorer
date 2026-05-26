"""
agents/explanation_agent.py
Explanation agent: takes the structured score from the Scoring Agent
and produces a clear, evidence-grounded, human-readable explanation.
"""

from typing import Dict, List
from agents.scoring_agent import MARKING_GUIDES


class ExplanationAgent:
    """
    Agent responsibility: transform raw score dicts into
    clear, formatted, evidence-based explanations for the Streamlit UI.
    """

    def build_explanation(
        self,
        score_result: Dict,
        ontology_enrichment: str,
        rag_context: str,
    ) -> Dict:
        """
        Return a dict with:
          - score_table: list of dicts for tabular display
          - total_score: int
          - feedback_html: formatted HTML string for Streamlit
          - grade: letter grade
          - ontology_note: ontology-based observation
        """
        question_id = score_result.get("question_id", 1)
        guide = MARKING_GUIDES[question_id]
        criteria_scores = score_result.get("criteria_scores", [])
        total = score_result.get("total_score", 0)

        # Build score table rows
        score_table = []
        for cs in criteria_scores:
            crit_id = cs["id"]
            crit_desc = next(
                (c["description"] for c in guide["criteria"] if c["id"] == crit_id),
                crit_id
            )
            score_table.append({
                "Criterion": crit_id,
                "Description": crit_desc,
                "Awarded": cs["awarded"],
                "Max": cs["max"],
                "Justification": cs.get("justification", ""),
            })

        grade = self._letter_grade(total)
        feedback_html = self._build_feedback_html(score_result, score_table, grade)
        ontology_note = self._summarize_ontology(ontology_enrichment)

        return {
            "score_table": score_table,
            "total_score": total,
            "grade": grade,
            "feedback_html": feedback_html,
            "ontology_note": ontology_note,
            "overall_feedback": score_result.get("overall_feedback", ""),
            "strengths": score_result.get("strengths", ""),
            "improvements": score_result.get("improvements", ""),
            "fallback_mode": score_result.get("fallback_mode", False),
        }

    def _letter_grade(self, score: int) -> str:
        if score >= 18:   return "A+"
        elif score >= 16: return "A"
        elif score >= 14: return "B+"
        elif score >= 12: return "B"
        elif score >= 10: return "C+"
        elif score >= 8:  return "C"
        elif score >= 6:  return "D"
        else:             return "F"

    def _build_feedback_html(
        self, score_result: Dict, score_table: List[Dict], grade: str
    ) -> str:
        total = score_result.get("total_score", 0)
        pct = (total / 20) * 100

        color = ("#2ecc71" if total >= 14 else
                 "#f39c12" if total >= 10 else "#e74c3c")

        rows = ""
        for row in score_table:
            bar_pct = int((row["Awarded"] / row["Max"]) * 100)
            bar_color = ("#27ae60" if bar_pct >= 75 else
                         "#f39c12" if bar_pct >= 50 else "#e74c3c")
            rows += f"""
            <tr>
              <td><b>{row['Criterion']}</b></td>
              <td style="font-size:0.85em">{row['Description']}</td>
              <td style="text-align:center">
                <span style="color:{bar_color};font-weight:bold">
                  {row['Awarded']}/{row['Max']}
                </span>
              </td>
              <td style="font-size:0.82em;color:#555">{row['Justification']}</td>
            </tr>"""

        html = f"""
<div style="font-family: 'Segoe UI', sans-serif; max-width: 900px;">
  <div style="text-align:center; padding:20px; background: linear-gradient(135deg, #1a1a2e, #16213e);
              border-radius: 12px; color: white; margin-bottom: 20px;">
    <div style="font-size: 3em; font-weight:900; color:{color}">{total}/20</div>
    <div style="font-size: 1.8em; color: #aaa;">Grade: <b style="color:white">{grade}</b></div>
    <div style="margin-top:8px; color: #ccc;">{pct:.0f}% — {self._performance_label(total)}</div>
  </div>

  <h3 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 6px;">
    📊 Mark Breakdown
  </h3>
  <table style="width:100%; border-collapse:collapse; font-size:0.9em;">
    <thead>
      <tr style="background:#3498db; color:white;">
        <th style="padding:8px">Criterion</th>
        <th style="padding:8px">Description</th>
        <th style="padding:8px">Score</th>
        <th style="padding:8px">Justification</th>
      </tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>

  <div style="margin-top:20px; padding:15px; background:#f8f9fa; border-radius:8px;
              border-left:4px solid #3498db;">
    <h4 style="margin:0 0 8px; color:#2c3e50">📝 Overall Feedback</h4>
    <p style="margin:0; color:#555">{score_result.get('overall_feedback', '')}</p>
  </div>

  <div style="display:grid; grid-template-columns:1fr 1fr; gap:15px; margin-top:15px;">
    <div style="padding:15px; background:#eafaf1; border-radius:8px; border-left:4px solid #2ecc71;">
      <h4 style="margin:0 0 8px; color:#27ae60">✅ Strengths</h4>
      <p style="margin:0; color:#555; font-size:0.9em">{score_result.get('strengths', 'N/A')}</p>
    </div>
    <div style="padding:15px; background:#fef9e7; border-radius:8px; border-left:4px solid #f39c12;">
      <h4 style="margin:0 0 8px; color:#d68910">💡 Areas for Improvement</h4>
      <p style="margin:0; color:#555; font-size:0.9em">{score_result.get('improvements', 'N/A')}</p>
    </div>
  </div>
</div>"""
        return html

    def _performance_label(self, score: int) -> str:
        if score >= 18:   return "Excellent"
        elif score >= 14: return "Very Good"
        elif score >= 10: return "Satisfactory"
        elif score >= 6:  return "Needs Improvement"
        else:             return "Unsatisfactory"

    def _summarize_ontology(self, ontology_enrichment: str) -> str:
        if not ontology_enrichment or "No specific" in ontology_enrichment:
            return "No ontology concepts were explicitly identified in the student answer."
        lines = ontology_enrichment.split("\n")
        concepts = [l for l in lines if l.strip().startswith("•")]
        if concepts:
            return (f"The answer referenced **{len(concepts)} ontology concept(s)**: "
                    + "; ".join(c.strip().lstrip("•").strip() for c in concepts[:3]))
        return ontology_enrichment[:200]


# ── Singleton ─────────────────────────────────────────────────────────────────
_explanation_agent = None

def get_explanation_agent() -> ExplanationAgent:
    global _explanation_agent
    if _explanation_agent is None:
        _explanation_agent = ExplanationAgent()
    return _explanation_agent
