# utils/prompts.py - Comprehensive Interview Prompts (Updated for 2 Phases)

class CaseInterviewPrompts:
    """Centralized prompt templates for case study interviews."""
    
    @staticmethod
    def generate_mcq_questions(role: str, skills: str, mcq_current: int) -> str:
        """Generate MCQ questions to assess candidate preferences."""
        return f"""Generate a single multiple-choice question for {role} role.

Context:
- Role: {role}
- Skills: {skills}
- Question Number: {mcq_current}

Based on the question number, focus on:
- Question 1: Problem-solving preferences (Analytical/data-driven vs Strategic/business vs Technical/implementation vs Operational/process optimization)
- Question 2: Industry preference (2 industries most relevant to {role}, 1 alternative industry, 1 "Other" option)
- Question 3: Case complexity preference (Structured problems with clear metrics vs Open-ended exploratory analysis vs Mixed approach with ambiguity vs Real-time decision making under uncertainty)

Requirements:
- Make the question highly relevant to the role and skills
- Provide exactly 4 options (A, B, C, D)
- Question {mcq_current} should assess the corresponding focus area above

Return JSON format:
{{
  "question": "...",
  "options": [
    {{"letter": "A", "text": "..."}},
    {{"letter": "B", "text": "..."}},
    {{"letter": "C", "text": "..."}},
    {{"letter": "D", "text": "..."}}
  ]
}}"""

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
  "tech_type": "..."
}}

Return ONLY valid JSON."""

    @staticmethod
    def generate_case_study(domain: str, industry: str, case_type: str, role: str, skills: str, tech_type: str) -> str:
        """Generate customized case study."""
        return f"""You are an expert case study designer, skilled at creating realistic business and technical scenarios that test a candidate's diagnostic, framing, and problem-solving skills.

Your goal is to generate a challenging, high-fidelity case study based on the provided parameters.

PARAMETERS:
- Domain: {domain}
- Industry: {industry}
- Case Type: {case_type}
- Candidate Role: {role}
- Candidate Skills: {skills}
- Tech Type: {tech_type}

GUIDING PRINCIPLES:
1. **Time Constraint (Crucial):** The problem must be solvable (i.e., can be diagnosed and framed) in **10 minutes**. The goal is to test the candidate's *initial approach*, *key questions*, and *hypothesis framing*, not to have them design a complete end-to-end solution.

2. **Create Realistic Tension:** The problem's core conflict must intelligently weave the parameters together. For example, the `client_objective` might conflict with the `tech_type`, or the `skills` are needed to solve a problem in an unfamiliar `domain`.

3. **Ambiguity is Key:** Provide enough context to start, but intentionally omit key details. The `hidden_information` section is critical.

4. **"Messy" Real-World Data:** The `available_data` should not be a clean list of metrics. Describe it as a mix of clean and unstructured sources (e.g., "CRM logs," "support tickets," "internal wikis").

5. **Impactful Hidden Info:** For the `hidden_information` section, include at least one piece of data that **subtly invalidates a common assumption** and one **key constraint** the client 'forgot' to mention (e.g., a new compliance rule, a key team member just quit, the 'real' budget is half of what's implied).

REQUIREMENTS:
- Return ONLY valid JSON.
- Do not include any text before or after the JSON object.
- Adhere perfectly to the requested JSON structure below.

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
    "additional_context": "Info to share if candidate asks for clarification (e.g., the 'forgotten' constraint)",
    "data_points": ["Available metric1 (e.g., a red herring)", "Available metric2 (the 'redirecting' data point)"],
    "key_assumptions": ["Important assumption1", "Important assumption2"]
  }},
  "available_data": {{
    "description": "What data sources exist (e.g., 'Mix of clean user logs and incomplete, unstructured support tickets')",
    "sample_metrics": ["metric1", "metric2", "metric3"]
  }},
  "expected_approach": {{
    "ideal_framework": "Brief description of a strong approach (e.g., 'Start by clarifying X, then probe assumption Y')",
    "key_analyses": ["Key questions to ask", "Initial hypotheses to test", "Key trade-offs to identify"],
    "success_indicators": ["What good performance looks like (e.g., 'Candidate identifies the hidden constraint')"]
  }}
}}
"""

    @staticmethod
    def generate_understanding_question(case_study: dict, previous_responses: list, question_number: int) -> str:
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
    def generate_approach_question(case_study: dict, candidate_approach: str, previous_responses: list, question_number: int) -> str:
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
    def evaluate_phase_performance(phase: str, candidate_responses: list, case_study: dict, is_technical: bool) -> str:
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

    @staticmethod
    def generate_final_evaluation(conversation: list, phase_evaluations: dict, case_study: dict, domain: str, role: str) -> str:
        """Generate comprehensive final evaluation report for Understanding and Approach phases only."""
        return f"""You are an expert interviewer evaluating a case study interview performance.

INTERVIEW CONTEXT:
- Role: {role}
- Domain: {domain}
- Case: {case_study.get('title', 'N/A')}

FULL CONVERSATION:
{conversation}

PHASE EVALUATIONS:
- Understanding Phase: {phase_evaluations.get('understanding', {{}})}
- Approach Phase: {phase_evaluations.get('approach', {{}})}

**NOTE:** This interview consisted of TWO phases only: Understanding and Approach. There was no followup/deep-dive phase.

Provide a comprehensive evaluation covering:

1. **Overall Performance** (1-10 scale)
   - Base this on both Understanding and Approach phases
   - Weight: Understanding 40%, Approach 60%

2. **Performance Level**: Choose one:
   - Outstanding (9-10): Exceptional structured thinking, insights, communication across both phases
   - Strong (7-8): Solid framework, good analysis, clear communication in both phases
   - Competent (5-6): Basic structure, adequate analysis, some gaps in one or both phases
   - Developing (3-4): Weak structure, surface-level analysis, communication issues
   - Needs Improvement (1-2): Poor structure, unclear thinking, major gaps in both phases

3. **Key Strengths** (3-5 bullet points)
   - Highlight strengths observed across Understanding and Approach phases
   - Be specific with examples from the conversation

4. **Development Areas** (3-5 bullet points)
   - Identify areas for improvement from both phases
   - Provide actionable, specific feedback

5. **Detailed Competency Assessment**:
   - Problem Structuring (1-10): How well they structured the problem
   - Analytical Thinking (1-10): Quality of analysis and reasoning
   - Communication Clarity (1-10): Clarity and effectiveness of communication
   - Business Judgment (1-10) OR Technical Depth (1-10): Domain-specific competency
   - Framework Rigor (1-10): Completeness and logic of their approach

6. **Phase-by-Phase Summary**:
   - Understanding Phase: 2-3 sentences on their performance
   - Approach Phase: 2-3 sentences on their performance

7. **Interview Summary** (3-4 sentences)
   - Overall assessment of candidate readiness
   - Key takeaways from the interview

8. **Next Steps & Recommendations** (4-5 actionable items)
   - Specific steps for improvement
   - Resources or practice areas to focus on
   - Readiness assessment for real interviews

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
    "framework_rigor": 7
  }},
  "phase_summaries": {{
    "understanding": "Summary of understanding phase performance",
    "approach": "Summary of approach phase performance"
  }},
  "interview_summary": "Overall summary text covering both phases",
  "next_steps": ["step1", "step2", "step3", "step4"]
}}

Be honest, specific, and constructive. Provide actionable feedback based on the TWO phases conducted.

Return ONLY valid JSON."""
