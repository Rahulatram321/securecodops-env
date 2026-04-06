from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class IssueType(str, Enum):
    BUG = "BUG"
    SECURITY = "SECURITY"
    PERFORMANCE = "PERFORMANCE"
    LOGIC = "LOGIC"
    MEMORY_LEAK = "MEMORY_LEAK"
    RACE_CONDITION = "RACE_CONDITION"

class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ActionType(str, Enum):
    IDENTIFY_ISSUE = "IDENTIFY_ISSUE"
    REQUEST_FILE = "REQUEST_FILE"
    ASK_QUESTION = "ASK_QUESTION"
    FORM_HYPOTHESIS = "FORM_HYPOTHESIS"
    NARROW_DOWN = "NARROW_DOWN"
    PROPOSE_FIX = "PROPOSE_FIX"

class Phase(str, Enum):
    INIT = "INIT"
    CONTEXT_FETCH = "CONTEXT_FETCH"
    ROOT_CAUSE = "ROOT_CAUSE"
    FINAL = "FINAL"

class Observation(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    task_id: str
    step_count: int = 0
    max_steps: int = 10
    code_snippet: Optional[str] = None
    language: Optional[str] = None
    context: Optional[str] = None
    logs: Optional[str] = None
    stack_trace: Optional[str] = None
    available_files: Optional[List[str]] = None
    revealed_files: Dict[str, str] = Field(default_factory=dict)
    current_phase: Optional[Phase] = None
    hints_used: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Action(BaseModel):
    action_type: ActionType
    line_numbers: Optional[List[int]] = None
    issue_type: Optional[IssueType] = None
    severity: Optional[Severity] = None
    suggested_fix: Optional[str] = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    file_name: Optional[str] = None
    question: Optional[str] = None
    hypothesis: Optional[str] = None
    explanation: Optional[str] = None
    test_case: Optional[str] = None

class RewardInfo(BaseModel):
    total_reward: float = Field(ge=0.0, le=1.0)
    line_detection_score: float = 0.0
    issue_classification_score: float = 0.0
    fix_quality_score: float = 0.0
    explanation_quality_score: float = 0.0
    investigation_efficiency_score: float = 0.0
    false_positive_penalty: float = 0.0
    irrelevant_request_penalty: float = 0.0
    wrong_severity_penalty: float = 0.0
    breakdown: Dict[str, float] = Field(default_factory=dict)
    feedback: str = ""

class StepResult(BaseModel):
    observation: Observation
    reward: float = Field(ge=0.0, le=1.0)
    done: bool
    info: RewardInfo

class EpisodeStep(BaseModel):
    step_number: int
    action: Action
    reward: float
    observation: Observation

class Episode(BaseModel):
    episode_id: str
    task_id: str
    steps: List[EpisodeStep] = Field(default_factory=list)
    total_reward: float = 0.0
    is_complete: bool = False
    final_score: Optional[float] = None
    ground_truth: Dict[str, Any] = Field(default_factory=dict)
    missed_issues: List[str] = Field(default_factory=list)
    false_positives: List[str] = Field(default_factory=list)
    reasoning_gap: Optional[str] = None
