from app.job_sources.providers.base import BaseJobProvider

class TuringProvider(BaseJobProvider):
    async def fetch_jobs(self) -> list[dict]:
        return [
            {
                "external_job_id": "tur-2001",
                "title": "Lead Python Engineer",
                "company": "Turing Global",
                "description": "Lead a team of remote developers and design scalable backends.",
                "location": "Remote - Worldwide",
                "source_url": "https://turing.com/jobs/tur-2001",
                "salary_min": 120000,
                "salary_max": 180000,
                "required_skills": "Python, Django, AWS, Leadership",
                "remote_type": "remote",
                "employment_type": "Full-time",
                "job_type": "full-time",
                "experience_level": "lead"
            }
        ]
