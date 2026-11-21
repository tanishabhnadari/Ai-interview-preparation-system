import streamlit as st
import os
import json
from pathlib import Path
from core.models import CandidateProfile, JobDescription, InterviewDifficulty, QuestionCategory
from core.session_manager import SessionManager
from modules.resume_parser import ResumeParser
from modules.speech_processor import SpeechProcessor
from database.db_manager import DatabaseManager
from utils.visualizer import create_radar_chart, create_progression_bar_chart
import config

# Page Configuration
st.set_page_config(
    page_title="AI Interview Preparation System",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #64748B;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 1.2rem;
        text-align: center;
    }
    .badge-tech {
        background-color: #DBEAFE;
        color: #1D4ED8;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .badge-diff {
        background-color: #FEF3C7;
        color: #B45309;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .highlight-card {
        background-color: #F0FDF4;
        border-left: 4px solid #22C55E;
        padding: 1rem;
        border-radius: 6px;
        margin-bottom: 1rem;
    }
    .warning-card {
        background-color: #FEF2F2;
        border-left: 4px solid #EF4444;
        padding: 1rem;
        border-radius: 6px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "session_manager" not in st.session_state:
    st.session_state.session_manager = SessionManager()

if "active_tab" not in st.session_state:
    st.session_state.active_tab = "setup"

if "candidate_skills" not in st.session_state:
    st.session_state.candidate_skills = []

if "match_data" not in st.session_state:
    st.session_state.match_data = None

sm: SessionManager = st.session_state.session_manager
resume_parser = ResumeParser()
speech_proc = SpeechProcessor()
db_mgr = DatabaseManager()

# Sidebar
with st.sidebar:
    st.title("🎯 AI Interviewer")
    st.caption("Intelligent Career Preparation Platform")
    
    # Engine Status
    api_key = config.GEMINI_API_KEY
    if api_key:
        st.success("🟢 Gemini AI Engine: Active")
    else:
        st.info("🟡 Local Heuristic NLP Engine: Active")
        with st.expander("🔑 Add Gemini API Key"):
            input_key = st.text_input("Gemini API Key", type="password", key="sidebar_key")
            if st.button("Save Key"):
                if input_key.strip():
                    config.GEMINI_API_KEY = input_key.strip()
                    sm.question_gen.api_key = input_key.strip()
                    sm.evaluator.api_key = input_key.strip()
                    st.success("Key applied successfully!")
                    st.rerun()

    st.divider()

    # Navigation buttons
    nav_options = {
        "setup": "⚙️ 1. Setup & Resume",
        "room": "🎙️ 2. Live Interview Room",
        "report": "📊 3. Performance Scorecard",
        "history": "🕒 4. Past Sessions"
    }

    selected_nav = st.radio(
        "Navigation",
        options=list(nav_options.keys()),
        format_func=lambda x: nav_options[x],
        index=list(nav_options.keys()).index(st.session_state.active_tab)
    )
    if selected_nav != st.session_state.active_tab:
        st.session_state.active_tab = selected_nav
        st.rerun()

    st.divider()
    if sm.current_session:
        st.write(f"**Session:** `{sm.current_session.session_id}`")
        st.write(f"**Candidate:** {sm.current_session.candidate.name}")
        st.write(f"**Progress:** {sm.current_session.current_index} / {len(sm.current_session.questions)}")

# TAB 1: SETUP & RESUME PARSING
if st.session_state.active_tab == "setup":
    st.markdown('<div class="main-header">New Interview Setup</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Upload candidate resume and job description to personalize questions.</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.subheader("1. Candidate Profile")
        cand_name = st.text_input("Candidate Full Name", value="Alex Taylor")
        target_role = st.selectbox(
            "Target Job Role",
            ["Software Engineer", "Python Developer", "AI Engineer", "Data Scientist", "Backend Developer", "System Architect"]
        )
        difficulty = st.selectbox(
            "Target Difficulty Level",
            [d.value for d in InterviewDifficulty],
            index=1
        )
        num_q = st.slider("Number of Questions", min_value=3, max_value=8, value=4)

        st.subheader("2. Upload Resume (PDF)")
        uploaded_resume = st.file_uploader("Upload your resume", type=["pdf"])

        resume_text = ""
        if uploaded_resume:
            temp_path = config.RESUME_DIR / uploaded_resume.name
            with open(temp_path, "wb") as f:
                f.write(uploaded_resume.getbuffer())
            
            resume_text = resume_parser.extract_text_from_pdf(str(temp_path))
            detected_skills = resume_parser.extract_skills(resume_text)
            st.session_state.candidate_skills = detected_skills

            st.success(f"Extracted {len(detected_skills)} skills from resume!")
            st.write("**Detected Skills:**", ", ".join(detected_skills[:12]) + ("..." if len(detected_skills) > 12 else ""))

    with col2:
        st.subheader("3. Job Description (JD)")
        jd_input = st.text_area(
            "Paste Target Job Description",
            height=200,
            value="Seeking a software engineer proficient in Python, SQL, REST APIs, Git, Docker, and Microservices. Experience with machine learning or cloud deployments (AWS) is a strong plus."
        )

        if st.button("🔍 Analyze Resume vs JD Match", use_container_width=True):
            if resume_text:
                match_results = resume_parser.analyze_match(st.session_state.candidate_skills, jd_input)
                st.session_state.match_data = match_results
            else:
                # Mock comparison based on default skills if no resume uploaded
                default_cand_skills = ["Python", "Git", "Docker", "SQL", "FastAPI"]
                st.session_state.candidate_skills = default_cand_skills
                match_results = resume_parser.analyze_match(default_cand_skills, jd_input)
                st.session_state.match_data = match_results

        if st.session_state.match_data:
            md = st.session_state.match_data
            st.markdown(f"#### Match Score: **{md['match_score']}%**")
            st.progress(int(md['match_score']))

            st.markdown(f"✅ **Matched Skills ({len(md['matched_skills'])}):** {', '.join(md['matched_skills']) if md['matched_skills'] else 'None'}")
            st.markdown(f"⚠️ **Skill Gaps / Missing ({len(md['missing_skills'])}):** {', '.join(md['missing_skills']) if md['missing_skills'] else 'None'}")

        st.divider()
        if st.button("🚀 Start Interview", type="primary", use_container_width=True):
            cand_profile = CandidateProfile(
                name=cand_name,
                target_role=target_role,
                experience_level=InterviewDifficulty(difficulty),
                detected_skills=st.session_state.candidate_skills,
                raw_resume_text=resume_text
            )
            jd_profile = JobDescription(
                title=target_role,
                required_skills=st.session_state.match_data["required_skills"] if st.session_state.match_data else [],
                raw_jd_text=jd_input
            )

            with st.spinner("Generating personalized interview questions..."):
                sm.start_new_session(cand_profile, jd_profile, num_questions=num_q)
            
            st.session_state.active_tab = "room"
            st.rerun()

# TAB 2: LIVE INTERVIEW ROOM
elif st.session_state.active_tab == "room":
    if not sm.current_session:
        st.warning("No active interview session. Please create one in Setup.")
        if st.button("Go to Setup"):
            st.session_state.active_tab = "setup"
            st.rerun()
    elif sm.current_session.is_completed:
        st.success("🎉 Interview Complete! View your detailed scorecard.")
        if st.button("View Performance Scorecard", type="primary"):
            st.session_state.active_tab = "report"
            st.rerun()
    else:
        current_q = sm.get_current_question()
        idx = sm.current_session.current_index
        total_q = len(sm.current_session.questions)

        st.markdown(f'<div class="main-header">Interview Room</div>', unsafe_allow_html=True)
        st.progress((idx) / total_q)
        st.caption(f"Question {idx + 1} of {total_q}")

        # Question Presentation Card
        st.markdown(f"""
        <div style="background-color: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 12px; padding: 1.5rem; margin-top: 1rem; margin-bottom: 1.5rem;">
            <div style="margin-bottom: 0.8rem;">
                <span class="badge-tech">{current_q.category.value}</span>
                <span class="badge-diff">{current_q.difficulty.value}</span>
                {f'<span style="background-color: #E0E7FF; color: #4338CA; padding: 4px 10px; border-radius: 12px; font-size: 0.85rem; font-weight: 600; margin-left: 6px;">Adaptive Follow-up</span>' if current_q.follow_up_for else ''}
            </div>
            <h3 style="color: #0F172A; margin: 0; font-size: 1.35rem; line-height: 1.4;">{current_q.text}</h3>
            {f'<p style="color: #64748B; margin-top: 0.8rem; font-size: 0.95rem; font-style: italic;">Hint: {current_q.context_hint}</p>' if current_q.context_hint else ''}
        </div>
        """, unsafe_allow_html=True)

        # Answer Input
        col_ans1, col_ans2 = st.columns([2, 1], gap="medium")
        with col_ans1:
            candidate_answer = st.text_area(
                "Your Response:",
                height=180,
                placeholder="Type or paste your answer here...",
                key=f"ans_input_{current_q.id}"
            )
        
        with col_ans2:
            st.markdown("#### Spoken Delivery Parameters")
            simulated_duration = st.slider(
                "Answer Duration (Seconds)",
                min_value=10,
                max_value=180,
                value=45,
                help="Adjust to reflect speaking duration for Words-Per-Minute (WPM) fluency analysis."
            )
            # Real-time preview of speech metrics
            if candidate_answer.strip():
                sample_metrics = speech_proc.analyze_speech(candidate_answer, duration_seconds=float(simulated_duration))
                st.metric("Estimated WPM", f"{sample_metrics.words_per_minute}")
                st.metric("Fillers Detected", f"{sample_metrics.total_filler_words}")

        col_b1, col_b2 = st.columns([1, 4])
        with col_b1:
            if st.button("Submit Answer ➔", type="primary", use_container_width=True):
                if not candidate_answer.strip():
                    st.warning("Please provide an answer before submitting.")
                else:
                    with st.spinner("AI Evaluating your response..."):
                        metrics = speech_proc.analyze_speech(candidate_answer, duration_seconds=float(simulated_duration))
                        eval_result = sm.submit_answer(candidate_answer, speech_metrics=metrics)
                    
                    st.success(f"Scored: {eval_result.overall_score}%")
                    st.rerun()

        # Display previous answer feedback if available
        if sm.current_session.evaluations:
            with st.expander("📝 View Feedback on Last Answer", expanded=False):
                last_eval = sm.current_session.evaluations[-1]
                st.write(f"**Score:** {last_eval.overall_score}%")
                st.write("**Strengths:**")
                for s in last_eval.strengths:
                    st.markdown(f"- ✅ {s}")
                st.write("**Areas for Improvement:**")
                for imp in last_eval.areas_for_improvement:
                    st.markdown(f"- ⚠️ {imp}")

# TAB 3: PERFORMANCE SCORECARD & REPORT
elif st.session_state.active_tab == "report":
    if not sm.current_session or not sm.current_session.evaluations:
        st.info("No completed evaluations to display. Complete an interview first.")
    else:
        session = sm.current_session
        st.markdown('<div class="main-header">Interview Performance Scorecard</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="sub-header">Comprehensive feedback for <b>{session.candidate.name}</b> • Target Role: <b>{session.candidate.target_role}</b></div>', unsafe_allow_html=True)

        # Overview Metrics Row
        mcol1, mcol2, mcol3, mcol4, mcol5 = st.columns(5)
        with mcol1:
            st.metric("Overall Score", f"{session.overall_score}%")
        with mcol2:
            avg_tech = sum(e.technical_score for e in session.evaluations) / len(session.evaluations)
            st.metric("Technical Depth", f"{avg_tech:.1f}%")
        with mcol3:
            avg_struct = sum(e.structure_score for e in session.evaluations) / len(session.evaluations)
            st.metric("Structure / STAR", f"{avg_struct:.1f}%")
        with mcol4:
            avg_comm = sum(e.communication_score for e in session.evaluations) / len(session.evaluations)
            st.metric("Communication", f"{avg_comm:.1f}%")
        with mcol5:
            avg_conf = sum(e.confidence_score for e in session.evaluations) / len(session.evaluations)
            st.metric("Confidence", f"{avg_conf:.1f}%")

        st.divider()

        # Visualizations Row
        vcol1, vcol2 = st.columns([1, 1])
        with vcol1:
            st.subheader("Competency Radar")
            radar_fig = create_radar_chart(session.evaluations)
            st.plotly_chart(radar_fig, use_container_width=True)

        with vcol2:
            st.subheader("Question Score Progression")
            bar_fig = create_progression_bar_chart(session.evaluations)
            st.plotly_chart(bar_fig, use_container_width=True)

        st.divider()

        # Detailed Question Breakdown
        st.subheader("Question-by-Question Deep Dive")
        for i, eval_item in enumerate(session.evaluations):
            with st.expander(f"Question {i+1}: {eval_item.question_text[:75]}... (Score: {eval_item.overall_score}%)", expanded=(i==0)):
                st.markdown(f"**Full Question:** {eval_item.question_text}")
                st.markdown(f"**Candidate Answer:**")
                st.info(eval_item.candidate_answer)

                sc1, sc2 = st.columns(2)
                with sc1:
                    st.markdown("**✅ Key Strengths:**")
                    for st_item in eval_item.strengths:
                        st.markdown(f"- {st_item}")
                
                with sc2:
                    st.markdown("**⚠️ Areas for Improvement:**")
                    for imp_item in eval_item.areas_for_improvement:
                        st.markdown(f"- {imp_item}")

                if eval_item.key_missed_concepts:
                    st.markdown(f"**💡 Missed Terminology / Concepts:** {', '.join(eval_item.key_missed_concepts)}")

                st.markdown("**🌟 Recommended Ideal Answer:**")
                st.markdown(f"> {eval_item.ideal_answer}")

                if eval_item.speech_metrics:
                    sm_m = eval_item.speech_metrics
                    st.caption(f"Speech Metrics: {sm_m.words_per_minute} WPM | Fillers: {sm_m.total_filler_words} | Fluency: {sm_m.fluency_score}%")

        st.divider()
        report_json = json.dumps(session.model_dump(), indent=2)
        st.download_button(
            "📥 Download Evaluation Report (JSON)",
            data=report_json,
            file_name=f"interview_report_{session.session_id}.json",
            mime="application/json"
        )

# TAB 4: PAST SESSIONS
elif st.session_state.active_tab == "history":
    st.markdown('<div class="main-header">Past Interview Sessions</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Review historical interview performances and analytics.</div>', unsafe_allow_html=True)

    sessions = db_mgr.list_sessions(limit=25)
    if not sessions:
        st.info("No past sessions recorded yet.")
    else:
        for s in sessions:
            with st.container():
                hcol1, hcol2, hcol3, hcol4, hcol5 = st.columns([2, 2, 1, 1, 1])
                with hcol1:
                    st.write(f"**{s['candidate_name']}**")
                    st.caption(f"Role: {s['target_role']} | {s['difficulty']}")
                with hcol2:
                    st.caption(f"Date: {s['created_at'][:19].replace('T', ' ')}")
                with hcol3:
                    st.metric("Score", f"{s['overall_score']}%")
                with hcol4:
                    if st.button("Load Report", key=f"load_{s['session_id']}"):
                        loaded = sm.load_session(s['session_id'])
                        if loaded:
                            st.session_state.active_tab = "report"
                            st.rerun()
                with hcol5:
                    if st.button("🗑️ Delete", key=f"del_{s['session_id']}"):
                        db_mgr.delete_session(s['session_id'])
                        st.rerun()
                st.divider()
