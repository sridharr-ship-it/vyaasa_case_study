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

    # ========== UNDERSTANDING PHASE - UNIFIED FUNCTION ==========  

    @staticmethod
    def generate_understanding_followup(company_name: str, situation: str, problem: str, candidate_response: str, question_number: int, max_questions: int = 3, last_question: str = "") -> str:
        """Generate conversational follow-up STRICTLY grounded in case study with smart deflection handling."""
        
        # Define what to probe at each stage
        probe_focus = {
            1: "their initial assumptions and how they'd start analyzing THIS specific problem",
            2: "what data or metrics they'd need for THIS case and how they'd validate their approach",
            3: "implementation strategy for THIS company and potential challenges"
        }
        
        current_probe = probe_focus.get(question_number, probe_focus[1])
        
        # Build context section
        context_section = ""
        if last_question and question_number > 1:
            if "Case Started!" not in last_question and "Share your initial understanding" not in last_question:
                context_section = f"""
    **PREVIOUS QUESTION:**
    "{last_question[:250]}"

    **THEIR RESPONSE:**
    "{candidate_response[:350]}"
    """
        
        return f"""You are conducting question {question_number} of {max_questions} in a case interview for {company_name}.

    **CASE DETAILS:**
    Company: {company_name}
    Situation: {situation[:400]}
    Problem: {problem[:400]}

    {context_section}

    **WHAT THEY JUST SAID:**
    "{candidate_response[:500]}"

    **YOUR TASK:**
    Generate a conversational response (50-80 words) that:
    1. Acknowledges what they said (if they're asking for help)
    2. Provides a brief case-specific hint/example (if needed)
    3. Asks ONE concrete follow-up question

    Output as plain text, conversational and supportive tone.

    **RESPONSE ANALYSIS - DETERMINE TYPE:**

    **TYPE 1: Asking for Clarification/Help (FIRST TIME)**
    Signs: "don't know", "need clarity", "explain", "not sure", "help me", "what does this mean"

    → **Structure (50-70 words):**
      [Acknowledgment] + [Case-specific hint with concrete details] + [Specific question]

    → **Template:**
    "I understand. For {company_name}, [brief hint: mention 2-3 specific data sources, constraints, or context from the case]. Given this context, [specific concrete question about one element]?"

    → **Example:**
    "I understand you need more context. For {company_name}'s situation regarding {problem[:50]}, they have access to [specific data/resources from case]. Considering this, which specific aspect would you prioritize analyzing first to address their challenge?"

    **TYPE 2: Persistent Deflection/Repeated Help Request**
    Signs: Similar request for help after you already gave hints in previous response

    → **Structure (60-80 words):**
      [More specific acknowledgment] + [Very concrete example with options] + [Simple choice question]

    → **Template:**
    "Let me be more specific. For {company_name}, consider these factors related to {problem[:30]}: [Option A - specific detail], [Option B - specific detail], or [Option C - specific detail]. Which would you prioritize first and why?"

    → **Example:**
    "Let me give you more specific options. For {company_name}'s challenge with {problem[:40]}, you could focus on: analyzing existing customer data patterns, investigating technical infrastructure limitations, or assessing market competition dynamics. Which of these would you tackle first?"

    **TYPE 3: Vague/Generic Response**
    Signs: Under 30 words, no case-specific details, could apply to any company

    → **Structure (40-50 words):**
      [Brief acknowledgment] + [Push for case-specificity]

    → **Template:**
    "How would that approach specifically work for {company_name} given specific constraint from case? Walk me through your first concrete step with their actual situation."

    → **Example:**
    "How would that approach specifically help {company_name} address {problem[:50]}? What would be your first concrete action given their constraints mentioned in the case?"

    **TYPE 4: Substantive & Case-Specific Response**
    Signs: 30+ words, mentions company/case details, shows reasoning

    → **Structure (30-40 words):**
      [Quote exact 3-5 words] + [Probe deeper with case context]

    → **Template:**
    "You mentioned '[exact quote]'. How would you validate that approach for {company_name} given specific case constraint?"

    → **Example:**
    "You mentioned 'customer segmentation analysis'. How would you validate those segments specifically for {company_name}'s situation with relevant case detail?"

    **TYPE 5: Off-topic/Irrelevant**
    Signs: Discussing something not in the case, inventing details

    → **Structure (35-45 words):**
      [Gentle redirect] + [Ground in case] + [Specific question]

    → **Template:**
    "Coming back to {company_name}'s core challenge with {problem[:40]}, how would you [specific action related to actual case]?"

    **CRITICAL RULES:**

    1. **Always be helpful when they're struggling:**
      - Don't just rephrase the same question
      - Give actual hints/examples from the case details
      - Make questions more concrete and specific
      - Provide 2-3 concrete options if they're really stuck

    2. **Stay STRICTLY grounded in the case:**
      - Every hint must reference {company_name}, {situation}, or {problem}
      - Every example must come from the actual case details provided
      - Every question must be case-specific
      - Never invent details not in the case

    3. **Progressive help strategy:**
      - First deflection: Brief hint + open question
      - Repeated deflection: Detailed hint + choice-based question
      - Never just keep asking without helping

    4. **Output format:**
      - Plain text only, no markdown, no formatting
      - Conversational and supportive tone (you're coaching, not testing)
      - 50-80 words for deflection responses (includes hint)
      - 30-50 words for good responses (just probe deeper)
      - No quotation marks around entire output

    5. **Verification before output:**
      ✓ Does it mention {company_name} or specific case element?
      ✓ Is it tied to {situation} or {problem}?
      ✓ Could this ONLY be asked about THIS case (not generic)?
      ✓ Did I provide help if they asked for it?

    **GOOD EXAMPLES:**

    **For first deflection:**
    ✅ "I understand. For {company_name}, the situation involves {situation[:60]}. They're dealing with {problem[:60]}. Given these specifics, what would be your first step in analyzing this challenge?"

    **For repeated deflection:**
    ✅ "Let me be more specific. For {company_name}'s challenge with {problem[:50]}, you could analyze: their existing customer behavior data, assess technical infrastructure gaps, or review competitive positioning. Which would you prioritize first and why?"

    **For vague response:**
    ✅ "How would that specifically help {company_name} with {problem[:50]}? Walk me through your first concrete action given their constraints."

    **For good response:**
    ✅ "You mentioned 'data quality issues'. How would you validate data quality specifically for {company_name}'s situation with relevant detail from case?"

    **BAD EXAMPLES:**

    ❌ "What would you analyze first?" (No company name, not case-specific, no help when they're struggling)
    ❌ "Think about the data." (Too generic, no case reference)
    ❌ "I already asked this. Please answer." (Dismissive, not helpful)
    ❌ "You mentioned customer analysis..." (When they didn't - fabricating what they said)

    Now generate your response (plain text, case-grounded, helpful, 50-80 words if deflection, 30-50 words if good response):"""


    # ========== APPROACH PHASE - UNIFIED FUNCTION ==========
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
        """Generate approach phase follow-up - stay case-grounded and probe depth."""
        
        # Define focus areas for each follow-up
        probe_areas = {
            1: "initial approach and framework structure",
            2: "data requirements and validation strategy" if is_technical else "analysis methodology and prioritization",
            3: "implementation details and risk mitigation",
            4: "timeline, resources, and success metrics"
        }
        
        current_focus = probe_areas.get(question_number, "implementation strategy")
        
        # Build context if we have previous question
        context_section = ""
        if last_question and question_number > 1:
            context_section = f"""
    **PREVIOUS QUESTION:**
    "{last_question[:200]}"

    **THEIR RESPONSE:**
    "{candidate_response[:400]}"
    """
        
        return f"""You are conducting approach question {question_number} of 4 for {company_name}.

    **CASE PROBLEM:**
    {problem[:400]}

    {context_section}

    **WHAT THEY JUST SAID:**
    "{candidate_response[:600]}"

    **YOUR TASK:**
    Generate ONE follow-up question (40-60 words) that probes their {current_focus} **specifically for {company_name}**.

    **CRITICAL RULES:**

    1. **STAY STRICTLY CASE-GROUNDED:**
      - Every question must reference {company_name}
      - Reference specific details from the problem statement
      - Push for case-specific details, not generic answers
      - If they gave generic advice, ask: "How does that specifically apply to {company_name}?"

    2. **DETECT RESPONSE QUALITY:**

      **If Generic/Vague (no company mention, could apply to any case):**
      → Push for specificity
      → "How would that specifically work for {company_name} given [constraint from case]? What's your first concrete step?"
      
      **If Missing Key Details:**
      → Probe the gap
      → "You mentioned [topic]. How would you specifically [action] for {company_name} considering [case detail]?"
      
      **If Strong & Case-Specific:**
      → Go deeper on one element
      → "You mentioned '[exact 3-5 word quote]'. How would you validate/implement that for {company_name}?"
      
      **If Off-topic:**
      → Redirect firmly
      → "Coming back to {company_name}'s challenge with [problem aspect], how would you [specific action]?"

    3. **TECHNICAL CASES - Probe for:**
      - Specific algorithms/models **for this case**
      - Data pipelines **for {company_name}'s** data
      - Architecture decisions **given this problem**
      - Performance metrics **relevant to this case**

    4. **NON-TECHNICAL CASES - Probe for:**
      - Analysis framework **customized to {company_name}**
      - Prioritization logic **for this situation**
      - Stakeholder management **in this case**
      - ROI/metrics **specific to {company_name}**

    5. **OUTPUT FORMAT:**
      - Plain text, no formatting
      - 40-60 words
      - Direct question only
      - Must mention {company_name} or specific case element

    6. **FORBIDDEN:**
      - ❌ Generic questions without case reference
      - ❌ Accepting generic frameworks without customization
      - ❌ Meta-commentary or explanations
      - ❌ Inventing details not in the case

    **VERIFICATION CHECKLIST:**
    ✓ Does it mention {company_name} or specific case element?
    ✓ Does it push for case-specific details (not generic)?
    ✓ Does it probe depth on {current_focus}?
    ✓ Is it 40-60 words, plain text?

    **GOOD EXAMPLES:**

    For generic response:
    ✅ "You mentioned using a recommendation system. What specific algorithm would fit {company_name}'s data characteristics, and how would you handle their incomplete customer records?"

    For missing details:
    ✅ "How would you prioritize which customer segments {company_name} should analyze first, given their limited data quality and 6-month timeline?"

    For strong response:
    ✅ "You mentioned 'collaborative filtering'. How would you validate that approach works for {company_name}'s sparse data, and what's your fallback strategy?"

    **BAD EXAMPLES:**

    ❌ "What algorithm would you use?" (No company reference, too generic)
    ❌ "Tell me more about your approach." (Vague, no depth)
    ❌ "How would you implement this?" (Not case-specific)

    Now generate your follow-up question (40-60 words, case-grounded, probing {current_focus}):"""


    # ========== EVALUATION PHASE (STRICT QUALITY CHECKS) ==========
    
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

        # Format Q&A pairs for the prompt
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
