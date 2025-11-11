--- START OF FILE interview_nodes.py ---



from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from config import get_llm_for_task
import json
import re
import time
from utils.prompts import CaseInterviewPrompts
class CaseStudyInterviewNodes:
    """Fixed interview node logic with proper phase management and no case regeneration."""
    
    
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
        
        # Strategy 3: Find JSON object directly using balanced braces
        brace_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                pass
        
        # If all strategies fail, return empty dict
        return {}

    
    # ========== MCQ CLASSIFICATION NODES ==========
    
    def generate_mcq_node(self, state: dict) -> dict:
        """Generate MCQ questions ONE AT A TIME."""
        role = state.get('role', ' ')
        skills = ', '.join(state.get('skills', []))
        mcq_current = state.get('mcq_current_question', 0)

        if len(state.get('mcq_answers', [])) >= 3:
            return {"current_activity": "processing_mcq"}

        llm = get_llm_for_task('mcq', temperature=0.5)
        prompt = CaseInterviewPrompts.generate_mcq_questions(role, skills, mcq_current + 1)
        response = llm.invoke([SystemMessage(content=prompt)])
        
        question_data = self.extract_json(response.content)

        # Properly formatted fallback with valid JSON structure
        if not question_data or 'question' not in question_data or 'options' not in question_data:
            fallback_questions = [
                {
                    "question": "What type of problems do you prefer working on?",
                    "options": [
                        {"letter": "A", "text": "Data analysis and pattern discovery"},
                        {"letter": "B", "text": "Strategic planning and recommendations"},
                        {"letter": "C", "text": "Technical system design"},
                        {"letter": "D", "text": "Operational/process optimization"},
                    ]
                },
                {
                    "question": "Which industry are you most interested in?",
                    "options": [
                        {"letter": "A", "text": "Finance/Banking"},
                        {"letter": "B", "text": "Healthcare/Life Sciences"},
                        {"letter": "C", "text": "Technology/E‑commerce"},
                        {"letter": "D", "text": "Other"},
                    ]
                },
                {
                    "question": "What case complexity do you prefer?",
                    "options": [
                        {"letter": "A", "text": "Well‑defined problems with clear metrics"},
                        {"letter": "B", "text": "Open‑ended exploratory analysis"},
                        {"letter": "C", "text": "Mixed – structured and exploratory"},
                        {"letter": "D", "text": "Real‑time decision making"},
                    ]
                },
            ]
            question_data = fallback_questions[min(mcq_current, len(fallback_questions) - 1)]

        # Now question_data is guaranteed to have 'question' and 'options'
        mcq_message = f"📋 Classification Question {mcq_current + 1}\n {question_data['question']}\n\n"
        for opt in question_data['options']:
            mcq_message += f"{opt['letter']}. {opt['text']}\n"
        mcq_message += "\nPlease respond with your answer (A, B, C, or D)"

        current_questions = state.get('mcq_questions', [])
        current_questions.append(question_data)

        return {
            "mcq_questions": current_questions,
            "mcq_current_question": mcq_current + 1,
            "messages": [AIMessage(content=mcq_message)],
            "current_activity": "awaiting_mcq_answer",
        }

    def process_mcq_answers_node(self, state: dict) -> dict:
        """Process MCQ answers to determine domain, industry, and case type."""
        mcq_questions = state.get('mcq_questions', [])
        classification_answers = state.get('classification_answers', [])

        role = state.get('role', '')
        skills = ', '.join(state.get('skills', []))
        
        llm = get_llm_for_task('fast', temperature=0.5)
        prompt = CaseInterviewPrompts.interpret_mcq_answers(mcq_questions,classification_answers,role,skills)
        
    
        
        response = llm.invoke([SystemMessage(content=prompt)])
        interpretation = self.extract_json(response.content)
        
        # Safely extract values
        domain = str(interpretation.get('domain'))
        industry = str(interpretation.get('industry'))
        case_type = str(interpretation.get('case_type'))
        tech_type = str(interpretation.get('tech_type'))
        
        # Format case type for display
        case_type_display = case_type.replace('_', ' ').title()
        
        confirmation_msg = f"""**Classification Complete!**

Based on your responses:
- **Domain**: {domain}
- **Industry**: {industry}
- **Case Type**: {case_type_display}
- **Tech Type**: {tech_type}

Generating your personalized case study..."""
        
        return {
            "domain": domain,
            "industry": industry,
            "case_type": case_type,
            'tech_type': tech_type,
            "mcq_completed": True,
            "messages": [AIMessage(content=confirmation_msg)],
            "current_activity": "generating_case",
            
        }
    
    # ========== CASE GENERATION NODE ==========
    
    def generate_case_node(self, state: dict) -> dict:
        """Generate case study and DISPLAY it before asking questions.
        
        CRITICAL FIX: Prevent regeneration if case already exists.
        """
        # *** FIX #1: Don't regenerate if case already exists ***
        if state.get('case_study') and state.get('case_study').get('company_name'):
            print(f"DEBUG: Case already exists ({state['case_study'].get('company_name')}), skipping regeneration")
            return {
                "current_phase": "understanding",
                "current_activity": "awaiting_understanding"
            }
        
        domain = state.get('domain', 'Data Science')
        industry = state.get('industry', 'Healthcare')
        case_type = state.get('case_type', 'problem_solving')
        role = state.get('role', 'Data Analyst')
        tech_type = state.get('tech_type','Technical')
        skills = ', '.join(state.get('skills', []))
        
        print(f"DEBUG: Generating NEW case for {industry} {domain}")
        
        llm = get_llm_for_task('case_generation', temperature=0.5)
        
        prompt = CaseInterviewPrompts.generate_case_study(domain,industry,case_type,role,skills,tech_type)
        response = llm.invoke([SystemMessage(content=prompt)])
        case_data = self.extract_json(response.content)
        
        if not case_data or 'problem_statement' not in case_data:
            case_data = {
                "title": f"{industry} {domain} Challenge",
                "company_name": f"{industry} Solutions Inc.",
                "company_context": f"Leading {industry} company",
                "situation": f"Challenges in {domain.lower()}",
                "problem_statement": f"Solve critical {domain.lower()} problem",
                "objective": "Improve key metrics by 15%",
                "initial_information": {
                    "known_facts": ["Historical data available", "Current performance below benchmark"],
                    "constraints": ["Budget: $500K", "Timeline: 6 months"],
                    "stakeholders": ["Executive team", "Operations", "Customers"]
                }
            }
        
        # FORMAT CASE PRESENTATION
        case_message = f"""
🎯 **CASE STUDY: {case_data.get('title', 'Business Challenge')}**

**Company:** {case_data.get('company_name', 'Unknown Company')}


**Situation:**
{case_data.get('situation', 'N/A')}

**Problem Statement:**
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
            case_message += "\n**Key Stakeholders:**\n"
            for stakeholder in initial_info['stakeholders']:
                case_message += f"- {stakeholder}\n"
        
        case_message += """
