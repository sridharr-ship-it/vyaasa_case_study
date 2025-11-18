# utils/prompts.py - Consolidated prompt functions

class CaseInterviewPrompts:
    """Centralized prompt templates for case study interviews."""
    
    # Industry-specific framework keywords
    INDUSTRY_FRAMEWORKS = {
        'consulting': {
            'frameworks': ['profitability analysis', 'market entry', '3Cs', '4Ps', 'Porter\'s Five Forces'],
            'focus_areas': ['revenue/cost drivers', 'competitive dynamics', 'customer segments', 'market positioning']
        },
        'data_science': {
            'frameworks': ['CRISP-DM', 'problem definition', 'data pipeline', 'model selection', 'validation strategy'],
            'focus_areas': ['data quality assessment', 'feature engineering', 'algorithm trade-offs', 'evaluation metrics', 'deployment strategy']
        },
        'engineering': {
            'frameworks': ['requirements analysis', 'design constraints', 'prototyping', 'validation testing', 'iterative design'],
            'focus_areas': ['technical specifications', 'material/technology selection', 'manufacturability', 'performance testing', 'safety protocols']
        },
        'medical': {
            'frameworks': ['clinical assessment', 'differential diagnosis', 'evidence-based protocols', 'treatment planning', 'patient monitoring'],
            'focus_areas': ['patient history', 'diagnostic testing', 'risk stratification', 'outcome measures', 'care coordination']
        },
        'finance': {
            'frameworks': ['financial analysis', 'risk assessment', 'valuation methods', 'scenario planning', 'portfolio optimization'],
            'focus_areas': ['cash flow analysis', 'cost-benefit analysis', 'regulatory compliance', 'market conditions', 'sensitivity analysis']
        },
        'nursing': {
            'frameworks': ['nursing process (ADPIE)', 'patient assessment', 'care planning', 'evidence-based practice', 'quality improvement'],
            'focus_areas': ['patient safety', 'care coordination', 'quality metrics', 'interdisciplinary collaboration', 'patient advocacy']
        },
        'operations': {
            'frameworks': ['process mapping', 'bottleneck analysis', 'lean methodology', 'Six Sigma', 'capacity planning'],
            'focus_areas': ['workflow optimization', 'resource allocation', 'quality control', 'inventory management', 'supply chain']
        },
        'product': {
            'frameworks': ['user research', 'product-market fit', 'prioritization', 'MVP definition', 'iteration planning'],
            'focus_areas': ['user needs', 'feature prioritization', 'roadmap planning', 'metrics definition', 'stakeholder alignment']
        },
        'default': {
            'frameworks': ['problem decomposition', 'root cause analysis', 'solution design', 'implementation planning', 'monitoring'],
            'focus_areas': ['stakeholder needs', 'resource constraints', 'risk mitigation', 'success criteria', 'timeline planning']
        }
    }
    
    @staticmethod
    def get_industry_context(role: str) -> dict:
        """Get industry-specific frameworks and focus areas based on role."""
        role_lower = role.lower() if role else 'default'
        
        industry_map = {
            'consultant': 'consulting', 'business analyst': 'consulting', 'strategist': 'consulting',
            'data scientist': 'data_science', 'ml engineer': 'data_science', 'data analyst': 'data_science',
            'software engineer': 'engineering', 'mechanical engineer': 'engineering', 'design engineer': 'engineering',
            'civil engineer': 'engineering', 'electrical engineer': 'engineering',
            'doctor': 'medical', 'physician': 'medical', 'healthcare': 'medical', 'clinical': 'medical',
            'registered nurse': 'nursing', 'nurse practitioner': 'nursing', 'rn': 'nursing',
            'financial analyst': 'finance', 'investment banker': 'finance', 'accountant': 'finance',
            'operations manager': 'operations', 'supply chain': 'operations', 'logistics': 'operations',
            'product manager': 'product', 'product owner': 'product',
        }
        
        for key, value in industry_map.items():
            if key in role_lower:
                return CaseInterviewPrompts.INDUSTRY_FRAMEWORKS.get(value, CaseInterviewPrompts.INDUSTRY_FRAMEWORKS['default'])
        
        return CaseInterviewPrompts.INDUSTRY_FRAMEWORKS.get('default')

    # ========== MCQ PHASE ==========
    
    @staticmethod
    def generate_mcq_questions(role: str, skills: str, mcq_current: int) -> str:
        """Generate MCQ questions to assess candidate preferences."""
        return f"""Generate a single multiple-choice question for the {role} role.

Context:
- Role: {role}
- Skills: {skills}
- Question Number: {mcq_current}

Based on the question number, focus on:
- Question 1: Problem-solving preferences 
  (Analytical/data-driven vs Strategic/business vs Technical/implementation vs Operational/process optimization)

- Question 2: Industry preference 
  (2 industries most relevant to {role}, 1 alternative industry, 1 "Other" option)

- Question 3: Case complexity preference 
  (Structured problems with clear metrics vs Open-ended exploratory analysis vs Mixed approach with ambiguity vs Real-time decision making under uncertainty)
  **Ensure this question is completely different from Question 1. 
  Do NOT ask about problem-solving style again. 
  Focus strictly on the level of complexity or ambiguity the candidate prefers.**

Requirements:
- Make the question highly relevant to the role and skills.
- Provide exactly 4 options (A, B, C, D).
- Question {mcq_current} must assess the corresponding focus area above without repeating or rephrasing another question.

Return JSON format:
{{
  "question": "...",
  "options": [
    {{"letter": "A", "text": "..."}},
    {{"letter": "B", "text": "..."}},
    {{"letter": "C", "text": "..."}},
    {{"letter": "D", "text": "..."}}
  ]
}}
"""


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

    # ========== CASE GENERATION ==========
    
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
  }}
}}
"""

    # ========== UNDERSTANDING PHASE ==========
    
    @staticmethod
    def generate_understanding_followup(company_name: str, situation: str, problem: str, candidate_response: str, question_number: int, max_questions: int = 3, last_question: str = "") -> str:
        """Generate targeted follow-up focused on specific probe area."""
        
        probes = {
            1: "initial assumptions and analysis approach",
            2: "data requirements and validation strategy", 
            3: "implementation plan and key challenges"
        }
        
        current_probe = probes.get(question_number, probes[1])
        
        return f"""Generate ONE follow-up question for {company_name} case interview (Question {question_number}/{max_questions}).

    CASE CONTEXT:
    Company: {company_name}
    Problem: {problem[:300]}
    Situation: {situation[:300]}

    CONVERSATION:
    Last Question: "{last_question[:200]}"
    Their Response: "{candidate_response[:400]}"

    PROBE FOCUS: {current_probe}

    TASK: Generate ONE question (25-40 words) that:
    1. Probes their {current_probe} specifically for {company_name}
    2. References the case details (not generic)
    3. If they asked a question → answer briefly first, then probe
    4. If they're confused → give 1-2 sentence hint, then probe
    5. If they gave analysis → probe deeper on {current_probe}

    FORMAT: Plain text, conversational, 25-40 words, ONE question only

    EXAMPLES:
    ✅ "For {company_name}'s readmission challenge, what assumptions would you make about which patient factors most influence 30-day readmission risk?"
    ✅ "Given {company_name}'s EHR and claims data, what specific metrics would you prioritize to validate your predictive model's accuracy?"
    ✅ "How would you implement this solution for {company_name}, and what's the biggest technical challenge you'd anticipate?"

    Generate question focused on {current_probe} for {company_name}:"""

    # ========== APPROACH PHASE ==========
    
    @staticmethod
    def generate_first_approach_question(company_name: str, problem: str, role: str, is_technical: bool) -> str:
        """Generate concise first question requesting structured approach - STRICTLY case-focused."""
        industry_context = CaseInterviewPrompts.get_industry_context(role)
        frameworks_list = ', '.join(industry_context['frameworks'][:3])
        
        base_prompt = f"""📊 **Approach Phase - Solution Framework**

