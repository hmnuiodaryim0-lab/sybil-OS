"""
Career Allocation Engine - Core Algorithm for Sybil-OS
Matches cognitive profiles to optimal job assignments using vector similarity.
"""

from typing import List, Dict, Optional, Tuple
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


# Define job role templates with ideal cognitive profiles
JOB_TEMPLATES = {
    "Software Engineer": {
        "logic_depth": 0.9,
        "empathy_level": 0.5,
        "stress_resilience": 0.7,
        "creative_entropy": 0.7,
        "social_cohesion": 0.6
    },
    "Product Manager": {
        "logic_depth": 0.8,
        "empathy_level": 0.8,
        "stress_resilience": 0.7,
        "creative_entropy": 0.6,
        "social_cohesion": 0.9
    },
    "Data Scientist": {
        "logic_depth": 0.95,
        "empathy_level": 0.4,
        "stress_resilience": 0.6,
        "creative_entropy": 0.8,
        "social_cohesion": 0.4
    },
    "Designer": {
        "logic_depth": 0.6,
        "empathy_level": 0.7,
        "stress_resilience": 0.5,
        "creative_entropy": 0.95,
        "social_cohesion": 0.6
    },
    "Customer Success": {
        "logic_depth": 0.5,
        "empathy_level": 0.95,
        "stress_resilience": 0.8,
        "creative_entropy": 0.4,
        "social_cohesion": 0.9
    },
    "Security Engineer": {
        "logic_depth": 0.9,
        "empathy_level": 0.3,
        "stress_resilience": 0.8,
        "creative_entropy": 0.5,
        "social_cohesion": 0.4
    },
    "Researcher": {
        "logic_depth": 0.95,
        "empathy_level": 0.5,
        "stress_resilience": 0.6,
        "creative_entropy": 0.9,
        "social_cohesion": 0.3
    }
}


class AllocationEngine:
    """
    Career allocation algorithm using cognitive profile matching.
    """
    
    def __init__(self, job_templates: Optional[Dict] = None):
        self.job_templates = job_templates or JOB_TEMPLATES
        self._build_template_matrix()
    
    def _build_template_matrix(self):
        """Build matrix of job templates for similarity computation."""
        self.template_names = list(self.job_templates.keys())
        self.template_matrix = np.array([
            [
                self.job_templates[job]["logic_depth"],
                self.job_templates[job]["empathy_level"],
                self.job_templates[job]["stress_resilience"],
                self.job_templates[job]["creative_entropy"],
                self.job_templates[job]["social_cohesion"]
            ]
            for job in self.template_names
        ])
    
    def _profile_to_vector(
        self, 
        logic_depth: float,
        empathy_level: float,
        stress_resilience: float,
        creative_entropy: float,
        social_cohesion: float
    ) -> np.ndarray:
        """Convert cognitive profile to feature vector."""
        return np.array([
            logic_depth,
            empathy_level,
            stress_resilience,
            creative_entropy,
            social_cohesion
        ])
    
    def compute_match_scores(
        self,
        logic_depth: float,
        empathy_level: float,
        stress_resilience: float,
        creative_entropy: float,
        social_cohesion: float
    ) -> List[Tuple[str, float]]:
        """
        Compute match scores between a profile and all job templates.
        
        Returns:
            List of (job_title, score) tuples sorted by score descending
        """
        profile_vector = self._profile_to_vector(
            logic_depth, empathy_level, stress_resilience,
            creative_entropy, social_cohesion
        ).reshape(1, -1)
        
        # Compute cosine similarity
        similarities = cosine_similarity(
            profile_vector, 
            self.template_matrix
        )[0]
        
        # Sort by similarity score
        scored_jobs = list(zip(self.template_names, similarities))
        scored_jobs.sort(key=lambda x: x[1], reverse=True)
        
        return scored_jobs
    
    def allocate(
        self,
        logic_depth: float,
        empathy_level: float,
        stress_resilience: float,
        creative_entropy: float,
        social_cohesion: float,
        top_k: int = 3
    ) -> Dict:
        """
        Allocate optimal job based on cognitive profile.
        
        Args:
            top_k: Number of top matches to return
            
        Returns:
            Dictionary with allocation results
        """
        scores = self.compute_match_scores(
            logic_depth, empathy_level, stress_resilience,
            creative_entropy, social_cohesion
        )
        
        primary_job, primary_score = scores[0]
        
        return {
            "primary_assignment": primary_job,
            "confidence_score": float(primary_score),
            "top_matches": [
                {"job": job, "score": float(score)} 
                for job, score in scores[:top_k]
            ],
            "profile_summary": {
                "logic_depth": logic_depth,
                "empathy_level": empathy_level,
                "stress_resilience": stress_resilience,
                "creative_entropy": creative_entropy,
                "social_cohesion": social_cohesion
            }
        }


# Example usage
if __name__ == "__main__":
    engine = AllocationEngine()
    
    # Example: High logic, low empathy, high creativity
    result = engine.allocate(
        logic_depth=0.9,
        empathy_level=0.3,
        stress_resilience=0.7,
        creative_entropy=0.95,
        social_cohesion=0.4
    )
    
    print("=== Allocation Result ===")
    print(f"Primary: {result['primary_assignment']}")
    print(f"Confidence: {result['confidence_score']:.2%}")
    print("\nTop Matches:")
    for match in result['top_matches']:
        print(f"  - {match['job']}: {match['score']:.2%}")
