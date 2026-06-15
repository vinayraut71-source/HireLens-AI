from app.job_sources.providers.base import BaseJobProvider

class ApnaProvider(BaseJobProvider):
    async def fetch_jobs(self) -> list[dict]:
        return [
            {
                "external_job_id": "ap-801",
                "title": "Delivery Associate",
                "company": "FastCart Logistics",
                "description": "Deliver packages around South Delhi zone.",
                "location": "New Delhi",
                "source_url": "https://apna.co/job/ap-801",
                "salary_min": 20000,
                "salary_max": 30000,
                "required_skills": "Driving, Navigation",
                "remote_type": "onsite",
                "employment_type": "Full-time",
                "job_type": "full-time",
                "experience_level": "entry-level"
            }
        ]
