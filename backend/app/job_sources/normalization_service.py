"""
Normalization engine — cleans and standardizes raw job posting values.
Sprint 12: Ingestion layer.
"""
import re

class NormalizationService:
    @staticmethod
    def normalize_company(company: str | None) -> str | None:
        """
        Cleans suffixes from company names to improve deduplication quality.
        Example: Google LLC / Google Inc. -> Google
        """
        if not company:
            return None
        # Remove suffixes like LLC, Inc., Inc, Corp., Corp, Co., Co, Ltd., Ltd, GmbH, etc.
        # Case insensitive regex with word boundaries
        cleaned = re.sub(
            r'\b(llc|inc|corp|co|ltd|gmbh|incorporated|corporation|limited|company)\b\.?', 
            '', 
            company, 
            flags=re.IGNORECASE
        )
        # Clean extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        # Return cleaned or fallback to original stripped if cleaned is empty
        return cleaned if cleaned else company.strip()

    @staticmethod
    def normalize_location(location: str | None) -> str | None:
        """
        Standardizes remote indicators and formats locations consistently.
        Example: Work From Home -> Remote
        """
        if not location:
            return None
        loc_lower = location.lower().strip()
        # Check remote indicators
        remote_indicators = ["remote", "wfh", "work from home", "work-from-home", "anywhere"]
        if any(ind in loc_lower for ind in remote_indicators):
            return "Remote"
        
        # Otherwise capitalize words
        return " ".join(word.capitalize() for word in location.strip().split())

    @staticmethod
    def normalize_employment_type(emp_type: str | None) -> str | None:
        """
        Maps raw employment types to standard formats.
        Example: FT -> Full-time
        """
        if not emp_type:
            return None
        emp_lower = emp_type.lower().strip()
        if "full" in emp_lower or emp_lower == "ft":
            return "Full-time"
        if "part" in emp_lower or emp_lower == "pt":
            return "Part-time"
        if "contract" in emp_lower or "temp" in emp_lower:
            return "Contract"
        if "intern" in emp_lower:
            return "Internship"
        return emp_type.strip()

    @staticmethod
    def normalize_salary(salary_min: int | None, salary_max: int | None) -> tuple[int | None, int | None]:
        """
        Ensures min and max salary values are logical and sorted.
        """
        if salary_min is not None and salary_max is not None and salary_min > salary_max:
            return salary_max, salary_min
        return salary_min, salary_max

    @staticmethod
    def normalize_skills(skills: list[str] | str | None) -> list[str]:
        """
        Splits and standardizes list of skills.
        """
        if not skills:
            return []
        if isinstance(skills, str):
            # Split by comma or semicolon
            skills_list = re.split(r'[,;]', skills)
        else:
            skills_list = skills
        
        normalized = []
        for s in skills_list:
            if isinstance(s, str):
                cleaned = s.strip()
                if cleaned:
                    normalized.append(cleaned)
        return normalized

    @staticmethod
    def normalize_job_type(job_type: str | None) -> str | None:
        """
        Standardizes job/employment types.
        """
        if not job_type:
            return None
        jt_lower = job_type.lower().strip()
        if "full" in jt_lower or jt_lower == "ft":
            return "Full-time"
        if "part" in jt_lower or jt_lower == "pt":
            return "Part-time"
        if "contract" in jt_lower or "temp" in jt_lower:
            return "Contract"
        if "intern" in jt_lower:
            return "Internship"
        return job_type.strip()

    @staticmethod
    def normalize_experience_level(exp_level: str | None) -> str | None:
        """
        Standardizes experience levels.
        """
        if not exp_level:
            return None
        el_lower = exp_level.lower().strip()
        if any(w in el_lower for w in ["entry", "junior", "jr", "fresher", "intern"]):
            return "Entry-level"
        if any(w in el_lower for w in ["mid", "intermediate", "associate"]):
            return "Mid-level"
        if any(w in el_lower for w in ["senior", "sr", "experienced"]):
            return "Senior"
        if any(w in el_lower for w in ["lead", "principal", "manager"]):
            return "Lead"
        if any(w in el_lower for w in ["executive", "director", "vp", "chief", "head"]):
            return "Executive"
        return exp_level.strip()

