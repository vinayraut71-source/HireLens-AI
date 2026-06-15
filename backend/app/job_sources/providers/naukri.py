from app.job_sources.providers.base import BaseJobProvider

class NaukriProvider(BaseJobProvider):
    async def fetch_jobs(self) -> list[dict]:
        return [
            {
                "external_job_id": "nk-201",
                "title": "Python FastAPI Backend Developer",
                "company": "Google Inc.",
                "description": "Build high-performance async backend APIs using Python and FastAPI.",
                "location": "Work From Home",
                "source_url": "https://www.naukri.com/job/nk-201",
                "salary_min": 120000,
                "salary_max": 160000,
                "required_skills": "Python, FastAPI, SQL",
                "remote_type": "remote",
                "employment_type": "full-time"
            },
            {
                "external_job_id": "nk-202",
                "title": "React Developer",
                "company": "Facebook Corp.",
                "description": "Develop modern frontend user interfaces with React.",
                "location": "Bangalore",
                "source_url": "https://www.naukri.com/job/nk-202",
                "salary_min": 80000,
                "salary_max": 120000,
                "required_skills": "React, JavaScript, CSS",
                "remote_type": "onsite",
                "employment_type": "FT"
            }
        ]
