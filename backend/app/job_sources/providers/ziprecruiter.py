from app.job_sources.providers.base import BaseJobProvider

class ZipRecruiterProvider(BaseJobProvider):
    async def fetch_jobs(self) -> list[dict]:
        return [
            {
                "external_job_id": "zr-1501",
                "title": "Systems Administrator",
                "company": "Enterprise Tech Corp.",
                "description": "Configure active directory and maintain cloud VMs.",
                "location": "Dallas, TX",
                "source_url": "https://www.ziprecruiter.com/job/zr-1501",
                "salary_min": 85000,
                "salary_max": 115000,
                "required_skills": "Active Directory, Windows Server, Azure",
                "remote_type": "onsite",
                "employment_type": "Full-time",
                "job_type": "full-time",
                "experience_level": "mid-level"
            }
        ]
