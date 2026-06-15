"""Resumes module — service layer."""
import re
import io
import uuid
import boto3
import logging
import pdfplumber
from docx import Document
from datetime import datetime
from botocore.exceptions import ClientError
import hashlib
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.core.config import settings
from app.resumes.models import ResumeProfile, ResumeVersion, ATSAnalysis

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

    async def analyze_ats(self, user_id: uuid.UUID, version_id: uuid.UUID, job_description: str) -> ATSAnalysis:
        # Fetch version and check profile/version soft-delete
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

        # Compute job description hash
        jd_clean = job_description.strip()
        if not jd_clean:
            raise HTTPException(status_code=400, detail="Job description cannot be empty")
        if len(jd_clean) > 50000:
            raise HTTPException(status_code=400, detail="Job description exceeds the maximum length of 50,000 characters.")
        jd_hash = hashlib.sha256(jd_clean.encode('utf-8')).hexdigest()

        # Check cache (idempotent scoring)
        cache_stmt = select(ATSAnalysis).where(
            ATSAnalysis.resume_version_id == version_id,
            ATSAnalysis.job_description_hash == jd_hash
        )
        cache_result = await self.db.execute(cache_stmt)
        cached_analysis = cache_result.scalar_one_or_none()
        if cached_analysis:
            return cached_analysis

        # Perform scoring
        jd_analysis = JobDescriptionAnalyzer.analyze(jd_clean)
        scores = ATSScoringService.score(version, jd_analysis)

        # Save the analysis
        analysis = ATSAnalysis(
            resume_version_id=version_id,
            job_description_hash=jd_hash,
            ats_score=scores["ats_score"],
            keyword_score=scores["keyword_score"],
            skills_score=scores["skills_score"],
            experience_score=scores["experience_score"],
            education_score=scores["education_score"],
            missing_keywords=scores["missing_keywords"],
            matched_keywords=scores["matched_keywords"],
            recommendations=scores["recommendations"],
            matched_skills=scores["matched_skills"],
            missing_skills=scores["missing_skills"],
            resume_strengths=scores["resume_strengths"],
            resume_weaknesses=scores["resume_weaknesses"],
            matched_sections=scores["matched_sections"]
        )

        try:
            self.db.add(analysis)
            await self.db.commit()
            await self.db.refresh(analysis)
        except Exception as e:
            logger.error(f"Failed to save ATS analysis for version {version_id}: {str(e)}", exc_info=True)
            await self.db.rollback()
            raise HTTPException(status_code=500, detail="Failed to save ATS analysis to database.")

        return analysis

    async def list_ats_history(self, user_id: uuid.UUID, version_id: uuid.UUID) -> list[ATSAnalysis]:
        # Validate ownership and soft delete status
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

        # Fetch history ordered by created_at desc
        history_stmt = select(ATSAnalysis).where(
            ATSAnalysis.resume_version_id == version_id
        ).order_by(ATSAnalysis.created_at.desc())
        history_result = await self.db.execute(history_stmt)
        return list(history_result.scalars().all())

    @staticmethod
    def _estimate_experience_years(resume_version: ResumeVersion) -> int:
        if not resume_version.experience:
            return 0
        total_years = 0
        current_year = datetime.now().year
        for exp in resume_version.experience:
            years = re.findall(r'\b(19\d\d|20\d\d)\b', exp)
            if len(years) >= 2:
                try:
                    y1, y2 = int(years[0]), int(years[1])
                    total_years += min(15, abs(y2 - y1))
                except ValueError:
                    pass
            elif len(years) == 1:
                if any(pw in exp.lower() for pw in ["present", "current", "now", "ongoing"]):
                    try:
                        y1 = int(years[0])
                        if y1 <= current_year:
                            total_years += min(15, abs(current_year - y1))
                    except ValueError:
                        pass
                else:
                    total_years += 1
        return total_years if total_years > 0 else len(resume_version.experience)

    @staticmethod
    def _estimate_education_level(education_list: list) -> int:
        if not education_list:
            return 0
        highest = 0
        for edu in education_list:
            edu_lower = edu.lower()
            if "phd" in edu_lower or "ph.d" in edu_lower or "doctorate" in edu_lower:
                highest = max(highest, 3)
            elif "master" in edu_lower or "ms" in edu_lower or "m.s." in edu_lower or "mba" in edu_lower:
                highest = max(highest, 2)
            elif "bachelor" in edu_lower or "bs" in edu_lower or "b.s." in edu_lower or "degree" in edu_lower or "university" in edu_lower or "college" in edu_lower:
                highest = max(highest, 1)
        return highest


