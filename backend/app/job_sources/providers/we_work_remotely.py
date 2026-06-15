from app.job_sources.providers.base import BaseJobProvider

class WeWorkRemotelyProvider(BaseJobProvider):
    async def fetch_jobs(self) -> list[dict]:
        return [
            {
                "external_job_id": "wwr-1801",
                "title": "Backend Rust Developer",
                "company": "RustLabs LLC",
                "description": "Write fast reliable concurrent backend servers in Rust.",
                "location": "Remote (US/Europe)",
                "source_url": "https://weworkremotely.com/jobs/wwr-1801",
                "salary_min": 110000,
                "salary_max": 160000,
                "required_skills": "Rust, Actix, WebAssembly",
                "remote_type": "remote",
                "employment_type": "Full-time",
                "job_type": "full-time",
                "experience_level": "senior"
            }
        ]
