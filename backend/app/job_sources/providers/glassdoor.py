from app.job_sources.providers.base import BaseJobProvider

class GlassdoorProvider(BaseJobProvider):
    async def fetch_jobs(self) -> list[dict]:
        return [
            {
                "external_job_id": "gd-1401",
                "title": "Data Scientist",
                "company": "Meta Platforms Inc.",
                "description": "Formulate predictive algorithms for recommendations.",
                "location": "Menlo Park, CA",
                "source_url": "https://www.glassdoor.com/job/gd-1401",
                "salary_min": 160000,
                "salary_max": 220000,
                "required_skills": "Python, R, Machine Learning",
                "remote_type": "hybrid",
                "employment_type": "Full-time",
                "job_type": "full-time",
                "experience_level": "senior"
            }
        ]