Now that we understand **{company_name}'s** challenge, outline your **solution approach for this specific case**.

**Problem:**
{problem[:300]}

**⚠️ REQUIREMENTS:**
- Minimum 500 words
- **Every point must be specific to {company_name}** - mention them throughout
- Customize frameworks to this exact situation (no generic templates)
- If unclear on any detail, **ask first**

**Your Approach for {company_name.upper()}:**

**1. Framework & Structure**
   - How will you solve **{company_name}'s** problem? (You may adapt: {frameworks_list})
   - What are the 3-4 major steps **for this case**?
   - What key areas need investigation **specifically here**?

"""
        
        if is_technical:
            base_prompt += f"""**2. Technical Approach**
   - What specific algorithms/models fit **{company_name}'s** problem?
   - What data does **{company_name}** need? How will you process it?
   - Technical architecture **for this case** (use CODE tab for pseudocode if needed)

**3. Execution Plan**
   - Implementation steps **for {company_name}**
   - Key milestones and timeline **in this case**
   - Biggest challenges **for {company_name}** and how you'd address them
"""
        else:
            base_prompt += f"""**2. Analysis Method**
   - How will you analyze **{company_name}'s** situation?
   - What data/insights do you need **for this case**?
   - How will you prioritize **given {company_name}'s** constraints?

