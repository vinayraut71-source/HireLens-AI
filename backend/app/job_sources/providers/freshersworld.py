from app.job_sources.providers.base import BaseJobProvider

class FreshersworldProvider(BaseJobProvider):
    async def fetch_jobs(self) -> list[dict]:
        return [
            {
                "external_job_id": "fw-1101",
                "title": "Graduate Engineer Trainee",
                "company": "Infosys Ltd.",
                "description": "Fresher engineer trainee role for system validation.",
                "location": "Chennai",
                "source_url": "https://www.freshersworld.com/jobs/fw-1101",
                "salary_min": 360000,
                "salary_max": 450000,
                "required_skills": "Java, C++, DBMS",
                "remote_type": "onsite",
                "employment_type": "Full-time",
                "job_type": "full-time",
                "experience_level": "fresher"
            }
        ]
