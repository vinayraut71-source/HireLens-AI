"""Resumes module — service layer."""
import re
import io
import uuid
import boto3
import logging
import pdfplumber
from docx import Document
from botocore.exceptions import ClientError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.core.config import settings
from app.resumes.models import ResumeProfile, ResumeVersion

logger = logging.getLogger(__name__)


class ResumeStorageService:
    """Handles interaction with MinIO bucket storage."""

    def __init__(self):
        self.endpoint_url = settings.MINIO_ENDPOINT
        if self.endpoint_url and not self.endpoint_url.startswith("http"):
            self.endpoint_url = f"http://{self.endpoint_url}"
        
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_key_id=settings.MINIO_SECRET_KEY,
            use_ssl=settings.MINIO_SECURE,
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME

    def upload_file(self, user_id: str, filename: str, file_data: bytes) -> str:
        """Upload a file to MinIO bucket and return its storage path."""
        import uuid
        unique_id = uuid.uuid4().hex
        object_key = f"resumes/{user_id}/{unique_id}_{filename}"
        
        # Ensure bucket exists
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError:
            try:
                self.s3_client.create_bucket(Bucket=self.bucket_name)
            except ClientError:
                # Silently catch and log/ignore errors if we are offline/mocking
                pass
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=file_data
            )
        except ClientError as e:
            # Let it propagate if we are not mocking
            raise e
        return object_key

    def download_file(self, storage_path: str) -> bytes:
        """Download a file from MinIO bucket and return its bytes."""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=storage_path)
            return response["Body"].read()
        except ClientError as e:
            raise e


class ResumeParsingService:
    """Service for extracting and structured parsing of resume contents without AI."""

    @staticmethod
    def extract_text_from_pdf(file_bytes: bytes) -> str:
        text_parts = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n".join(text_parts)

    @staticmethod
    def extract_text_from_docx(file_bytes: bytes) -> str:
        doc = Document(io.BytesIO(file_bytes))
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])

    @staticmethod
    def parse_text(text: str) -> dict:
        """Deterministic, heuristic parsing of resume content."""
        # Contact Info
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        phone_match = re.search(r'\+?\d[\d\-\(\)\s]{7,18}\d', text)
        
        # Extract first clean line as candidate name
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        name = ""
        if lines:
            cand_name = lines[0]
            # Filter out header-like text or very long names
            if len(cand_name) <= 60 and "@" not in cand_name and not any(c.isdigit() for c in cand_name):
                name = cand_name

        contact_info = {
            "name": name,
            "email": email_match.group(0) if email_match else "",
            "phone": phone_match.group(0) if phone_match else "",
        }

        # Structured fields matching header heuristics
        sections = {
            "education": [],
            "experience": [],
            "skills": [],
            "certifications": []
        }
        
        current_section = None
        
        for line in text.split("\n"):
            line_clean = line.strip()
            if not line_clean:
                continue
            
            line_lower = line_clean.lower()
            
            # Check section header transitions
            if any(h in line_lower for h in ["education", "academic background", "academic history", "educational background", "academics"]) and len(line_clean) < 35:
                current_section = "education"
                continue
            elif any(h in line_lower for h in ["experience", "employment", "work history", "employment history", "professional experience", "work experience"]) and len(line_clean) < 35:
                current_section = "experience"
                continue
            elif any(h in line_lower for h in ["skills", "technologies", "expertise", "technical skills"]) and len(line_clean) < 35:
                current_section = "skills"
                continue
            elif any(h in line_lower for h in ["certifications", "licenses", "credentials", "certificates"]) and len(line_clean) < 35:
                current_section = "certifications"
                continue
            
            if current_section:
                sections[current_section].append(line_clean)

        # Post-process skills list
        skills_list = []
        for s in sections["skills"]:
            if "," in s:
                skills_list.extend([item.strip() for item in s.split(",") if item.strip()])
            else:
                skills_list.append(s)

        return {
            "contact_info": contact_info,
            "education": sections["education"],
            "experience": sections["experience"],
            "skills": skills_list if skills_list else sections["skills"],
            "certifications": sections["certifications"],
        }


