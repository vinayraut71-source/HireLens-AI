from app.job_sources.providers.base import BaseJobProvider

class RemoteOKProvider(BaseJobProvider):
    async def fetch_jobs(self) -> list[dict]:
        return [
            {
                "external_job_id": "rok-1701",
                "title": "Technical Writer",
                "company": "GitLab Inc.",
                "description": "Document microservice architecture and database schemas.",
                "location": "Anywhere (Remote)",
                "source_url": "https://remoteok.com/remote-jobs/rok-1701",
                "salary_min": 70000,
                "salary_max": 95000,
                "required_skills": "Markdown, Git, Writing",
                "remote_type": "remote",
                "employment_type": "Contract",
                "job_type": "contract",
                "experience_level": "mid-level"
            }
        ]
