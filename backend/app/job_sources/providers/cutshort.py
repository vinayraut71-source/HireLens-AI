from app.job_sources.providers.base import BaseJobProvider

class CutshortProvider(BaseJobProvider):
    async def fetch_jobs(self) -> list[dict]:
        return [
            {
                "external_job_id": "cs-901",
                "title": "Senior DevOps Engineer",
                "company": "ScaleUp Solutions LLC",
                "description": "Design and manage Kubernetes clusters in AWS.",
                "location": "Pune",
                "source_url": "https://cutshort.io/job/cs-901",
                "salary_min": 1800000,
                "salary_max": 2500000,
                "required_skills": "Kubernetes, AWS, Terraform",
                "remote_type": "hybrid",
                "employment_type": "Full-time",
                "job_type": "full-time",
                "experience_level": "senior"
            }
        ]
