# interview_nodes.py - Complete updated version with unified prompts

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from config import get_llm_for_task
import json
import re
import time
from utils.prompts import CaseInterviewPrompts


class CaseStudyInterviewNodes:
    """Interview node logic - all prompts centralized in utils.prompts."""
    
    def extract_json(self, text: str) -> dict:
        """Extract JSON from LLM response with multiple fallback strategies."""
        
        if not text:
            return {}
        
        # Strategy 1: Try json code blocks
        json_match = re.search(r'``````', text, flags=re.DOTALL | re.IGNORECASE)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Strategy 2: Try any code blocks
        code_match = re.search(r'``````', text, flags=re.DOTALL)
        if code_match:
            try:
                return json.loads(code_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Strategy 3: Find JSON object directly
        brace_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                pass
        
        return {}
    
    def validate_response_length(self, state: dict) -> dict:
        """Validation node - check minimum word requirements."""
        messages = state.get('messages', [])
        current_activity = state.get('current_activity', '')
        
        if not messages:
            return state
        
        last_human_msg = None
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                last_human_msg = msg.content
                break
        
        if not last_human_msg:
            return state
        
        word_count = len(last_human_msg.split())
        
        if current_activity == 'awaiting_approach_structured':
            min_words = 250
            error_context = "comprehensive approach"
        else:
            min_words = 10
            error_context = "response"
        
        if word_count < min_words:
            error_msg = f"""⚠️ **Response Too Short**

Your {error_context} needs at least **{min_words} words** for proper evaluation.

**Current:** {word_count} words | **Required:** {min_words} words

Please provide a more detailed response."""
            
            messages = messages[:-1]
            messages.append(AIMessage(content=error_msg))
            
            return {
                'messages': messages,
                'validation_failed': True
            }
        
        return {'validation_failed': False}
    
    # ========== MCQ CLASSIFICATION PHASE ==========
    
    def generate_mcq_node(self, state: dict) -> dict:
        """Generate MCQ questions ONE AT A TIME."""
        role = state.get('role', '')
        skills = ', '.join(state.get('skills', []))
        mcq_current = state.get('mcq_current_question', 0)
        answers = state.get('classification_answers', [])
        
        if len(answers) >= 3 or mcq_current >= 3:
            print("DEBUG: MCQ complete")
            return {
                "mcq_completed": True,
                "current_activity": "processing_mcq"
            }
        
        llm = get_llm_for_task('mcq', temperature=0.5)
        prompt = CaseInterviewPrompts.generate_mcq_questions(role, skills, mcq_current + 1)
        response = llm.invoke([SystemMessage(content=prompt)])
        
        question_data = self.extract_json(response.content)
        
        if not question_data or 'question' not in question_data:
            fallback_questions = [
                {
                    "question": "What type of problems do you prefer?",
                    "options": [
                        {"letter": "A", "text": "Data analysis"},
                        {"letter": "B", "text": "Strategic planning"},
                        {"letter": "C", "text": "Technical design"},
                        {"letter": "D", "text": "Process optimization"},
                    ]
                },
                {
                    "question": "Which industry interests you most?",
                    "options": [
                        {"letter": "A", "text": "Finance/Banking"},
                        {"letter": "B", "text": "Healthcare"},
                        {"letter": "C", "text": "Technology"},
                        {"letter": "D", "text": "Other"},
                    ]
                },
                {
                    "question": "Preferred case complexity?",
                    "options": [
                        {"letter": "A", "text": "Well-defined problems"},
                        {"letter": "B", "text": "Open-ended analysis"},
                        {"letter": "C", "text": "Mixed approach"},
                        {"letter": "D", "text": "Real-time decisions"},
                    ]
                },
            ]
            question_data = fallback_questions[min(mcq_current, 2)]
        
        mcq_message = f"📋 Question {mcq_current + 1}/3\n\n{question_data['question']}\n\n"
        for opt in question_data['options']:
            mcq_message += f"{opt['letter']}. {opt['text']}\n"
        mcq_message += "\nPlease respond with A, B, C, or D"
        
        current_questions = state.get('mcq_questions', [])
        current_questions.append(question_data)
        
        print(f"DEBUG: Generated MCQ {mcq_current + 1}/3")
        return {
            "mcq_questions": current_questions,
            "mcq_current_question": mcq_current + 1,
            "messages": [AIMessage(content=mcq_message)],
            "current_activity": "awaiting_mcq_answer",
        }

    def process_mcq_answers_node(self, state: dict) -> dict:
        """Process MCQ answers using centralized prompt."""
        if state.get('mcq_completed') and state.get('domain'):
            print("DEBUG: MCQ already processed")
            return {
                "current_phase": "understanding",
                "current_activity": "awaiting_understanding"
            }
        
        mcq_questions = state.get('mcq_questions', [])
        classification_answers = state.get('classification_answers', [])
        
        if len(classification_answers) != 3:
            print(f"DEBUG: Need 3 answers, got {len(classification_answers)}")
            return {}
        
        role = state.get('role', '')
        skills = ', '.join(state.get('skills', []))
        
        llm = get_llm_for_task('fast', temperature=0.5)
        prompt = CaseInterviewPrompts.interpret_mcq_answers(mcq_questions, classification_answers, role, skills)
        
        response = llm.invoke([SystemMessage(content=prompt)])
        interpretation = self.extract_json(response.content)
        
        domain = str(interpretation.get('domain', 'Data Science'))
        industry = str(interpretation.get('industry', 'Technology'))
        case_type = str(interpretation.get('case_type', 'problem_solving'))
        tech_type = str(interpretation.get('tech_type', 'Technical'))
        
        confirmation_msg = f"""**Classification Complete!**

- **Domain**: {domain}
- **Industry**: {industry}
- **Case Type**: {case_type.replace('_', ' ').title()}
- **Tech Type**: {tech_type}

Generating your case study..."""
        
        print(f"DEBUG: Classification - {domain}, {industry}, {tech_type}")
        return {
            "domain": domain,
            "industry": industry,
            "case_type": case_type,
            'tech_type': tech_type,
            "mcq_completed": True,
            "messages": [AIMessage(content=confirmation_msg)],
            "current_phase": "case_gen",
            "current_activity": "generating_case",
        }
    
    # ========== CASE GENERATION ==========
    
    def generate_case_node(self, state: dict) -> dict:
        """Generate case study using centralized prompt."""
        if state.get('case_study') and state.get('case_study').get('company_name'):
            print("DEBUG: Case already exists")
            return {
                "current_phase": "understanding",
                "current_activity": "awaiting_understanding",
                "understanding_question_count": 0
            }
        
        domain = state.get('domain', 'Data Science')
        industry = state.get('industry', 'Healthcare')
        case_type = state.get('case_type', 'problem_solving')
        role = state.get('role', 'Data Analyst')
        tech_type = state.get('tech_type', 'Technical')
        skills = ', '.join(state.get('skills', []))
        
        print(f"DEBUG: Generating case - {industry} {domain}")
        
        llm = get_llm_for_task('case_generation', temperature=0.5)
        prompt = CaseInterviewPrompts.generate_case_study(domain, industry, case_type, role, skills, tech_type)
        response = llm.invoke([SystemMessage(content=prompt)])
        case_data = self.extract_json(response.content)
        
        if not case_data or 'problem_statement' not in case_data:
            case_data = {
                "title": f"{industry} {domain} Challenge",
                "company_name": f"{industry} Solutions Inc.",
                "situation": f"Challenges in {domain.lower()}",
                "problem_statement": f"Solve critical {domain.lower()} problem",
                "initial_information": {
                    "known_facts": ["Data available"],
                    "constraints": ["Budget: $500K", "Timeline: 6 months"],
                    "stakeholders": ["Executive team", "Operations"]
                }
            }
        
        case_message = f"""🎯 **CASE STUDY: {case_data.get('title', 'Challenge')}**

**Company:** {case_data.get('company_name', 'Unknown')}

**Situation:**
{case_data.get('situation', 'N/A')}

**Problem:**
{case_data.get('problem_statement', 'N/A')}

"""
        
        initial_info = case_data.get('initial_information', {})
        
        if initial_info.get('known_facts'):
            case_message += "\n**Known Facts:**\n"
            for fact in initial_info['known_facts']:
                case_message += f"- {fact}\n"
        
        if initial_info.get('constraints'):
            case_message += "\n**Constraints:**\n"
            for constraint in initial_info['constraints']:
                case_message += f"- {constraint}\n"
        
        if initial_info.get('stakeholders'):
            case_message += "\n**Stakeholders:**\n"
            for stakeholder in initial_info['stakeholders']:
                case_message += f"- {stakeholder}\n"
        
        case_message += "\n---\n\n⏱️ **Case Started!**\n\nShare your **initial understanding** of this problem.\n\n💡 *Minimum 10 words required.*"
        
        print(f"DEBUG: Case generated - {case_data.get('company_name')}")
        return {
            "case_study": case_data,
            "messages": [AIMessage(content=case_message)],
            "current_phase": "understanding",
            "current_activity": "awaiting_understanding",
            "understanding_question_count": 0,
            "interview_start_time": time.time(),
        }
    
    # ========== UNDERSTANDING PHASE ==========
    
    def understanding_node(self, state: dict) -> dict:
        """Understanding phase - using unified prompt function."""
        messages = state.get('messages', [])
        case_study = state.get('case_study', {})
        count = state.get('understanding_question_count', 0)
        max_questions = 3
        
        if state.get('validation_failed'):
            return {"current_activity": "awaiting_understanding"}
        
        problem = str(case_study.get('problem_statement', 'the given problem'))
        company_name = str(case_study.get('company_name', 'the company'))
        situation = str(case_study.get('situation', 'the situation at hand'))
        # Get last human message
        last_human_msg = None 
        last_messages = messages[-2:] if len(messages) >= 2 else messages
        for msg in last_messages:
            if isinstance(msg, HumanMessage):
                last_human_msg = msg.content
                break
        print(f"DEBUG: Previous human response: {last_human_msg} ")
        if count >= max_questions:
            return {"understanding_complete": True, "current_activity": "phase_complete"}
        
        if not last_human_msg:
            return {"current_activity": "awaiting_understanding"}
        
        # EXTRACT PREVIOUS AI QUESTION (for context)
        # In understanding_node function:

# EXTRACT PREVIOUS AI QUESTION (for context)
        last_ai_question = ""
        if len(messages) >= 2:
            for msg in reversed(messages[-3:]):  # Look at last 3 messages
                if isinstance(msg, AIMessage):
                    # Skip the case study generation message
                    if "Case Started!" not in msg.content and "Share your initial understanding" not in msg.content:
                        last_ai_question = msg.content
                        break
                    # If it's the first question ("Share your initial understanding"), pass empty string
                    elif "Share your initial understanding" in msg.content and count == 1:
                        last_ai_question = ""  # Don't include case study question
                        break

        print(f"[DEBUG]  AI question (filtered): {last_ai_question}")

        print(f"DEBUG:  candidate  response: {last_human_msg} ")
        llm = get_llm_for_task('conversation', temperature=0.15)
        
        # Generate follow-up with previous question context
        prompt = CaseInterviewPrompts.generate_understanding_followup(
            company_name,
            situation,
            problem,
            str(last_human_msg),
            count + 1, 
            max_questions,
            last_ai_question  # Pass previous question
        )
        
        try:
            response = llm.invoke([SystemMessage(content=prompt)])
            question = response.content.strip().replace('**', '').replace('*', '')
        except Exception as e:
            print(f"DEBUG: Error generating understanding Q{count+1}: {e}")
            question = "Can you elaborate on your reasoning about this situation?"
        
        return {
            "messages": [AIMessage(content=question)],
            "understanding_question_count": count + 1,
            "current_activity": "awaiting_understanding"
        }


    def understanding_evaluation_node(self, state: dict) -> dict:
        """Evaluate understanding phase using STRICT centralized prompt."""
        print("DEBUG: Evaluating understanding phase")
        evaluation = self._evaluate_phase(state, 'understanding')
        
        return {
            "understanding_evaluation": evaluation,
            "current_phase": "approach",
            "approach_question_count": 0,
            "current_activity": "awaiting_approach"
        }
    
    # ========== APPROACH PHASE ==========
    
    def approach_node(self, state: dict) -> dict:
        """Approach phase - comprehensive solution design with strict case-grounding."""
        messages = state.get("messages", [])
        case_study = state.get("case_study", {})
        count = state.get("approach_question_count", 0)
        max_questions = 4
        
        if state.get("validation_failed"):
            return {"current_activity": "awaiting_approach"}
        
        company_name = case_study.get("company_name", "the company")
        problem = str(case_study.get("problem_statement", ""))
        role = state.get("role", "general")
        tech_type = state.get("tech_type", "")
        is_technical = tech_type == "Technical"
        
        # Get last human message
        last_human_msg = None
        for msg in reversed(messages[-3:]):
            if isinstance(msg, HumanMessage):
                last_human_msg = msg.content
                break
        
        print(f"[DEBUG] Approach - count={count}/{max_questions}, role={role}, tech={is_technical}")
        
        if count >= max_questions:
            return {"approach_complete": True, "current_activity": "phase_complete"}
        
        # Generate first question or follow-up
        if count == 0 or not last_human_msg:
            prompt = CaseInterviewPrompts.generate_first_approach_question(
                company_name, problem, role, is_technical
            )
            question = prompt
            print(f"[DEBUG] Generated approach Q1 - structured framework for {company_name}")
        else:
            # Get previous AI question
            last_ai_question = ""
            for msg in reversed(messages[-5:]):
                if isinstance(msg, AIMessage):
                    last_ai_question = msg.content
                    break
            
            # Generate follow-up with new prompt
            llm = get_llm_for_task("conversation", temperature=0.0)
            
            followup_prompt = CaseInterviewPrompts.generate_approach_followup(
                company_name=company_name,
                problem=problem,
                candidate_response=str(last_human_msg),
                question_number=count + 1,
                is_technical=is_technical,
                last_question=last_ai_question
            )
            
            try:
                response = llm.invoke([SystemMessage(content=followup_prompt)])
                question = response.content.strip()
                
                # Clean up any meta-commentary
                question = question.replace('**', '').replace('"', '')
                
                print(f"[DEBUG] Generated approach Q{count+1} for {company_name}")
            except Exception as e:
                print(f"[DEBUG] Error generating approach Q{count+1}: {e}")
                question = f"How would you implement that specifically for {company_name}?"
        
        return {
            "messages": [AIMessage(content=question)],
            "approach_question_count": count + 1,
            "current_activity": "awaiting_approach"
        }


    def approach_evaluation_node(self, state: dict) -> dict:
        """Evaluate approach phase using STRICT centralized prompt."""
        print("DEBUG: Evaluating approach phase")
        evaluation = self._evaluate_phase(state, 'approach')
        
        return {
            "approach_evaluation": evaluation,
            "current_phase": "final",
            "current_activity": "generating_final_evaluation"
        }
    
    # ========== EVALUATION HELPERS (STRICT QUALITY-BASED) ==========
    
    def evaluate_phase(self, state: dict, phase_name: str) -> dict:
        """Evaluate phase with STRICT quality assessment and detailed error handling."""
        messages = state.get("messages", [])
        case_study = state.get("case_study", {})
        tech_type = state.get("tech_type", "")
        is_technical = tech_type == "Technical"
        
        # Extract Q&A pairs
        conversation_pairs = []
        current_question = None
        
        for msg in messages[-30:]:
            if isinstance(msg, AIMessage):
                if "Case Started!" not in msg.content and "Share your initial understanding" not in msg.content:
                    current_question = msg.content
            elif isinstance(msg, HumanMessage) and current_question:
                conversation_pairs.append({
                    "question": current_question,
                    "response": msg.content
                })
                current_question = None
            
            if len(conversation_pairs) >= 5:
                break
        
        print(f"[DEBUG] Extracted {len(conversation_pairs)} Q&A pairs for evaluation")
        
        # Validation check
        if len(conversation_pairs) == 0:
            print(f"[ERROR] No conversation pairs found for {phase_name} evaluation")
            return {
                "score": 0.0,
                "strengths": ["No responses detected"],
                "weaknesses": ["Unable to evaluate - no conversation data"],
                "key_observations": ["System error: No conversation pairs extracted"],
                "candidate_key_responses": [],
                "case_specificity_score": 0.0,
                "depth_score": 0.0,
                "response_quality_score": 0.0,
                "overall_comment": f"Error: Unable to evaluate {phase_name} phase due to missing conversation data.",
                "evaluation_error": True,
                "error_details": "No Q&A pairs extracted from conversation"
            }
        
        llm = get_llm_for_task("evaluation", temperature=0.2)
        
        eval_prompt = CaseInterviewPrompts.evaluate_phase_performance(
            phase_name,
            conversation_pairs,
            case_study,
            is_technical
        )
        
        # Attempt evaluation with detailed error handling
        max_retries = 2
        evaluation = None
        last_error = None
        
        for attempt in range(max_retries):
            try:
                print(f"[DEBUG] Evaluation attempt {attempt + 1}/{max_retries} for {phase_name}")
                response = llm.invoke([SystemMessage(content=eval_prompt)])
                
                if not response or not response.content:
                    raise ValueError("Empty response from LLM")
                
                evaluation = self.extract_json(response.content)
                
                # Validate required fields
                required_fields = ["score", "strengths", "weaknesses", "key_observations"]
                missing_fields = [field for field in required_fields if field not in evaluation]
                
                if missing_fields:
                    raise ValueError(f"Missing required fields: {missing_fields}")
                
                # Validation successful
                print(f"[DEBUG] {phase_name} evaluation successful - score={evaluation.get('score', 0)}")
                break
                
            except json.JSONDecodeError as e:
                last_error = f"JSON parsing error: {str(e)}"
                print(f"[ERROR] {last_error}")
                print(f"[DEBUG] Raw response: {response.content[:500] if response else 'None'}")
                
            except ValueError as e:
                last_error = f"Validation error: {str(e)}"
                print(f"[ERROR] {last_error}")
                
            except Exception as e:
                last_error = f"Unexpected error: {type(e).__name__} - {str(e)}"
                print(f"[ERROR] {last_error}")
            
            # If not last attempt, wait before retry
            if attempt < max_retries - 1:
                print(f"[DEBUG] Retrying evaluation...")
                time.sleep(1)
        
        # If all retries failed, create detailed fallback
        if not evaluation or "score" not in evaluation:
            print(f"[ERROR] All evaluation attempts failed for {phase_name}")
            
            # Extract candidate responses for context
            candidate_responses = [pair["response"][:200] for pair in conversation_pairs[:3]]
            
            evaluation = {
                "score": 5.0,  # Neutral score when evaluation fails
                "strengths": ["Participated in the interview"],
                "weaknesses": [
                    "Unable to generate detailed evaluation due to system error",
                    "Please review responses manually"
                ],
                "key_observations": [
                    f"Evaluation system encountered an error: {last_error}",
                    f"Responded to {len(conversation_pairs)} questions",
                    "Manual review recommended for accurate assessment"
                ],
                "candidate_key_responses": candidate_responses,
                "case_specificity_score": 5.0,
                "depth_score": 5.0,
                "response_quality_score": 5.0,
                "overall_comment": f"Evaluation for {phase_name} phase could not be completed due to system error. "
                                f"The candidate provided {len(conversation_pairs)} responses. "
                                f"Manual review is recommended. Error: {last_error}",
                "evaluation_error": True,
                "error_details": last_error
            }
        
        # Ensure candidate_key_responses exists
        if "candidate_key_responses" not in evaluation:
            evaluation["candidate_key_responses"] = [pair["response"][:200] for pair in conversation_pairs[:2]]
        
        return evaluation

    def final_evaluation_node(self, state: dict) -> dict:
        """Generate STRICT final evaluation with comprehensive error handling."""
        messages = state.get("messages", [])
        case_study = state.get("case_study", {})
        domain = state.get("domain", "")
        role = state.get("role", "")
        tech_type = state.get("tech_type", "")
        is_technical = tech_type == "Technical"
        
        understanding_eval = state.get("understanding_evaluation", {})
        approach_eval = state.get("approach_evaluation", {})
        
        # Check for phase evaluation errors
        has_errors = (understanding_eval.get("evaluation_error") or 
                    approach_eval.get("evaluation_error"))
        
        if has_errors:
            error_msg = "⚠️ **Evaluation Issues Detected**\n\n"
            if understanding_eval.get("evaluation_error"):
                error_msg += f"- Understanding phase: {understanding_eval.get('error_details', 'Unknown error')}\n"
            if approach_eval.get("evaluation_error"):
                error_msg += f"- Approach phase: {approach_eval.get('error_details', 'Unknown error')}\n"
            
            print(f"[WARNING] Phase evaluation errors detected:\n{error_msg}")
        
        candidate_responses = [msg.content for msg in messages if isinstance(msg, HumanMessage)]
        
        print(f"[DEBUG] Generating final evaluation - {len(candidate_responses)} responses")
        
        llm = get_llm_for_task("evaluation", temperature=0.3)
        
        prompt = CaseInterviewPrompts.generate_final_evaluation(
            candidate_responses,
            understanding_eval,
            approach_eval,
            case_study,
            domain,
            role,
            is_technical
        )
        
        max_retries = 2
        final_eval = None
        last_error = None
        
        for attempt in range(max_retries):
            try:
                print(f"[DEBUG] Final evaluation attempt {attempt + 1}/{max_retries}")
                response = llm.invoke([SystemMessage(content=prompt)])
                
                if not response or not response.content:
                    raise ValueError("Empty response from LLM")
                
                final_eval = self.extract_json(response.content)
                
                # Validate structure
                required_fields = ["overall_score", "performance_level", "dimension_scores"]
                missing_fields = [field for field in required_fields if field not in final_eval]
                
                if missing_fields:
                    raise ValueError(f"Missing required fields: {missing_fields}")
                
                print(f"[DEBUG] Final evaluation complete - overall={final_eval.get('overall_score', 0)}")
                break
                
            except Exception as e:
                last_error = f"{type(e).__name__}: {str(e)}"
                print(f"[ERROR] Final evaluation error: {last_error}")
                
                if attempt < max_retries - 1:
                    time.sleep(1)
        
        # Fallback with error context
        if not final_eval or "dimension_scores" not in final_eval:
            print(f"[ERROR] All final evaluation attempts failed")
            
            # Calculate average from phase scores if available
            avg_score = 5.0
            if understanding_eval.get("score") and approach_eval.get("score"):
                avg_score = (understanding_eval["score"] + approach_eval["score"]) / 2
            
            final_eval = {
                "overall_score": avg_score,
                "performance_level": "Competent" if avg_score >= 5 else "Developing",
                "interview_summary": f"Interview completed with {len(candidate_responses)} responses. "
                                f"Automated evaluation encountered errors. "
                                f"Phase scores - Understanding: {understanding_eval.get('score', 'N/A')}, "
                                f"Approach: {approach_eval.get('score', 'N/A')}. "
                                f"Manual review recommended.",
                "dimension_scores": [
                    {
                        "dimension": "Domain Expertise & Technical Skills",
                        "weight": 30,
                        "score": avg_score,
                        "justification": "Automated evaluation failed. Manual review needed.",
                        "candidate_response_excerpt": candidate_responses[-1][:200] if candidate_responses else "N/A"
                    },
                    {
                        "dimension": "Problem-Solving & Critical Thinking",
                        "weight": 25,
                        "score": avg_score,
                        "justification": "Automated evaluation failed. Manual review needed.",
                        "candidate_response_excerpt": candidate_responses[-2][:200] if len(candidate_responses) > 1 else "N/A"
                    },
                    {
                        "dimension": "Communication & Collaboration",
                        "weight": 20,
                        "score": avg_score,
                        "justification": "Automated evaluation failed. Manual review needed.",
                        "candidate_response_excerpt": candidate_responses[-3][:200] if len(candidate_responses) > 2 else "N/A"
                    },
                    {
                        "dimension": "Adaptability & Creativity",
                        "weight": 25,
                        "score": avg_score,
                        "justification": "Automated evaluation failed. Manual review needed.",
                        "candidate_response_excerpt": candidate_responses[-4][:200] if len(candidate_responses) > 3 else "N/A"
                    }
                ],
                "key_strengths": ["Completed interview", "Provided responses to questions"],
                "development_areas": ["Manual evaluation required due to system error"],
                "phase_breakdown": {
                    "understanding": f"Score: {understanding_eval.get('score', 'Error')} - {understanding_eval.get('overall_comment', 'Evaluation failed')}",
                    "approach": f"Score: {approach_eval.get('score', 'Error')} - {approach_eval.get('overall_comment', 'Evaluation failed')}"
                },
                "recommended_next_steps": [
                    "Review responses manually for accurate assessment",
                    "Check system logs for technical issues",
                    "Contact support if errors persist"
                ],
                "evaluation_error": True,
                "error_details": last_error or "Final evaluation generation failed"
            }
        
        print(f"[DEBUG] Final evaluation complete - overall={final_eval.get('overall_score', 0)}")
        
        return {
            "final_evaluation": final_eval,
            "interview_complete": True,
            "current_activity": "interview_complete",
            "completion_time": time.time()
        }


    # ========== ROUTING ==========
    
    def route_by_activity(self, state: dict) -> str:
        """Router based on current activity and phase."""
        current_activity = state.get('current_activity', '')
        current_phase = state.get('current_phase', 'classification')
        
        print(f"DEBUG: Routing - phase={current_phase}, activity={current_activity}")
        
        # Validation routing
        if state.get('validation_failed'):
            return "validation_failed"
        
        # Phase-based routing
        if current_phase == 'classification':
            if current_activity == 'awaiting_mcq_answer':
                return "process_mcq_answers"
            elif current_activity == 'processing_mcq':
                return "generate_case"
            else:
                return "generate_mcq"
        
        elif current_phase == 'understanding':
            if current_activity == 'awaiting_understanding':
                return "understanding"
            elif current_activity == 'phase_complete':
                return "understanding_evaluation"
            else:
                return "generate_case"
        
        elif current_phase == 'approach':
            if current_activity in ['awaiting_approach_structured', 'awaiting_approach']:
                return "validate_response"
            elif current_activity == 'phase_complete':
                return "approach_evaluation"
            else:
                return "approach"
        
        elif current_phase == 'final':
            return "final_evaluation"
        
        # Default fallback
        print(f"DEBUG: Using fallback routing")
        return "generate_mcq"

    def handle_validation_failed(self, state: dict) -> dict:
        """Handle validation failure - return to awaiting state."""
        print("DEBUG: Handling validation failure")
        return {
            "current_activity": state.get('current_activity', 'awaiting_understanding'),
            "validation_failed": False  # Reset for next attempt
        }
