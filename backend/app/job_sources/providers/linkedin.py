from app.job_sources.providers.base import BaseJobProvider

class LinkedInProvider(BaseJobProvider):
    async def fetch_jobs(self) -> list[dict]:
        return [
            {
                "external_job_id": "li-101",
                "title": "Python FastAPI Backend Developer",
                "company": "Google LLC",
                "description": "Build high-performance async backend APIs using Python and FastAPI.",
                "location": "Remote",
                "source_url": "https://www.linkedin.com/jobs/view/li-101",
                "salary_min": 120000,
                "salary_max": 160000,
                "required_skills": "Python, FastAPI, SQL",
                "remote_type": "remote",
                "employment_type": "full-time"
            },
            {
                "external_job_id": "li-102",
                "title": "Data Analyst",
                "company": "Netflix Inc.",
                "description": "Analyze user stream data and build dashboards.",
                "location": "Los Angeles, CA",
                "source_url": "https://www.linkedin.com/jobs/view/li-102",
                "salary_min": 95000,
                "salary_max": 130000,
                "required_skills": "Python, SQL, Tableau",
                "remote_type": "hybrid",
                "employment_type": "FT"
            }
        ]
