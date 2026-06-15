from app.job_sources.providers.base import BaseJobProvider

class ShineProvider(BaseJobProvider):
    async def fetch_jobs(self) -> list[dict]:
        return [
            {
                "external_job_id": "sh-1201",
                "title": "Business Development Executive",
                "company": "EduStar Inc.",
                "description": "Call prospects and showcase online educational curriculum.",
                "location": "Hyderabad",
                "source_url": "https://www.shine.com/jobs/sh-1201",
                "salary_min": 400000,
                "salary_max": 600000,
                "required_skills": "Sales, Communication",
                "remote_type": "onsite",
                "employment_type": "Full-time",
                "job_type": "full-time",
                "experience_level": "entry-level"
            }
        ]