---

⏱️ **case study  Started!**

Please share your **initial understanding** of this problem. What are the key issues you identify?

💡 *Note: If you need clarification, data, or hints, just ask naturally - I'll help you.*
"""
        
        print(f"DEBUG: Case generated: {case_data.get('company_name', 'Unknown')}")
        
        # Start timer and move to understanding phase
        return {
            "case_study": case_data,
            "messages": [AIMessage(content=case_message)],
            "current_phase": "understanding",
            "current_activity": "awaiting_understanding",
            "understanding_question_count": 0,  # Reset counter
            "interview_start_time": time.time(),
            "understanding_complete": False
        }
    
    # ========== UNDERSTANDING PHASE ==========
    def understanding_node(self, state: dict) -> dict:
        """Understanding phase - ask 3 probing questions.
        
        *** FIX #2: Handle initial minimal responses properly ***
        """
        messages = state.get('messages', [])
        case_study = state.get('case_study', {})
        count = state.get('understanding_question_count', 0)
        max_questions = 3
        
        company_name = case_study.get('company_name', 'the company')
        problem = case_study.get('problem_statement', '')
        
        # Get last human message
        last_human_msg = None
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                last_human_msg = msg.content
                break
        
        print(f"DEBUG: Understanding - count={count}/{max_questions}, has_response={bool(last_human_msg)}")
        
        # *** CRITICAL FIX: If count=0 and we HAVE a response, this is the FIRST user response ***
        if count == 0 and last_human_msg:
            print(f"DEBUG: Initial response received: '{last_human_msg}...', generating first follow-up question")
            
            llm = get_llm_for_task('conversation', temperature=0.5)
            
            system_prompt = f"""The candidate just gave their initial understanding of {company_name}'s problem.

