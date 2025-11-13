# app.py - Pure graph.stream() approach for all phases

import streamlit as st
import time
from datetime import datetime
from typing import Dict, List
from langchain_core.messages import HumanMessage, AIMessage
from graph.graph_builder import build_interview_graph
import io
import json
import streamlit.components.v1 as components
def inject_clipboard_blocker():
    """Inject JavaScript to block copy-paste operations"""
    components.html(
        """
        <script>
        const disableClipboard = () => {
            const parent = window.parent.document;
            const inputs = parent.querySelectorAll('textarea, input[type="text"]');
            
            inputs.forEach(input => {
                if (!input.hasAttribute('data-clipboard-disabled')) {
                    ['copy', 'paste', 'cut'].forEach(event => {
                        input.addEventListener(event, (e) => {
                            e.preventDefault();
                            alert(`❌ ${event.charAt(0).toUpperCase() + event.slice(1)} is disabled during the interview.`);
                        });
                    });
                    
                    input.addEventListener('keydown', (e) => {
                        if ((e.ctrlKey || e.metaKey) && ['c', 'v', 'x'].includes(e.key)) {
                            e.preventDefault();
                            alert('❌ Keyboard shortcuts are disabled.');
                        }
                    });
                    
                    input.addEventListener('contextmenu', (e) => e.preventDefault());
                    input.setAttribute('data-clipboard-disabled', 'true');
                }
            });
        };
        
        disableClipboard();
        const observer = new MutationObserver(disableClipboard);
        observer.observe(window.parent.document.body, { childList: true, subtree: true });
        </script>
        """,
        height=0,
    )

try:
    from streamlit_ace import st_ace
    EDITOR_AVAILABLE = True
except ImportError:
    EDITOR_AVAILABLE = False
    st.warning("⚠️ Code editor not available. Install with: pip install streamlit-ace")

