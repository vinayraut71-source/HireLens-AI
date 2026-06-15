from app.job_sources.providers.base import BaseJobProvider

class TimesJobsProvider(BaseJobProvider):
    async def fetch_jobs(self) -> list[dict]:
        return [
            {
                "external_job_id": "tj-1301",
                "title": "Database Administrator",
                "company": "Tata Consultancy Services",
                "description": "Administer Oracle database instances and perform data backups.",
                "location": "Kolkata",
                "source_url": "https://www.timesjobs.com/job/tj-1301",
                "salary_min": 600000,
                "salary_max": 900000,
                "required_skills": "Oracle, SQL, Linux",
                "remote_type": "onsite",
                "employment_type": "Full-time",
                "job_type": "full-time",
                "experience_level": "mid-level"
            }
        ]
