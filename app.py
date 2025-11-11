--- START OF FILE app.py ---

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


def initialize_session_state():
    """Initialize all session state variables"""
    defaults = {
        'initialized': False,
        'messages': [],
        'candidate_name': '',
        'role': '',
        'skills': [],
        'interview_state': {},
        'graph': None,
        'nodes': None,
        'start_time': None,
        'current_page': 'welcome',
        'approach_framework': '',
        'approach_technical': '',
        'approach_code': 'Write your code here...',
        'approach_implementation': '',
        'code_language': 'python',
        'debug_mode': False,
        'ai_processing': False,
        'waiting_for_user': False,
        'awaiting_custom_industry': False,  # ADD THIS
        'temp_q2_answer': ''                 # ADD THIS
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
    total_questions = 3 + 3 + 4 
    completed = 0
    if state.get('mcq_completed'):
        completed += 3
    completed += state.get('understanding_question_count', 0)
    completed += state.get('approach_question_count', 0)
  
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
                       
                        'interview_complete': False,
                        'understanding_question_count': 0,
                        'approach_question_count': 0,
                       
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
                # Display answer buttons
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
                        
                        # Check if Question 2 (idx=1) and Option D (opt_idx=3) - "Other"
                        if idx == 1 and opt_idx == 3:
                            st.session_state['awaiting_custom_industry'] = True
                            st.session_state['temp_q2_answer'] = option_text
                            st.rerun()
                        else:
                            new_answers.append(option_text)
                            st.session_state.interview_state['classification_answers'] = new_answers
                            st.rerun()
                
                # Show custom industry input if "Other" was selected in Q2
                if idx == 1 and st.session_state.get('awaiting_custom_industry', False):
                    st.markdown("---")
                    st.info("📝 Please specify your preferred industry:")
                    
                    # Create unique keys based on current answer count
                    answers_count = len(st.session_state.interview_state.get('classification_answers', []))
                    custom_industry_key = f"custom_industry_input_{answers_count}"
                    confirm_btn_key = f"confirm_industry_btn_{answers_count}"
                    
                    custom_industry = st.text_input(
                        label="Your Industry Preference",
                        placeholder="e.g., Manufacturing, Retail, Healthcare",
                        key=custom_industry_key
                    )
                    
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        if st.button("✅ Confirm", use_container_width=True, type="primary", key=confirm_btn_key):
                            if custom_industry.strip():
                                new_answers = st.session_state.interview_state.get('classification_answers', []).copy()
                                new_answers.append(custom_industry.strip())
                                st.session_state.interview_state['classification_answers'] = new_answers
                                st.session_state['awaiting_custom_industry'] = False
                                st.session_state.pop('temp_q2_answer', None)
                                st.rerun()
                            else:
                                st.warning("⚠️ Please enter an industry name.")
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
    transcript.append('=' * 80)
    transcript.append('TECHNICAL CASE INTERVIEW - CHAT TRANSCRIPT')
    transcript.append('=' * 80)
    transcript.append('')
    
    # Candidate Information
    transcript.append(f'Candidate: {st.session_state.candidate_name}')
    transcript.append(f'Target Role: {st.session_state.role}')
    skills_str = ', '.join(st.session_state.skills) if st.session_state.skills else 'Not specified'
    transcript.append(f'Skills: {skills_str}')
    transcript.append(f'Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    duration = format_time_remaining(int(time.time() - st.session_state.start_time))
    transcript.append(f'Duration: {duration}')
    transcript.append('')
    transcript.append('=' * 80)
    
    # Case Study Details
    case_study = state.get('case_study')
    if case_study and isinstance(case_study, dict):
        transcript.append('CASE STUDY DETAILS')
        transcript.append('-' * 80)
        transcript.append(f'Title: {case_study.get("title", "N/A")}')
        transcript.append(f'Company: {case_study.get("company_name", "N/A")}')
        transcript.append(f'Domain: {state.get("domain", "N/A")}')
        transcript.append(f'Case Type: {state.get("case_type", "N/A")}')
        transcript.append(f'Technical Type: {state.get("tech_type", "N/A")}')
        transcript.append('\nSITUATION:')
        transcript.append(f'{case_study.get("situation", "N/A")}')
        transcript.append('\nPROBLEM STATEMENT:')
        transcript.append(f'{case_study.get("problem_statement", "N/A")}')
        transcript.append('')
        transcript.append('=' * 80)
    
    # Interview Conversation
    transcript.append('INTERVIEW CONVERSATION')
    transcript.append('=' * 80)
    transcript.append('')
    
    for msg in messages:
        if isinstance(msg, AIMessage):
            timestamp = datetime.now().strftime('%H:%M:%S')
            transcript.append(f'[{timestamp}] CASE STUDY (Vyaasa):')
            transcript.append('-' * 80)
            transcript.append(msg.content)
            transcript.append('')
        
        elif isinstance(msg, HumanMessage):
            timestamp = datetime.now().strftime('%H:%M:%S')
            transcript.append(f'[{timestamp}] CANDIDATE ({st.session_state.candidate_name}):')
            transcript.append('-' * 80)
            transcript.append(msg.content)
            transcript.append('')
    
    transcript.append('')
    transcript.append('=' * 80)
    transcript.append(f'END OF TRANSCRIPT - Total Messages: {len(messages)}')
    transcript.append('=' * 80)
    
    return '\n'.join(transcript)

def generate_evaluation_report() -> str:
    """Generate a comprehensive evaluation report"""
    state = st.session_state.interview_state
    final_eval = state.get('final_evaluation', {})
    case_study = state.get('case_study', {})
    
    report = []
    report.append("=" * 80)
    report.append("TECHNICAL CASE INTERVIEW - EVALUATION REPORT")
    report.append("=" * 80)
    
    # Metadata
    report.append("\nCandidate: " + st.session_state.candidate_name)
    report.append("Target Role: " + st.session_state.role)
    report.append("Date: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    report.append("Interview Duration: " + format_time_remaining(int(time.time() - st.session_state.start_time)))

    # Case Context
    report.append("\n" + "=" * 80)
    report.append("CASE STUDY CONTEXT")
    report.append("-" * 80)
    report.append(f'Title: {case_study.get("title", "N/A")}')
    report.append(f'Company: {case_study.get("company_name", "N/A")}')
    report.append(f'Problem: {case_study.get("problem_statement", "N/A")}')
    
    # Overall Assessment
    report.append("\n" + "=" * 80)
    report.append("OVERALL ASSESSMENT")
    report.append("=" * 80)
    report.append(f"\nOverall Score: {final_eval.get('overall_score', 'N/A')} / 10")
    report.append(f"Performance Level: {final_eval.get('performance_level', 'N/A')}")
    report.append(f"\nSummary: {final_eval.get('interview_summary', 'No summary available.')}")
        
    # Dimension Scores
    dimension_scores = final_eval.get('dimension_scores', [])
    if dimension_scores:
        report.append("\n\n" + "=" * 80)
        report.append("DIMENSION-WISE EVALUATION")
        report.append("=" * 80)
        
        for dim in dimension_scores:
            report.append(f"\nDimension: {dim.get('dimension', 'N/A')} (Weight: {dim.get('weight', 0)}%)")
            report.append(f"  - Score: {dim.get('score', 0)}/10")
            report.append(f"  - Justification: {dim.get('justification', 'N/A')}")
            excerpt = dim.get('candidate_response_excerpt', 'N/A')
            report.append(f'  - Supporting Response: "{excerpt[:250]}..."')
    
    # Strengths
    strengths = final_eval.get('key_strengths', [])
    if strengths:
        report.append("\n\n" + "=" * 80)
        report.append("KEY STRENGTHS")
        report.append("=" * 80)
        for i, strength in enumerate(strengths, 1):
            report.append(f"{i}. {strength}")
    
    # Development Areas
    dev_areas = final_eval.get('development_areas', [])
    if dev_areas:
        report.append("\n\n" + "=" * 80)
        report.append("AREAS FOR DEVELOPMENT")
        report.append("=" * 80)
        for i, area in enumerate(dev_areas, 1):
            report.append(f"{i}. {area}")

    # Phase Breakdown
    phase_breakdown = final_eval.get('phase_breakdown', {})
    if phase_breakdown:
        report.append("\n\n" + "=" * 80)
        report.append("PHASE-BY-PHASE BREAKDOWN")
        report.append("=" * 80)
        report.append(f"\nUnderstanding Phase: {phase_breakdown.get('understanding', 'N/A')}")
        report.append(f"Approach Phase: {phase_breakdown.get('approach', 'N/A')}")
        report.append(f"Follow-up Phase: {phase_breakdown.get('followup', 'N/A')}")
        
    # Recommendations
    recommendations = final_eval.get('recommended_next_steps', [])
    if recommendations:
        report.append("\n\n" + "=" * 80)
        report.append("RECOMMENDED NEXT STEPS")
        report.append("=" * 80)
        for i, rec in enumerate(recommendations, 1):
            report.append(f"{i}. {rec}")
    
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
    final_eval = state.get('final_evaluation', {})
    
    metadata = {
        "candidate_name": st.session_state.candidate_name,
        "role": st.session_state.role,
        "skills": st.session_state.skills,
        "interview_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "overall_score": final_eval.get('overall_score', 'N/A'),
        "performance_level": final_eval.get('performance_level', 'N/A'),
        "phase_scores": {
            "understanding": state.get('understanding_evaluation', {}).get('score', 0),
            "approach": state.get('approach_evaluation', {}).get('score', 0)
        },
        "case_domain": state.get('domain', 'N/A'),
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
    final_eval = state.get('final_evaluation', {})
    
    st.markdown("## 📊 Your Performance Report")
    
    col1, col2 = st.columns(2)
    
    with col1:
        overall_score = final_eval.get('overall_score', 0)
        st.metric("Overall Score", f"{overall_score}/10")
    
    with col2:
        performance_level = final_eval.get('performance_level', 'N/A')
        st.metric("Performance Level", performance_level)

    st.markdown("---")
    
    if final_eval:
        st.markdown("### 📝 Overall Assessment")
        st.write(final_eval.get('interview_summary', 'No feedback available'))
        
        # Dimension scores table
        dimension_scores = final_eval.get('dimension_scores', [])
        if dimension_scores:
            st.markdown("### 📊 Dimension Scores")
            for dim in dimension_scores:
                with st.expander(f"{dim.get('dimension', 'N/A')} - {dim.get('score', 0)}/10 (Weight: {dim.get('weight', 0)}%)"):
                    st.write(f"**Justification:** {dim.get('justification', 'N/A')}")
                    excerpt = dim.get('candidate_response_excerpt')
                    if excerpt:
                        st.info(f"**Your Response:** \"{excerpt[:200]}...\"")
        
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
                'Final': state.get('interview_complete', False)
            }
            
            for phase, completed in phases.items():
                status = "✅" if completed else "⏳"
                st.markdown(f"{status} {phase}")
            
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