# ==================== PAGE CONFIGURATION ====================
st.set_page_config(
    page_title="Case Study Interview",
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
    
    /* ADD THIS - Validation error styling */
    .validation-error {
        background-color: #ffebee;
        color: #c62828;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #c62828;
        margin: 1rem 0;
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
        'candidate_name': '',
        'role': '',
        'skills': [],
        'graph': None,
        'config': {"configurable": {"thread_id": "interview_thread_1"}},
        'interview_state': {},
        'current_page': 'welcome',
        'approach_framework': '',
        'approach_technical': '',
        'approach_code': '# Write your code here...\n\n',
        'approach_implementation': '',
        'code_language': 'python',
        'debug_mode': False,
        'validation_error': '',
        'awaiting_graph_response': False
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

# ==================== GRAPH STREAM HELPER ====================
def process_graph_stream(trigger_message: str = None) -> bool:
    """
    Process graph stream and update state.
    Returns True if graph execution completed successfully.
    """
    if not st.session_state.graph:
        st.error("Graph not initialized")
        return False
    
    graph = st.session_state.graph
    config = st.session_state.config
    current_state = st.session_state.interview_state
    
    # Add trigger message if provided
    if trigger_message:
        if 'messages' not in current_state:
            current_state['messages'] = []
        current_state['messages'].append(HumanMessage(content=trigger_message))
    
    try:
        # Stream through graph
        for event in graph.stream(current_state, config):
            if st.session_state.debug_mode:
                st.sidebar.write(f"Event: {list(event.keys())}")
            
            for node_name, node_state in event.items():
                if node_state:
                    # Update state from graph output
                    for key, value in node_state.items():
                        if key == 'messages':
                            # Append new messages
                            if 'messages' not in current_state:
                                current_state['messages'] = []
                            existing_ids = {id(m) for m in current_state['messages']}
                            for msg in value:
                                if id(msg) not in existing_ids:
                                    current_state['messages'].append(msg)
                        else:
                            # Update other state fields
                            current_state[key] = value
        
        # Update session state
        st.session_state.interview_state = current_state
        return True
    
    except Exception as e:
        st.error(f"Graph execution error: {str(e)}")
        if st.session_state.debug_mode:
            import traceback
            st.code(traceback.format_exc())
        return False

# ==================== UTILITY FUNCTIONS ====================
def calculate_progress(state: Dict) -> float:
    """Calculate overall interview progress percentage"""
    total_questions = 3 + 3 + 4
    completed = 0
    if state.get('mcq_completed'):
        completed += 3
    completed += state.get('understanding_question_count', 0)
    completed += state.get('approach_question_count', 0)
    return (completed / total_questions) * 100

# ==================== UTILITY FUNCTIONS ====================
def aggregate_approach_content() -> str:
    """Aggregate all approach workspace content"""
    parts = []
    
    if st.session_state.approach_framework.strip():
        parts.append(f"**FRAMEWORK & METHODOLOGY:**\n{st.session_state.approach_framework}")
    
    if st.session_state.approach_technical.strip():
        parts.append(f"**TECHNICAL APPROACH:**\n{st.session_state.approach_technical}")
    
    code = st.session_state.approach_code.strip()
    if code and code not in ["# Write your code here...\n\n", "# Write your code here..."]:
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
        <h1 style="margin:0; font-size: 2rem;">💼 Technical Case Study System</h1>
        <p style="margin:0.5rem 0 0 0; font-size: 0.9rem;">
            Candidate: {st.session_state.candidate_name} | Role: {st.session_state.role}
        </p>
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
        'case_gen': ('🎯', 'Case Generation', 'Creating Personalized Case'),
        'understanding': ('🤔', 'Problem Understanding', 'Clarifying Questions'),
        'approach': ('💡', 'Solution Approach', 'Framework Development'),
        'final': ('📊', 'Final Evaluation', 'Comprehensive Feedback')
    }
    
    emoji, title, description = phase_info.get(current_phase, ('📌', 'Interview', 'In Progress'))
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown(f"<div style='font-size: 3rem; text-align: center;'>{emoji}</div>", 
                   unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"### {title}")
        st.caption(description)
def render_chat_messages():
    """Render only the last conversation message pair (AI question + Human answer)"""
    state = st.session_state.interview_state
    current_phase = state.get('current_phase', 'classification')
    
    # DON'T display messages during MCQ or case generation
    if current_phase in ['classification', 'case_gen']:
        return
    
    messages = state.get('messages', [])
    if not messages:
        return
    
    # Only show the last 2 messages (AI question + Human answer)
    last_messages = messages[-2:] if len(messages) >= 2 else messages
    
    for msg in last_messages:
        if isinstance(msg, AIMessage):
            st.markdown(f"""
            <div class="ai-message">
                <strong>{msg.content}</strong><br>
            </div>
            """, unsafe_allow_html=True)
        
def render_approach_workspace():
    """Render approach workspace with tabs based on technical type"""
    state = st.session_state.interview_state
    
    # Get technical type
    tech_type = state.get("tech_type", "")
    domain = state.get("domain", "")
    role = state.get("role", "")
    
    # Technical detection with fallback
    technical_keywords = ["data science", "machine learning", "ml", "ai", "software", "data analyst", "data scientist", "engineer"]
    is_technical = (
        tech_type == "Technical" or
        any(keyword in domain.lower() for keyword in technical_keywords) or
        any(keyword in role.lower() for keyword in technical_keywords)
    )
    
    st.markdown("### 📋 Solution Approach Workspace")
    st.info("Structure your approach using the tabs below. **Minimum 250 words required.**")
    
    if is_technical:
        # ✅ TECHNICAL CASE: Framework, Technical, Code tabs
        tab1, tab2, tab3 = st.tabs(["📋 Framework", "⚙️ Technical", "💻 Code"])
        
        with tab1:
            st.markdown("**Framework & Methodology**")
            st.session_state.approach_framework = st.text_area(
                "Framework",
                value=st.session_state.get("approach_framework", ""),
                height=300,
                placeholder="• Overall framework and approach\n• Key phases/steps\n• Methodology specific to this case...",
                key="fw_input_tech",
                label_visibility="collapsed"
            )
        
        with tab2:
            st.markdown("**Technical Approach**")
            st.session_state.approach_technical = st.text_area(
                "Technical",
                value=st.session_state.get("approach_technical", ""),
                height=300,
                placeholder="• Algorithms/models for this case\n• Data preprocessing strategy\n• Tools/libraries\n• Architecture decisions...",
                key="tech_input",
                label_visibility="collapsed"
            )
        
        with tab3:
            st.markdown("**Code/Pseudocode**")
            
            # Language selector
            col1, col2 = st.columns([3, 1])
            with col2:
                language = st.selectbox(
                    "Language",
                    ["python", "javascript", "sql", "r", "c_cpp", "pseudocode"],
                    index=0,
                    key="lang_select"
                )
                st.session_state.code_language = language
            
            # Code input
            st.session_state.approach_code = st.text_area(
                "Code",
                value=st.session_state.get("approach_code", "# Write your code here...\n\n"),
                height=400,
                placeholder=f"# Write your {language} code or pseudocode here\n# Example:\n# def analyze_data(df):\n#     # Your implementation\n#     pass",
                key="code_input",
                label_visibility="collapsed"
            )
    
    else:
        # ❌ NON-TECHNICAL CASE: Framework and Implementation tabs
        tab1, tab2 = st.tabs(["📋 Framework", "📝 Implementation"])
        
        with tab1:
            st.markdown("**Framework & Methodology**")
            st.session_state.approach_framework = st.text_area(
                "Framework",
                value=st.session_state.get("approach_framework", ""),
                height=400,
                placeholder="• Overall framework and approach\n• Key phases/steps\n• Analysis methodology\n• Prioritization logic...",
                key="fw_non_tech",
                label_visibility="collapsed"
            )
        
        with tab2:
            st.markdown("**Implementation Plan**")
            st.session_state.approach_implementation = st.text_area(
                "Implementation",
                value=st.session_state.get("approach_implementation", ""),
                height=400,
                placeholder="• Step-by-step execution plan\n• Timeline and milestones\n• Resource requirements\n• Risk mitigation strategies...",
                key="impl_input",
                label_visibility="collapsed"
            )
    
    # Validation error display
    if st.session_state.get("validation_error"):
        st.markdown(
            f'<div class="validation-error">⚠️ {st.session_state.validation_error}</div>',
            unsafe_allow_html=True
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Submit button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📤 Submit Complete Approach", type="primary", use_container_width=True, key="submit_full_approach"):
            combined = aggregate_approach_content()
            
            # Validate
            is_valid, error_msg = validate_response(combined, "awaiting_approach_structured")
            if not is_valid:
                st.session_state.validation_error = error_msg
                st.rerun()
            else:
                st.session_state.validation_error = ""
                
                # Process
                with st.spinner("Processing your approach..."):
                    updated_state = stream_graph_update(combined)
                    
                    # Clear workspace
                    st.session_state.approach_framework = ""
                    st.session_state.approach_technical = ""
                    st.session_state.approach_code = "# Write your code here...\n\n"
                    st.session_state.approach_implementation = ""
                    st.rerun()

def render_standard_input():
    """Render standard text input"""
    st.markdown("### 💭 Your Response")
    st.caption("Please provide at least 10 words")
    
    user_input = st.text_area(
        "Your response",
        height=150,
        placeholder="Type your answer here (minimum 10 words)...",
        key="std_input"
    )
    
    # Validation error display
    if st.session_state.validation_error:
        st.markdown(f"""
        <div class="validation-error">
            {st.session_state.validation_error}
        </div>
        """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📤 Submit", type="primary", use_container_width=True, key="submit_std_btn"):
            word_count = len(user_input.split())
            
            if word_count < 10:
                st.session_state.validation_error = f"⚠️ Need 10+ words, got {word_count}."
                st.rerun()
            else:
                st.session_state.validation_error = ""
                
                with st.spinner("Processing..."):
                    success = process_graph_stream(user_input)
                    if success:
                        st.rerun()

# ==================== PAGE VIEWS ====================
def welcome_page():
    """Welcome page"""
    apply_custom_css()
    
    st.markdown("""
    <div class="interview-header">
        <h1 style="margin:0;">💼 Technical Case Study System</h1>
        <p style="margin:0.5rem 0 0 0;">Comprehensive consulting-style case interview</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("candidate_info"):
        st.markdown("### Your Information")
        
        name = st.text_input("Full Name *", placeholder="John Doe")
        role = st.text_input("Target Role *", placeholder="Data Scientist")
        skills_input = st.text_input("Key Skills (comma-separated)", placeholder="Python, ML, SQL")
        
        st.markdown("### Interview Structure")
        st.info("""
    - **Phase 1:** Classification (3 MCQs)
    - **Phase 2:** Understanding (3 questions)
    - **Phase 3:** Approach (4 questions, first requires 250 words)
    - **Phase 4:** Final Evaluation
    
    ⚠️ **Note:** Copy-paste functionality is disabled during the CASE to ensure authenticity.
    """)
        
        submitted = st.form_submit_button("🚀 Start Case study", use_container_width=True, type="primary")
        
        if submitted:
            if not name or not role:
                st.error("Please provide your name and role.")
            else:
                st.session_state.candidate_name = name
                st.session_state.role = role
                st.session_state.skills = [s.strip() for s in skills_input.split(',')] if skills_input else []
                
                with st.spinner("Initializing..."):
                    # Build graph
                    st.session_state.graph = build_interview_graph()
                    
                    # Initialize state
                    st.session_state.interview_state = {
                        'messages': [],
                        'candidate_name': name,
                        'role': role,
                        'skills': st.session_state.skills,
                        'current_phase': 'classification',
                        'current_activity': 'start',
                        'mcq_current_question': 0,
                        'mcq_questions': [],
                        'classification_answers': [],
                        'mcq_completed': False,
                        'case_study': None,
                        'understanding_question_count': 0,
                        'understanding_complete': False,
                        'approach_question_count': 0,
                        'approach_complete': False,
                        'interview_complete': False,
                        'validation_failed': False
                    }
                    
                    # Trigger first MCQ generation via graph stream
                    process_graph_stream()
                    
                    st.session_state.initialized = True
                    st.session_state.current_page = "interview"
                
                st.success("✅ Initialized! Starting interview...")
                time.sleep(1)
                st.rerun()


def interview_page():
    """Unified interview page with consistent UI"""
    apply_custom_css()
    render_header()
    inject_clipboard_blocker()
    state = st.session_state.interview_state
    current_phase = state.get('current_phase', 'classification')
    
    # Check if interview complete
    if state.get('interview_complete'):
        st.session_state.current_page = "results"
        st.rerun()
        return
    
    # Handle MCQ phase separately
    if current_phase == 'classification' or not state.get('mcq_completed'):
        mcq_phase(state, None)
        return
    
    # Show phase status for all other phases
    render_phase_status()
    st.markdown("---")
    
    # Handle case generation
    if current_phase == 'case_gen':
        if not state.get('case_study'):
            if not st.session_state.get('ai_processing', False):
                st.session_state.ai_processing = True
                with st.spinner("🎯 Generating your personalized case study..."):
                    try:
                        process_graph_stream()
                        st.session_state.ai_processing = False
                        st.rerun()
                    except Exception as e:
                        st.session_state.ai_processing = False
                        st.error(f"Error generating case: {str(e)}")
                        if st.session_state.get('debug_mode', False):
                            import traceback
                            st.code(traceback.format_exc())
                return
        else:
            st.session_state.interview_state['current_phase'] = 'understanding'
            st.rerun()
            return
    
    # Display chat messages for conversation phases
    if current_phase in ['understanding', 'approach', 'final']:
        render_chat_messages()
        st.markdown("---")
    
    # Handle conversation phases
    if current_phase in ['understanding', 'approach']:
        handle_conversation_phase(state, current_phase)
    
    elif current_phase == 'final':
        if not state.get('final_evaluation'):
            if not st.session_state.get('ai_processing', False):
                st.session_state.ai_processing = True
                with st.spinner("📊 Generating comprehensive evaluation..."):
                    try:
                        process_graph_stream()
                        st.session_state.ai_processing = False
                        st.rerun()
                    except Exception as e:
                        st.session_state.ai_processing = False
                        st.error(f"Error generating evaluation: {str(e)}")
                        if st.session_state.get('debug_mode', False):
                            import traceback
                            st.code(traceback.format_exc())
                return
        else:
            st.session_state.current_page = "results"
            st.rerun()

def handle_conversation_phase(state, current_phase):
    """Handle understanding and approach phases"""
    messages = state.get('messages', [])
    phase_complete = state.get(f'{current_phase}_complete', False)
    
    last_message_is_human = len(messages) > 0 and isinstance(messages[-1], HumanMessage)
    last_message_is_ai = len(messages) > 0 and isinstance(messages[-1], AIMessage)
    needs_ai_response = len(messages) == 0 or last_message_is_human
    
    # Handle phase completion
    if phase_complete:
        if current_phase == 'understanding':
            if not st.session_state.get('ai_processing', False):
                st.session_state.ai_processing = True
                with st.spinner("📊 Evaluating understanding phase..."):
                    try:
                        process_graph_stream()
                        st.session_state.ai_processing = False
                        st.session_state.interview_state['current_phase'] = 'approach'
                        st.rerun()
                    except Exception as e:
                        st.session_state.ai_processing = False
                        st.error(f"Error: {str(e)}")
                        if st.session_state.get('debug_mode', False):
                            import traceback
                            st.code(traceback.format_exc())
                return
        
        elif current_phase == 'approach':
            if not st.session_state.get('ai_processing', False):
                st.session_state.ai_processing = True
                with st.spinner("📊 Evaluating approach phase..."):
                    try:
                        process_graph_stream()
                        st.session_state.ai_processing = False
                        st.session_state.interview_state['current_phase'] = 'final'
                        st.rerun()
                    except Exception as e:
                        st.session_state.ai_processing = False
                        st.error(f"Error: {str(e)}")
                        if st.session_state.get('debug_mode', False):
                            import traceback
                            st.code(traceback.format_exc())
                return
    
    # Process AI response if needed
    if needs_ai_response and not phase_complete:
        if not st.session_state.get('ai_processing', False):
            st.session_state.ai_processing = True
            with st.spinner("Vyaasa is thinking..."):
                try:
                    process_graph_stream()
                    st.session_state.ai_processing = False
                    st.rerun()
                except Exception as e:
                    st.session_state.ai_processing = False
                    st.error(f"Error: {str(e)}")
                    if st.session_state.get('debug_mode', False):
                        import traceback
                        st.code(traceback.format_exc())
            return
    
    # Reset AI processing flag
    st.session_state.ai_processing = False
    
    # Show input if waiting for user
    show_input = (not phase_complete) and (last_message_is_ai or len(messages) == 0)
    
    if show_input:
        current_activity = state.get('current_activity', '')
        approach_count = state.get('approach_question_count', 0)
        
        # ✅ FIX: Check for approach phase and show workspace
        if current_phase == 'approach':
            render_approach_workspace()
        else:
            render_standard_input()


def render_standard_input():
    """Render standard text input with validation"""
    st.markdown("### 💭 Your Response")
    
    # Initialize validation error in session state if not exists
    if 'validation_error' not in st.session_state:
        st.session_state.validation_error = ""
    
    with st.form("response_form", clear_on_submit=True):
        user_input = st.text_area(
            "Type your answer here",
            height=150,
            placeholder="Share your thoughts, ask questions, or provide your analysis...",
            label_visibility="collapsed",
            key="user_response_input"
        )
        
        # Show validation error if exists
        if st.session_state.validation_error:
            st.error(st.session_state.validation_error)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.form_submit_button(
                "📤 Submit Response", 
                use_container_width=True, 
                type="primary"
            )
        
        if submitted:
            if user_input.strip():
                # Validate word count
                word_count = len(user_input.strip().split())
                
                if word_count < 10:
                    st.session_state.validation_error = f"⚠️ Please provide at least 10 words. You entered {word_count} word(s)."
                    st.rerun()
                else:
                    # Clear validation error
                    st.session_state.validation_error = ""
                    
                    # Add message and process
                    new_messages = st.session_state.interview_state.get('messages', [])
                    st.session_state.interview_state['messages'] = new_messages
                    
                    # Process response
                    if not st.session_state.get('ai_processing', False):
                        st.session_state.ai_processing = True
                        with st.spinner("Processing your response..."):
                            try:
                                process_graph_stream(user_input.strip())
                                st.session_state.ai_processing = False
                                st.rerun()
                            except Exception as e:
                                st.session_state.ai_processing = False
                                st.error(f"Error: {str(e)}")
                                if st.session_state.get('debug_mode', False):
                                    import traceback
                                    st.code(traceback.format_exc())
            else:
                st.session_state.validation_error = "⚠️ Please enter a response before submitting."
                st.rerun()


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
            transcript.append(f'[{timestamp}] VYAASA:')
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
    import io
    import zipfile
    import json
    
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





def render_sidebar():
    """Render sidebar with navigation and progress tracking"""
    with st.sidebar:
        st.markdown("## 🎯 Interview Control Panel")
        
        if st.session_state.get('initialized', False):
            st.markdown(f"**Candidate:** {st.session_state.candidate_name}")
            st.markdown(f"**Role:** {st.session_state.role}")
            st.markdown("---")
            
            st.markdown("### Interview Progress")
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
            

            
            st.markdown("---")
            
            if st.button("🔄 Restart Interview", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
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
    
    # Add validation check
    if not isinstance(final_eval, dict):
        st.error("Error: Evaluation data is not properly formatted. Please restart the interview.")
        if st.button("🔄 Start New Interview", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        return
    
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
                dim_name = dim.get('dimension', 'N/A')
                dim_score = dim.get('score', 0)
                dim_weight = dim.get('weight', 0)
                
                with st.expander(f"{dim_name} - {dim_score}/10 (Weight: {dim_weight}%)"):
                    st.write(f"**Justification:** {dim.get('justification', 'N/A')}")
                    excerpt = dim.get('candidate_response_excerpt', '')
                    if excerpt:
                        # Truncate long excerpts
                        display_excerpt = excerpt[:200] + "..." if len(excerpt) > 200 else excerpt
                        st.info(f"**Your Response:** \"{display_excerpt}\"")
        
        st.markdown("### 💪 Key Strengths")
        strengths = final_eval.get('key_strengths', [])
        if strengths:
            for strength in strengths:
                st.success(f"✓ {strength}")
        else:
            st.info("No specific strengths recorded.")
        
        st.markdown("### 🎯 Development Areas")
        dev_areas = final_eval.get('development_areas', [])
        if dev_areas:
            for area in dev_areas:
                st.info(f"→ {area}")
        else:
            st.info("No specific development areas recorded.")
        
        st.markdown("### 🚀 Recommended Next Steps")
        next_steps = final_eval.get('recommended_next_steps', [])
        if next_steps:
            for rec in next_steps:
                st.warning(f"💡 {rec}")
        else:
            st.info("No specific recommendations recorded.")
    
    st.markdown("---")
    
    # Download and restart buttons
    col1, col2 = st.columns(2)
    
    with col1:
        try:
            # Generate ZIP file
            zip_data = create_interview_report_zip()
            
            # Generate filename with timestamp
            candidate_name = st.session_state.get('candidate_name', 'Candidate')
            filename = f"Interview_Report_{candidate_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            
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
            if st.session_state.get('debug_mode', False):
                import traceback
                st.code(traceback.format_exc())
    
    with col2:
        if st.button("🔄 Start New Interview", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


def main():
    """Main application entry point"""
    initialize_session_state()
    render_sidebar()
    
    if not st.session_state.get('initialized', False):
        welcome_page()
    else:
        # Use unified interview_page instead of separate pages
        current_page = st.session_state.get('current_page', 'interview')
        
        if current_page == "results":
            results_page()
        else:
            interview_page()


def mcq_phase(state, messages):
    """Handle MCQ classification phase"""
    
    mcq_completed = state.get('mcq_completed', False)
    
    if mcq_completed:
        st.session_state.interview_state['current_phase'] = 'case_gen'
        st.rerun()
        return
    
    # Phase indicator header
    st.markdown("""
    <div class="phase-indicator">
        <h2>📋 Phase 1: Classification Assessment</h2>
        <p>Answer 3 multiple-choice questions to determine your case study domain.</p>
    </div>
    """, unsafe_allow_html=True)
    
    mcq_questions = state.get('mcq_questions', [])
    answers = state.get('classification_answers', [])
    
    # Generate new question if needed
    if len(mcq_questions) < 3:
        if len(mcq_questions) == len(answers):
            with st.spinner(f"Generating question {len(mcq_questions) + 1}/3..."):
                try:
                    process_graph_stream()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error generating question: {str(e)}")
                    if st.session_state.get('debug_mode', False):
                        import traceback
                        st.code(traceback.format_exc())
                    return
    
    mcq_questions = st.session_state.interview_state.get('mcq_questions', [])
    
    if not mcq_questions:
        st.warning("Generating your first question...")
        return
    
    # Progress indicator
    st.markdown(f"### Progress: {len(answers)}/3 questions answered")
    st.progress(len(answers) / 3)
    st.markdown("---")
    
    # Display all questions with their status
    for idx, q in enumerate(mcq_questions):
        st.markdown(f"### Question {idx + 1}")
        question_text = q.get('question', 'Question text missing')
        st.markdown(f"**{question_text}**")
        
        options = q.get('options', [])
        
        if idx < len(answers):
            # Show answered questions
            st.success(f"✅ Your answer: {answers[idx]}")
        else:
            if idx == len(answers):
                # Current question - show answer buttons
                for opt_idx, option in enumerate(options):
                    if isinstance(option, dict):
                        option_text = option.get('text', str(option))
                        option_letter = option.get('letter', chr(65 + opt_idx))
                    else:
                        option_text = str(option)
                        option_letter = chr(65 + opt_idx)
                    
                    option_key = f"mcq_q{idx}_opt{opt_idx}_v11"
                    
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
                            
                            with st.spinner("Processing your answer..."):
                                try:
                                    process_graph_stream(option_text)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
                                    if st.session_state.get('debug_mode', False):
                                        import traceback
                                        st.code(traceback.format_exc())
                
                # Show custom industry input if "Other" was selected in Q2
                if idx == 1 and st.session_state.get('awaiting_custom_industry', False):
                    st.markdown("---")
                    st.info("📝 Please specify your preferred industry:")
                    
                    # Create unique keys based on current answer count
                    answers_count = len(st.session_state.interview_state.get('classification_answers', []))
                    custom_industry_key = f"custom_industry_input_{answers_count}_v5"
                    confirm_btn_key = f"confirm_industry_btn_{answers_count}_v5"
                    
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
                                
                                with st.spinner("Processing your answer..."):
                                    try:
                                        process_graph_stream(custom_industry.strip())
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
                                        if st.session_state.get('debug_mode', False):
                                            import traceback
                                            st.code(traceback.format_exc())
                            else:
                                st.warning("⚠️ Please enter an industry name.")
            else:
                # Future questions - locked until previous answered
                st.info("👆 Please answer the previous question first")
        
        st.markdown("---")
    
    # Complete classification when all 3 questions answered
    if len(answers) >= 3:
        st.success("✅ All 3 questions answered! Classification complete!")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("➡️ Continue to Understanding Phase", type="primary", use_container_width=True, key="continue_btn_v3"):
                with st.spinner("Analyzing your responses..."):
                    try:
                        process_graph_stream()
                        st.session_state.interview_state['mcq_completed'] = True
                        st.session_state.interview_state['current_phase'] = 'case_gen'
                        
                        # Clean up MCQ data
                        st.session_state.interview_state['mcq_questions'] = []
                        st.session_state.interview_state['classification_answers'] = []
                        
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error processing answers: {str(e)}")
                        if st.session_state.get('debug_mode', False):
                            import traceback
                            st.code(traceback.format_exc())
if __name__ == "__main__":
    main()
