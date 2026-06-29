from dataclasses import dataclass
from typing import List, Dict

@dataclass
class Conflict:
    agent_a: str
    agent_b: str
    topic: str
    severity: str
    agent_a_position: str
    agent_b_position: str

@dataclass
class CalibrationScore:
    agent: str
    round1_confidence: int
    round2_confidence: int
    delta: int
    verdict_changed: bool
    round1_verdict: str
    round2_verdict: str

def detect_conflicts(round1: list, round2: list) -> list:
    conflicts = []
    
    r1map = {a.get("agent"): a for a in round1}
    
    for agent_r2 in round2:
        name = agent_r2.get("agent", "")
        for disagreement in agent_r2.get("disagreements", []):
            other = disagreement.get("with_agent", "")
            reason = disagreement.get("reason", "")
            point = disagreement.get("point", "")
            
            severity = classify_conflict_severity(
                reason,
                r1map.get(name, {}),
                r1map.get(other, {})
            )
            
            conflict = Conflict(
                agent_a=name,
                agent_b=other,
                topic=point,
                severity=severity,
                agent_a_position=reason,
                agent_b_position=get_counterposition(other, name, round2)
            )
            conflicts.append(conflict.__dict__)
    
    return conflicts

def classify_conflict_severity(reason: str, agent_a_data: dict, agent_b_data: dict) -> str:
    reason_lower = reason.lower()
    
    critical_keywords = ["critical", "severe", "security", "injection", "vulnerability", "exploit"]
    high_keywords = ["high", "performance", "n+1", "complexity", "blocking"]
    
    a_verdict = agent_a_data.get("verdict", "APPROVE")
    b_verdict = agent_b_data.get("verdict", "APPROVE")
    
    if a_verdict != b_verdict and (a_verdict == "BLOCK" or b_verdict == "BLOCK"):
        return "HIGH"
    
    if any(kw in reason_lower for kw in critical_keywords):
        return "CRITICAL"
    
    if any(kw in reason_lower for kw in high_keywords):
        return "HIGH"
    
    return "MEDIUM"

def get_counterposition(agent_name: str, disagreed_with: str, round2: list) -> str:
    for agent in round2:
        if agent.get("agent") == agent_name:
            for d in agent.get("disagreements", []):
                if d.get("with_agent") == disagreed_with:
                    return d.get("reason", "")
            for a in agent.get("agreements", []):
                if a.get("with_agent") == disagreed_with:
                    return f"Actually agrees: {a.get('reason', '')}"
    return "No explicit counter-position"

def calculate_calibration(round1: list, round2: list) -> list:
    calibrations = []
    
    r1map = {a.get("agent"): a for a in round1}
    
    for agent_r2 in round2:
        name = agent_r2.get("agent", "")
        r1 = r1map.get(name, {})
        
        r1_conf = r1.get("confidence", 50)
        r2_conf = agent_r2.get("updated_confidence", 50)
        r1_verdict = r1.get("verdict", "APPROVE")
        r2_verdict = agent_r2.get("updated_verdict", "APPROVE")
        
        cal = CalibrationScore(
            agent=name,
            round1_confidence=r1_conf,
            round2_confidence=r2_conf,
            delta=r2_conf - r1_conf,
            verdict_changed=r1_verdict != r2_verdict,
            round1_verdict=r1_verdict,
            round2_verdict=r2_verdict
        )
        calibrations.append(cal.__dict__)
    
    return calibrations

def debate_impact_score(conflicts: list, calibrations: list) -> dict:
    total_delta = sum(abs(c["delta"]) for c in calibrations)
    avg_delta = total_delta / len(calibrations) if calibrations else 0
    
    verdict_changes = sum(1 for c in calibrations if c["verdict_changed"])
    
    critical_conflicts = sum(1 for c in conflicts if c["severity"] == "CRITICAL")
    high_conflicts = sum(1 for c in conflicts if c["severity"] == "HIGH")
    
    impact = (
        (avg_delta * 0.4) +
        (verdict_changes * 20) +
        (critical_conflicts * 15) +
        (high_conflicts * 8)
    )
    
    return {
        "score": round(min(impact, 100), 1),
        "avg_confidence_delta": round(avg_delta, 1),
        "verdict_changes": verdict_changes,
        "critical_conflicts": critical_conflicts,
        "high_conflicts": high_conflicts,
        "interpretation": interpret_impact(impact)
    }

def interpret_impact(score: float) -> str:
    if score >= 60:
        return "High debate impact — agents significantly influenced each other"
    elif score >= 30:
        return "Moderate debate impact — some positions shifted through discussion"
    else:
        return "Low debate impact — agents largely maintained original positions"