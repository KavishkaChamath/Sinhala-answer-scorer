"""
app.py  —  Streamlit UI for the Offline Intelligent Sinhala Answer Scorer
Run: streamlit run app.py
UPDATED: fixed session_state bug, full Sinhala UI, About tab removed
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import requests
from agents.orchestrator import get_orchestrator
from agents.scoring_agent import MARKING_GUIDES

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="සිංහල පිළිතුරු ලකුණු දීමේ පද්ධතිය",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Sinhala:wght@400;700&family=Inter:wght@300;400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans Sinhala', 'Inter', sans-serif; }
.status-online  { color: #2ecc71; font-weight: bold; }
.status-offline { color: #e74c3c; font-weight: bold; }
.info-box {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    color: white; padding: 20px; border-radius: 12px; margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)


# ── Helper: OLLAMA status ─────────────────────────────────────────────────────
@st.cache_data(ttl=30)
def check_ollama_status():
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        models = r.json().get("models", [])
        return True, [m["name"] for m in models]
    except Exception:
        return False, []


# ── FIX: initialise session state BEFORE any widget renders ──────────────────
# This prevents the StreamlitAPIException when loading sample answers.
if "answer_input" not in st.session_state:
    st.session_state["answer_input"] = ""

# If a sample-load button was pressed on the previous run, apply it now —
# before the text_area widget is instantiated this run.
if "load_sample_text" in st.session_state:
    st.session_state["answer_input"] = st.session_state.pop("load_sample_text")


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/11/Flag_of_Sri_Lanka.svg/320px-Flag_of_Sri_Lanka.svg.png",
        width=80
    )
    st.title("🏛️ ශ්‍රී ලංකා ඉතිහාස\nලකුණු දීමේ පද්ධතිය")
    st.markdown("---")

    online, models = check_ollama_status()
    if online:
        st.markdown('<span class="status-online">🟢 OLLAMA සක්‍රියයි</span>', unsafe_allow_html=True)
        if models:
            st.caption(f"මාදිලිය: {', '.join(models[:3])}")
    else:
        st.markdown('<span class="status-offline">🔴 OLLAMA අක්‍රියයි</span>', unsafe_allow_html=True)
        st.warning("⚠️ විකල්ප ලකුණු දීම ක්‍රියාත්මකයි.\nධාවනය කරන්න: `ollama serve`")

    st.markdown("---")
    st.markdown("**📚 විෂය:** පුරාණ ශ්‍රී ලංකාව (අනුරාධපුර යුගය)")
    st.markdown("**🏆 මුළු ලකුණු:** ප්‍රශ්නයකට 20")
    st.markdown("**🌐 ක්‍රමය:** සම්පූර්ණ නොබැඳි (Offline)")
    st.markdown("---")
    st.markdown("**හොඳ ලකුණු ලබා ගන්නේ කෙසේද:**")
    st.caption(
        "• සිංහලෙන් සවිස්තරාත්මකව ලියන්න\n"
        "• රජවරුන්, ස්මාරක, දිනයන් සඳහන් කරන්න\n"
        "• හේතු හා ප්‍රතිඵල පැහැදිලි කරන්න\n"
        "• අවම වශයෙන් වචන 50ක් ලියන්න"
    )


# ── Main header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="info-box">
  <h1 style="margin:0; font-size:1.9em">🏛️ නොබැඳි බුද්ධිමත් සිංහල පිළිතුරු ලකුණු දීමේ පද්ධතිය</h1>
  <p style="margin:8px 0 0; color:#aaa; font-size:0.95em">
    පුරාණ ශ්‍රී ලංකාව — අනුරාධපුර යුගය
  </p>
</div>
""", unsafe_allow_html=True)

# ── Two tabs only (About tab removed) ────────────────────────────────────────
tab_score, tab_questions = st.tabs(["📝 පිළිතුර ලකුණු කරන්න", "📖 ප්‍රශ්න බලන්න"])