class ResumeVersionService:
    """Handles database transactions for resume profiles and versions."""

    def __init__(self, db: AsyncSession, storage_service: ResumeStorageService):
        self.db = db
        self.storage_service = storage_service

    async def list_profiles(self, user_id: uuid.UUID) -> list[ResumeProfile]:
        stmt = select(ResumeProfile).where(
            ResumeProfile.user_id == user_id,
            ResumeProfile.is_deleted == False
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_profile(self, user_id: uuid.UUID, profile_id: uuid.UUID) -> ResumeProfile | None:
        stmt = select(ResumeProfile).where(
            ResumeProfile.id == profile_id,
            ResumeProfile.user_id == user_id,
            ResumeProfile.is_deleted == False
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_versions(self, user_id: uuid.UUID, profile_id: uuid.UUID) -> list[ResumeVersion]:
        stmt = select(ResumeVersion).where(
            ResumeVersion.profile_id == profile_id,
            ResumeVersion.user_id == user_id,
            ResumeVersion.is_deleted == False
        ).order_by(ResumeVersion.version_number.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def upload_resume(
        self,
        user_id: uuid.UUID,
        filename: str,
        file_content: bytes,
        mime_type: str,
        upload_source: str = "upload"
    ) -> ResumeVersion:
        # Check if user has an existing profile
        stmt = select(ResumeProfile).where(
            ResumeProfile.user_id == user_id,
            ResumeProfile.is_deleted == False
        ).order_by(ResumeProfile.created_at.asc())
        result = await self.db.execute(stmt)
        profile = result.scalars().first()

        try:
            if not profile:
                # Create a new profile if it's the first upload
                profile = ResumeProfile(
                    user_id=user_id,
                    name=filename,
                    is_default=True,
                    version_count=0
                )
                self.db.add(profile)
                await self.db.flush()

            # Upload the file to storage service
            storage_path = self.storage_service.upload_file(
                user_id=str(user_id),
                filename=filename,
                file_data=file_content
            )

            # Create the version
            version_number = profile.version_count + 1
            version = ResumeVersion(
                profile_id=profile.id,
                user_id=user_id,
                version_number=version_number,
                original_filename=filename,
                storage_path=storage_path,
                file_size=len(file_content),
                mime_type=mime_type,
                upload_source=upload_source,
                extracted_text=""
            )
            self.db.add(version)
            await self.db.flush()

            # Update the profile properties
            profile.version_count = version_number
            profile.active_version_id = version.id
            
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

        return version

    async def activate_version(
        self,
        user_id: uuid.UUID,
        profile_id: uuid.UUID,
        version_id: uuid.UUID
    ) -> ResumeProfile:
        # Verify profile ownership
        stmt = select(ResumeProfile).where(
            ResumeProfile.id == profile_id,
            ResumeProfile.user_id == user_id,
            ResumeProfile.is_deleted == False
        )
        result = await self.db.execute(stmt)
        profile = result.scalar_one_or_none()
        if not profile:
            raise HTTPException(status_code=404, detail="Resume profile not found")

        # Verify version exists and belongs to this profile
        stmt = select(ResumeVersion).where(
            ResumeVersion.id == version_id,
            ResumeVersion.profile_id == profile_id,
            ResumeVersion.user_id == user_id,
            ResumeVersion.is_deleted == False
        )
        result = await self.db.execute(stmt)
        version = result.scalar_one_or_none()
        if not version:
            raise HTTPException(status_code=404, detail="Resume version not found")

        try:
            profile.active_version_id = version_id
            await self.db.commit()
            await self.db.refresh(profile)
        except Exception:
            await self.db.rollback()
            raise

        return profile

    async def parse_version(self, user_id: uuid.UUID, version_id: uuid.UUID) -> ResumeVersion:
        # Fetch the version, ensuring parent profile is not soft-deleted
        stmt = (
            select(ResumeVersion)
            .join(ResumeProfile, ResumeVersion.profile_id == ResumeProfile.id)
            .where(
                ResumeVersion.id == version_id,
                ResumeVersion.user_id == user_id,
                ResumeVersion.is_deleted == False,
                ResumeProfile.is_deleted == False
            )
        )
        result = await self.db.execute(stmt)
        version = result.scalar_one_or_none()
        if not version:
            raise HTTPException(status_code=404, detail="Resume version not found")

        # Retrieve file bytes from MinIO S3
        try:
            file_bytes = self.storage_service.download_file(version.storage_path)
        except Exception as e:
            logger.error(f"Failed to download file from storage for version {version_id}: {str(e)}", exc_info=True)
            try:
                version.status = "error"
                await self.db.commit()
            except Exception as db_err:
                logger.error(f"Database error writing failed status for version {version_id}: {str(db_err)}", exc_info=True)
                await self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to download file from storage: {str(e)}")

        # Extract text based on mime_type or file extension
        try:
            if "pdf" in version.mime_type.lower() or version.original_filename.lower().endswith(".pdf"):
                text = ResumeParsingService.extract_text_from_pdf(file_bytes)
            elif "docx" in version.mime_type.lower() or version.original_filename.lower().endswith(".docx") or "word" in version.mime_type.lower():
                text = ResumeParsingService.extract_text_from_docx(file_bytes)
            else:
                raise ValueError("Unsupported file format for parsing")
        except Exception as e:
            logger.error(f"Error extracting text from file for version {version_id}: {str(e)}", exc_info=True)
            try:
                version.status = "error"
                await self.db.commit()
            except Exception as db_err:
                logger.error(f"Database error writing failed status for version {version_id}: {str(db_err)}", exc_info=True)
                await self.db.rollback()
            raise HTTPException(status_code=422, detail=f"Error extracting text from file: {str(e)}")

        # Run the structured heuristic parsing
        parsed_data = ResumeParsingService.parse_text(text)

        # Update the ResumeVersion record (idempotency: overrides text and parsed metadata)
        try:
            version.extracted_text = text
            version.contact_info = parsed_data["contact_info"]
            version.education = parsed_data["education"]
            version.experience = parsed_data["experience"]
            version.skills = parsed_data["skills"]
            version.certifications = parsed_data["certifications"]
            version.status = "ready"
            
            await self.db.commit()
            await self.db.refresh(version)
        except Exception as e:
            logger.error(f"Failed to save parsed details to database for version {version_id}: {str(e)}", exc_info=True)
            await self.db.rollback()
            raise HTTPException(status_code=500, detail="Database save failed during parsing.")

        return version

    async def get_parsed_data(self, user_id: uuid.UUID, version_id: uuid.UUID) -> dict:
        stmt = (
            select(ResumeVersion)
            .join(ResumeProfile, ResumeVersion.profile_id == ResumeProfile.id)
            .where(
                ResumeVersion.id == version_id,
                ResumeVersion.user_id == user_id,
                ResumeVersion.is_deleted == False,
                ResumeProfile.is_deleted == False
            )
        )
        result = await self.db.execute(stmt)
        version = result.scalar_one_or_none()
        if not version:
            raise HTTPException(status_code=404, detail="Resume version not found")
        
        # If not parsed yet or has errored, raise 400 Bad Request
        if version.status == "error":
            raise HTTPException(status_code=400, detail="Parsing failed for this resume version.")
        if version.contact_info is None:
            raise HTTPException(status_code=400, detail="Resume version has not been parsed yet. Please run parse first.")
            
        return {
            "contact_info": version.contact_info,
            "education": version.education,
            "experience": version.experience,
            "skills": version.skills,
            "certifications": version.certifications,
        }


