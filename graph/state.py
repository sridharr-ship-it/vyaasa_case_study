# graph/state.py - COMPLETE WITH SEPARATE PHASE COUNTERS
from typing import TypedDict, List, Dict, Any, Optional
from typing_extensions import Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class InterviewState(TypedDict):
    """State for case study interview system with separate phase counters."""
    
    # Candidate Information
    candidate_name: str
    role: str
    skills: List[str]
    is_technical_role: bool
    
    # Messages
    messages: Annotated[List[BaseMessage], add_messages]
    
    # MCQ Classification
    mcq_questions: List[Dict[str, Any]]
    mcq_answers: List[str]
    mcq_current_question: int
    mcq_completed: bool
    
    # Phase Management
    current_phase: str
    current_activity: str
    
    # SEPARATE COUNTERS FOR EACH PHASE (KEY FIX)
    understanding_question_count: int
    approach_question_count: int
    followup_question_count: int
    
    # Deprecated - kept for backward compatibility
    phase_question_count: int
    
    # Phase max questions
    phase_max_questions: Dict[str, int]
    
    # Phase Completion Flags
    understanding_complete: bool
    approach_complete: bool
    followup_complete: bool
    interview_complete: bool
    
    # Timer
    interview_start_time: Optional[float]
    interview_duration: int
    time_elapsed: float
    time_remaining: float
    timer_expired: bool
    
    # Case Study
    case_study: Dict[str, Any]
    domain: Optional[str]
    industry: Optional[str]
    case_type: Optional[str]
    tech_type: Optional[str]
    
    # Evaluations
    understanding_evaluation: Dict[str, Any]
    approach_evaluation: Dict[str, Any]
    followup_evaluation: Dict[str, Any]
    final_evaluation: Dict[str, Any]
    
    # Performance Signals
    structure_signals: List[str]
    problem_solving_signals: List[str]
    communication_signals: List[str]
    technical_signals: List[str]
    business_judgment_signals: List[str]
