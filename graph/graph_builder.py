# graph/graph_builder.py - FIXED VERSION WITH PROPER CASE-TO-UNDERSTANDING ROUTING

from langgraph.graph import StateGraph, END
from .state import InterviewState
from .nodes.interview_nodes import CaseStudyInterviewNodes

def build_interview_graph():
    """Build interview graph with proper phase transitions."""
    
    nodes = CaseStudyInterviewNodes()
    graph = StateGraph(InterviewState)
    
    # Add all nodes
    graph.add_node("classification_node", nodes.generate_mcq_node)
    graph.add_node("mcq_processing_node", nodes.process_mcq_answers_node)
    graph.add_node("case_generation_node", nodes.generate_case_node)
    graph.add_node("understanding_node", nodes.understanding_node)
    graph.add_node("understanding_evaluation_node", nodes.understanding_evaluation_node)
    graph.add_node("approach_node", nodes.approach_node)
    graph.add_node("approach_evaluation_node", nodes.approach_evaluation_node)
    graph.add_node("followup_node", nodes.followup_node)
    graph.add_node("followup_evaluation_node", nodes.followup_evaluation_node)
    graph.add_node("final_evaluation_node", nodes.final_evaluation_node)
    
    # Set entry point
    graph.set_entry_point("classification_node")
    
    # ========== CLASSIFICATION FLOW ==========
    
    def after_classification(state):
        """Route after MCQ classification."""
        if state.get('mcq_answers') and len(state['mcq_answers']) >= 3:
            return "process"
        return "wait"
    
    graph.add_conditional_edges(
        "classification_node",
        after_classification,
        {"process": "mcq_processing_node", "wait": END}
    )
    
    graph.add_edge("mcq_processing_node", "case_generation_node")
    
    # *** CRITICAL FIX: Route from case generation based on state ***
    def after_case_generation(state):
        """Route after case generation.
        
        If case already existed (skipped regeneration), continue to understanding.
        If case was just generated, END to wait for user response.
        """
        # Check if we just generated a new case or skipped
        # When case is generated, activity is set to "awaiting_understanding"
        if state.get('current_activity') == 'awaiting_understanding':
            # If count is 0, this is first time showing case - wait for response
            if state.get('understanding_question_count', 0) == 0:
                return "wait"
            # If count > 0, we have a response - continue to understanding node
            else:
                return "continue"
        return "wait"
    
    graph.add_conditional_edges(
        "case_generation_node",
        after_case_generation,
        {
            "continue": "understanding_node",
            "wait": END
        }
    )
    
    # ========== UNDERSTANDING PHASE ==========
    
    def should_continue_understanding(state):
        """Route understanding phase."""
        activity = state.get('current_activity', '')
        
        # If phase complete, evaluate
        if state.get('understanding_complete'):
            return "evaluate"
        
        # If waiting for response, end turn
        if activity == 'awaiting_understanding':
            return "wait"
        
        # Continue in phase
        return "continue"
    
    graph.add_conditional_edges(
        "understanding_node",
        should_continue_understanding,
        {
            "evaluate": "understanding_evaluation_node",
            "continue": "understanding_node",
            "wait": END
        }
    )
    
    # After evaluation, move to approach
    graph.add_edge("understanding_evaluation_node", "approach_node")
    
    # ========== APPROACH PHASE ==========
    
    def should_continue_approach(state):
        """Route approach phase."""
        activity = state.get('current_activity', '')
        
        # If phase complete, evaluate
        if state.get('approach_complete'):
            return "evaluate"
        
        # If waiting for response, end turn
        if activity == 'awaiting_approach':
            return "wait"
        
        # Continue in phase
        return "continue"
    
    graph.add_conditional_edges(
        "approach_node",
        should_continue_approach,
        {
            "evaluate": "approach_evaluation_node",
            "continue": "approach_node",
            "wait": END
        }
    )
    
    # After evaluation, move to followup
    graph.add_edge("approach_evaluation_node", "followup_node")
    
    # ========== FOLLOWUP PHASE ==========
    
    def should_continue_followup(state):
        """Route followup phase."""
        activity = state.get('current_activity', '')
        
        # If phase complete, evaluate
        if state.get('followup_complete'):
            return "evaluate"
        
        # If waiting for response, end turn
        if activity == 'awaiting_followup':
            return "wait"
        
        # Continue in phase
        return "continue"
    
    graph.add_conditional_edges(
        "followup_node",
        should_continue_followup,
        {
            "evaluate": "followup_evaluation_node",
            "continue": "followup_node",
            "wait": END
        }
    )
    
    # After evaluation, generate final report
    graph.add_edge("followup_evaluation_node", "final_evaluation_node")
    graph.add_edge("final_evaluation_node", END)
    
    return graph.compile(debug=False)
