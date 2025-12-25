"""
Causal context to enrich LLM prompts.
Encodes domain knowledge about football causes and effects.
"""

CAUSAL_KNOWLEDGE_BASE = """
## Causal knowledge base - Football

### A. Offensive relations

#### A1. Finishing quality
| Observation | Probable cause | Confidence |
|-------------|----------------|------------|
| xG > goals (gap > 1.0) | Finishing under-performance | High |
| xG < goals (gap > 1.0) | Over-performance or luck | High |
| Shots on target / total shots < 30% | Low accuracy | Medium |
| Shots inside box < 40% | Predictable attacks, long shots | Medium |

#### A2. Chance creation
| Observation | Probable cause | Confidence |
|-------------|----------------|------------|
| Possession > 60% but xG < 1.0 | Sterile possession | High |
| Low final third passes | Inefficient midfield | Medium |
| Cross success < 20% | Wingers struggling | Medium |

### B. Defensive relations

#### B1. Goals conceded
| Observation | Probable cause | Confidence |
|-------------|----------------|------------|
| xGA < goals conceded | Individual errors or keeper performance | High |
| Corners conceded > 8 + goal from set piece | Set piece weakness | High |
| Defensive duels lost > 55% | Physical or positioning issue | Medium |

#### B2. Defensive organization
| Observation | Probable cause | Confidence |
|-------------|----------------|------------|
| Opponent shots inside box > 60% | Low block or broken lines | Medium |
| Low interceptions + high fouls | Late defending, forced fouls | Medium |

### C. Context factors

#### C1. Home/away effect
| Context | Average effect |
|---------|----------------|
| Home match (NOT neutral venue) | +12% to +18% win probability |
| Away match (NOT neutral venue) | -12% to -18% win probability |
| Neutral venue (tournaments, international competitions) | No home advantage - ignore is_home flag |

**IMPORTANT**: For matches played on neutral ground (e.g., World Cup, Africa Cup of Nations, Euro finals),
the home/away designation is purely administrative. Check `is_neutral_venue` field - if True,
DO NOT mention or apply home advantage in your analysis, even if `is_home` is True.

#### C2. Fatigue and schedule
| Context | Estimated effect | Confidence |
|---------|------------------|------------|
| 3 matches in 7 days | -5% to -10% performance | Medium |
| 4+ matches in 14 days | -10% to -15% performance | Medium |
| Long travel (>3000km) | -3% to -8% performance | Low |

#### C3. Absences and squad
| Context | Estimated effect |
|---------|------------------|
| Starting goalkeeper absent | Variable, often -5% to -15% |
| Starting center back absent | -5% to -12% defensive stability |
| Creative midfielder absent | -10% to -20% chance creation |
| Star striker absent | -15% to -30% depending on reliance |

### D. Confounders to consider

Always check these confounders before concluding:
1. Opponent strength
2. Home vs away
3. Squad availability
4. Score state (team leading/trailing)
5. Competition context (league vs cup)

### E. Reasoning rules

1. Correlation != causation
2. Look for mechanisms (X causes Y via Z)
3. Quantify uncertainty (High/Medium/Low)
"""


CAUSAL_REASONING_INSTRUCTIONS = """
## Causal reasoning instructions

You are a football analyst. For each analysis, follow this process:

Step 1: OBSERVE
- List raw facts (score, stats, events)
- No interpretation at this stage

Step 2: COMPARE
- Compare to team averages
- Compare to expectations (xG, recent form)
- Note significant gaps (>20% or >1 std)

Step 3: HYPOTHESES
- Generate 2-4 causal hypotheses
- Use the knowledge base provided

Step 4: EVIDENCE
- For each hypothesis, list evidence for and against
- Use only available data

Step 5: CONCLUSION
- Identify most likely causes
- Provide confidence level
- Mention limits of the analysis

Expected response format:

## Causal analysis: [Topic]

### Facts observed
[Factual list]

### Significant gaps
[Comparisons vs expectations]

### Causes identified

**Primary cause**: [Description]
- Mechanism: [How it produces the effect]
- Evidence: [Data supporting it]
- Confidence: [High/Medium/Low]

**Secondary cause** (if applicable): [Description]
...

### Limits
[What cannot be concluded with certainty]
"""


def get_causal_context() -> str:
    """Return the full causal context for prompt injection."""
    return f"{CAUSAL_KNOWLEDGE_BASE}\n\n{CAUSAL_REASONING_INSTRUCTIONS}"
