"""
Deduplication engine — identifies duplicate job postings.
Sprint 12: Ingestion layer.
"""
import difflib
from sqlalchemy import select
from app.jobs.models import Job

class DeduplicationService:
    @staticmethod
    def calculate_title_similarity(title1: str, title2: str) -> float:
        """
        Calculates the similarity ratio of two job titles.
        Uses difflib SequenceMatcher on case-insensitive stripped inputs.
        """
        t1 = title1.lower().strip()
        t2 = title2.lower().strip()
        return difflib.SequenceMatcher(None, t1, t2).ratio()

    @classmethod
    async def find_duplicate(
        cls, db, normalized_company: str | None, title: str, location: str | None, ingestion_hash: str | None
    ) -> Job | None:
        """
        Finds if a job already exists in the system based on matching ingestion_hash
        OR matching normalized_company, normalized_location, and title similarity >= 0.8.
        """
        # 1. First search by ingestion_hash (fast path)
        if ingestion_hash:
            stmt = select(Job).where(Job.ingestion_hash == ingestion_hash, Job.is_deleted == False)
            res = await db.execute(stmt)
            job = res.scalar_one_or_none()
            if job:
                return job

        # 2. Search by company, location, and title similarity (slow path)
        if normalized_company and location:
            stmt = select(Job).where(
                Job.normalized_company == normalized_company,
                Job.normalized_location == location,
                Job.is_deleted == False
            )
            res = await db.execute(stmt)
            candidates = res.scalars().all()
            for candidate in candidates:
                similarity = cls.calculate_title_similarity(candidate.title, title)
                if similarity >= 0.8:
                    return candidate
        return None
