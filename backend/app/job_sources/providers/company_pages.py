from app.job_sources.providers.base import BaseJobProvider

class CompanyPagesProvider(BaseJobProvider):
    async def fetch_jobs(self) -> list[dict]:
        return [
            {
                "external_job_id": "cp-601",
                "title": "Devops Engineer",
                "company": "Microsoft",
                "description": "Deploy and maintain cloud infrastructure pipelines.",
                "location": "Redmond",
                "source_url": "https://careers.microsoft.com/jobs/cp-601",
                "salary_min": 130000,
                "salary_max": 180000,
                "required_skills": "Azure, Kubernetes, Terraform, CI/CD",
                "remote_type": "hybrid",
                "employment_type": "full-time"
            }
        ]
