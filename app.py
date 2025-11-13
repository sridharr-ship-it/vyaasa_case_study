# app.py - Production-ready case interview system

import streamlit as st
import time
from datetime import datetime
from typing import Dict, List
from langchain_core.messages import HumanMessage, AIMessage
from graph.graph_builder import build_interview_graph
import io
import json
import streamlit.components.v1 as components

# Try importing streamlit-ace for code editor
try:
    from streamlit_ace import st_ace
    EDITOR_AVAILABLE = True
except ImportError:
    EDITOR_AVAILABLE = False
    st.warning("⚠️ Code editor not available. Install with: `pip install streamlit-ace`")

# ========== PAGE CONFIGURATION ==========

st.set_page_config(
    page_title="Case Study Interview",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== CLIPBOARD BLOCKER ==========

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

# ========== CUSTOM STYLING ==========

def apply_custom_css():
    """Apply professional styling with VS Code theme"""
    st.markdown("""
        <style>
        /* Main container */
        .main {
            background-color: #f8f9fa;
        }
        
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }
        
        /* Interview header */
        .interview-header {
            background: linear-gradient(135deg, #0076a8 0%, #00a3e0 100%);
            padding: 2rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            color: white;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        /* Phase indicators */
        .phase-indicator {
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            margin-bottom: 1.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        /* Chat messages */
        .chat-message {
            padding: 1.5rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .chat-message.ai {
            background-color: #e3f2fd;
            border-left: 4px solid #0076a8;
        }
        
        .chat-message.human {
            background-color: #f1f8e9;
            border-left: 4px solid #66bb6a;
        }
        
        /* Validation errors */
        .validation-error {
            background-color: #ffebee;
            color: #c62828;
            padding: 1rem;
            border-radius: 5px;
            border-left: 4px solid #c62828;
            margin: 1rem 0;
        }
        
        /* Tabs - VS Code Theme */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: #1e1e1e;
            padding: 0.5rem;
            border-radius: 5px;
        }
        
        .stTabs [data-baseweb="tab"] {
            background-color: #2d2d2d;
            color: #cccccc;
            border-radius: 4px;
            padding: 0.5rem 1rem;
            font-weight: 500;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #007acc;
            color: white;
        }
        
        /* Text areas - VS Code Theme */
        textarea {
            background-color: #1e1e1e !important;
            color: #d4d4d4 !important;
            border: 1px solid #3e3e3e !important;
            font-family: 'Consolas', 'Courier New', monospace !important;
        }
        
        /* Buttons */
        .stButton > button {
            width: 100%;
            border-radius: 5px;
            font-weight: 600;
            padding: 0.75rem 1.5rem;
            transition: all 0.3s;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        
        /* Progress bars */
        .stProgress > div > div > div {
            background-color: #0076a8;
        }
        
        /* Info boxes */
        .stInfo {
            background-color: #e3f2fd;
            border-left: 4px solid #0076a8;
        }
        
        /* Success boxes */
        .stSuccess {
            background-color: #f1f8e9;
            border-left: 4px solid #66bb6a;
        }
        
        /* Warning boxes */
        .stWarning {
            background-color: #fff3e0;
            border-left: 4px solid #fb8c00;
        }
        
        /* Sidebar */
        .css-1d391kg {
            background-color: #f8f9fa;
        }
        
        /* Results page */
        .results-container {
            background: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .dimension-card {
            background: #f8f9fa;
            padding: 1.5rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            border-left: 4px solid #0076a8;
        }
        </style>
    """, unsafe_allow_html=True)

# ========== SESSION STATE INITIALIZATION ==========

def initialize_session_state():
    """Initialize all session state variables"""
    defaults = {
        'current_page': 'welcome',
        'interview_started': False,
        'interview_state': None,
        'graph': None,
        'messages_history': [],
        'mcq_answers': [],
        'classification_answers': [],
        'approach_framework': '',
        'approach_technical': '',
        'approach_code': '# Write your code here...\n\n',
        'approach_implementation': '',
        'code_language': 'python',
        'validation_error': '',
        'custom_industry': '',
        'show_custom_industry': False,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# ========== CONTENT AGGREGATION ==========

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

# ========== GRAPH PROCESSING ==========

def process_graph_stream(user_input: str) -> bool:
    """Process user input through graph stream"""
    try:
        if not st.session_state.graph:
            st.session_state.graph = build_interview_graph()
        
        if not st.session_state.interview_state:
            st.session_state.interview_state = st.session_state.graph.get_state(st.session_state.graph.config)
        
        # Add user message
        current_state = st.session_state.interview_state
        current_messages = current_state.get('messages', [])
        current_messages.append(HumanMessage(content=user_input))
        
        # Update state with user input
        updates = {'messages': current_messages}
        
        # Handle MCQ answers
        current_activity = current_state.get('current_activity', '')
        if current_activity == 'awaiting_mcq_answer':
            answers = current_state.get('classification_answers', [])
            answers.append(user_input.upper())
            updates['classification_answers'] = answers
        
        # Stream through graph
        for event in st.session_state.graph.stream(updates, st.session_state.graph.config):
            for node_name, node_output in event.items():
                if 'messages' in node_output:
                    current_messages.extend(node_output['messages'])
                    st.session_state.messages_history = current_messages
        
        # Update interview state
        st.session_state.interview_state = st.session_state.graph.get_state(st.session_state.graph.config)
        
        return True
        
    except Exception as e:
        st.error(f"❌ Error processing input: {str(e)}")
        return False

# ========== UI COMPONENTS ==========

def render_header():
    """Render interview header"""
    st.markdown("""
        <div class="interview-header">
            <h1 style="margin:0; font-size: 2.5rem;">🎯 Case Study Interview</h1>
            <p style="margin:0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9;">
                AI-Powered Assessment Platform
            </p>
        </div>
    """, unsafe_allow_html=True)

def render_phase_indicator():
    """Render current phase indicator"""
    if not st.session_state.interview_state:
        return
    
    state = st.session_state.interview_state
    current_phase = state.get('current_phase', 'classification')
    
    phases = {
        'classification': {'name': 'Classification', 'icon': '📋', 'progress': 25},
        'understanding': {'name': 'Understanding', 'icon': '🧠', 'progress': 50},
        'approach': {'name': 'Approach', 'icon': '🎯', 'progress': 75},
        'final': {'name': 'Evaluation', 'icon': '✅', 'progress': 100}
    }
    
    phase_info = phases.get(current_phase, phases['classification'])
    
    st.markdown(f"""
        <div class="phase-indicator">
            <h3 style="margin:0; color:#0076a8;">
                {phase_info['icon']} Current Phase: {phase_info['name']}
            </h3>
            <p style="margin:0.5rem 0 0 0; color:#666;">
                Progress: {phase_info['progress']}%
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    st.progress(phase_info['progress'] / 100)

def render_chat_history():
    """Render chat message history"""
    messages = st.session_state.messages_history
    
    for i, msg in enumerate(messages):
        if isinstance(msg, AIMessage):
            st.markdown(f"""
                <div class="chat-message ai">
                    <strong>🤖 Interviewer:</strong><br>
                    {msg.content}
                </div>
            """, unsafe_allow_html=True)
        elif isinstance(msg, HumanMessage):
            st.markdown(f"""
                <div class="chat-message human">
                    <strong>👤 You:</strong><br>
                    {msg.content}
                </div>
            """, unsafe_allow_html=True)

def render_approach_workspace():
    """Render approach workspace for structured response"""
    state = st.session_state.interview_state
    tech_type = state.get("tech_type", "")
    is_technical = (tech_type == "Technical")
    
    st.markdown("### 📋 Solution Approach Workspace")
    st.info("Structure your approach using the tabs below. **Minimum 500 words required.**")
    
    if is_technical:
        # For technical cases: Framework, Technical, Code tabs
        tab1, tab2, tab3 = st.tabs(["📋 Framework", "⚙️ Technical", "💻 Code"])
        
        with tab1:
            st.markdown("**Framework & Methodology**")
            st.session_state.approach_framework = st.text_area(
                "Framework",
                value=st.session_state.approach_framework,
                height=300,
                placeholder="• Overall framework and approach\n• Key phases/steps\n• Methodology specific to this case...",
                key="fw_input",
                label_visibility="collapsed"
            )
        
        with tab2:
            st.markdown("**Technical Approach**")
            st.session_state.approach_technical = st.text_area(
                "Technical",
                value=st.session_state.approach_technical,
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
                    key="lang_select"
                )
                st.session_state.code_language = language
            
            # Code editor (with fallback)
            if EDITOR_AVAILABLE:
                code_content = st_ace(
                    value=st.session_state.approach_code,
                    language=language if language != "pseudocode" else "python",
                    theme="monokai",
                    height=400,
                    key="ace_editor"
                )
                if code_content:
                    st.session_state.approach_code = code_content
            else:
                # Fallback to text area if ace editor not available
                st.session_state.approach_code = st.text_area(
                    "Code",
                    value=st.session_state.approach_code,
                    height=400,
                    placeholder=f"# Write your {language} code or pseudocode here\n# Example:\n# def predict_loan_default(data):\n#     # Your implementation\n#     pass",
                    key="code_fallback",
                    label_visibility="collapsed"
                )
                
                # Show installation hint if editor not available
                if not EDITOR_AVAILABLE:
                    st.info("💡 **Tip:** Install `streamlit-ace` for a better code editor: `pip install streamlit-ace`")
    
    else:
        # For non-technical cases: Framework and Implementation tabs
        tab1, tab2 = st.tabs(["📋 Framework", "📝 Implementation"])
        
        with tab1:
            st.markdown("**Framework & Methodology**")
            st.session_state.approach_framework = st.text_area(
                "Framework",
                value=st.session_state.approach_framework,
                height=400,
                placeholder="• Overall framework and approach\n• Key phases/steps\n• Analysis methodology\n• Prioritization logic...",
                key="fw_nontechnical",
                label_visibility="collapsed"
            )
        
        with tab2:
            st.markdown("**Implementation Plan**")
            st.session_state.approach_implementation = st.text_area(
                "Implementation",
                value=st.session_state.approach_implementation,
                height=400,
                placeholder="• Step-by-step execution plan\n• Timeline and milestones\n• Resource requirements\n• Risk mitigation strategies...",
                key="impl_input",
                label_visibility="collapsed"
            )
    
    # Validation error display
    if st.session_state.validation_error:
        st.markdown(
            f'<div class="validation-error">⚠️ {st.session_state.validation_error}</div>',
            unsafe_allow_html=True
        )
    
    # Submit button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("✅ Submit Approach", type="primary", use_container_width=True, key="submit_approach_btn"):
            combined = aggregate_approach_content()
            word_count = len(combined.split())
            
            if word_count < 500:
                st.session_state.validation_error = f"❌ Need 500+ words, got {word_count}."
                st.rerun()
            else:
                st.session_state.validation_error = ""
                with st.spinner("Processing your approach..."):
                    success = process_graph_stream(combined)
                    if success:
                        # Clear workspace
                        st.session_state.approach_framework = ""
                        st.session_state.approach_technical = ""
                        st.session_state.approach_code = "# Write your code here...\n\n"
                        st.session_state.approach_implementation = ""
                        st.rerun()

def render_standard_input():
    """Render standard text input with form submission"""
    state = st.session_state.interview_state
    current_activity = state.get('current_activity', '')
    
    # MCQ answer input
    if current_activity == 'awaiting_mcq_answer':
        st.markdown("### 💬 Your Answer")
        
        with st.form(key="mcq_form", clear_on_submit=True):
            user_input = st.text_input(
                "Enter your answer (A, B, C, or D):",
                max_chars=1,
                key="mcq_input"
            )
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                submitted = st.form_submit_button(
                    "✅ Submit Answer",
                    type="primary",
                    use_container_width=True
                )
            
            if submitted and user_input:
                if user_input.upper() in ['A', 'B', 'C', 'D']:
                    with st.spinner("Processing..."):
                        success = process_graph_stream(user_input.upper())
                        if success:
                            st.rerun()
                else:
                    st.error("❌ Please enter A, B, C, or D")
    
    # Standard response input
    else:
        st.markdown("### 💬 Your Response")
        
        with st.form(key="response_form", clear_on_submit=True):
            user_input = st.text_area(
                "Share your thoughts, ask questions, or provide your analysis...",
                height=150,
                key="user_response"
            )
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                submitted = st.form_submit_button(
                    "📤 Submit Response",
                    type="primary",
                    use_container_width=True
                )
            
            if submitted and user_input and user_input.strip():
                word_count = len(user_input.split())
                
                if word_count < 10:
                    st.error(f"❌ Please provide at least 10 words (current: {word_count})")
                else:
                    with st.spinner("Processing your response..."):
                        success = process_graph_stream(user_input)
                        if success:
                            st.rerun()

# ========== MAIN PAGES ==========

def welcome_page():
    """Render welcome page"""
    render_header()
    
    st.markdown("""
        ## 👋 Welcome to the AI Case Interview Platform
        
        This interactive platform simulates a real case study interview experience with adaptive questioning
        and comprehensive evaluation.
    """)
    
    # Profile input
    with st.form("profile_form"):
        st.markdown("### 📝 Your Profile")
        
        col1, col2 = st.columns(2)
        
        with col1:
            role = st.text_input(
                "Role/Position",
                placeholder="e.g., Data Scientist, Product Manager",
                help="Your current or target role"
            )
        
        with col2:
            skills = st.text_input(
                "Key Skills",
                placeholder="e.g., Python, SQL, ML",
                help="Comma-separated skills"
            )
        
        st.markdown("### 📋 Interview Structure")
        st.info("""
        - **Phase 1:** Classification (3 MCQs)
        - **Phase 2:** Understanding (3 questions)
        - **Phase 3:** Approach (4 questions, first requires 500 words)
        - **Phase 4:** Final Evaluation
        
        ⚠️ **Note:** Copy-paste functionality is disabled during the interview to ensure authenticity.
        """)
        
        submitted = st.form_submit_button(
            "🚀 Start Interview",
            type="primary",
            use_container_width=True
        )
        
        if submitted:
            if not role or not skills:
                st.error("❌ Please fill in all fields")
            else:
                # Initialize graph with profile
                st.session_state.graph = build_interview_graph()
                initial_state = {
                    'role': role,
                    'skills': skills.split(','),
                    'current_phase': 'classification',
                    'current_activity': 'generating_mcq'
                }
                
                # Process through graph to generate first MCQ
                for event in st.session_state.graph.stream(initial_state, st.session_state.graph.config):
                    for node_name, node_output in event.items():
                        if 'messages' in node_output:
                            st.session_state.messages_history = node_output['messages']
                
                st.session_state.interview_state = st.session_state.graph.get_state(st.session_state.graph.config)
                st.session_state.interview_started = True
                st.session_state.current_page = 'interview'
                st.rerun()

def interview_page():
    """Unified interview page with consistent UI"""
    apply_custom_css()
    inject_clipboard_blocker()  # Activate clipboard blocker
    
    render_header()
    render_phase_indicator()
    
    # Check if interview is complete
    state = st.session_state.interview_state
    if state and state.get('interview_complete'):
        st.session_state.current_page = 'results'
        st.rerun()
    
    # Render chat history
    st.markdown("### 💬 Interview Conversation")
    render_chat_history()
    
    st.markdown("---")
    
    # Render appropriate input based on current activity
    current_activity = state.get('current_activity', '') if state else ''
    
    if current_activity in ['awaiting_approach', 'awaiting_approach_structured']:
        render_approach_workspace()
    else:
        render_standard_input()

def results_page():
    """Render results and evaluation page"""
    apply_custom_css()
    render_header()
    
    st.markdown("## 📊 Interview Results")
    
    state = st.session_state.interview_state
    if not state:
        st.error("❌ No interview data available")
        return
    
    final_eval = state.get('final_evaluation', {})
    understanding_eval = state.get('understanding_evaluation', {})
    approach_eval = state.get('approach_evaluation', {})
    
    # Overall Score
    overall_score = final_eval.get('overall_score', 0)
    performance_level = final_eval.get('performance_level', 'N/A')
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Overall Score", f"{overall_score:.1f}/10")
    with col2:
        st.metric("Performance Level", performance_level)
    with col3:
        duration = state.get('completion_time', 0) - state.get('interview_start_time', 0)
        st.metric("Duration", f"{int(duration/60)} min")
    
    # Interview Summary
    st.markdown("### 📝 Summary")
    st.info(final_eval.get('interview_summary', 'No summary available'))
    
    # Dimension Scores
    st.markdown("### 📊 Dimension Breakdown")
    
    for dimension in final_eval.get('dimension_scores', []):
        with st.expander(f"{dimension['dimension']} - {dimension['score']}/10"):
            st.markdown(f"**Weight:** {dimension['weight']}%")
            st.markdown(f"**Justification:** {dimension['justification']}")
            st.markdown(f"**Your Response:**")
            st.code(dimension.get('candidate_response_excerpt', 'N/A'))
    
    # Strengths and Development Areas
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ✅ Key Strengths")
        for strength in final_eval.get('key_strengths', []):
            st.success(f"• {strength}")
    
    with col2:
        st.markdown("### 📈 Development Areas")
        for area in final_eval.get('development_areas', []):
            st.warning(f"• {area}")
    
    # Phase Breakdown
    st.markdown("### 🔍 Phase Performance")
    
    tab1, tab2 = st.tabs(["Understanding Phase", "Approach Phase"])
    
    with tab1:
        st.markdown(f"**Score:** {understanding_eval.get('score', 0)}/10")
        st.markdown(f"**Comment:** {understanding_eval.get('overall_comment', 'N/A')}")
        
        if understanding_eval.get('strengths'):
            st.markdown("**Strengths:**")
            for s in understanding_eval['strengths']:
                st.markdown(f"• {s}")
        
        if understanding_eval.get('weaknesses'):
            st.markdown("**Areas for Improvement:**")
            for w in understanding_eval['weaknesses']:
                st.markdown(f"• {w}")
    
    with tab2:
        st.markdown(f"**Score:** {approach_eval.get('score', 0)}/10")
        st.markdown(f"**Comment:** {approach_eval.get('overall_comment', 'N/A')}")
        
        if approach_eval.get('strengths'):
            st.markdown("**Strengths:**")
            for s in approach_eval['strengths']:
                st.markdown(f"• {s}")
        
        if approach_eval.get('weaknesses'):
            st.markdown("**Areas for Improvement:**")
            for w in approach_eval['weaknesses']:
                st.markdown(f"• {w}")
    
    # Next Steps
    st.markdown("### 🎯 Recommended Next Steps")
    for step in final_eval.get('recommended_next_steps', []):
        st.markdown(f"• {step}")
    
    # Export Options
    st.markdown("---")
    st.markdown("### 📥 Export Results")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Download Chat Transcript", use_container_width=True):
            transcript = generate_transcript()
            st.download_button(
                "💾 Save Transcript",
                transcript,
                file_name=f"interview_transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
    
    with col2:
        if st.button("📊 Download Evaluation Report", use_container_width=True):
            report = generate_evaluation_report(final_eval, understanding_eval, approach_eval)
            st.download_button(
                "💾 Save Report",
                report,
                file_name=f"evaluation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with col3:
        if st.button("📦 Download All (ZIP)", use_container_width=True):
            zip_data = generate_zip_package(final_eval, understanding_eval, approach_eval)
            st.download_button(
                "💾 Save ZIP",
                zip_data,
                file_name=f"interview_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                mime="application/zip"
            )
    
    # Restart option
    st.markdown("---")
    if st.button("🔄 Start New Interview", type="primary", use_container_width=True):
        # Clear all session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ========== EXPORT FUNCTIONS ==========

def generate_transcript() -> str:
    """Generate interview transcript"""
    messages = st.session_state.messages_history
    transcript = "CASE STUDY INTERVIEW TRANSCRIPT\n"
    transcript += "=" * 50 + "\n\n"
    
    for msg in messages:
        if isinstance(msg, AIMessage):
            transcript += "INTERVIEWER:\n"
            transcript += msg.content + "\n\n"
        elif isinstance(msg, HumanMessage):
            transcript += "CANDIDATE:\n"
            transcript += msg.content + "\n\n"
    
    return transcript

def generate_evaluation_report(final_eval, understanding_eval, approach_eval) -> str:
    """Generate JSON evaluation report"""
    report = {
        "final_evaluation": final_eval,
        "understanding_phase": understanding_eval,
        "approach_phase": approach_eval,
        "timestamp": datetime.now().isoformat()
    }
    return json.dumps(report, indent=2)

def generate_zip_package(final_eval, understanding_eval, approach_eval) -> bytes:
    """Generate ZIP package with all files"""
    import zipfile
    
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add transcript
        transcript = generate_transcript()
        zip_file.writestr("transcript.txt", transcript)
        
        # Add evaluation report
        report = generate_evaluation_report(final_eval, understanding_eval, approach_eval)
        zip_file.writestr("evaluation.json", report)
        
        # Add metadata
        metadata = {
            "candidate_profile": {
                "role": st.session_state.interview_state.get('role', 'N/A'),
                "skills": st.session_state.interview_state.get('skills', [])
            },
            "case_study": st.session_state.interview_state.get('case_study', {}),
            "timestamp": datetime.now().isoformat()
        }
        zip_file.writestr("metadata.json", json.dumps(metadata, indent=2))
    
    return zip_buffer.getvalue()

# ========== MAIN APP ==========

def main():
    """Main application entry point"""
    initialize_session_state()
    
    # Route to appropriate page
    if st.session_state.current_page == 'welcome':
        welcome_page()
    elif st.session_state.current_page == 'interview':
        interview_page()
    elif st.session_state.current_page == 'results':
        results_page()

if __name__ == "__main__":
    main()