class JobDescriptionAnalyzer:
    """Helper service to parse job description text deterministically."""

    COMMON_KEYWORDS = [
        "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust", "ruby", "php",
        "react", "angular", "vue", "next.js", "node.js", "express", "django", "fastapi", "flask",
        "spring boot", "dotnet", "aws", "azure", "gcp", "docker", "kubernetes", "sql", "postgresql",
        "mysql", "mongodb", "redis", "elasticsearch", "git", "ci/cd", "agile", "scrum", "jira",
        "machine learning", "deep learning", "nlp", "artificial intelligence", "data science",
        "pandas", "numpy", "tensorflow", "pytorch", "html", "css", "linux", "rest api", "graphql"
    ]

    CERTIFICATION_KEYWORDS = [
        "AWS Certified", "PMP", "CSM", "CISSP", "CCNA", "CompTIA", "ITIL", "Certified ScrumMaster"
    ]

    @classmethod
    def analyze(cls, text: str) -> dict:
        text_lower = text.lower()
        keywords = [kw for kw in cls.COMMON_KEYWORDS if re.search(rf"\b{re.escape(kw)}\b", text_lower)]

        required_skills = set()
        preferred_skills = set()
        
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        for line in lines:
            line_lower = line.lower()
            line_kws = [kw for kw in cls.COMMON_KEYWORDS if re.search(rf"\b{re.escape(kw)}\b", line_lower)]
            if line_kws:
                is_preferred = any(pw in line_lower for pw in ["preferred", "plus", "nice to have", "desired", "beneficial", "optional", "bonus", "advantage"])
                if is_preferred:
                    preferred_skills.update(line_kws)
                else:
                    required_skills.update(line_kws)

        preferred_skills = preferred_skills - required_skills

        experience_years = 0
        exp_matches = re.findall(r'(\d+)\+?\s*(?:to|-)?\s*(\d+)?\s*years?', text_lower)
        if exp_matches:
            years_found = []
            for match in exp_matches:
                try:
                    years_found.append(int(match[0]))
                except ValueError:
                    pass
            if years_found:
                experience_years = max(years_found)

        education_req = "Bachelor's"
        edu_lower = text_lower
        if "phd" in edu_lower or "ph.d" in edu_lower or "doctorate" in edu_lower:
            education_req = "PhD"
        elif "master" in edu_lower or "ms" in edu_lower or "m.s." in edu_lower:
            education_req = "Master's"
        elif "bachelor" in edu_lower or "bs" in edu_lower or "b.s." in edu_lower:
            education_req = "Bachelor's"
        elif "any" in edu_lower or "none" in edu_lower or "no degree" in edu_lower:
            education_req = "None"

        certifications = [cert for cert in cls.CERTIFICATION_KEYWORDS if cert.lower() in text_lower]

        return {
            "required_skills": list(required_skills),
            "preferred_skills": list(preferred_skills),
            "years_of_experience": experience_years,
            "education_requirements": education_req,
            "certifications": certifications,
            "keywords": keywords
        }


