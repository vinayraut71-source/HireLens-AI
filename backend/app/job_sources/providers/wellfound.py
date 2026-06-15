from app.job_sources.providers.base import BaseJobProvider

class WellfoundProvider(BaseJobProvider):
    async def fetch_jobs(self) -> list[dict]:
        return [
            {
                "external_job_id": "wf-501",
                "title": "Full Stack Engineer",
                "company": "OpenAI",
                "description": "Design user interfaces and API microservices for machine learning products.",
                "location": "San Francisco",
                "source_url": "https://www.wellfound.com/jobs/wf-501",
                "salary_min": 140000,
                "salary_max": 220000,
                "required_skills": "Python, TypeScript, React, Docker",
                "remote_type": "hybrid",
                "employment_type": "full-time"
            }
        ]
