from app.job_sources.providers.base import BaseJobProvider

class GoogleJobsProvider(BaseJobProvider):
    async def fetch_jobs(self) -> list[dict]:
        return [
            {
                "external_job_id": "gj-1601",
                "title": "Cloud Architect",
                "company": "Google LLC",
                "description": "Design secure scalable enterprise systems on GCP.",
                "location": "Sunnyvale, CA",
                "source_url": "https://careers.google.com/jobs/gj-1601",
                "salary_min": 170000,
                "salary_max": 240000,
                "required_skills": "GCP, Architecture, Kubernetes",
                "remote_type": "hybrid",
                "employment_type": "Full-time",
                "job_type": "full-time",
                "experience_level": "lead"
            }
        ]
