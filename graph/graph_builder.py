"""Graph construction - Fixed routing to prevent infinite loops."""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from graph.state import InterviewState
from graph.nodes.interview_nodes import CaseStudyInterviewNodes

nodes_handler = CaseStudyInterviewNodes()

def route_from_start(state: InterviewState) -> str:
    """Route from START based on current state."""
    current_phase = state.get('current_phase', 'classification')
    mcq_completed = state.get('mcq_completed', False)
    case_exists = state.get('case_study') is not None
    
    print(f"[ROUTER] Phase: {current_phase}, MCQ done: {mcq_completed}, Case exists: {case_exists}")
    
    # If MCQ not completed, generate questions
    if not mcq_completed:
        answers = state.get('classification_answers', [])
        if len(answers) < 3:
            return "generate_mcq"
        else:
            return "process_mcq_answers"
    
    # If MCQ done but no case, generate case
    if mcq_completed and not case_exists:
        return "generate_case"
    
    # If case exists, handle interview phases
    if case_exists:
        if current_phase == 'understanding':
            if not state.get('understanding_complete'):
                return "understanding"
            else:
                return "understanding_evaluation"
        
        elif current_phase == 'approach':
            if not state.get('approach_complete'):
                return "approach"
            else:
                return "approach_evaluation"
        
        elif current_phase == 'final':
            return "final_evaluation"
    
    # Default: end
    return "__end__"

def build_interview_graph():
    """Build interview graph with proper routing."""
    workflow = StateGraph(InterviewState)
    
    # Add all nodes
    workflow.add_node("generate_mcq", nodes_handler.generate_mcq_node)
    workflow.add_node("process_mcq_answers", nodes_handler.process_mcq_answers_node)
    workflow.add_node("generate_case", nodes_handler.generate_case_node)
    workflow.add_node("understanding", nodes_handler.understanding_node)
    workflow.add_node("understanding_evaluation", nodes_handler.understanding_evaluation_node)
    workflow.add_node("approach", nodes_handler.approach_node)
    workflow.add_node("approach_evaluation", nodes_handler.approach_evaluation_node)
    workflow.add_node("validate_response", nodes_handler.validate_response_length)
    workflow.add_node("validation_failed", nodes_handler.handle_validation_failed)
    workflow.add_node("final_evaluation", nodes_handler.final_evaluation_node)
    
    # Start with conditional routing
    workflow.add_conditional_edges(
        START,
        route_from_start,
        {
            "generate_mcq": "generate_mcq",
            "process_mcq_answers": "process_mcq_answers",
            "generate_case": "generate_case",
            "understanding": "understanding",
            "understanding_evaluation": "understanding_evaluation",
            "approach": "approach",
            "approach_evaluation": "approach_evaluation",
            "final_evaluation": "final_evaluation",
            "__end__": END
        }
    )
    
    # All nodes end immediately - NO LOOPS
    workflow.add_edge("generate_mcq", END)
    workflow.add_edge("process_mcq_answers", END)
    workflow.add_edge("generate_case", END)
    workflow.add_edge("understanding", END)
    workflow.add_edge("understanding_evaluation", END)
    workflow.add_edge("approach", END)
    workflow.add_edge("validate_response", END)
    workflow.add_edge("validation_failed", END)
    workflow.add_edge("approach_evaluation", END)
    workflow.add_edge("final_evaluation", END)
    
    return workflow.compile(
        checkpointer=MemorySaver(),
        debug=False
    )
