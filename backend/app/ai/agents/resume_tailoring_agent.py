import json
import logging
from app.ai.agents.base import BaseAgent
from app.ai.providers.gemini import GeminiClient
from app.resumes.models import ResumeVersion
from app.resumes.service import JobDescriptionAnalyzer, ATSScoringService, ResumeVersionService

logger = logging.getLogger(__name__)


class ResumeTailoringAgent(BaseAgent):
    def __init__(self):
        super().__init__("ResumeTailoringAgent")
        self.gemini_client = GeminiClient()

    async def run(self, resume_version: ResumeVersion, job_description: str, mode: str = "deterministic") -> dict:
        """Runs the agent to analyze the resume and generate suggestions."""
        suggestions = await self.generate_tailoring_suggestions(resume_version, job_description, mode)
        # Fetch original ATS scores
        jd_analysis = self.analyze_resume(resume_version, job_description)
        original_scores = ATSScoringService.score(resume_version, jd_analysis)
        improved_score = self.estimate_improved_ats_score(original_scores, suggestions)
        
        return {
            "original_ats_score": original_scores["ats_score"],
            "tailored_ats_score": improved_score,
            "suggestions": suggestions
        }

    def analyze_resume(self, resume_version: ResumeVersion, job_description: str) -> dict:
        """Runs deterministic job description analysis."""
        return JobDescriptionAnalyzer.analyze(job_description)

    def extract_keywords(self, text: str) -> list[str]:
        """Extracts common keywords from a text block."""
        return JobDescriptionAnalyzer.analyze(text)["keywords"]

    def detect_missing_keywords(self, resume_text: str, jd_keywords: list[str]) -> list[str]:
        """Identifies which job description keywords are missing from the resume."""
        resume_text_lower = resume_text.lower()
        missing = []
        for kw in jd_keywords:
            if kw.lower() not in resume_text_lower:
                missing.append(kw)
        return missing

    async def generate_tailoring_suggestions(self, resume_version: ResumeVersion, job_description: str, mode: str) -> list[dict]:
        """Generates resume tailoring suggestions."""
        if mode == "ai_assisted":
            try:
                prompt = (
                    f"You are an expert technical recruiter and ATS optimization agent.\n"
                    f"Analyze the following resume and job description to suggest section-specific bullet rewrites, "
                    f"quantified achievements, and structural improvement suggestions.\n\n"
                    f"Resume:\n{resume_version.extracted_text or ''}\n\n"
                    f"Job Description:\n{job_description}\n\n"
                    f"Respond ONLY with a valid JSON array of suggestions. Each suggestion must have exactly these keys: "
                    f"'section_name' (allowed: 'summary', 'experience', 'education', 'skills', 'projects', 'certifications'), "
                    f"'suggestion_type' (allowed: 'keyword_addition', 'bullet_rewrite', 'section_improvement', 'skill_recommendation', 'ats_optimization'), "
                    f"'original_content' (text or null), 'suggested_content' (text), 'confidence_score' (float), 'reason' (text explaining why), "
                    f"and 'severity_level' (allowed: 'low', 'medium', 'high', 'critical')."
                )
                system_instruction = "You are a professional ATS Resume Tailoring Agent. Return output strictly as a JSON list."
                response_text = await self.gemini_client.generate_content(prompt, system_instruction)
                
                # Parse the JSON array
                # Strip backticks/markdown if present
                clean_text = response_text.strip()
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
                clean_text = clean_text.strip()

                suggestions = json.loads(clean_text)
                if isinstance(suggestions, list):
                    valid_suggestions = []
                    for s in suggestions:
                        if all(k in s for k in ["section_name", "suggestion_type", "original_content", "suggested_content", "confidence_score", "reason"]):
                            sev = s.get("severity_level")
                            if sev not in ["low", "medium", "high", "critical"]:
                                st = s["suggestion_type"]
                                if st == "skill_recommendation":
                                    sev = "critical"
                                elif st == "ats_optimization":
                                    sev = "high"
                                elif st in ["bullet_rewrite", "section_improvement"]:
                                    sev = "medium"
                                elif st == "keyword_addition":
                                    sev = "low"
                                else:
                                    sev = "medium"
                            s["severity_level"] = sev
                            valid_suggestions.append(s)
                    if valid_suggestions:
                        return valid_suggestions
            except Exception as e:
                logger.error(f"Failed to generate AI tailoring suggestions: {str(e)}", exc_info=True)
                # Fallback to deterministic on failure

        # Deterministic rules fallback
        jd_analysis = self.analyze_resume(resume_version, job_description)
        resume_text = resume_version.extracted_text or ""
        suggestions = []

        # 1. Compare ATS missing keywords
        missing_kws = self.detect_missing_keywords(resume_text, jd_analysis["keywords"])
        for kw in missing_kws[:5]:  # limit to top 5
            suggestions.append({
                "section_name": "skills",
                "suggestion_type": "keyword_addition",
                "original_content": None,
                "suggested_content": f"Add keyword '{kw}' to your skills list or professional summary.",
                "confidence_score": 0.95,
                "reason": f"Keyword '{kw}' appears {job_description.lower().count(kw.lower())} times in the job description but does not appear in your resume.",
                "severity_level": "low"
            })

        # 2. Compare required skills
        resume_skills_set = {s.lower().strip() for s in (resume_version.skills or [])}
        missing_skills = [s for s in jd_analysis["required_skills"] if s.lower() not in resume_skills_set]
        for skill in missing_skills[:5]:
            suggestions.append({
                "section_name": "skills",
                "suggestion_type": "skill_recommendation",
                "original_content": None,
                "suggested_content": f"List required skill '{skill}' in your technical skills section.",
                "confidence_score": 0.90,
                "reason": f"Required skill '{skill}' is specified in the job description but is not listed in your resume skills.",
                "severity_level": "critical"
            })

        # 3. Compare certifications
        jd_certs = jd_analysis["certifications"]
        if jd_certs:
            resume_certs_lower = [c.lower() for c in (resume_version.certifications or [])]
            missing_certs = [cert for cert in jd_certs if cert.lower() not in resume_certs_lower]
            for cert in missing_certs:
                suggestions.append({
                    "section_name": "certifications",
                    "suggestion_type": "ats_optimization",
                    "original_content": None,
                    "suggested_content": f"List your certification: {cert}.",
                    "confidence_score": 0.85,
                    "reason": f"Job requires {cert} certification but no matching certification was found.",
                    "severity_level": "high"
                })

        # 4. Compare education requirements
        jd_edu = jd_analysis["education_requirements"]
        jd_level = ATSScoringService.EDU_LEVELS.get(jd_edu.lower(), 1)
        resume_level = ResumeVersionService._estimate_education_level(resume_version.education or [])
        if resume_level < jd_level:
            suggestions.append({
                "section_name": "education",
                "suggestion_type": "ats_optimization",
                "original_content": None,
                "suggested_content": f"Ensure your academic credentials list the {jd_edu} degree requested by the job description.",
                "confidence_score": 0.80,
                "reason": f"Job requires {jd_edu} degree but only a lower level of education was detected on your resume.",
                "severity_level": "high"
            })

        # 5. Compare experience requirements
        jd_exp_years = jd_analysis["years_of_experience"]
        resume_exp_years = ResumeVersionService._estimate_experience_years(resume_version)
        if resume_exp_years < jd_exp_years:
            suggestions.append({
                "section_name": "experience",
                "suggestion_type": "section_improvement",
                "original_content": None,
                "suggested_content": f"Highlight details of your work history to align with the required {jd_exp_years} years.",
                "confidence_score": 0.80,
                "reason": f"Experience level (~{resume_exp_years} years) is below the required {jd_exp_years} years.",
                "severity_level": "medium"
            })

        # General fallbacks if resume is already perfect
        if not suggestions:
            suggestions.append({
                "section_name": "experience",
                "suggestion_type": "section_improvement",
                "original_content": None,
                "suggested_content": "Quantify achievements in your experience section (e.g. 'Improved efficiency by 20%').",
                "confidence_score": 0.75,
                "reason": "Experience section lacks quantified achievements.",
                "severity_level": "medium"
            })

        return suggestions

    def estimate_improved_ats_score(self, original_scores: dict, suggestions: list[dict]) -> int:
        """Estimates the potential ATS score increase if recommendations are implemented."""
        original_keyword_score = original_scores.get("keyword_score", 0)
        original_skills_score = original_scores.get("skills_score", 0)
        original_experience_score = original_scores.get("experience_score", 0)
        original_education_score = original_scores.get("education_score", 0)

        has_keyword_sug = any(s["suggestion_type"] == "keyword_addition" for s in suggestions)
        has_skills_sug = any(s["suggestion_type"] == "skill_recommendation" for s in suggestions)

        improved_keyword_score = min(100, original_keyword_score + 25) if has_keyword_sug else original_keyword_score
        improved_skills_score = min(100, original_skills_score + 25) if has_skills_sug else original_skills_score

        improved_ats_score = min(100, round(0.3 * improved_keyword_score + 0.3 * improved_skills_score + 0.2 * original_experience_score + 0.2 * original_education_score))
        
        # Ensure it is at least the original score
        return max(original_scores.get("ats_score", 0), improved_ats_score)
