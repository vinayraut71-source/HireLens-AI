from app.job_sources.providers.base import BaseJobProvider

class InstahyreProvider(BaseJobProvider):
    async def fetch_jobs(self) -> list[dict]:
        return [
            {
                "external_job_id": "ih-1001",
                "title": "Machine Learning Engineer",
                "company": "DeepAI",
                "description": "Develop and deploy deep learning models using PyTorch.",
                "location": "Bengaluru",
                "source_url": "https://www.instahyre.com/job-1001",
                "salary_min": 1500000,
                "salary_max": 2400000,
                "required_skills": "PyTorch, Python, NLP",
                "remote_type": "onsite",
                "employment_type": "Full-time",
                "job_type": "full-time",
                "experience_level": "mid-level"
            }
        ]
