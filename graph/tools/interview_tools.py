# graph/tools/interview_tools.py - WITH PROPER TOOL DEFINITIONS
from langchain_core.tools import tool

@tool
def clarification_tool(question: str) -> str:
    """Provides clarification on case study terms, concepts, or context when the candidate explicitly asks for it.
    
    Use this tool when the candidate needs:
    - Definition of specific terms
    - Context about the company or industry
    - Clarification of problem constraints
    - More details about stakeholders or objectives
    
    Args:
        question: What the candidate needs clarified
    
    Returns:
        Clarification response
    """
    return f"""**Clarification Provided:**

Based on your question about "{question}", here's additional context:

In this case study, the key points to understand are:
- The problem is focused on predictive modeling and risk assessment
- The business objective is to reduce losses from defaults/readmissions
- Available data includes historical records with relevant features
- The solution should be both accurate and interpretable for stakeholders

**Important considerations:**
- Think about data quality and feature engineering
- Consider both technical model performance and business impact
- Balance false positives vs false negatives based on business costs

Is there a specific aspect of the problem you'd like me to elaborate on?"""

@tool
def data_tool(data_request: str) -> str:
    """Provides additional data, metrics, or statistics from the case study when requested.
    
    Use this tool when the candidate needs:
    - Specific numbers or metrics
    - Historical data trends
    - Quantitative information
    - Performance statistics
    - Dataset characteristics
    
    Args:
        data_request: What specific data the candidate is requesting
    
    Returns:
        Relevant data from the case
    """
    return f"""**Data Provided:**

Regarding your request for "{data_request}", here's relevant information:

**Sample Data Characteristics:**
- Historical dataset: ~50,000 records
- Outcome distribution: 20% positive class (defaults/readmissions)
- Features available: 30+ variables including demographics, financial/clinical metrics, and behavioral indicators
- Time period: Last 3 years of data
- Data quality: 15% missing values on average, some features have up to 30% missingness

**Key Metrics:**
- Current baseline performance (if any existing model): 0.65 AUC
- Business cost: $5,000 average loss per default/readmission
- Volume: 10,000 predictions needed per month

**Note:** Specific values are simplified for this case. Focus on the approach rather than exact calculations."""

@tool
def hint_tool(topic: str) -> str:
    """Provides a strategic hint to help the candidate progress when they're stuck.
    
    Use this tool when the candidate:
    - Is stuck on approach
    - Missing a key perspective
    - Needs guidance on direction
    - Requests help with methodology
    
    Args:
        topic: Area where the candidate needs guidance
    
    Returns:
        A helpful hint
    """
    return f"""**Strategic Hint:**

For "{topic}", consider this framework:

**1. Problem Framing**
- This is a binary classification problem
- Focus on both model metrics (AUC, precision/recall) and business metrics (cost savings)
- Consider the entire ML lifecycle: data → features → model → deployment → monitoring

**2. Key Analytical Steps**
- **Data Exploration:** Understand distributions, correlations, missing patterns
- **Feature Engineering:** Create predictive features from raw data
- **Model Selection:** Balance interpretability vs accuracy (logistic regression vs tree ensembles vs neural nets)
- **Threshold Optimization:** Align predictions with business objectives
- **Validation:** Proper train/test split, consider temporal aspects

**3. Business Considerations**
- What's the cost of a false positive vs false negative?
- How will predictions be used (automated decision vs human review)?
- What are regulatory/compliance requirements?
- How will the model be maintained and updated?

**Recommended Structure:** Define problem → Explore data → Engineer features → Build model → Validate → Deploy → Monitor

Try articulating your approach using this structure!"""