**Their response:** {last_human_msg}

Generate ONE focused follow-up question to probe deeper into their understanding.
Ask about their assumptions, what data they'd need, or what constraints they see.

Keep it under 80 words, NO markdown, just the question."""
            
            response = llm.invoke([SystemMessage(content=system_prompt)])
            question_text = response.content.strip().replace('**', '').replace('*', '')
            
            print(f"DEBUG: Generated first follow-up question, incrementing count to 1")
            
            return {
                "messages": [AIMessage(content=question_text)],
                "understanding_question_count": 1,  # *** INCREMENT to 1 ***
                "current_activity": "awaiting_understanding"
            }
        
        # If count=0 and no response, case was just shown - wait
        if count == 0 and not last_human_msg:
            print(f"DEBUG: Waiting for candidate's initial understanding")
            return {
                "current_activity": "awaiting_understanding"
            }
        
        # If phase complete, move to evaluation
        if count >= max_questions:
            print(f"DEBUG: Understanding COMPLETE")
            return {
                "understanding_complete": True,
                "current_activity": "phase_complete"
            }
        
        # If we asked a question but no response yet, wait
        if count > 0 and not last_human_msg:
            print(f"DEBUG: Waiting for response to question {count}")
            return {
                "current_activity": "awaiting_understanding"
            }
        
        # Generate next follow-up question (count is 1 or 2 at this point)
        llm = get_llm_for_task('conversation', temperature=0.5)
        
        system_prompt = f"""You are conducting understanding phase question {count + 1} of {max_questions}.

CRITICAL: ONLY mention "{company_name}" - NO other company names!

**Case Details:**
Company: {company_name}
Problem: {problem}

**Candidate's Last Response:**
{last_human_msg[:500] if last_human_msg else "Initial response"}

**YOUR TASK:**
Generate ONE focused probing question about their understanding.

**RULES:**
1. Reference what THEY said
2. Make it specific to {company_name}
3. Keep under 80 words
4. NO markdown, just the question

