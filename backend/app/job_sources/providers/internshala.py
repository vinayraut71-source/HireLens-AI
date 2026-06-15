from app.job_sources.providers.base import BaseJobProvider

class InternshalaProvider(BaseJobProvider):
    async def fetch_jobs(self) -> list[dict]:
        return [
            {
                "external_job_id": "is-701",
                "title": "Software Engineering Intern",
                "company": "TechLabs",
                "description": "Learn React and assist in front-end page layouts.",
                "location": "Mumbai",
                "source_url": "https://internshala.com/internship/detail/is-701",
                "salary_min": 15000,
                "salary_max": 25000,
                "required_skills": "HTML, CSS, JavaScript",
                "remote_type": "onsite",
                "employment_type": "Internship",
                "job_type": "internship",
                "experience_level": "fresher"
            }
        ]
