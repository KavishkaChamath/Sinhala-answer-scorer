"""
ontology/anuradhapura_ontology.py
Builds and queries an OWL-style ontology for the Anuradhapura Period
using owlready2 (falls back to a dict-based ontology if not installed).
"""

import json
from typing import Dict, List, Optional

# ── Dict-based ontology (always available, no extra deps) ──────────────────────

ONTOLOGY: Dict = {
    "concepts": {
        # Rulers
        "Pandukabhaya":        {"type": "Ruler", "period": "377–307 BCE", "contributions": ["founded Anuradhapura", "city planning", "Abhaya Wewa"]},
        "DevanampiyaTissa":    {"type": "Ruler", "period": "247–207 BCE", "contributions": ["accepted Buddhism", "Thuparamaya", "Tissa Wewa", "friendship with Ashoka"]},
        "Dutugamunu":          {"type": "Ruler", "period": "161–137 BCE", "contributions": ["unified Sri Lanka", "Ruwanwelisaya", "Mirisawetiya", "Lohaprasada", "defeated Elara"]},
        "Elara":               {"type": "Ruler", "period": "205–161 BCE", "contributions": ["just rule", "Tamil king"]},
        "Valagamba":           {"type": "Ruler", "period": "89–77 BCE",  "contributions": ["drove out Dravidians", "Abhayagiri Dagoba", "Pali Canon written"]},
        "Mahasena":            {"type": "Ruler", "period": "274–301 CE", "contributions": ["Minneriya Tank", "Jetavanaramaya", "many irrigation works"]},
        "Kashyapa":            {"type": "Ruler", "period": "473–495 CE", "contributions": ["Sigiriya fortress"]},
        "Dhatusena":           {"type": "Ruler", "period": "455–473 CE", "contributions": ["Kalawewa Tank"]},

        # Monuments / Structures
        "Ruwanwelisaya":       {"type": "Stupa",       "builder": "Dutugamunu",       "significance": "largest stupa, symbol of Buddhist state"},
        "Thuparamaya":         {"type": "Stupa",       "builder": "DevanampiyaTissa", "significance": "first stupa in Sri Lanka"},
        "Jetavanaramaya":      {"type": "Stupa",       "builder": "Mahasena",         "significance": "one of tallest ancient structures"},
        "AbhayagiriDagoba":    {"type": "Stupa",       "builder": "Valagamba",        "significance": "major Mahayana center"},
        "Mirisawetiya":        {"type": "Stupa",       "builder": "Dutugamunu",       "significance": "built to celebrate victory"},
        "Lohaprasada":         {"type": "Palace",      "builder": "Dutugamunu",       "significance": "Brazen Palace, nine-storey structure"},
        "Sigiriya":            {"type": "FortressPalace","builder": "Kashyapa",       "significance": "rock fortress palace with frescoes"},
        "SriMahaBodhi":        {"type": "SacredTree",  "bringer": "SanghamittaTheri","significance": "oldest recorded tree, cutting of Bodhi tree"},

        # Irrigation
        "TissaWewa":           {"type": "Tank", "builder": "DevanampiyaTissa", "location": "Anuradhapura"},
        "AbhayaWewa":          {"type": "Tank", "builder": "Pandukabhaya",     "location": "Anuradhapura", "altName": "Basawakkulama"},
        "MinneriyaTank":       {"type": "Tank", "builder": "Mahasena",         "location": "Minneriya"},
        "KalawewaTank":        {"type": "Tank", "builder": "Dhatusena",        "location": "Kalawewa"},
        "Bisokotuwa":          {"type": "Technology", "description": "unique sluice gate system for regulating water flow from tanks"},

        # Religious / Cultural
        "MahindaThero":        {"type": "Monk",   "role": "brought Buddhism to Sri Lanka", "sent_by": "Ashoka"},
        "SanghamittaTheri":    {"type": "Nun",    "role": "brought Bodhi tree sapling"},
        "Buddhaghosa":         {"type": "Scholar","role": "wrote Visuddhimagga at Anuradhapura"},
        "Mahavamsa":           {"type": "Chronicle", "written_by": "Mahanama Thero", "content": "history of Sri Lanka from Vijaya to 4th century"},
        "PaliCanon":           {"type": "Scripture", "written_at": "Aluvihara", "during": "reign of Valagamba", "language": "Pali"},
        "Theravada":           {"type": "BuddhistSchool", "dominant_in": "Anuradhapura period"},

        # Places
        "Anuradhapura":        {"type": "Capital",  "founded_by": "Pandukabhaya", "period": "377 BCE – 1017 CE"},
        "Aluvihara":           {"type": "Monastery","significance": "Pali Canon written here"},
        "Mihintale":           {"type": "Site",     "significance": "where Buddhism arrived, Mahinda met Tissa"},
    },

    "relationships": [
        {"subject": "Dutugamunu",       "predicate": "built",         "object": "Ruwanwelisaya"},
        {"subject": "Dutugamunu",       "predicate": "built",         "object": "Mirisawetiya"},
        {"subject": "Dutugamunu",       "predicate": "built",         "object": "Lohaprasada"},
        {"subject": "Dutugamunu",       "predicate": "defeated",      "object": "Elara"},
        {"subject": "DevanampiyaTissa", "predicate": "built",         "object": "Thuparamaya"},
        {"subject": "DevanampiyaTissa", "predicate": "built",         "object": "TissaWewa"},
        {"subject": "DevanampiyaTissa", "predicate": "converted_by",  "object": "MahindaThero"},
        {"subject": "Mahasena",         "predicate": "built",         "object": "MinneriyaTank"},
        {"subject": "Mahasena",         "predicate": "built",         "object": "Jetavanaramaya"},
        {"subject": "Pandukabhaya",     "predicate": "built",         "object": "AbhayaWewa"},
        {"subject": "Pandukabhaya",     "predicate": "founded",       "object": "Anuradhapura"},
        {"subject": "Valagamba",        "predicate": "built",         "object": "AbhayagiriDagoba"},
        {"subject": "Valagamba",        "predicate": "commissioned",  "object": "PaliCanon"},
        {"subject": "MahindaThero",     "predicate": "converted",     "object": "DevanampiyaTissa"},
        {"subject": "SanghamittaTheri", "predicate": "brought",       "object": "SriMahaBodhi"},
        {"subject": "Buddhaghosa",      "predicate": "wrote",         "object": "Visuddhimagga"},
        {"subject": "Kashyapa",         "predicate": "built",         "object": "Sigiriya"},
        {"subject": "Dhatusena",        "predicate": "built",         "object": "KalawewaTank"},
    ],

    # Sinhala keyword → ontology concept mappings
    "sinhala_keywords": {
        "දුටුගැමුණු": "Dutugamunu",
        "රුවන්වැලිසාය": "Ruwanwelisaya",
        "දේවානම්පිය තිස්ස": "DevanampiyaTissa",
        "මිහිඳු": "MahindaThero",
        "බෞද්ධ": "Theravada",
        "ථූපාරාමය": "Thuparamaya",
        "ජේතවනාරාමය": "Jetavanaramaya",
        "අභයගිරි": "AbhayagiriDagoba",
        "මහාවංශ": "Mahavamsa",
        "පාලි": "PaliCanon",
        "අළුවිහාර": "Aluvihara",
        "වාරිමාර්ග": "Bisokotuwa",
        "මිනේරිය": "MinneriyaTank",
        "තිස්සවැව": "TissaWewa",
        "අභයවැව": "AbhayaWewa",
        "කලාවැව": "KalawewaTank",
        "පණ්ඩුකාභය": "Pandukabhaya",
        "වළගම්බා": "Valagamba",
        "මහාසේන": "Mahasena",
        "ශ්‍රී මහා බෝධිය": "SriMahaBodhi",
        "සංඝමිත්තා": "SanghamittaTheri",
        "සිගිරිය": "Sigiriya",
        "ඇළ": "canal",
        "ඉරිගල": "Elara",
        "ලොහාපාසාද": "Lohaprasada",
        "මිරිසවැටිය": "Mirisawetiya",
    }
}