**3. Execution Plan**
   - Implementation steps **for {company_name}**
   - Key milestones **in this case**
   - Biggest challenges **for {company_name}** and mitigation
"""
        
        base_prompt += f"\n\n✅ **Remember:** 500+ words, ALL specific to **{company_name}**. No generic frameworks!\n💬 **Need clarification?** Ask before starting."
        return base_prompt
    
    @staticmethod
    def generate_approach_followup(company_name: str, problem: str, candidate_response: str, question_number: int, is_technical: bool, last_question: str = "") -> str:
        """Generate approach follow-up focused on specific probe area."""
        
        probes = {
            1: "framework structure and approach logic",
            2: "data/validation strategy" if is_technical else "analysis methodology and prioritization",
            3: "implementation details and risk mitigation",
            4: "timeline, resources, and success metrics"
        }
        
        current_focus = probes.get(question_number, "implementation strategy")
        
        return f"""Generate ONE follow-up question for {company_name} approach phase (Q{question_number}/4).

    CASE PROBLEM: {problem[:300]}

    CONVERSATION:
    Last Q: "{last_question[:150]}"
    Response: "{candidate_response[:500]}"

    PROBE FOCUS: {current_focus}

    TASK: Generate ONE question (30-50 words) that:
    1. Probes {current_focus} specifically for {company_name}
    2. References case details (not generic)
    3. Pushes for concrete, case-specific details
    4. If generic response → ask "How specifically for {company_name}?"
    5. If strong response → probe deeper on one specific element

    {'TECHNICAL FOCUS: Algorithms, data pipelines, architecture, metrics for THIS case' if is_technical else 'BUSINESS FOCUS: Framework customization, prioritization, stakeholder management, ROI for THIS case'}

    FORMAT: Plain text, 30-50 words, ONE question, must mention {company_name}

    EXAMPLES:
    ✅ "You mentioned collaborative filtering. How would you validate that works for {company_name}'s sparse data, and what's your fallback if accuracy drops below 80%?"
    ✅ "How would you prioritize which customer segments {company_name} analyzes first, given their 6-month timeline and limited data quality?"
    ✅ "What specific technical architecture would you build for {company_name}'s scale, and how would you handle their real-time processing requirements?"

    Generate question probing {current_focus} for {company_name}:"""

    # ========== EVALUATION PHASE ==========
    
    @staticmethod
    def evaluate_phase_performance(phase_name: str, conversation_pairs: list, case_study: dict, is_technical: bool) -> str:
        """Evaluate phase performance with STRICT quality assessment - analyzes Q&A alignment."""
        
        technical_focus = """
- Technical Depth (CRITICAL): Specific algorithms, methods, tools mentioned? Or just generic buzzwords?
- Data Thinking: Clear data pipeline, preprocessing, validation strategy? Or vague mentions?
- Quantitative Rigor: Actual metrics, formulas, statistical reasoning? Or hand-waving?
- Implementation Detail: Architecture diagrams, pseudocode, tech stack choices? Or surface-level?
""" if is_technical else """
- Business Judgment: Strategic thinking with trade-offs, ROI, priorities? Or basic statements?
- Stakeholder Awareness: Named specific stakeholders with impact analysis? Or generic mentions?
- Commercial Awareness: Market dynamics, competitive landscape, revenue impact? Or missing?
"""

        qa_formatted = ""
        for i, pair in enumerate(conversation_pairs, 1):
            qa_formatted += f"""
