# graph/graph_builder.py - Updated with Understanding and Approach phases only

from langgraph.graph import StateGraph, END
from .state import InterviewState
from .nodes.interview_nodes import CaseStudyInterviewNodes

def build_interview_graph():
    """Build interview graph with Understanding and Approach phases only."""
    
    nodes = CaseStudyInterviewNodes()
    graph = StateGraph(InterviewState)
    
    # Add nodes (removed followup nodes)
    graph.add_node("classification_node", nodes.generate_mcq_node)
    graph.add_node("mcq_processing_node", nodes.process_mcq_answers_node)
    graph.add_node("case_generation_node", nodes.generate_case_node)
    graph.add_node("understanding_node", nodes.understanding_node)
    graph.add_node("understanding_evaluation_node", nodes.understanding_evaluation_node)
    graph.add_node("approach_node", nodes.approach_node)
    graph.add_node("approach_evaluation_node", nodes.approach_evaluation_node)
    graph.add_node("final_evaluation_node", nodes.final_evaluation_node)
    
    # Set entry point
    graph.set_entry_point("classification_node")
    
    # Classification flow
    def after_classification(state):
        if state.get('mcq_answers') and len(state['mcq_answers']) >= 3:
            return "process"
        return "wait"
    
    graph.add_conditional_edges(
        "classification_node",
        after_classification,
        {"process": "mcq_processing_node", "wait": END}
    )
    
    graph.add_edge("mcq_processing_node", "case_generation_node")
    
    def after_case_generation(state):
        if state.get('current_activity') == 'awaiting_understanding':
            if state.get('understanding_question_count', 0) == 0:
                return "wait"
            else:
                return "continue"
        return "wait"
    
    graph.add_conditional_edges(
        "case_generation_node",
        after_case_generation,
        {"continue": "understanding_node", "wait": END}
    )
    
    # Understanding phase
    def should_continue_understanding(state):
        activity = state.get('current_activity', '')
        if state.get('understanding_complete'):
            return "evaluate"
        if activity == 'awaiting_understanding':
            return "wait"
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
    
    graph.add_edge("understanding_evaluation_node", "approach_node")
    
    # Approach phase
    def should_continue_approach(state):
        activity = state.get('current_activity', '')
        if state.get('approach_complete'):
            return "evaluate"
        if activity == 'awaiting_approach' or activity == 'awaiting_approach_structured':
            return "wait"
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
    
    # After approach evaluation, go directly to final evaluation (no followup)
    graph.add_edge("approach_evaluation_node", "final_evaluation_node")
    graph.add_edge("final_evaluation_node", END)
    
    return graph.compile(debug=False)
