from app.job_sources.providers.base import BaseJobProvider

class FounditProvider(BaseJobProvider):
    async def fetch_jobs(self) -> list[dict]:
        return [
            {
                "external_job_id": "fi-401",
                "title": "Product Manager",
                "company": "Apple Corp.",
                "description": "Drive product execution and lifecycle of consumer hardware/software.",
                "location": "Cupertino",
                "source_url": "https://www.foundit.com/job/fi-401",
                "salary_min": 150000,
                "salary_max": 200000,
                "required_skills": "Product Management, Roadmap, Agile",
                "remote_type": "onsite",
                "employment_type": "full-time"
            }
        ]
