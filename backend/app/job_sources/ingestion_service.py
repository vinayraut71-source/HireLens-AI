"""
Ingestion engine — manages provider pipelines, data normalization, deduplication, and lifecycle.
Sprint 12: Ingestion layer.
"""
import time
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.jobs.models import Job
from app.job_sources.models import ExternalJobSource
from app.job_sources.providers import PROVIDER_REGISTRY
from app.job_sources.normalization_service import NormalizationService
from app.job_sources.deduplication_service import DeduplicationService

logger = logging.getLogger(__name__)


class JobIngestionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def ingest_jobs(self, source: str) -> dict:
        """
        Ingest jobs from a single provider source.
        Processes, normalizes, deduplicates, and tracks job listings.
        """
        start_time = time.time()
        provider = PROVIDER_REGISTRY.get(source.lower().strip())
        if not provider:
            raise ValueError(f"Unknown job provider source: {source}")

        raw_jobs = await provider.fetch_jobs()
        processed_count = 0
        new_count = 0
        updated_count = 0

        for item in raw_jobs:
            ext_id = item.get("external_job_id")
            if not ext_id:
                continue

            # 1. Normalization
            norm_company = NormalizationService.normalize_company(item.get("company"))
            norm_loc = NormalizationService.normalize_location(item.get("location"))
            norm_emp = NormalizationService.normalize_employment_type(item.get("employment_type"))
            norm_sal_min, norm_sal_max = NormalizationService.normalize_salary(
                item.get("salary_min"), item.get("salary_max")
            )
            norm_skills = NormalizationService.normalize_skills(item.get("required_skills"))
            norm_jt = NormalizationService.normalize_job_type(item.get("job_type") or item.get("employment_type"))
            norm_el = NormalizationService.normalize_experience_level(item.get("experience_level"))

            # 2. Ingestion Hash computation
            payload_str = (
                f"{norm_company.lower() if norm_company else ''}|"
                f"{item['title'].lower().strip()}|"
                f"{norm_loc.lower() if norm_loc else ''}|"
                f"{item['description'].lower().strip()}"
            )
            ingestion_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

            # 3. Deduplication Check
            duplicate = await DeduplicationService.find_duplicate(
                self.db, norm_company, item["title"], norm_loc, ingestion_hash
            )

            now = datetime.now(timezone.utc)

            if duplicate:
                # Update existing job record (idempotency, updates if fields changed)
                duplicate.title = item["title"]
                duplicate.company = item.get("company")
                duplicate.description = item["description"]
                duplicate.source_url = item.get("source_url")
                duplicate.location = item.get("location")
                duplicate.remote_type = item.get("remote_type")
                duplicate.salary_min = norm_sal_min
                duplicate.salary_max = norm_sal_max
                duplicate.required_skills = norm_skills
                duplicate.external_source = source
                duplicate.external_job_id = ext_id
                duplicate.normalized_company = norm_company
                duplicate.normalized_location = norm_loc
                duplicate.ingestion_hash = ingestion_hash
                duplicate.last_seen_at = now
                duplicate.job_status = "active"
                duplicate.job_type = norm_jt
                duplicate.experience_level = norm_el
                duplicate.is_deleted = False

                # Update or create external job source tracking record
                stmt_track = select(ExternalJobSource).where(
                    ExternalJobSource.source_name == source,
                    ExternalJobSource.source_job_id == ext_id
                )
                res_track = await self.db.execute(stmt_track)
                track_rec = res_track.scalar_one_or_none()

                if track_rec:
                    track_rec.last_seen_at = now
                    track_rec.source_url = item.get("source_url")
                else:
                    new_track = ExternalJobSource(
                        source_name=source,
                        source_job_id=ext_id,
                        source_url=item.get("source_url"),
                        last_seen_at=now
                    )
                    self.db.add(new_track)

                updated_count += 1
            else:
                # Insert new job record
                new_job = Job(
                    user_id=None,
                    title=item["title"],
                    company=item.get("company"),
                    description=item["description"],
                    source_url=item.get("source_url"),
                    location=item.get("location"),
                    remote_type=item.get("remote_type"),
                    salary_min=norm_sal_min,
                    salary_max=norm_sal_max,
                    required_skills=norm_skills,
                    external_source=source,
                    external_job_id=ext_id,
                    normalized_company=norm_company,
                    normalized_location=norm_loc,
                    ingestion_hash=ingestion_hash,
                    last_seen_at=now,
                    job_status="active",
                    job_type=norm_jt,
                    experience_level=norm_el
                )
                self.db.add(new_job)

                # Create external job source tracking record
                new_track = ExternalJobSource(
                    source_name=source,
                    source_job_id=ext_id,
                    source_url=item.get("source_url"),
                    last_seen_at=now
                )
                self.db.add(new_track)

                new_count += 1

            processed_count += 1

        try:
            await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to ingest jobs for source {source}: {str(e)}", exc_info=True)
            await self.db.rollback()
            raise

        duration = round(time.time() - start_time, 3)
        return {
            "status": "success",
            "processed_count": processed_count,
            "new_count": new_count,
            "updated_count": updated_count,
            "duration_seconds": duration
        }

    async def ingest_all_sources(self) -> dict:
        """
        Ingest jobs from all configured providers.
        """
        start_time = time.time()
        processed_count = 0
        new_count = 0
        updated_count = 0

        for source in PROVIDER_REGISTRY.keys():
            res = await self.ingest_jobs(source)
            processed_count += res["processed_count"]
            new_count += res["new_count"]
            updated_count += res["updated_count"]

        duration = round(time.time() - start_time, 3)
        return {
            "status": "success",
            "processed_count": processed_count,
            "new_count": new_count,
            "updated_count": updated_count,
            "duration_seconds": duration
        }

    async def refresh_existing_jobs(self) -> dict:
        """
        Iterates over active ingested jobs to re-normalize and compute fields.
        """
        start_time = time.time()
        stmt = select(Job).where(Job.external_source.isnot(None), Job.is_deleted == False)
        res = await self.db.execute(stmt)
        active_jobs = res.scalars().all()
        updated_count = 0

        for job in active_jobs:
            # Re-normalize
            norm_company = NormalizationService.normalize_company(job.company)
            norm_loc = NormalizationService.normalize_location(job.location)
            norm_sal_min, norm_sal_max = NormalizationService.normalize_salary(
                job.salary_min, job.salary_max
            )
            
            job.normalized_company = norm_company
            job.normalized_location = norm_loc
            job.salary_min = norm_sal_min
            job.salary_max = norm_sal_max
            job.job_type = NormalizationService.normalize_job_type(job.job_type)
            job.experience_level = NormalizationService.normalize_experience_level(job.experience_level)
            
            # Re-hash
            payload_str = (
                f"{norm_company.lower() if norm_company else ''}|"
                f"{job.title.lower().strip()}|"
                f"{norm_loc.lower() if norm_loc else ''}|"
                f"{job.description.lower().strip()}"
            )
            job.ingestion_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
            updated_count += 1

        try:
            await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to refresh ingested jobs: {str(e)}", exc_info=True)
            await self.db.rollback()
            raise

        duration = round(time.time() - start_time, 3)
        return {
            "status": "success",
            "processed_count": len(active_jobs),
            "new_count": 0,
            "updated_count": updated_count,
            "duration_seconds": duration
        }

    async def mark_expired_jobs(self) -> dict:
        """
        Identify jobs not seen in the last 30 days and mark them as expired.
        """
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        
        # Select active ingested jobs not seen for 30 days
        stmt = (
            update(Job)
            .where(
                Job.external_source.isnot(None),
                Job.job_status == "active",
                Job.last_seen_at < thirty_days_ago,
                Job.is_deleted == False
            )
            .values(job_status="expired", updated_at=datetime.now(timezone.utc))
        )
        res = await self.db.execute(stmt)
        expired_count = res.rowcount
        await self.db.commit()

        return {
            "expired_count": expired_count
        }
