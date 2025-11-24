from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class IntentResult:
    intent: str
    entities: Dict[str, Any] = field(default_factory=dict)
    needs_data: bool = True
    confidence: float = 0.0
    reasoning: str = ""


@dataclass
class ToolCallResult:
    name: str
    arguments: Dict[str, Any]
    output: Any = None
    error: Optional[str] = None


@dataclass
class AnalysisResult:
    brief: str
    data_points: List[str] = field(default_factory=list)
    gaps: List[str] = field(default_factory=list)
    safety_notes: List[str] = field(default_factory=list)
