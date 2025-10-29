# utils/prompts.py - Comprehensive Interview Prompts

class CaseInterviewPrompts:
    """Centralized prompt templates for case study interviews."""

    @staticmethod
    def interpret_mcq_answers(mcq_questions: list, mcq_answers: list, role: str, skills: str) -> str:
        """Interpret MCQ answers to classify case parameters."""
        return f"""You are a case interview expert. Analyze the candidate's MCQ responses to determine the best case study parameters.

CANDIDATE PROFILE:
- Role: {role}
- Skills: {skills}

MCQ QUESTIONS & ANSWERS:
{mcq_questions}

CANDIDATE'S ANSWERS:
{mcq_answers}

Based on their answers, determine:
- domain: The analysis domain (e.g., "Data Science", "Business Strategy", "Technical Architecture")
- industry: Specific industry (e.g., "Finance", "Healthcare", "Technology", "Retail")
- case_type: Either "problem_solving" (structured problem with clear goal) or "descriptive" (open-ended analysis)
- tech_type: determine the candidate type either "Technical" or "Non Technical" with the given {role} 
Return in JSON format:
{{
    "domain": "..",
    "industry": "....",
    "case_type": "...",
    "tech_type":"..."
}}

Return ONLY valid JSON."""

    @staticmethod
    def generate_case_study(domain: str, industry: str, case_type: str, role: str, skills: str,tech_type:str) -> str:
        """Generate customized case study."""
        return f"""You are an expert case study designer. Create a realistic, challenging case study tailored to the candidate.

PARAMETERS:
- Domain: {domain}
- Industry: {industry}
- Case Type: {case_type}
- Candidate Role: {role}
- Candidate Skills: {skills}
- tech type:{tech_type}

REQUIREMENTS:

1. Create a realistic company scenario
2. Present a clear, specific problem
3. Include enough context to start, but not all details
4. Make it challenging but solvable in 10 minutes
5. Ensure relevance to candidate's role , tech type and skills

STRUCTURE:
{{
    "title": "Compelling case title",
    "company_name": "Realistic company name (can be anonymous like 'Client Co.')",
    "company_size": "Startup / Mid-size / Enterprise",
    "situation": "2-3 sentences describing current situation and context",
    "problem_statement": "Clear, specific problem the candidate must solve (2-3 sentences)",
    "initial_information": {{
        "client_objective": "What the client wants to achieve",
        "known_constraints": ["constraint1", "constraint2"],
        "stakeholders": ["stakeholder1", "stakeholder2"]
    }},
    "hidden_information": {{
        "additional_context": "Info to share if candidate asks for clarification",
        "data_points": ["Available metric1", "Available metric2"],
        "key_assumptions": ["Important assumption1", "Important assumption2"]
    }},
    "available_data": {{
        "description": "What data sources exist",
        "sample_metrics": ["metric1", "metric2", "metric3"]
    }},
    "expected_approach": {{
        "ideal_framework": "Brief description of a strong approach",
        "key_analyses": ["Analysis1", "Analysis2", "Analysis3"],
        "success_indicators": ["What good performance looks like"]
    }}
}}

Make the case:
- Realistic and relevant
- Appropriately challenging for the role
- Clear enough to start, ambiguous enough to test thinking
- Connected to candidate's domain,tech type and skills

Return ONLY valid JSON."""

    @staticmethod
    def generate_final_evaluation(conversation: list, phase_evaluations: dict, 
                                   case_study: dict, domain: str, role: str) -> str:
        """Generate comprehensive final evaluation."""
        return f"""You are an expert interviewer evaluating a case study interview performance.

INTERVIEW CONTEXT:
- Role: {role}
- Domain: {domain}
- Case: {case_study.get('title', 'N/A')}

FULL CONVERSATION:
{conversation}

PHASE EVALUATIONS:
- Understanding Phase: {phase_evaluations.get('understanding', {})}
- Approach Phase: {phase_evaluations.get('approach', {})}
- Followup Phase: {phase_evaluations.get('followup', {})}

Provide a comprehensive evaluation covering:

1. **Overall Performance** (1-10 scale)
2. **Performance Level**: Choose one:
   - Outstanding (9-10): Exceptional structured thinking, insights, communication
   - Strong (7-8): Solid framework, good analysis, clear communication
   - Competent (5-6): Basic structure, adequate analysis, some gaps
   - Developing (3-4): Weak structure, surface-level analysis, communication issues
   - Needs Improvement (1-2): Poor structure, unclear thinking, major gaps

3. **Key Strengths** (3-5 bullet points)
4. **Development Areas** (3-5 bullet points)
5. **Detailed Competency Assessment**:
   - Problem Structuring (1-10)
   - Analytical Thinking (1-10)
   - Communication Clarity (1-10)
   - Business Judgment (1-10) OR Technical Depth (1-10) if technical role
   - Creativity & Insights (1-10)

6. **Interview Summary** (2-3 sentences)
7. **Next Steps & Recommendations** (3-4 actionable items)

Return in JSON format:
{{
    "overall_score": 7.5,
    "performance_level": "Strong",
    "key_strengths": ["strength1", "strength2", "strength3"],
    "development_areas": ["area1", "area2", "area3"],
    "competency_scores": {{
        "problem_structuring": 8,
        "analytical_thinking": 7,
        "communication": 8,
        "business_judgment": 7,
        "creativity": 6
    }},
    "interview_summary": "Summary text",
    "next_steps": ["step1", "step2", "step3"]
}}

Be honest, specific, and constructive. Provide actionable feedback.

Return ONLY valid JSON."""

    @staticmethod
    def generate_understanding_question(case_study: dict, previous_responses: list, 
                                       question_number: int) -> str:
        """Generate probing question for understanding phase."""
        return f"""Generate a probing follow-up question to test the candidate's understanding of the case.

CASE: {case_study.get('problem_statement', '')}

CANDIDATE'S PREVIOUS RESPONSES:
{previous_responses}

QUESTION #{question_number}

Focus areas to probe:
- Key assumptions they're making
- Important stakeholders they should consider
- Critical constraints or limitations
- Depth of problem comprehension
- Missing considerations

Generate ONE specific, probing question that:
1. Tests their understanding depth
2. Is conversational and supportive
3. Reveals gaps or strengthens clarity
4. Builds naturally from their previous response

Return ONLY the question text, no formatting or labels."""

    @staticmethod
    def generate_approach_question(case_study: dict, candidate_approach: str,
                                   previous_responses: list, question_number: int) -> str:
        """Generate challenging question for approach phase."""
        return f"""Generate a challenging follow-up question about the candidate's proposed approach.

CASE: {case_study.get('problem_statement', '')}

CANDIDATE'S APPROACH:
{candidate_approach}

PREVIOUS DISCUSSION:
{previous_responses}

QUESTION #{question_number}

Challenge the candidate on:
- Framework completeness and rigor
- Trade-offs they haven't considered
- Alternative approaches
- Prioritization logic
- Practical implementation concerns

Generate ONE challenging but fair question that:
1. Tests depth of their framework
2. Explores alternatives or trade-offs
3. Pushes them to think more critically
4. Maintains respectful, professional tone

Return ONLY the question text."""

    @staticmethod
    def generate_followup_question(case_study: dict, full_conversation: list,
                                   question_number: int, total_questions: int) -> str:
        """Generate dynamic followup question."""
        return f"""Generate a thought-provoking followup question for the case interview.

CASE: {case_study.get('problem_statement', '')}

FULL CONVERSATION SO FAR:
{full_conversation}

QUESTION #{question_number} of {total_questions}

Focus areas (choose based on what hasn't been covered):
- Risk analysis and mitigation
- Success metrics and measurement
- Implementation challenges
- Stakeholder management
- "What if" scenarios (constraint changes)
- Scalability considerations
- Edge cases

Generate ONE insightful question that:
1. Explores a new dimension not yet discussed
2. Tests practical thinking
3. Reveals business judgment
4. Is specific to this case and conversation

Return ONLY the question text."""

    @staticmethod
    def evaluate_phase_performance(phase: str, candidate_responses: list,
                                   case_study: dict, is_technical: bool) -> str:
        """Evaluate candidate's performance in a specific phase."""
        technical_focus = """
    - Technical Depth: Use of appropriate methods, algorithms, tools
    - Data Thinking: How they consider data requirements and limitations
    - Quantitative Rigor: Mathematical/statistical reasoning""" if is_technical else """
    - Business Judgment: Strategic thinking and commercial awareness
    - Stakeholder Awareness: Consideration of different perspectives"""

        return f"""Evaluate the candidate's performance in the {phase} phase of the case interview.

CASE: {case_study.get('problem_statement', '')}

CANDIDATE'S RESPONSES IN THIS PHASE:
{candidate_responses}

Assess the following:

1. **Phase-Specific Evaluation**:
   {phase.title()} Phase Focus:
   - Problem Understanding: How well they grasp the core issues
   - Structured Thinking: Organization and logic of their response
   - Communication: Clarity and articulation
   {technical_focus}

2. **Positive Signals** (what they did well):
   - Strong points in their thinking
   - Good questions they asked
   - Insightful observations

3. **Areas for Improvement**:
   - Gaps in their analysis
   - Weak points in reasoning
   - Missed opportunities

4. **Red Flags** (if any):
   - Logical errors
   - Unrealistic assumptions
   - Poor communication

Return in JSON format:
{{
    "phase": "{phase}",
    "score": <1-10>,
    "strengths": ["strength1", "strength2"],
    "weaknesses": ["weakness1", "weakness2"],
    "key_observations": ["obs1", "obs2", "obs3"],
    "signals": {{
        "structure": ["signal1", "signal2"],
        "problem_solving": ["signal1", "signal2"],
        "communication": ["signal1", "signal2"],
        {"\"technical\": [\"signal1\", \"signal2\"]" if is_technical else "\"business_judgment\": [\"signal1\", \"signal2\"]"}
    }},
    "red_flags": ["flag1"] or []
}}

Be specific and evidence-based. Return ONLY valid JSON."""