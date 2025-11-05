# app.py - FINAL VERSION WITH VS CODE EDITOR

import streamlit as st
import time
from datetime import datetime
from typing import Dict, List
from langchain_core.messages import HumanMessage, AIMessage
from graph.graph_builder import build_interview_graph
from graph.nodes.interview_nodes import CaseStudyInterviewNodes
# ==================== REPORT GENERATION FUNCTIONS ====================
import io
import zipfile
import json
from datetime import datetime



try:
    from streamlit_ace import st_ace
    EDITOR_AVAILABLE = True
except ImportError:
    EDITOR_AVAILABLE = False
    st.warning("⚠️ Code editor not available. Install with: pip install streamlit-ace")


# ==================== PAGE CONFIGURATION ====================
st.set_page_config(
    page_title="Case study",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==================== CUSTOM CSS STYLING ====================
def apply_custom_css():
    """Apply professional styling with VS Code theme"""
    st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    .interview-header {
        background: linear-gradient(135deg, #0076a8 0%, #00a3e0 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .phase-indicator {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin-bottom: 1.5rem;
    }
    .ai-message {
        background-color: #e3f2fd;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #2196f3;
    }
    .candidate-message {
        background-color: #f1f8e9;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #4caf50;
    }
    .stButton>button {
        border-radius: 5px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    .stProgress > div > div {
        background-color: #00a3e0;
    }
    
    /* VS Code-like tab styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #2d2d30;
        border-radius: 8px 8px 0 0;
        padding: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #3e3e42;
        color: #cccccc;
        border: none;
        padding: 10px 20px;
        font-family: 'Consolas', 'Monaco', monospace;
        border-radius: 5px 5px 0 0;
        margin-right: 4px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #1e1e1e;
        color: #ffffff;
        border-bottom: 2px solid #007acc;
    }
    
    /* Code editor styling */
    .ace_editor {
        border: 1px solid #3c3c3c;
        border-radius: 4px;
        font-size: 14px;
    }
    
    /* Text areas with monospace font */
    textarea {
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace !important;
    }
    </style>
    """, unsafe_allow_html=True)


# ==================== SESSION STATE INITIALIZATION ====================
def initialize_session_state():
    """Initialize all session state variables"""
    defaults = {
        'initialized': False,
        'messages': [],
        'candidate_name': "",
        'role': "",
        'skills': [],
        'interview_state': {},
        'graph': None,
        'nodes': None,
        'start_time': None,
        'current_page': "welcome",
        'approach_framework': "",
        'approach_technical': "",
        'approach_code': "# Write your code here...\n\n",
        'approach_implementation': "",
        'code_language': "python",
        'debug_mode': False,
        'ai_processing': False,
        'waiting_for_user': False
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


# ==================== UTILITY FUNCTIONS ====================
def format_time_remaining(seconds: int) -> str:
    """Format remaining time as MM:SS"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def calculate_progress(state: Dict) -> float:
    """Calculate overall interview progress percentage"""
    total_questions = 3 + 3 + 4 + 3
    completed = 0
    if state.get('mcq_completed'):
        completed += 3
    completed += state.get('understanding_question_count', 0)
    completed += state.get('approach_question_count', 0)
    completed += state.get('followup_question_count', 0)
    return (completed / total_questions) * 100


def aggregate_approach_content() -> str:
    """Aggregate all approach workspace content"""
    parts = []
    
    if st.session_state.approach_framework.strip():
        parts.append(f"**FRAMEWORK & METHODOLOGY:**\n{st.session_state.approach_framework}")
    
    if st.session_state.approach_technical.strip():
        parts.append(f"**TECHNICAL APPROACH:**\n{st.session_state.approach_technical}")
    
    code = st.session_state.approach_code.strip()
    if code and code != "# Write your code here...\n\n" and code != "# Write your code here...":
        language = st.session_state.get('code_language', 'python')
        parts.append(f"**CODE/PSEUDOCODE ({language.upper()}):**\n``````")
    
    if st.session_state.approach_implementation.strip():
        parts.append(f"**IMPLEMENTATION PLAN:**\n{st.session_state.approach_implementation}")
    
    return "\n\n".join(parts) if parts else ""


# ==================== UI COMPONENTS ====================
def render_header():
    """Render professional header"""
    state = st.session_state.interview_state
    progress = calculate_progress(state)
    
    st.markdown(f"""
    <div class="interview-header">
        <h1 style="margin:0; font-size: 2rem;">💼 Technical Case study System</h1>
        <p style="margin:0.5rem 0 0 0; font-size: 0.9rem;">Candidate: {st.session_state.candidate_name} | Role: {st.session_state.role}</p>
        <div style="margin-top: 1rem;">Progress: {progress:.0f}%</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.progress(progress / 100)


def render_phase_status():
    """Render current phase status"""
    state = st.session_state.interview_state
    current_phase = state.get('current_phase', 'classification')
    
    phase_info = {
        'classification': ('📋', 'Classification Assessment', 'MCQ Questions'),
        'understanding': ('🤔', 'Problem Understanding', 'Clarifying Questions'),
        'approach': ('🎯', 'Solution Approach', 'Framework Development'),
        'followup': ('💬', 'Deep Dive', 'Follow-up Discussion'),
        'final': ('📊', 'Final Evaluation', 'Comprehensive Feedback')
    }
    
    emoji, title, description = phase_info.get(current_phase, ('📌', 'Interview', 'In Progress'))
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown(f"<div style='font-size: 3rem; text-align: center;'>{emoji}</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"### {title}")
        st.caption(description)
    
   

def render_chat_messages():
    """Render all conversation messages"""
    state = st.session_state.interview_state
    messages = state.get('messages', [])
    
    if not messages:
        return
    
    for msg in messages:
        if isinstance(msg, AIMessage):
            st.markdown(f"""
            <div class="ai-message">
                <strong>{msg.content}</strong><br>
            </div>
            """, unsafe_allow_html=True)
        elif isinstance(msg, HumanMessage):
            st.markdown(f"""
            <div class="candidate-message">
                <strong>👤 </strong><br>{msg.content}
            </div>
            """, unsafe_allow_html=True)

def render_approach_workspace():
    """Render approach workspace - FIRST question gets tabs based on role type"""
    state = st.session_state.interview_state
    count = state.get('approach_question_count', 0)
    current_activity = state.get('current_activity', '')
    
    # Get technical role status
    tech_type = state.get('tech_type', '')
    is_technical = tech_type == "Technical"
    
    # *** CRITICAL: Only show workspace for FIRST question (count=1) ***
    if count == 1 and current_activity == 'awaiting_approach_structured':
        st.markdown("### 📝 Solution Approach Workspace")
        st.info("📊 **Structure your approach using the tabs below. All content will be combined when you submit.**")
        
        # *** CONDITIONAL: Show 3 tabs for technical, 1 tab for non-technical ***
        if is_technical:
            # THREE-TAB INTERFACE FOR TECHNICAL ROLES
            tab1, tab2, tab3 = st.tabs(["📋 Framework", "⚙️ Technical Approach", "💻 Code Editor"])
            
            with tab1:
                st.markdown("**Framework & Methodology**")
                st.caption("Describe your overall framework, key steps, and structure")
                st.session_state.approach_framework = st.text_area(
                    "Framework Structure",
                    value=st.session_state.get('approach_framework', ''),
                    height=250,
                    placeholder="• Outline your framework\n• Key phases/steps\n• Areas of analysis\n• Overall methodology...",
                    key="approach_framework_input",
                    label_visibility="collapsed"
                )
            
            with tab2:
                st.markdown("**Technical Approach**")
                st.caption("Algorithms, models, techniques - use code tab for implementation")
                st.session_state.approach_technical = st.text_area(
                    "Technical Approach",
                    value=st.session_state.get('approach_technical', ''),
                    height=250,
                    placeholder="• Algorithms/models to use\n• Data preprocessing steps\n• Analysis techniques\n• Tools/libraries...",
                    key="approach_technical_input",
                    label_visibility="collapsed"
                )
            
            with tab3:
                st.markdown("**💻 Code/Pseudocode Editor**")
                st.caption("Write implementation code or pseudocode (optional)")
                
                # Language selector
                col1, col2 = st.columns([3, 1])
                with col2:
                    language = st.selectbox(
                        "Language",
                        ["python", "javascript", "java", "sql", "r", "c_cpp"],
                        index=0,
                        key="code_lang"
                    )
                    st.session_state.code_language = language
                
                # VS Code-style editor
                if EDITOR_AVAILABLE:
                    code_content = st_ace(
                        value=st.session_state.get('approach_code', '# Write your code here...\n\n'),
                        language=language,
                        theme="monokai",
                        height=400,
                        font_size=14,
                        tab_size=4,
                        show_gutter=True,
                        keybinding="vscode",
                        key="ace_editor"
                    )
                    if code_content:
                        st.session_state.approach_code = code_content
                else:
                    st.session_state.approach_code = st.text_area(
                        "Code",
                        value=st.session_state.get('approach_code', '# Write your code here...\n\n'),
                        height=400,
                        key="code_fallback",
                        label_visibility="collapsed"
                    )
        
        else:
            # SINGLE TAB FOR NON-TECHNICAL ROLES
            st.markdown("### 📋 Framework & Methodology")
            st.caption("Describe your overall framework, approach, and methodology")
            st.session_state.approach_framework = st.text_area(
                "Framework & Approach",
                value=st.session_state.get('approach_framework', ''),
                height=400,
                placeholder="• Outline your framework and methodology\n• Key phases and steps\n• Analysis approach\n• Data gathering methods\n• Tools and techniques you would use\n• Implementation plan...",
                key="approach_framework_nontechnical",
                label_visibility="collapsed"
            )
            
            # Clear technical fields for non-technical roles
            st.session_state.approach_technical = ""
            st.session_state.approach_code = ""
        
        # Submit button (same for both)
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("📤 Submit Complete Approach", type="primary", use_container_width=True, key="submit_full_approach"):
                combined = aggregate_approach_content()
                
                if combined.strip():
                    current_state = st.session_state.interview_state
                    current_state['messages'].append(HumanMessage(content=combined))
                    
                    # Clear workspace
                    st.session_state.approach_framework = ""
                    st.session_state.approach_technical = ""
                    st.session_state.approach_code = "# Write your code here...\n\n"
                    
                    st.session_state.interview_state = current_state
                    st.rerun()
                else:
                    st.warning("⚠️ Please provide your approach before submitting.")
    
    else:
        # *** Normal text box for questions 2, 3, 4 (count >= 2) ***
        st.markdown("### 💬 Your Response")
        user_response = st.text_area(
            "Your Response",
            height=180,
            placeholder="Type your response here...",
            key=f"approach_text_{count}",
            label_visibility="collapsed"
        )
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Submit Response", type="primary", use_container_width=True, key=f"submit_text_{count}"):
                if user_response.strip():
                    current_state = st.session_state.interview_state
                    current_state['messages'].append(HumanMessage(content=user_response))
                    st.session_state.interview_state = current_state
                    st.rerun()
                else:
                    st.warning("⚠️ Please provide a response.")

# ==================== PAGE VIEWS ====================
def welcome_page():
    """Welcome and candidate information collection"""
    apply_custom_css()
    
    st.markdown("""
    <div class="interview-header">
        <h1 style="margin:0;">💼 Technical Case study System</h1>
        <p style="margin:0.5rem 0 0 0; opacity: 0.9;">Experience a comprehensive consulting-style technical case study</p>
    </div>
    """, unsafe_allow_html=True)
    
    
    with st.form("candidate_info"):
        st.markdown("### Your Information")
        
        
        name = st.text_input("Full Name *", placeholder="John Doe")
        role = st.text_input("Target Role *", placeholder="Data Scientist")
        
        
        skills_input = st.text_input("Key Technical Skills (comma-separated)", 
                                     placeholder="Python, Machine Learning, SQL")
        
        st.markdown("### case study structure")
        st.info("""
        **Phase 1:** Classification (3 MCQs) - Determine case study domain  
        **Phase 2:** Understanding (3 questions) - Problem clarification  
        **Phase 3:** Approach (4 questions) - Solution development  
        **Phase 4:** Follow-up (3 questions) - Deep dive discussion  
        **Phase 5:** Final Evaluation - Comprehensive feedback  
        """)
        
      
        submitted = st.form_submit_button("🚀 Start case study", use_container_width=True, type="primary")
        
        if submitted:
            if not name or not role:
                st.error("Please provide your name, role.")
    
            else:
                st.session_state.candidate_name = name
                st.session_state.role = role
                st.session_state.skills = [s.strip() for s in skills_input.split(',')] if skills_input else []
                
                with st.spinner("Initializing case study system..."):
                    st.session_state.graph = build_interview_graph()
                    st.session_state.nodes = CaseStudyInterviewNodes()
                    
                    st.session_state.interview_state = {
                        'messages': [],
                        'candidate_name': name,
                        'role': role,
                        'skills': st.session_state.skills,
                        'current_phase': 'classification',
                        'mcq_current_question': 0,
                        'mcq_questions': [],
                        'classification_answers': [],
                        'mcq_completed': False,
                        'understanding_complete': False,
                        'approach_complete': False,
                        'followup_complete': False,
                        'interview_complete': False,
                        'understanding_question_count': 0,
                        'approach_question_count': 0,
                        'followup_question_count': 0,
                        'start_time': time.time()
                    }
                    
                    st.session_state.start_time = time.time()
                    st.session_state.initialized = True
                    st.session_state.current_page = "mcq"
                
                st.success("✅ System initialized! Starting case study...")
                time.sleep(1)
                st.rerun()


def mcq_phase():
    """MCQ Classification Phase"""
    apply_custom_css()
    render_header()
    
    state = st.session_state.interview_state
    
    # If already completed, redirect
    if state.get('mcq_completed'):
        st.session_state.current_page = "interview"
        st.rerun()
        return
    
    st.markdown("""
    <div class="phase-indicator">
        <h2>📋 Phase 1: Classification Assessment</h2>
        <p>Answer 3 multiple-choice questions to determine your case study domain.</p>
    </div>
    """, unsafe_allow_html=True)
    
    mcq_questions = state.get('mcq_questions', [])
    answers = state.get('classification_answers', [])
    
    # Generate questions one at a time
    if len(mcq_questions) < 3:
        if len(mcq_questions) == len(answers):
            with st.spinner(f"Generating question {len(mcq_questions) + 1}/3..."):
                try:
                    result = st.session_state.nodes.generate_mcq_node(state)
                    st.session_state.interview_state.update(result)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error generating question: {str(e)}")
                    if st.session_state.debug_mode:
                        import traceback
                        st.code(traceback.format_exc())
                    return
    
    mcq_questions = st.session_state.interview_state.get('mcq_questions', [])
    
    if not mcq_questions:
        st.warning("Generating your first question...")
        return
    
    st.markdown(f"### Progress: {len(answers)}/3 questions answered")
    st.progress(len(answers) / 3)
    st.markdown("---")
    
    for idx, q in enumerate(mcq_questions):
        st.markdown(f"### Question {idx + 1}")
        question_text = q.get('question', 'Question text missing')
        st.markdown(f"**{question_text}**")
        
        options = q.get('options', [])
        
        if idx < len(answers):
            st.success(f"✅ Your answer: {answers[idx]}")
        else:
            if idx == len(answers):
                for opt_idx, option in enumerate(options):
                    if isinstance(option, dict):
                        option_text = option.get('text', str(option))
                        option_letter = option.get('letter', chr(65 + opt_idx))
                    else:
                        option_text = str(option)
                        option_letter = chr(65 + opt_idx)
                    
                    option_key = f"mcq_q{idx}_opt{opt_idx}_v6"
                    
                    if st.button(
                        f"{option_letter}) {option_text}",
                        key=option_key,
                        use_container_width=True
                    ):
                        new_answers = st.session_state.interview_state.get('classification_answers', []).copy()
                        new_answers.append(option_text)
                        st.session_state.interview_state['classification_answers'] = new_answers
                        st.rerun()
            else:
                st.info("👆 Please answer the previous question first")
        
        st.markdown("---")
    
    if len(answers) >= 3:
        st.success("✅ All 3 questions answered! Classification complete!")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("➡️ Continue to Understanding Phase", type="primary", use_container_width=True, key="continue_btn"):
                with st.spinner("Analyzing your responses..."):
                    try:
                        result = st.session_state.nodes.process_mcq_answers_node(st.session_state.interview_state)
                        st.session_state.interview_state.update(result)
                        st.session_state.interview_state['mcq_completed'] = True
                        st.session_state.interview_state['current_phase'] = 'understanding'
                        
                        # Clear MCQ data
                        st.session_state.interview_state['mcq_questions'] = []
                        st.session_state.interview_state['classification_answers'] = []
                        
                        st.session_state.current_page = "interview"
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error processing answers: {str(e)}")
                        if st.session_state.debug_mode:
                            import traceback
                            st.code(traceback.format_exc())


def interview_phase():
    """Main interview phase"""
    apply_custom_css()
    render_header()
    
    state = st.session_state.interview_state
    current_phase = state.get('current_phase', 'understanding')
    
    # Ensure we're not in MCQ phase
    if current_phase == 'classification' or not state.get('mcq_completed'):
        st.session_state.current_page = "mcq"
        st.rerun()
        return
    
    render_phase_status()
    st.markdown("---")
    
    # Generate case study if needed
    if not state.get('case_study'):
        if not st.session_state.ai_processing:
            st.session_state.ai_processing = True
            with st.spinner("Generating your personalized case study..."):
                try:
                    nodes = st.session_state.nodes
                    result = nodes.generate_case_node(state)
                    st.session_state.interview_state.update(result)
                    st.session_state.ai_processing = False
                    st.rerun()
                except Exception as e:
                    st.session_state.ai_processing = False
                    st.error(f"Error generating case: {str(e)}")
                    if st.session_state.debug_mode:
                        import traceback
                        st.code(traceback.format_exc())
                    return
        return
    
    # Display messages
    render_chat_messages()
    
    messages = state.get('messages', [])
    phase_complete = state.get(f'{current_phase}_complete', False)
    
    # Determine if we need AI response
    last_message_is_human = len(messages) > 0 and isinstance(messages[-1], HumanMessage)
    last_message_is_ai = len(messages) > 0 and isinstance(messages[-1], AIMessage)
    needs_ai_response = len(messages) == 0 or last_message_is_human
    
    # Process AI response if needed
    if needs_ai_response and not phase_complete and not st.session_state.ai_processing:
        st.session_state.ai_processing = True
        
        with st.spinner("Vyaasa is thinking..."):
            try:
                nodes = st.session_state.nodes
                
                if current_phase == 'understanding':
                    result = nodes.understanding_node(state)
                    st.session_state.interview_state.update(result)
                    
                    if st.session_state.interview_state.get('understanding_complete'):
                        eval_result = nodes.understanding_evaluation_node(st.session_state.interview_state)
                        st.session_state.interview_state.update(eval_result)
                        st.session_state.interview_state['current_phase'] = 'approach'
                        
                elif current_phase == 'approach':
                    result = nodes.approach_node(state)
                    st.session_state.interview_state.update(result)
                    
                    if st.session_state.interview_state.get('approach_complete'):
                        eval_result = nodes.approach_evaluation_node(st.session_state.interview_state)
                        st.session_state.interview_state.update(eval_result)
                        st.session_state.interview_state['current_phase'] = 'followup'
                        
                elif current_phase == 'followup':
                    result = nodes.followup_node(state)
                    st.session_state.interview_state.update(result)
                    
                    if st.session_state.interview_state.get('followup_complete'):
                        eval_result = nodes.followup_evaluation_node(st.session_state.interview_state)
                        st.session_state.interview_state.update(eval_result)
                        st.session_state.interview_state['current_phase'] = 'final'
                        
                elif current_phase == 'final':
                    result = nodes.final_evaluation_node(state)
                    st.session_state.interview_state.update(result)
                    st.session_state.interview_state['interview_complete'] = True
                    st.session_state.current_page = "results"
                
                st.session_state.ai_processing = False
                st.rerun()
                
            except Exception as e:
                st.session_state.ai_processing = False
                st.error(f"Error: {str(e)}")
                if st.session_state.debug_mode:
                    import traceback
                    st.code(traceback.format_exc())
        return
    
    # Reset AI processing flag
    st.session_state.ai_processing = False
    
    st.markdown("---")
    
    # Show input if waiting for user
    show_input = not phase_complete and (last_message_is_ai or len(messages) == 0)
    
    if show_input:
        if current_phase == 'approach' and state.get('approach_question_count', 0) == 1:
            # Special workspace for first approach question
            render_approach_workspace()
        else:
            # Normal text input for all other questions
            st.markdown("### 💭 Your Response")
            
            with st.form("response_form", clear_on_submit=True):
                user_input = st.text_area(
                    "Type your answer here",
                    height=150,
                    placeholder="Share your thoughts, ask questions, or provide your analysis...",
                    label_visibility="collapsed",
                    key="user_response_input"
                )
                
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    submitted = st.form_submit_button(
                        "📤 Submit Response", 
                        use_container_width=True, 
                        type="primary"
                    )
                
                if submitted and user_input.strip():
                    new_messages = st.session_state.interview_state.get('messages', [])
                    new_messages.append(HumanMessage(content=user_input.strip()))
                    st.session_state.interview_state['messages'] = new_messages
                    st.rerun()
                elif submitted:
                    st.warning("⚠️ Please enter a response before submitting.")

def generate_chat_transcript() -> str:
    """Generate a formatted chat transcript of the entire interview"""
    state = st.session_state.interview_state
    messages = state.get('messages', [])
    
    transcript = []
    transcript.append("=" * 80)
    transcript.append("TECHNICAL CASE INTERVIEW - CHAT TRANSCRIPT")
    transcript.append("=" * 80)
    transcript.append(f"\nCandidate: {st.session_state.candidate_name}")
    transcript.append(f"Target Role: {st.session_state.role}")
    transcript.append(f"Skills: {', '.join(st.session_state.skills)}")
    transcript.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    transcript.append(f"Duration: {format_time_remaining(int(time.time() - st.session_state.start_time))}")
    transcript.append("\n" + "=" * 80)
    
    # Add case study details
    case_study = state.get('case_study', {})
    if case_study:
        transcript.append("\n\nCASE STUDY DETAILS")
        transcript.append("-" * 80)
        transcript.append(f"Domain: {case_study.get('domain', 'N/A')}")
        transcript.append(f"Type: {state.get('tech_type', 'N/A')}")
        transcript.append(f"\nScenario:\n{case_study.get('scenario', 'N/A')}")
        transcript.append(f"\nObjective:\n{case_study.get('objective', 'N/A')}")
        
        constraints = case_study.get('constraints', [])
        if constraints:
            transcript.append(f"\nConstraints:")
            for i, constraint in enumerate(constraints, 1):
                transcript.append(f"  {i}. {constraint}")
    
    # Add conversation
    transcript.append("\n\n" + "=" * 80)
    transcript.append("INTERVIEW CONVERSATION")
    transcript.append("=" * 80 + "\n")
    
    current_phase = None
    msg_count = 0
    
    for msg in messages:
        # Detect phase changes based on message content
        if isinstance(msg, AIMessage):
            content_lower = msg.content.lower()
            if 'understanding' in content_lower and current_phase != 'understanding':
                current_phase = 'understanding'
                transcript.append(f"\n{'=' * 80}")
                transcript.append("PHASE: PROBLEM UNDERSTANDING")
                transcript.append("=" * 80 + "\n")
            elif 'approach' in content_lower and current_phase != 'approach':
                current_phase = 'approach'
                transcript.append(f"\n{'=' * 80}")
                transcript.append("PHASE: SOLUTION APPROACH")
                transcript.append("=" * 80 + "\n")
            elif 'follow' in content_lower and current_phase != 'followup':
                current_phase = 'followup'
                transcript.append(f"\n{'=' * 80}")
                transcript.append("PHASE: FOLLOW-UP DISCUSSION")
                transcript.append("=" * 80 + "\n")
        
        msg_count += 1
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        if isinstance(msg, AIMessage):
            transcript.append(f"[{timestamp}] CASE STUDY (Vyaasa):")
            transcript.append("-" * 80)
            transcript.append(f"{msg.content}\n")
        elif isinstance(msg, HumanMessage):
            transcript.append(f"[{timestamp}] CANDIDATE ({st.session_state.candidate_name}):")
            transcript.append("-" * 80)
            transcript.append(f"{msg.content}\n")
    
    transcript.append("\n" + "=" * 80)
    transcript.append(f"END OF TRANSCRIPT - Total Messages: {msg_count}")
    transcript.append("=" * 80)
    
    return "\n".join(transcript)


def generate_evaluation_report() -> str:
    """Generate a comprehensive evaluation report"""
    state = st.session_state.interview_state
    
    report = []
    report.append("=" * 80)
    report.append("TECHNICAL CASE INTERVIEW - EVALUATION REPORT")
    report.append("=" * 80)
    report.append(f"\nCandidate: {st.session_state.candidate_name}")
    report.append(f"Target Role: {st.session_state.role}")
    report.append(f"Skills: {', '.join(st.session_state.skills)}")
    report.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("\n" + "=" * 80)
    
    # Phase Scores
    report.append("\n\nPHASE SCORES")
    report.append("-" * 80)
    
    understanding_eval = state.get('understanding_evaluation', {})
    approach_eval = state.get('approach_evaluation', {})
    followup_eval = state.get('followup_evaluation', {})
    
    understanding_score = understanding_eval.get('score', 0)
    approach_score = approach_eval.get('score', 0)
    followup_score = followup_eval.get('score', 0)
    total_score = understanding_score + approach_score + followup_score
    
    report.append(f"\n1. Problem Understanding Phase: {understanding_score}/10")
    if understanding_eval.get('feedback'):
        report.append(f"   Feedback: {understanding_eval['feedback']}")
    
    report.append(f"\n2. Solution Approach Phase: {approach_score}/10")
    if approach_eval.get('feedback'):
        report.append(f"   Feedback: {approach_eval['feedback']}")
    
    report.append(f"\n3. Follow-up Discussion Phase: {followup_score}/10")
    if followup_eval.get('feedback'):
        report.append(f"   Feedback: {followup_eval['feedback']}")
    
    report.append(f"\n{'─' * 80}")
    report.append(f"TOTAL SCORE: {total_score}/30")
    
    # Final Evaluation
    final_eval = state.get('final_evaluation', {})
    
    if final_eval:
        report.append("\n\n" + "=" * 80)
        report.append("OVERALL ASSESSMENT")
        report.append("=" * 80)
        report.append(f"\n{final_eval.get('interview_summary', 'No summary available')}")
        
        # Dimension Scores
        dimension_scores = final_eval.get('dimension_scores', [])
        if dimension_scores:
            report.append("\n\n" + "=" * 80)
            report.append("DIMENSION-WISE EVALUATION")
            report.append("=" * 80)
            
            for i, dim in enumerate(dimension_scores, 1):
                report.append(f"\n{i}. {dim['dimension']}")
                report.append(f"   Score: {dim['score']}/10 (Weight: {dim['weight']}%)")
                report.append(f"   Justification: {dim['justification']}")
                if 'candidate_response_excerpt' in dim:
                    excerpt = dim['candidate_response_excerpt']
                    report.append(f"   Your Response Excerpt: \"{excerpt[:200]}...\"")
                report.append("")
        
        # Strengths
        strengths = final_eval.get('key_strengths', [])
        if strengths:
            report.append("\n" + "=" * 80)
            report.append("KEY STRENGTHS")
            report.append("=" * 80)
            for i, strength in enumerate(strengths, 1):
                report.append(f"{i}. {strength}")
        
        # Development Areas
        dev_areas = final_eval.get('development_areas', [])
        if dev_areas:
            report.append("\n\n" + "=" * 80)
            report.append("DEVELOPMENT AREAS")
            report.append("=" * 80)
            for i, area in enumerate(dev_areas, 1):
                report.append(f"{i}. {area}")
        
        # Recommendations
        recommendations = final_eval.get('recommended_next_steps', [])
        if recommendations:
            report.append("\n\n" + "=" * 80)
            report.append("RECOMMENDED NEXT STEPS")
            report.append("=" * 80)
            for i, rec in enumerate(recommendations, 1):
                report.append(f"{i}. {rec}")
    
    # Interview Metadata
    report.append("\n\n" + "=" * 80)
    report.append("INTERVIEW METADATA")
    report.append("=" * 80)
    case_study = state.get('case_study', {})
    report.append(f"\nCase Domain: {case_study.get('domain', 'N/A')}")
    report.append(f"Technical Type: {state.get('tech_type', 'N/A')}")
    report.append(f"Questions Asked: {len(state.get('messages', []))}")
    report.append(f"Interview Duration: {format_time_remaining(int(time.time() - st.session_state.start_time))}")
    
    report.append("\n\n" + "=" * 80)
    report.append("END OF EVALUATION REPORT")
    report.append("=" * 80)
    
    return "\n".join(report)


def create_interview_report_zip() -> bytes:
    """Create a ZIP file containing chat transcript and evaluation report"""
    # Create BytesIO object to store ZIP in memory
    zip_buffer = io.BytesIO()
    
    # Generate reports
    chat_transcript = generate_chat_transcript()
    evaluation_report = generate_evaluation_report()
    
    # Generate metadata JSON
    state = st.session_state.interview_state
    metadata = {
        "candidate_name": st.session_state.candidate_name,
        "role": st.session_state.role,
        "skills": st.session_state.skills,
        "interview_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "scores": {
            "understanding": state.get('understanding_evaluation', {}).get('score', 0),
            "approach": state.get('approach_evaluation', {}).get('score', 0),
            "followup": state.get('followup_evaluation', {}).get('score', 0)
        },
        "domain": state.get('case_study', {}).get('domain', 'N/A'),
        "tech_type": state.get('tech_type', 'N/A')
    }
    
    # Create ZIP file
    with zipfile.ZipFile(zip_buffer, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        # Add chat transcript
        zf.writestr('01_Chat_Transcript.txt', chat_transcript.encode('utf-8'))
        
        # Add evaluation report
        zf.writestr('02_Evaluation_Report.txt', evaluation_report.encode('utf-8'))
        
        # Add metadata JSON
        zf.writestr('03_Metadata.json', json.dumps(metadata, indent=2).encode('utf-8'))
    
    # Reset buffer position to beginning
    zip_buffer.seek(0)
    
    return zip_buffer.getvalue()

def results_page():
    """Display final interview results"""
    apply_custom_css()
    
    st.markdown("""
    <div class="interview-header">
        <h1 style="margin:0;">🎉 Case Interview Completed!</h1>
        <p style="margin:0.5rem 0 0 0; opacity: 0.9;">Thank you for participating</p>
    </div>
    """, unsafe_allow_html=True)
    
    state = st.session_state.interview_state
    
    st.markdown("## 📊 Your Performance Report")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        understanding_score = state.get('understanding_evaluation', {}).get('score', 0)
        st.metric("Understanding Phase", f"{understanding_score}/10")
    
    with col2:
        approach_score = state.get('approach_evaluation', {}).get('score', 0)
        st.metric("Approach Phase", f"{approach_score}/10")
    
    with col3:
        followup_score = state.get('followup_evaluation', {}).get('score', 0)
        st.metric("Follow-up Phase", f"{followup_score}/10")
    
    st.markdown("---")
    
    final_eval = state.get('final_evaluation', {})
    
    if final_eval:
        st.markdown("### 📝 Overall Assessment")
        st.write(final_eval.get('interview_summary', 'No feedback available'))
        
        # Dimension scores table
        dimension_scores = final_eval.get('dimension_scores', [])
        if dimension_scores:
            st.markdown("### 📊 Dimension Scores")
            for dim in dimension_scores:
                with st.expander(f"{dim['dimension']} - {dim['score']}/10 (Weight: {dim['weight']}%)"):
                    st.write(f"**Justification:** {dim['justification']}")
                    if 'candidate_response_excerpt' in dim:
                        st.info(f"**Your Response:** \"{dim['candidate_response_excerpt'][:200]}...\"")
        
        st.markdown("### 💪 Key Strengths")
        for strength in final_eval.get('key_strengths', []):
            st.success(f"✓ {strength}")
        
        st.markdown("### 🎯 Development Areas")
        for area in final_eval.get('development_areas', []):
            st.info(f"→ {area}")
        
        st.markdown("### 🚀 Recommended Next Steps")
        for rec in final_eval.get('recommended_next_steps', []):
            st.warning(f"💡 {rec}")
    
    st.markdown("---")
    
    # Updated download and restart buttons
    col1, col2 = st.columns(2)
    
    with col1:
        try:
            # Generate ZIP file
            zip_data = create_interview_report_zip()
            
            # Generate filename with timestamp
            filename = f"Interview_Report_{st.session_state.candidate_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            
            # Download button
            st.download_button(
                label="📥 Download Complete Report (ZIP)",
                data=zip_data,
                file_name=filename,
                mime="application/zip",
                use_container_width=True,
                type="primary"
            )
            
        except Exception as e:
            st.error(f"Error generating report: {str(e)}")
            if st.session_state.debug_mode:
                import traceback
                st.code(traceback.format_exc())
    
    with col2:
        if st.button("🔄 Start New Interview", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


# ==================== SIDEBAR ====================
def render_sidebar():
    """Render sidebar with navigation and debug options"""
    with st.sidebar:
        st.markdown("## 🎯 Case study Control Panel")
        
        if st.session_state.initialized:
            st.markdown(f"**Candidate:** {st.session_state.candidate_name}")
            st.markdown(f"**Role:** {st.session_state.role}")
            st.markdown("---")
            
            st.markdown("### Case study Progress")
            state = st.session_state.interview_state
            
            phases = {
                'Classification': state.get('mcq_completed', False),
                'Understanding': state.get('understanding_complete', False),
                'Approach': state.get('approach_complete', False),
                'Follow-up': state.get('followup_complete', False),
                'Final': state.get('interview_complete', False)
            }
            
            for phase, completed in phases.items():
                status = "✅" if completed else "⏳"
                st.markdown(f"{status} {phase}")
            
            st.markdown("---")
            
            st.session_state.debug_mode = st.checkbox("🐛 Debug Mode", value=st.session_state.debug_mode)
            
            if st.session_state.debug_mode:
                st.markdown("### Debug Info")
                st.json({
                    'current_page': st.session_state.current_page,
                    'current_phase': state.get('current_phase'),
                    'message_count': len(state.get('messages', [])),
                    'ai_processing': st.session_state.ai_processing,
                    'case_study_generated': bool(state.get('case_study')),
                    'approach_count': state.get('approach_question_count', 0)
                })
            
            st.markdown("---")
            
            if st.button("🔄 Restart Case study", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()


# ==================== MAIN APPLICATION ====================
def main():
    """Main application entry point"""
    initialize_session_state()
    render_sidebar()
    
    if not st.session_state.initialized:
        welcome_page()
    elif st.session_state.current_page == "mcq":
        mcq_phase()
    elif st.session_state.current_page == "interview":
        interview_phase()
    elif st.session_state.current_page == "results":
        results_page()


if __name__ == "__main__":
    main()