class AnuradhapuraOntology:
    """Query interface for the Anuradhapura ontology."""

    def __init__(self):
        self.data = ONTOLOGY

    # ── Core queries ──────────────────────────────────────────────────────────

    def get_concept(self, name: str) -> Optional[Dict]:
        return self.data["concepts"].get(name)

    def get_relationships(self, subject: str) -> List[Dict]:
        return [r for r in self.data["relationships"] if r["subject"] == subject]

    def find_builder(self, monument: str) -> Optional[str]:
        concept = self.data["concepts"].get(monument, {})
        return concept.get("builder") or concept.get("built_by")

    def find_built_by(self, ruler: str) -> List[str]:
        return [r["object"] for r in self.data["relationships"]
                if r["subject"] == ruler and r["predicate"] == "built"]

    def get_all_rulers(self) -> List[str]:
        return [k for k, v in self.data["concepts"].items() if v.get("type") == "Ruler"]

    def get_all_tanks(self) -> List[str]:
        return [k for k, v in self.data["concepts"].items() if v.get("type") == "Tank"]

    # ── Sinhala keyword extraction ────────────────────────────────────────────

    def extract_concepts_from_sinhala(self, text: str) -> List[Dict]:
        """Return ontology concepts mentioned in a Sinhala text."""
        found = []
        for sinhala_word, concept_name in self.data["sinhala_keywords"].items():
            if sinhala_word in text:
                concept = self.data["concepts"].get(concept_name)
                if concept:
                    found.append({
                        "keyword": sinhala_word,
                        "concept": concept_name,
                        "details": concept
                    })
        return found

    # ── Scoring helpers ───────────────────────────────────────────────────────

    def validate_claim(self, claim: str) -> Dict:
        """
        Check whether a claim like 'Dutugamunu built Ruwanwelisaya' is supported.
        Simple substring matching against relationship triples.
        """
        for rel in self.data["relationships"]:
            if (rel["subject"].lower() in claim.lower() and
                    rel["object"].lower() in claim.lower()):
                return {"valid": True, "relationship": rel}
        return {"valid": False, "relationship": None}

    def get_concept_summary(self, concept_name: str) -> str:
        """Return a short human-readable summary of a concept."""
        c = self.data["concepts"].get(concept_name)
        if not c:
            return f"Concept '{concept_name}' not found in ontology."
        parts = [f"**{concept_name}** (type: {c.get('type','unknown')})"]
        for k, v in c.items():
            if k != "type":
                parts.append(f"  - {k}: {v}")
        return "\n".join(parts)

    def enrich_explanation(self, concepts_found: List[Dict]) -> str:
        """Build an ontology-grounded explanation string from found concepts."""
        if not concepts_found:
            return "No specific ontology concepts identified in the answer."
        lines = ["**Ontology concepts identified in answer:**"]
        for item in concepts_found:
            c = item["details"]
            name = item["concept"]
            c_type = c.get("type", "Concept")
            detail_parts = []
            if "contributions" in c:
                detail_parts.append("contributions: " + ", ".join(c["contributions"]))
            if "significance" in c:
                detail_parts.append("significance: " + c["significance"])
            if "builder" in c:
                detail_parts.append("builder: " + c["builder"])
            if "role" in c:
                detail_parts.append("role: " + c["role"])
            detail_str = "; ".join(detail_parts) if detail_parts else ""
            lines.append(f"  • **{name}** [{c_type}] — {detail_str}")
            # Add relevant relationships
            rels = self.get_relationships(name)
            for rel in rels[:2]:
                lines.append(f"      ↳ {rel['subject']} → {rel['predicate']} → {rel['object']}")
        return "\n".join(lines)


# ── Convenience singleton ─────────────────────────────────────────────────────
ontology = AnuradhapuraOntology()

if __name__ == "__main__":
    # Quick smoke test
    print(ontology.get_concept_summary("Dutugamunu"))
    print()
    text = "දුටුගැමුණු රජු රුවන්වැලිසාය ඉදිකළේය"
    found = ontology.extract_concepts_from_sinhala(text)
    print("Found concepts:", [f["concept"] for f in found])
    print(ontology.enrich_explanation(found))
