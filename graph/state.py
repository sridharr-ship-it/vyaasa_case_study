"""State definition for case study interview system."""

from typing import TypedDict, List, Dict, Any, Optional
from typing_extensions import Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class InterviewState(TypedDict):
    """State for case study interview system."""
    
    # ========== CANDIDATE INFORMATION ==========
    candidate_name: str
    role: str
    skills: List[str]
    
    # ========== MESSAGES ==========
    messages: Annotated[List[BaseMessage], add_messages]
    
    # ========== MCQ CLASSIFICATION ==========
    mcq_questions: List[Dict[str, Any]]
    classification_answers: List[str]  # Stores A, B, C, D answers
    mcq_current_question: int
    mcq_completed: bool
    
    # ========== CLASSIFICATION RESULTS ==========
    domain: Optional[str]
    industry: Optional[str]
    case_type: Optional[str]
    tech_type: Optional[str]  # "Technical" or "Business"
    
    # ========== CASE STUDY ==========
    case_study: Optional[Dict[str, Any]]
    
    # ========== PHASE MANAGEMENT ==========
    current_phase: str  # 'classification', 'case_gen', 'understanding', 'approach', 'final'
    current_activity: str  # Detailed activity state
    
    # ========== UNDERSTANDING PHASE ==========
    understanding_question_count: int
    understanding_complete: bool
    understanding_evaluation: Optional[Dict[str, Any]]
    
    # ========== APPROACH PHASE ==========
    approach_question_count: int
    approach_complete: bool
    approach_evaluation: Optional[Dict[str, Any]]
    
    # ========== VALIDATION ==========
    validation_failed: bool
    validation_error: Optional[str]
    
    # ========== FINAL EVALUATION ==========
    final_evaluation: Optional[Dict[str, Any]]
    interview_complete: bool
    
    # ========== OPTIONAL: TIMING ==========
    interview_start_time: Optional[float]
    completion_time: Optional[float]


def create_initial_state(
    candidate_name: str,
    role: str,
    skills: List[str]
) -> InterviewState:
    """
    Create initial interview state with candidate information.
    
    Args:
        candidate_name: Candidate's full name
        role: Target role (e.g., "Data Scientist")
        skills: List of key skills
    
    Returns:
        Initialized InterviewState
    """
    return {
        # Candidate info
        "candidate_name": candidate_name,
        "role": role,
        "skills": skills,
        
        # Messages
        "messages": [],
        
        # MCQ Classification
        "mcq_questions": [],
        "classification_answers": [],
        "mcq_current_question": 0,
        "mcq_completed": False,
        
        # Classification results
        "domain": None,
        "industry": None,
        "case_type": None,
        "tech_type": None,
        
        # Case study
        "case_study": None,
        
        # Phase management
        "current_phase": "classification",
        "current_activity": "start",
        
        # Understanding phase
        "understanding_question_count": 0,
        "understanding_complete": False,
        "understanding_evaluation": None,
        
        # Approach phase
        "approach_question_count": 0,
        "approach_complete": False,
        "approach_evaluation": None,
        
        # Validation
        "validation_failed": False,
        "validation_error": None,
        
        # Final evaluation
        "final_evaluation": None,
    # Formatted text report for download

        "interview_complete": False,
        
        # Timing
        "interview_start_time": None,
        "completion_time": None,
    }


def get_state_summary(state: InterviewState) -> str:
    """
    Generate a human-readable summary of the current state.
    
    Args:
        state: Current interview state
    
    Returns:
        Formatted state summary string
    """
    return f"""
╔═══════════════════════════════════════════════════════════════╗
│                     INTERVIEW STATE SUMMARY                    │
╚═══════════════════════════════════════════════════════════════╝

Candidate: {state.get('candidate_name', 'N/A')}
Role: {state.get('role', 'N/A')}
Skills: {', '.join(state.get('skills', []))}

─────────────────────────────────────────────────────────────────

CLASSIFICATION:
  MCQ Questions: {state.get('mcq_current_question', 0)}/3
  Answers: {state.get('classification_answers', [])}
  Completed: {'✓' if state.get('mcq_completed') else '✗'}
  Domain: {state.get('domain', 'Not set')}
  Industry: {state.get('industry', 'Not set')}
  Case Type: {state.get('case_type', 'Not set')}
  Tech Type: {state.get('tech_type', 'Not set')}

─────────────────────────────────────────────────────────────────

CURRENT PHASE: {state.get('current_phase', 'N/A').upper()}
Activity: {state.get('current_activity', 'N/A')}

─────────────────────────────────────────────────────────────────

UNDERSTANDING PHASE:
  Questions Asked: {state.get('understanding_question_count', 0)}/3
  Complete: {'✓' if state.get('understanding_complete') else '✗'}

APPROACH PHASE:
  Questions Asked: {state.get('approach_question_count', 0)}/4
  Complete: {'✓' if state.get('approach_complete') else '✗'}

─────────────────────────────────────────────────────────────────

VALIDATION:
  Failed: {'Yes' if state.get('validation_failed') else 'No'}
  Error: {state.get('validation_error', 'None')}

─────────────────────────────────────────────────────────────────

INTERVIEW:
  Complete: {'✓' if state.get('interview_complete') else '✗'}
  Messages: {len(state.get('messages', []))}

╚═══════════════════════════════════════════════════════════════╝
"""


# Export the State type alias for convenience
State = InterviewState
