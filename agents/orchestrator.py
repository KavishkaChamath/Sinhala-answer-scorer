"""
agents/orchestrator.py
Orchestrator agent: coordinates the full pipeline —
  RAG Agent → Ontology → Scoring Agent → Explanation Agent
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.rag_agent import get_rag_agent
from agents.scoring_agent import get_scoring_agent, MARKING_GUIDES
from agents.explanation_agent import get_explanation_agent
from ontology.anuradhapura_ontology import ontology as onto
from typing import Dict


class OrchestratorAgent:
    """
    Top-level agent that manages the full scoring workflow.

    Workflow:
    1. RAG Agent    → retrieve relevant context chunks
    2. Ontology     → extract & enrich concepts from student answer
    3. Scoring Agent→ LLM-based mark assignment per criterion
    4. Explanation  → build clear breakdown + feedback
    """

    def __init__(self):
        self.rag = get_rag_agent()
        self.scorer = get_scoring_agent()
        self.explainer = get_explanation_agent()

    def run(self, question_id: int, student_answer: str) -> Dict:
        """
        Execute the full pipeline and return a complete result dict.
        """

        # ── Step 1: RAG retrieval ─────────────────────────────────────────────
        print(f"[Orchestrator] Step 1: RAG retrieval for Q{question_id}")
        guide = MARKING_GUIDES[question_id]
        rag_context = self.rag.get_context(
            question=guide["question_en"],
            student_answer=student_answer,
            top_k=5
        )

        # ── Step 2: Ontology enrichment ───────────────────────────────────────
        print(f"[Orchestrator] Step 2: Ontology enrichment")
        concepts_found = onto.extract_concepts_from_sinhala(student_answer)
        ontology_enrichment = onto.enrich_explanation(concepts_found)

        # ── Step 3: Scoring via OLLAMA ────────────────────────────────────────
        print(f"[Orchestrator] Step 3: Scoring with OLLAMA")
        score_result = self.scorer.score(
            question_id=question_id,
            student_answer=student_answer,
            rag_context=rag_context,
            ontology_enrichment=ontology_enrichment,
        )

        # ── Step 4: Explanation generation ───────────────────────────────────
        print(f"[Orchestrator] Step 4: Generating explanation")
        explanation = self.explainer.build_explanation(
            score_result=score_result,
            ontology_enrichment=ontology_enrichment,
            rag_context=rag_context,
        )

        # ── Combine all outputs ───────────────────────────────────────────────
        return {
            "question_id": question_id,
            "question_si": guide["question_si"],
            "question_en": guide["question_en"],
            "student_answer": student_answer,
            "rag_context": rag_context,
            "ontology_enrichment": ontology_enrichment,
            "concepts_found": [c["concept"] for c in concepts_found],
            **explanation,
        }


# ── Singleton ─────────────────────────────────────────────────────────────────
_orchestrator: OrchestratorAgent | None = None

def get_orchestrator() -> OrchestratorAgent:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = OrchestratorAgent()
    return _orchestrator


if __name__ == "__main__":
    orch = get_orchestrator()
    result = orch.run(
        question_id=3,
        student_answer="දුටුගැමුණු රජු ඉලාරා රජු පරාජය කොට ශ්‍රී ලංකාව එක් රාජ්‍යයක් ලෙස සංස්ථාපිත කළේය. ඔහු රුවන්වැලිසාය ස්තූපය ඉදිකළ අතර බෞද්ධ ආගමේ ශ්‍රේෂ්ඨ ආරක්‍ෂකයෙකු ලෙස ගෞරවයට පාත්‍ර විය."
    )
    print(f"\nTotal Score: {result['total_score']}/20  Grade: {result['grade']}")
    print(f"Concepts found: {result['concepts_found']}")