**Exchange {i}:**
INTERVIEWER: "{pair['question'][:250]}"
CANDIDATE: "{pair['response'][:400]}"
"""
        
        return f"""You are a STRICT evaluator for {phase_name} phase. Grade based on QUALITY and RESPONSE ALIGNMENT.

**CASE CONTEXT:**
Company: {case_study.get('company_name', 'NA')}
Problem: {case_study.get('problem_statement', '')}

**CONVERSATION (QUESTION-ANSWER PAIRS):**
{qa_formatted}

**EVALUATION CRITERIA - Be STRICT:**

**1. Response Alignment (CRITICAL - Check Each Exchange):**
   - Did the candidate actually ANSWER the question asked?
   - Or did they deflect, avoid, or copy-paste the question back?
   - Pattern detection:
     * If response is 70%+ similar to question → COPY-PASTE DETECTED → Score 0-1
     * If response contains "no idea", "don't know", "can you explain" → DEFLECTION → Score 1-2
     * If response is under 30 words without specific analysis → TOO BRIEF → Score 2-4
     * If response is off-topic from question → OFF-TOPIC → Score 2-4

**2. Response Quality RED FLAGS - Auto-score reductions:**
   
   **SEVERE Issues (Auto-score 0-2):**
   - Copy-pasted interviewer's question as answer → 0-1 points (CRITICAL FAIL)
   - Repeatedly said "no idea", "don't know", or refused to engage → 0-2 points
   - Asked to skip questions or move on → 0-1 points
   
   **Major Issues (Score 1-4):**
   - Deflected with questions instead of analyzing → 1-3 points
   - Asked for complete explanations instead of attempting analysis → 2-3 points
   - Responses under 30 words with no depth (multiple times) → 2-4 points
   
   **Moderate Issues (Score 3-6):**
   - Generic statements with no case-specific application → 3-5 points
   - Buzzwords without substance → 3-5 points
   - No mention of company/case specifics → 4-6 points
   - Surface-level analysis without depth → 4-6 points

**3. Depth of Analysis:**
   - Did they provide SPECIFIC details tailored to THIS case?
   - Or generic statements that could apply to any case?
   - Did they mention company name and case-specific factors?

**4. Structured Thinking:**
   - Clear framework with logical flow?
   - Or scattered, unorganized thoughts?
   - Did they break down the problem systematically?

**5. Case-Specificity (CRITICAL FOR HIGH SCORES):**
   - Every point anchored to {case_study.get('company_name', 'the company')}?
   - Or generic advice that ignores case context?
   - Did they customize frameworks to THIS situation?

{technical_focus}

**SCORING GUIDE - BE STRICT:**
- 9-10 EXCEPTIONAL: Deep, specific, insightful, perfectly case-customized, ANSWERED ALL QUESTIONS
- 7-8 STRONG: Good analysis with specific details, answered questions directly
- 5-6 COMPETENT: Basic understanding but lacks depth OR missed some question alignment
- 3-4 DEVELOPING: Surface-level, generic, minimal case connection, poor question alignment
- 1-2 NEEDS IMPROVEMENT: Deflection, copy-paste, or severely lacking
- 0-1 CRITICAL FAIL: Copy-pasted questions, refused to answer, completely off-topic

**DETECTION METHODOLOGY:**
For each exchange, check:
1. Response length vs question length (if similar → possible copy-paste)
2. Word overlap between question and response (>70% → copy-paste)
3. Deflection keywords present in response
4. Whether response actually addresses what was asked

**IMPORTANT:**
- Just answering questions ≠ high score
- Must demonstrate QUALITY thinking specific to THIS case
- Generic frameworks without customization = max 5-6/10
- Copy-paste or deflection = auto 0-2/10

Return ONLY valid JSON:
{{
    "score": 5.5,
    "alignment_issues": [
        {{
            "exchange_number": 1,
            "issue_type": "copy-paste|deflection|off-topic|too-brief|none",
            "severity": "critical|major|moderate|minor",
            "evidence": "Exact evidence from response"
        }}
    ],
    "strengths": ["Specific strength with example"],
    "weaknesses": ["Specific gap with example"],
    "key_observations": ["Evidence-based observation 1", "observation 2"],
    "candidate_key_responses": ["excerpt 1", "excerpt 2"],
    "case_specificity_score": 4.0,
    "depth_score": 5.0,
    "response_quality_score": 3.0,
    "overall_comment": "Detailed assessment including alignment issues..."
}}
"""

    @staticmethod
    def generate_final_evaluation(conversation: list, understanding_eval: dict, approach_eval: dict, case_study: dict, domain: str, role: str, is_technical: bool) -> str:
        """Generate comprehensive final evaluation with STRICT dimension scoring."""
        
        return f"""Generate a comprehensive, STRICT final evaluation. High scores require exceptional, case-specific work.