# ════════════════════════════════════════════════════════════════════════════
# TAB 1: SCORE ANSWER
# ════════════════════════════════════════════════════════════════════════════
with tab_score:
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.subheader("1️⃣ ප්‍රශ්නය තෝරන්න")

        q_options = {
            f"Q{qid}: {guide['question_si'][:55]}…": qid
            for qid, guide in MARKING_GUIDES.items()
        }
        selected_q_label = st.selectbox(
            "ප්‍රශ්නය තෝරන්න:",
            options=list(q_options.keys()),
            key="question_select"
        )
        question_id = q_options[selected_q_label]
        guide = MARKING_GUIDES[question_id]

        st.markdown(f"""
        <div style="background:#eaf4fb; border-radius:10px; padding:15px; margin-top:10px;">
            <b>🇱🇰 සිංහල:</b><br>
            <span style="font-size:1.05em">{guide['question_si']}</span><br><br>
            <b>🇬🇧 English:</b><br>
            <span style="color:#555; font-size:0.9em">{guide['question_en']}</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("**ලකුණු ලබාදීමේ නිර්ණායක:**")
        for c in guide["criteria"]:
            st.markdown(f"• **{c['id']}** ({c['max_marks']} ලකුණු): {c['description']}")

    with col2:
        st.subheader("2️⃣ ශිෂ්‍යයාගේ පිළිතුර ඇතුළත් කරන්න")

        # Text area — its value is controlled via st.session_state["answer_input"]
        student_answer = st.text_area(
            "ඔබේ පිළිතුර සිංහලෙන් ලියන්න:",
            height=220,
            placeholder="සිංහල භාෂාවෙන් ඔබේ පිළිතුර ලියන්න...",
            key="answer_input"
        )

        word_count = len(student_answer.split()) if student_answer.strip() else 0
        st.caption(
            f"වචන ගණන: {word_count} "
            f"{'✅' if word_count >= 30 else '⚠️ (අවම වශයෙන් වචන 50ක් ලියන්න)'}"
        )

        # ── Sample answers ────────────────────────────────────────────────
        # Buttons write to "load_sample_text" (a staging key), NOT "answer_input".
        # At the top of the next rerun the value is moved into "answer_input"
        # BEFORE the text_area widget is created — avoiding the Streamlit error.
        with st.expander("💡 නිදර්ශන පිළිතුරු පූරණය කරන්න"):
            samples = {
                "Q1 - හොඳ පිළිතුරක් (බෞද්ධ ආගම)": (
                    "මිහිඳු හිමිගේ ශ්‍රී ලංකාවට පැමිණීමත් සමඟ 247 BCE දී දේවානම්පිය තිස්ස රජු "
                    "බෞද්ධ ධර්මය පිළිගත්තේය. ශ්‍රී මහා බෝධිය ශ්‍රී ලංකාවට ගෙනාවේ සංඝමිත්තා හිමිය. "
                    "ථූපාරාමය, රුවන්වැලිසාය, ජේතවනාරාමය ඇතුළු ශ්‍රේෂ්ඨ ස්තූප ගොඩනගා ගත්තේය. "
                    "අළුවිහාරයේදී පාලි ත්‍රිපිටකය ලිඛිතව රචනා කරන ලදී. "
                    "මහාවංශ ඉතිහාස ග්‍රන්ථය ලෙස රචනා විය. බෞද්ධ ආගම රජ්‍ය ආගම ලෙස ස්ථාපිත විය."
                ),
                "Q3 - හොඳ පිළිතුරක් (දුටුගැමුණු)": (
                    "දුටුගැමුණු රජු ශ්‍රී ලංකා ඉතිහාසයේ වීරයෙකි. ඔහු ඉලාරා රජු ජය ගෙන "
                    "ශ්‍රී ලංකාව ඒකීය රාජ්‍යයක් කළේය. රුවන්වැලිසාය, මිරිසවැටිය ස්තූප ඉදිකළ අතර "
                    "ලෝහාපාසාද ශ්‍රේෂ්ඨ ගොඩනැගිල්ල ඉදිකළේය. ඔහු සිංහල බෞද්ධ ජාතික අනන්‍යතාව "
                    "ස්ථාපිත කළේය. මහාවංශ ග්‍රන්ථයෙහි ඔහුගේ ජීවිත කතාව ඇතුළත් ය."
                ),
                "Q2 - සාමාන්‍ය පිළිතුරක් (වාරිමාර්ග)": (
                    "අනුරාධපුර රාජ්‍යයේ ජලාශ ඉදිකළේය. "
                    "මිනේරිය ටැංකිය ප්‍රසිද්ධ ජලාශයකි. ගොවිතැනට ජලය ලබාදීම ප්‍රධාන අරමුණ විය."
                ),
            }
            for label, text in samples.items():
                if st.button(f"පූරණය: {label}", key=f"sample_{label}"):
                    # Stage the text — applied at top of next rerun BEFORE widget renders
                    st.session_state["load_sample_text"] = text
                    st.rerun()

        score_btn = st.button(
            "🎯 පිළිතුර ලකුණු කරන්න",
            type="primary",
            use_container_width=True,
            disabled=word_count < 5
        )

    # ── Scoring output ─────────────────────────────────────────────────────
    if score_btn and student_answer.strip():
        with st.spinner("⏳ පිළිතුර විශ්ලේෂණය කරමින්... CPU පමණක් ඇති විට මෙය විනාඩි 2-4ක් ගත විය හැක..."):
            try:
                orchestrator = get_orchestrator()
                result = orchestrator.run(question_id, student_answer)
                st.session_state["last_result"] = result
            except Exception as e:
                st.error(f"ලකුණු දීමේ දෝෂය: {e}")
                st.stop()

    if "last_result" in st.session_state:
        result = st.session_state["last_result"]
        st.markdown("---")
        st.subheader("📊 ලකුණු ලබාදීමේ ප්‍රතිඵල")

        if result.get("fallback_mode"):
            st.warning(
                "⚠️ OLLAMA ප්‍රතිචාර නොදැක්වීය (timeout/offline) — මූලික කීවර්ඩ් ලකුණු ක්‍රමය භාවිතා විය. "
                "16GB RAM යන්ත්‍රයකදී AI ලකුණු නිවැරදිව ක්‍රියා කරයි."
            )

        total = result["total_score"]
        grade = result["grade"]

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("මුළු ලකුණු", f"{total}/20", f"{(total/20)*100:.0f}%")
        with c2:
            st.metric("ශ්‍රේණිය", grade)
        with c3:
            st.metric("හඳුනාගත් සංකල්ප", len(result.get("concepts_found", [])))

        st.markdown("#### 📋 නිර්ණායක අනුව ලකුණු විස්තරය")
        for row in result["score_table"]:
            pct = (row["Awarded"] / row["Max"]) * 100
            with st.container():
                rc1, rc2, rc3 = st.columns([1, 4, 2])
                with rc1:
                    st.markdown(f"**{row['Criterion']}**")
                with rc2:
                    st.caption(row["Description"])
                    st.progress(pct / 100, text=row["Justification"])
                with rc3:
                    st.markdown(f"**{row['Awarded']}/{row['Max']}** ලකුණු")

        col_a, col_b = st.columns(2)
        with col_a:
            st.success(f"✅ **ශක්තිමත් කරුණු:** {result.get('strengths', '')}")
        with col_b:
            st.warning(f"💡 **වැඩිදියුණු කළ යුතු කරුණු:** {result.get('improvements', '')}")

        st.info(f"📝 **සමස්ත ප්‍රතිඵලය:** {result.get('overall_feedback', '')}")

        with st.expander("🔬 Ontology විශ්ලේෂණ විස්තර"):
            st.markdown(result.get("ontology_enrichment", "Ontology දත්ත නොමැත."))
            if result.get("concepts_found"):
                st.markdown(f"**හඳුනාගත් සංකල්ප:** {', '.join(result['concepts_found'])}")

        with st.expander("📚 RAG — ලබාගත් දැනුම් පදනම් සන්දර්භය"):
            st.text(result.get("rag_context", "සන්දර්භය ලබා ගත නොහැකි විය.")[:1500] + "...")


# ════════════════════════════════════════════════════════════════════════════
# TAB 2: VIEW QUESTIONS
# ════════════════════════════════════════════════════════════════════════════
with tab_questions:
    st.subheader("📖 සියලුම ප්‍රශ්න සහ ලකුණු ලබාදීමේ මාර්ගෝපදේශ")
    for qid, guide in MARKING_GUIDES.items():
        with st.expander(f"Q{qid}: {guide['question_si'][:70]}…"):
            st.markdown(f"**සිංහල:** {guide['question_si']}")
            st.markdown(f"**English:** {guide['question_en']}")
            st.markdown("**මුළු ලකුණු: 20**")
            st.markdown("| නිර්ණායකය | විස්තරය | ලකුණු |")
            st.markdown("|-----------|---------|-------|")
            for c in guide["criteria"]:
                st.markdown(f"| **{c['id']}** | {c['description']} | {c['max_marks']} |")

    st.markdown("---")
    st.caption("40_CS4032 Natural Language Processing — Individual Assignment 02")
    st.caption("විෂය ක්ෂේත්‍රය: පුරාණ ශ්‍රී ලංකාව (අනුරාධපුර යුගය)")
