from app.job_sources.providers.base import BaseJobProvider

class ArcProvider(BaseJobProvider):
    async def fetch_jobs(self) -> list[dict]:
        return [
            {
                "external_job_id": "arc-1901",
                "title": "React Native Developer",
                "company": "MobileStudio",
                "description": "Develop iOS and Android apps using React Native.",
                "location": "WFH",
                "source_url": "https://arc.dev/jobs/arc-1901",
                "salary_min": 90000,
                "salary_max": 130000,
                "required_skills": "React Native, iOS, Android",
                "remote_type": "remote",
                "employment_type": "Full-time",
                "job_type": "full-time",
                "experience_level": "mid-level"
            }
        ]
