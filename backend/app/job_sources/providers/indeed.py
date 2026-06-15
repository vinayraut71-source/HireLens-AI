from app.job_sources.providers.base import BaseJobProvider

class IndeedProvider(BaseJobProvider):
    async def fetch_jobs(self) -> list[dict]:
        return [
            {
                "external_job_id": "ind-301",
                "title": "Senior Python FastAPI Backend Developer",
                "company": "Google",
                "description": "Build high-performance async backend APIs using Python and FastAPI.",
                "location": "Remote",
                "source_url": "https://www.indeed.com/viewjob/ind-301",
                "salary_min": 130000,
                "salary_max": 185000,
                "required_skills": "Python, FastAPI, SQL, Docker",
                "remote_type": "remote",
                "employment_type": "full-time"
            },
            {
                "external_job_id": "ind-302",
                "title": "Front End Engineer",
                "company": "Amazon",
                "description": "Build responsive customer-facing shopping apps.",
                "location": "Seattle",
                "source_url": "https://www.indeed.com/viewjob/ind-302",
                "salary_min": 110000,
                "salary_max": 150000,
                "required_skills": "JavaScript, React, HTML",
                "remote_type": "onsite",
                "employment_type": "full-time"
            }
        ]