**CASE STUDY:**
Company: {case_study.get('company_name', 'N/A')}
Problem: {case_study.get('problem_statement', '')}

**CANDIDATE PROFILE:**
- Role: {role}
- Domain: {domain}
- Type: {'Technical' if is_technical else 'Non-Technical'}

**PHASE EVALUATIONS:**
Understanding Phase: {understanding_eval}
Approach Phase: {approach_eval}

**ALL CANDIDATE RESPONSES:**
{conversation[-15:]}

**CRITICAL EVALUATION RULES:**
1. **Case-Specificity is MANDATORY for high scores**
   - Must mention company name throughout
   - Must customize solutions to THIS case
   - Generic advice = max 6/10

2. **Depth Over Breadth**
   - Specific examples, metrics, methods required
   - Buzzwords without substance = low scores
   - "We should use ML" < "Use Random Forest for tabular data with XGBoost for comparison"

3. **Dimension Scoring** (Be STRICT):
   - 9-10: Exceptional, industry-leading quality
   - 7-8: Strong professional-level work
   - 5-6: Adequate but lacks depth
   - 3-4: Weak, generic, or surface-level
   - 1-2: Poor quality or off-topic

4. **Performance Levels**:
   - Outstanding (9-10): Rare - exceptional case-specific insights
   - Strong (7-8): Good professional work with depth
   - Competent (5-6): Basic but lacks sophistication
   - Developing (3-4): Surface-level understanding
   - Needs Improvement (1-2): Significant gaps

**DIMENSION DEFINITIONS:**

1. **Domain Expertise & Technical Skills** (Weight: 30%):
   - Demonstrated specific knowledge of {domain}?
   - Used appropriate methods/frameworks for {role}?
   - Showed depth beyond surface-level understanding?

2. **Problem-Solving & Critical Thinking** (Weight: 25%):
   - Identified root causes specific to THIS case?
   - Proposed logical, case-tailored solutions?
   - Considered trade-offs and alternatives?

3. **Communication & Collaboration** (Weight: 20%):
   - Clear, structured explanations?
   - Directly answered questions?
   - Stakeholder-aware communication?

4. **Adaptability & Creativity** (Weight: 25%):
   - Customized approach to {case_study.get('company_name', 'this case')}?
   - Showed creative problem-solving?
   - Adapted to case constraints?

Return ONLY valid JSON:
{{
  "overall_score": 6.5,
  "performance_level": "Competent",
  "interview_summary": "3-4 sentence honest assessment...",
  "dimension_scores": [
    {{
      "dimension": "Domain Expertise & Technical Skills",
      "weight": 30,
      "score": 6.5,
      "justification": "Specific evidence-based assessment with examples...",
      "candidate_response_excerpt": "Actual quote from candidate..."
    }},
    {{
      "dimension": "Problem-Solving & Critical Thinking",
      "weight": 25,
      "score": 6.0,
      "justification": "Assessment...",
      "candidate_response_excerpt": "Quote..."
    }},
    {{
      "dimension": "Communication & Collaboration",
      "weight": 20,
      "score": 7.0,
      "justification": "Assessment...",
      "candidate_response_excerpt": "Quote..."
    }},
    {{
      "dimension": "Adaptability & Creativity",
      "weight": 25,
      "score": 5.5,
      "justification": "Assessment...",
      "candidate_response_excerpt": "Quote..."
    }}
  ],
  "key_strengths": ["Specific strength 1", "strength 2"],
  "development_areas": ["Specific area 1 with actionable advice", "area 2"],
  "phase_breakdown": {{
    "understanding": "2-3 sentence assessment with score context",
    "approach": "2-3 sentence assessment with score context"
  }},
  "recommended_next_steps": [
    "Specific, actionable step 1",
    "step 2",
    "step 3",
    "step 4"
  ]
}}

BE HONEST AND STRICT. Just answering questions ≠ high score. Quality matters."""
