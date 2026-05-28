# 🏛️ Offline Intelligent Sinhala Answer Scorer
### Scope: Ancient Sri Lanka (Anuradhapura Period)

---

## 📁 Project Structure

```
sinhala_scorer/
├── app.py                          ← Main Streamlit application
├── requirements.txt                ← Python dependencies
├── README.md                       ← This file
│
├── knowledge_base/
│   ├── anuradhapura_history.txt    ← History text (RAG source)
│   └── questions_marking_guides.txt← Questions + marking criteria
│
├── ontology/
│   └── anuradhapura_ontology.py    ← History concepts + relationships
│
└── agents/
    ├── rag_agent.py                ← RAG retrieval agent (TF-IDF)
    ├── scoring_agent.py            ← OLLAMA scoring agent
    ├── explanation_agent.py        ← Explanation formatter
    └── orchestrator.py             ← Master pipeline coordinator
```

---

## 🚀 Step-by-Step Setup

### Step 1: Install Python dependencies
```bash
cd sinhala_scorer
pip install -r requirements.txt
```

### Step 2: Install OLLAMA
```bash
# Linux/Mac:
curl -fsSL https://ollama.ai/install.sh | sh

# Windows: download from https://ollama.ai/download
```

### Step 3: Pull a language model
```bash
# Recommended (3.8GB, good Sinhala understanding):
ollama pull llama3.2

# Lighter alternative (if low RAM):
ollama pull gemma2:2b

# Or use:
ollama pull mistral
```

### Step 4: Start OLLAMA server
```bash
ollama serve
# Keep this terminal open!
```

### Step 5: (Optional) Change model in scoring_agent.py
```python
# agents/scoring_agent.py line 14
OLLAMA_MODEL = "llama3.2"  # change to your pulled model
```

### Step 6: Run the Streamlit app
```bash
streamlit run app.py
```

Open browser at: **http://localhost:8501**

---

## 🏗️ System Architecture

```
Student Answer (Sinhala)
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│                  ORCHESTRATOR AGENT                      │
│  Coordinates: RAG → Ontology → Scoring → Explanation    │
└──────┬──────────────────────────────────────────────────┘
       │
       ├──► [1. RAG AGENT]
       │         Indexes knowledge_base/*.txt with TF-IDF
       │         Retrieves top-5 relevant text chunks
       │         Returns: context string
       │
       ├──► [2. ONTOLOGY MODULE]
       │         30+ concepts: rulers, monuments, tanks, monks
       │         20+ semantic relationships
       │         Sinhala keyword → concept extraction
       │         Returns: enriched concept list
       │
       ├──► [3. SCORING AGENT]
       │         Builds prompt: question + context + ontology + guide
       │         Calls: OLLAMA local LLM (llama3.2 / mistral / gemma2)
       │         Parses: JSON score per criterion
       │         Fallback: keyword heuristics if OLLAMA offline
       │         Returns: {criteria_scores, total_score, feedback}
       │
       └──► [4. EXPLANATION AGENT]
                 Formats score table
                 Generates letter grade
                 Builds HTML feedback panel
                 Highlights strengths + improvements
                 Returns: display-ready result
```

---

## 📋 Questions (5 questions × 20 marks)

| Q# | Question (Sinhala) | Topic |
|----|-------------------|-------|
| Q1 | අනුරාධපුර යුගයේ බෞද්ධ ආගමේ භූමිකාව... | Buddhism |
| Q2 | අනුරාධපුර රාජධානියේ වාරිමාර්ග ශිෂ්ටාචාරය... | Irrigation |
| Q3 | රජ දුටුගැමුණු ශ්‍රී ලංකා ඉතිහාසයට... | King Dutugamunu |
| Q4 | අනුරාධපුර රාජධානියේ පාලන ක්‍රමය... | Administration |
| Q5 | අනුරාධපුර රාජධානිය පරිහානියට... | Decline & Legacy |

Each question has **5 criteria × 4 marks = 20 marks total**.

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| OLLAMA not connecting | Run `ollama serve` in a separate terminal |
| Model not found | Run `ollama pull llama3.2` |
| Low RAM | Use `ollama pull gemma2:2b` (lighter model) |
| Slow scoring | Normal — LLM takes 10-30s per answer locally |
| Sinhala not rendering | Install Noto Sans Sinhala font |

---

## 📊 Marking Scheme Coverage

| Component | Marks | Status |
|-----------|-------|--------|
| A. Problem Setup (Anuradhapura) | 10 | ✅ |
| B. 5 Questions + Marking Guides | 15 | ✅ |
| C. RAG Implementation | 15 | ✅ |
| D. Ontology | 15 | ✅ |
| E. Agent-Based Architecture | 15 | ✅ |
| F. Explainable Scoring | 20 | ✅ |
| G. Streamlit UI | 5 | ✅ |
| H. Report + Evidence | 5 | 📝 (add video URL) |