Return ONLY the question text."""
        
        try:
            response = llm.invoke([SystemMessage(content=system_prompt)])
            question_text = response.content.strip().replace('**', '').replace('*', '')
        except Exception as e:
            print(f"DEBUG: Error: {e}")
            question_text = f"Can you elaborate on the key constraints that {company_name} faces?"
        
        print(f"DEBUG: Generated understanding question {count + 1}/{max_questions}")
        
        return {
            "messages": [AIMessage(content=question_text)],
            "understanding_question_count": count + 1,
            "current_activity": "awaiting_understanding"
        }
    
    def understanding_evaluation_node(self, state: dict) -> dict:
        """Silent evaluation of understanding phase."""
        evaluation = self._evaluate_phase(state, 'understanding')
        
        print(f"DEBUG: Understanding evaluation complete. Moving to approach phase.")
        
        return {
            "understanding_evaluation": evaluation,
            "current_phase": "approach",
            "approach_question_count": 0,  # Reset counter for approach
            "approach_complete": False,
            "current_activity": "awaiting_approach"
        }
    
    # ========== APPROACH PHASE ==========
    
    def approach_node(self, state: dict) -> dict:
        """Approach phase - ask 4 questions about their solution approach.
        FIRST question gets structured workspace (3 tabs for technical, 1 for non-technical).
        """
        messages = state.get('messages', [])
        case_study = state.get('case_study', {})
        role = state.get('role', 'Analyst')
        skills = state.get('skills', [])
        tech_type = state.get("tech_type", '')
        is_technical_role = tech_type == "Technical"
        count = state.get('approach_question_count', 0)
        max_questions = 4
        company_name = case_study.get('company_name', 'the company')
        problem = case_study.get('problem_statement', '')
        
        # Get last human message
        last_human_msg = None
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                last_human_msg = msg.content
                break
        
        print(f"DEBUG: Approach - count={count}/{max_questions}, tech={is_technical_role}, has_response={bool(last_human_msg)}")
        
        # Check if complete
        if count >= max_questions:
            print(f"DEBUG: Approach COMPLETE")
            return {
                "approach_complete": True,
                "current_activity": "phase_complete"
            }
        
        # First time (count=0) - generate STRUCTURED framework question
        if count == 0:
            llm = get_llm_for_task('conversation', temperature=0.7)
            
            # Build framework instruction based on technical vs non-technical
            framework_guidance = f"""📊 **Approach Phase - Framework Development**

    Now that we understand {company_name}'s problem, I'd like you to **document your solution approach**.

    **Please provide:**

    1. **Framework Structure**: Outline your overall framework or methodology
    - What major steps or phases would you follow?
    - What key areas need analysis?
    - How would you structure your approach?
    """
            
            if is_technical_role:
                framework_guidance += """
    2. **Technical Approach**:
    - What specific algorithms, models, or technical methods would you use?
    - What data transformations or preprocessing steps are needed?
    - **Use the CODE tab** to provide pseudocode or implementation sketches
    - What tools/libraries would you leverage?

    3. **Implementation Details**:
    - Technical architecture and design decisions
    - Data pipeline and processing flow
    """
            
            framework_guidance += f"""
    {'3' if is_technical_role else '2'}. **Implementation Plan**:
    - What's the logical sequence of steps?
    - What are key dependencies?
    - What potential challenges do you foresee for {company_name}?
    """
            
            if is_technical_role:
                framework_guidance += """
    💡 **Use the workspace tabs below to organize your approach:**
    - **📋 Framework**: High-level framework and methodology
    - **⚙️ Technical Approach**: Algorithms, methods, techniques
    - **💻 Code Editor**: Implementation code or pseudocode (optional)
    """
            else:
                framework_guidance += """
    💡 **Use the workspace to document your comprehensive framework and approach.**
    """
            
            framework_guidance += "\nTake your time to provide a comprehensive approach."
            
            print(f"DEBUG: Generated first STRUCTURED approach question (technical={is_technical_role})")
            return {
                "messages": [AIMessage(content=framework_guidance)],
                "approach_question_count": 1,
                "current_activity": "awaiting_approach_structured"
            }
        
        # If we just received the structured approach (count=1, has response)
        if count == 1 and last_human_msg:
            print(f"DEBUG: Received structured approach, generating follow-up question 2")
            llm = get_llm_for_task('conversation', temperature=0.7)
            
            system_prompt = f"""You are conducting approach phase question 2 of {max_questions}.

    CRITICAL: ONLY mention "{company_name}"!

    **Case:** {company_name} - {problem}
    **Role:** {role}

    **Candidate's Structured Approach:**
    {last_human_msg[:500]}

    **YOUR TASK:**
    Generate ONE follow-up question about their approach for {company_name}.

    Focus on:
    - Specific analysis techniques they'd use
    - Trade-offs in their proposed approach
    - How they'd prioritize different aspects

    **RULES:**
    1. Reference what THEY said in their approach
    2. Make it specific to {company_name}
    3. Challenge their assumptions constructively
    4. Keep under 80 words
    5. NO markdown, just the question

    Return ONLY the question text."""
            
            try:
                response = llm.invoke([SystemMessage(content=system_prompt)])
                question_text = response.content.strip().replace('**', '').replace('*', '')
            except Exception as e:
                print(f"DEBUG: Error: {e}")
                question_text = f"What specific analysis techniques would you prioritize first for {company_name}?"
            
            print(f"DEBUG: Generated approach question 2/{max_questions}")
            return {
                "messages": [AIMessage(content=question_text)],
                "approach_question_count": 2,
                "current_activity": "awaiting_approach"
            }
        
        # If waiting for response
        if not last_human_msg:
            print(f"DEBUG: Waiting for response to question {count}")
            return {
                "current_activity": "awaiting_approach"
            }
        
        # Generate follow-up questions 3 and 4
        llm = get_llm_for_task('conversation', temperature=0.7)
        
        system_prompt = f"""You are conducting approach phase question {count + 1} of {max_questions}.

    CRITICAL: ONLY mention "{company_name}"!

    **Case:** {company_name} - {problem}
    **Role:** {role}

    **Candidate's Previous Response:**
    {last_human_msg[:500]}

    **YOUR TASK:**
    Generate ONE follow-up question about their approach for {company_name}.

    **Question {count + 1} should focus on:**
    - Implementation challenges for {company_name}
    - Data requirements or validation methods
    - Timeline and resource considerations
    - Risk mitigation strategies

    **RULES:**
    1. Reference what THEY said
    2. Make it specific to {company_name}
    3. Keep under 80 words
    4. NO markdown, just the question

    Return ONLY the question text."""
        
        try:
            response = llm.invoke([SystemMessage(content=system_prompt)])
            question_text = response.content.strip().replace('**', '').replace('*', '')
        except Exception as e:
            print(f"DEBUG: Error: {e}")
            question_text = f"What implementation challenges do you anticipate for {company_name}?"
        
        print(f"DEBUG: Generated approach question {count + 1}/{max_questions}")
        return {
            "messages": [AIMessage(content=question_text)],
            "approach_question_count": count + 1,
            "current_activity": "awaiting_approach"
        }

    def approach_evaluation_node(self, state: dict) -> dict:
        """Silent evaluation of approach phase."""
        evaluation = self._evaluate_phase(state, 'approach')
        
        return {
            "approach_evaluation": evaluation,
            "current_phase": "followup",
            "followup_question_count": 0,  # Reset counte       r
            "followup_complete": False,
            "current_activity": "awaiting_followup"
        }
    
    # ========== FOLLOWUP PHASE ==========


    
    # ========== FINAL EVALUATION ==========
    
    def _evaluate_phase(self, state: dict, phase_name: str) -> dict:
        """Helper method to evaluate a specific phase WITH candidate responses."""
        messages = state.get('messages', [])
        case_study = state.get('case_study', {})
        
        # Extract candidate responses from this phase
        candidate_responses = []
        for msg in reversed(messages[:30]):
            if isinstance(msg, HumanMessage):
                candidate_responses.insert(0, msg.content)
                if len(candidate_responses) >= 5:
                    break
        
        llm = get_llm_for_task('evaluation', temperature=0.3)
        
        eval_prompt = f"""Evaluate the candidate's {phase_name} phase performance.

    Case Problem: {case_study.get('problem_statement', '')}

    Candidate's Responses in this Phase:
    {json.dumps(candidate_responses)}

    Evaluate based on:
    - Depth of analysis
    - Clarity of communication
    - Structured thinking
    - Relevant insights
    - Technical accuracy

    **CRITICAL: Include the candidate's KEY RESPONSES in your evaluation for reporting.**

    Return ONLY valid JSON:
    {{
    "score": 7.5,
    "strengths": ["strength1", "strength2"],
    "weaknesses": ["area1", "area2"],
    "key_observations": ["observation1", "observation2"],
    "candidate_key_responses": ["response excerpt 1", "response excerpt 2"],
    "overall_comment": "..."
    }}"""
        
        response = llm.invoke([SystemMessage(content=eval_prompt)])
        evaluation = self.extract_json(response.content)
        
        if not evaluation:
            evaluation = {
                "score": 7.0,
                "strengths": ["Engaged with the problem"],
                "weaknesses": ["Could provide more depth"],
                "key_observations": ["Demonstrated basic understanding"],
                "candidate_key_responses": candidate_responses[:2] if candidate_responses else ["No response recorded."],
                "overall_comment": "Satisfactory performance. Could benefit from deeper probing."
            }
        
        # Ensure responses are included
        if 'candidate_key_responses' not in evaluation or not evaluation['candidate_key_responses']:
            evaluation['candidate_key_responses'] = candidate_responses[:2] if candidate_responses else ["No response recorded."]
        
        return evaluation


    def final_evaluation_node(self, state: dict) -> dict:
        """Generate comprehensive final evaluation WITH detailed dimension scores and responses."""
        messages = state.get('messages', [])
        case_study = state.get('case_study', {})
        domain = state.get('domain', '')
        role = state.get('role', '')
        
        # Get phase evaluations (now include responses)
        understanding_eval = state.get('understanding_evaluation', {})
        approach_eval = state.get('approach_evaluation', {})
        followup_eval = state.get('followup_evaluation', {})
        
        candidate_responses = [
            msg.content for msg in messages
            if isinstance(msg, HumanMessage)
        ]
        
        llm = get_llm_for_task('evaluation', temperature=0.3)
        
        prompt = f"""Generate a comprehensive final interview evaluation report with DIMENSION SCORES.

    **Case Study:**
    {case_study.get('problem_statement', '')}

    **Candidate Profile:**
    - Role: {role}
    - Domain: {domain}

    **Phase Evaluations (with candidate responses):**
    Understanding Phase: {json.dumps(understanding_eval)}
    Approach Phase: {json.dumps(approach_eval)}
    Follow-up Phase: {json.dumps(followup_eval)}

    **All Candidate Responses:**
    {json.dumps(candidate_responses[-15:])}

    Generate detailed evaluation covering:

    1. Overall score (1-10)
    2. **DIMENSION SCORES with candidate response excerpts:**
    - Domain Expertise & Technical Skills (25%)
    - Problem-Solving Skills & Critical Thinking (25%)
    - Structured Thinking (25%)
    - Professionalism (25%)

    3. Key strengths and development areas
    4. Phase-wise breakdown
    5. Recommended next steps

    **CRITICAL:** For EACH dimension, include:
    - Score (1-10)
    - Brief justification
    - Specific candidate response excerpt that demonstrates this dimension

    Return ONLY valid JSON:
    {{
    "overall_score": 7.5,
    "performance_level": "Strong",
    "interview_summary": "...",
    "dimension_scores": [
        {{
        "dimension": "Domain Expertise & Technical Skills",
        "weight": 25,
        "score": 8.0,
        "justification": "...",
        "candidate_response_excerpt": "..."
        }},
        {{
        "dimension": "Problem-Solving Skills & Critical Thinking",
        "weight": 15,
        "score": 7.5,
        "justification": "...",
        "candidate_response_excerpt": "..."
        }},
        {{
        "dimension": "Clarity",
        "weight": 15,
        "score": 8.5,
        "justification": "...",
        "candidate_response_excerpt": "..."
        }},
        {{
        "dimension": "Business Acumen",
        "weight": 15,
        "score": 7.0,
        "justification": "...",
        "candidate_response_excerpt": "..."
        }},
        {{
        "dimension": "Structured Thinking",
        "weight": 15,
        "score": 8.0,
        "justification": "...",
        "candidate_response_excerpt": "..."
        }},
        {{
        "dimension": "Professionalism",
        "weight": 15,
        "score": 9.0,
        "justification": "...",
        "candidate_response_excerpt": "..."
        }}
    ],
    "key_strengths": ["strength1", "strength2", "strength3"],
    "development_areas": ["area1", "area2", "area3"],
    "phase_breakdown": {{
        "understanding": "...",
        "approach": "...",
        "followup": "..."
    }},
    "recommended_next_steps": ["step1", "step2", "step3"]
    }}"""
        
        response = llm.invoke([SystemMessage(content=prompt)])
        final_eval = self.extract_json(response.content)
        
        if not final_eval or 'dimension_scores' not in final_eval:
            final_eval = {
                "overall_score": 7.0,
                "performance_level": "Satisfactory",
                "interview_summary": "Candidate demonstrated a solid understanding of the core problem and proposed a reasonable approach. Further development is needed in probing for unstated assumptions and detailing technical implementations.",
                "dimension_scores": [
                    {
                        "dimension": "Domain Expertise & Technical Skills",
                        "weight": 25,
                        "score": 7.0,
                        "justification": "Showed adequate technical knowledge for the role but could provide more specific examples.",
                        "candidate_response_excerpt": candidate_responses[-3] if len(candidate_responses) >= 3 else "N/A"
                    },
                    {
                        "dimension": "Problem-Solving Skills & Critical Thinking",
                        "weight": 15,
                        "score": 7.5,
                        "justification": "Effectively broke down the problem into manageable components.",
                        "candidate_response_excerpt": candidate_responses[-2] if len(candidate_responses) >= 2 else "N/A"
                    },
                    {
                        "dimension": "Structured Thinking",
                        "weight": 15,
                        "score": 8.0,
                        "justification": "Presented a logical and well-organized framework for their approach.",
                        "candidate_response_excerpt": candidate_responses[-1] if candidate_responses else "N/A"
                    }
                ],
                "key_strengths": ["Clear and concise communication", "Logical problem structuring", "Maintained professional demeanor"],
                "development_areas": ["Deeper technical analysis is needed", "Consider edge cases and potential risks more thoroughly", "Proactively ask for clarifying data"],
                "phase_breakdown": {
                    "understanding": "Good grasp of the core issues, but could have asked more probing questions.",
                    "approach": "A reasonable and structured framework was proposed. Lacked some detail on implementation."
                },
                "recommended_next_steps": ["Practice more complex case studies", "Deepen knowledge of specific algorithms relevant to the domain", "Focus on anticipating potential roadblocks in project plans"]
            }
        
        # Format comprehensive report
        score = final_eval.get('overall_score', 7.0)
        level = final_eval.get('performance_level', 'Satisfactory')
        
        report = f"""
    ╔══════════════════════════════════════════════════════════════════════════════╗
    📊 FINAL INTERVIEW EVALUATION
    ╚══════════════════════════════════════════════════════════════════════════════╝

    **Overall Score:** {score}/10
    **Performance Level:** {level}

    ---

    **📝 Interview Summary:**
    {final_eval.get('interview_summary', 'N/A')}

    ---

    **📊 DIMENSION SCORES:**
    """
        
        # Add detailed dimension scores with responses
        for dim in final_eval.get('dimension_scores', []):
            report += f"""
    **{dim.get('dimension', 'N/A')}** (Weight: {dim.get('weight', 0)}%)
    - Score: {dim.get('score', 0)}/10
    - Justification: {dim.get('justification', 'N/A')}
    - Candidate Response: "{dim.get('candidate_response_excerpt', 'N/A')[:200]}..."
    """
        
        report += "\n---\n\n**✅ KEY STRENGTHS:**\n"
        for strength in final_eval.get('key_strengths', []):
            report += f"\n✓ {strength}"
        
        report += "\n\n---\n\n**📈 AREAS FOR DEVELOPMENT:**\n"
        for area in final_eval.get('development_areas', []):
            report += f"\n⚠ {area}"
        
        report += "\n\n---\n\n**🔍 PHASE BREAKDOWN:**\n"
        breakdown = final_eval.get('phase_breakdown', {})
        report += f"\n**Understanding Phase:** {breakdown.get('understanding', 'N/A')}"
        report += f"\n**Approach Phase:** {breakdown.get('approach', 'N/A')}"

        
        report += "\n\n---\n\n**🎯 RECOMMENDED NEXT STEPS:**\n"
        for step in final_eval.get('recommended_next_steps', []):
            report += f"\n→ {step}"
        
        report += "\n\n╔══════════════════════════════════════════════════════════════════════════════╗\n"
        report += "                       Thank you for participating!\n"
        report += "╚══════════════════════════════════════════════════════════════════════════════╝\n"
        
        return {
            "final_evaluation": final_eval,
            "messages": [AIMessage(content=report)],
            "interview_complete": True,
            "current_activity": "complete"
        }