class ATSScoringService:
    """Helper service to compute deterministic ATS score breakdowns."""

    EDU_LEVELS = {"none": 0, "bachelor's": 1, "master's": 2, "phd": 3}

    @classmethod
    def score(cls, resume_version: ResumeVersion, jd_analysis: dict) -> dict:
        resume_text_lower = (resume_version.extracted_text or "").lower()
        
        # 1. Keywords Match
        jd_keywords = jd_analysis["keywords"]
        matched_keywords = []
        if jd_keywords:
            matched_keywords = [kw for kw in jd_keywords if re.search(rf"\b{re.escape(kw)}\b", resume_text_lower)]
        
        missing_keywords = list(set(jd_keywords) - set(matched_keywords))
        keyword_score = round((len(matched_keywords) / len(jd_keywords)) * 100) if jd_keywords else 100

        # 2. Skills Match
        resume_skills_set = {s.lower().strip() for s in (resume_version.skills or [])}
        required_skills = jd_analysis["required_skills"]
        preferred_skills = jd_analysis["preferred_skills"]

        matched_required = [s for s in required_skills if any(s.lower() in rs or rs in s.lower() for rs in resume_skills_set)]
        matched_preferred = [s for s in preferred_skills if any(s.lower() in rs or rs in s.lower() for rs in resume_skills_set)]

        required_score = (len(matched_required) / len(required_skills)) * 100 if required_skills else 100
        preferred_score = (len(matched_preferred) / len(preferred_skills)) * 100 if preferred_skills else 100
        skills_score = round(0.8 * required_score + 0.2 * preferred_score)

        # 3. Education Match
        jd_edu = jd_analysis["education_requirements"]
        jd_level = cls.EDU_LEVELS.get(jd_edu.lower(), 1)
        resume_level = ResumeVersionService._estimate_education_level(resume_version.education or [])

        if resume_level >= jd_level:
            education_score = 100
        else:
            education_score = round((resume_level / jd_level) * 100) if jd_level > 0 else 100

        # 4. Experience Match
        jd_exp_years = jd_analysis["years_of_experience"]
        resume_exp_years = ResumeVersionService._estimate_experience_years(resume_version)

        if resume_exp_years >= jd_exp_years:
            experience_score = 100
        else:
            experience_score = round((resume_exp_years / jd_exp_years) * 100) if jd_exp_years > 0 else 100

        # Overall Weighted Score
        ats_score = round(0.3 * keyword_score + 0.3 * skills_score + 0.2 * experience_score + 0.2 * education_score)

        # Matched/Missing Skills (Sprint 4 enhanced)
        matched_skills = list(set(matched_required) | set(matched_preferred))
        missing_skills = list(set(required_skills) - set(matched_required))

        # Strengths (Sprint 4 enhanced)
        strengths = []
        if experience_score == 100:
            strengths.append(f"Meets or exceeds required experience level ({jd_exp_years} years).")
        if education_score == 100:
            strengths.append(f"Meets required education level: {jd_edu}.")
        if keyword_score >= 80:
            strengths.append("Strong keyword alignment with the job description.")
        if len(matched_required) > 0:
            strengths.append(f"Possesses key required skills: {', '.join(matched_required[:3])}.")
        if not strengths:
            strengths.append("Found basic resume formatting.")

        # Weaknesses (Sprint 4 enhanced)
        weaknesses = []
        if experience_score < 100:
            weaknesses.append(f"Experience level (~{resume_exp_years} years) is below the required {jd_exp_years} years.")
        if education_score < 100:
            weaknesses.append(f"Education degree does not meet the preferred/required {jd_edu} level.")
        if missing_skills:
            weaknesses.append(f"Missing critical required skills: {', '.join(missing_skills[:3])}.")
        if keyword_score < 50:
            weaknesses.append("Low keyword overlap with the role description.")
        if not weaknesses:
            weaknesses.append("No critical gaps identified in the resume content.")

        # Matched Sections (Sprint 4 enhanced)
        matched_sections = []
        if resume_version.education:
            matched_sections.append("Education")
        if resume_version.experience:
            matched_sections.append("Experience")
        if resume_version.skills:
            matched_sections.append("Skills")
        if resume_version.certifications:
            matched_sections.append("Certifications")
        if resume_version.contact_info and (resume_version.contact_info.get("name") or resume_version.contact_info.get("email")):
            matched_sections.append("Contact Info")

        # Recommendations
        recommendations = []
        if keyword_score < 70 and missing_keywords:
            recommendations.append(f"Add missing keywords: {', '.join(missing_keywords[:5])} to your resume to pass automated screens.")
        if skills_score < 70 and required_skills:
            missing_req = list(set(required_skills) - set(matched_required))
            if missing_req:
                recommendations.append(f"Incorporate missing required skills such as: {', '.join(missing_req[:5])} into your skills or experience sections.")
        if experience_score < 100:
            recommendations.append(f"Your experience section suggests ~{resume_exp_years} years of experience. Highlight more details of your work history to align with the required {jd_exp_years} years.")
        if education_score < 100:
            recommendations.append(f"Ensure your academic credentials list the {jd_edu} degree requested by the job description.")
        
        # Certifications check
        jd_certs = jd_analysis["certifications"]
        if jd_certs:
            resume_certs_lower = [c.lower() for c in (resume_version.certifications or [])]
            missing_certs = [cert for cert in jd_certs if cert.lower() not in resume_certs_lower]
            if missing_certs:
                recommendations.append(f"Consider adding or obtaining certifications: {', '.join(missing_certs)}.")

        if not recommendations:
            recommendations.append("Your resume aligns very well with the job description requirements.")

        return {
            "ats_score": ats_score,
            "keyword_score": keyword_score,
            "skills_score": skills_score,
            "experience_score": experience_score,
            "education_score": education_score,
            "missing_keywords": missing_keywords,
            "matched_keywords": matched_keywords,
            "recommendations": recommendations,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "resume_strengths": strengths,
            "resume_weaknesses": weaknesses,
            "matched_sections": matched_sections
        }


