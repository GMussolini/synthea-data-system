"""
Search utilities
"""
from schemas.search import AdvancedSearchParams

def calculate_match_score(patient, params: AdvancedSearchParams) -> float:
    """Calculate relevance score for search results"""
    score = 1.0
    matches = 0
    total_criteria = 0
    
    if params.name:
        total_criteria += 1
        if params.name.lower() in patient.name.lower():
            matches += 1
            # Exact match gets higher score
            if params.name.lower() == patient.name.lower():
                score += 0.5
    
    if params.cpf:
        total_criteria += 1
        if params.cpf in patient.cpf:
            matches += 1
            score += 0.3
    
    if params.medical_condition:
        total_criteria += 1
        if patient.medical_conditions:
            for condition in patient.medical_conditions:
                if params.medical_condition.lower() in condition.lower():
                    matches += 1
                    score += 0.2
                    break
    
    if params.medication:
        total_criteria += 1
        if patient.medications:
            for med in patient.medications:
                if params.medication.lower() in med.lower():
                    matches += 1
                    score += 0.1
                    break
    
    if params.allergy:
        total_criteria += 1
        if patient.allergies:
            for allergy in patient.allergies:
                if params.allergy.lower() in allergy.lower():
                    matches += 1
                    score += 0.1
                    break
    
    # Boost score for email match
    if params.email and patient.email:
        if params.email.lower() in patient.email.lower():
            score += 0.2
    
    # Boost score for phone match
    if params.phone and patient.phone:
        if params.phone in patient.phone:
            score += 0.2
    
    if total_criteria > 0:
        score *= (matches / total_criteria)
    
    return min(score, 2.0)  # Cap at 2.0