from app.job_sources.providers.base import BaseJobProvider
from app.job_sources.providers.linkedin import LinkedInProvider
from app.job_sources.providers.naukri import NaukriProvider
from app.job_sources.providers.indeed import IndeedProvider
from app.job_sources.providers.foundit import FounditProvider
from app.job_sources.providers.wellfound import WellfoundProvider
from app.job_sources.providers.company_pages import CompanyPagesProvider

# India
from app.job_sources.providers.internshala import InternshalaProvider
from app.job_sources.providers.apna import ApnaProvider
from app.job_sources.providers.cutshort import CutshortProvider
from app.job_sources.providers.instahyre import InstahyreProvider
from app.job_sources.providers.freshersworld import FreshersworldProvider
from app.job_sources.providers.shine import ShineProvider
from app.job_sources.providers.timesjobs import TimesJobsProvider

# Global
from app.job_sources.providers.glassdoor import GlassdoorProvider
from app.job_sources.providers.ziprecruiter import ZipRecruiterProvider
from app.job_sources.providers.google_jobs import GoogleJobsProvider

# Remote
from app.job_sources.providers.remoteok import RemoteOKProvider
from app.job_sources.providers.we_work_remotely import WeWorkRemotelyProvider
from app.job_sources.providers.arc import ArcProvider
from app.job_sources.providers.turing import TuringProvider

PROVIDER_REGISTRY: dict[str, BaseJobProvider] = {
    "linkedin": LinkedInProvider(),
    "naukri": NaukriProvider(),
    "indeed": IndeedProvider(),
    "foundit": FounditProvider(),
    "wellfound": WellfoundProvider(),
    "company_pages": CompanyPagesProvider(),
    
    # India
    "internshala": InternshalaProvider(),
    "apna": ApnaProvider(),
    "cutshort": CutshortProvider(),
    "instahyre": InstahyreProvider(),
    "freshersworld": FreshersworldProvider(),
    "shine": ShineProvider(),
    "timesjobs": TimesJobsProvider(),
    
    # Global
    "glassdoor": GlassdoorProvider(),
    "ziprecruiter": ZipRecruiterProvider(),
    "google_jobs": GoogleJobsProvider(),
    
    # Remote
    "remoteok": RemoteOKProvider(),
    "we_work_remotely": WeWorkRemotelyProvider(),
    "arc": ArcProvider(),
    "turing": TuringProvider(),
}

__all__ = [
    "BaseJobProvider",
    "LinkedInProvider",
    "NaukriProvider",
    "IndeedProvider",
    "FounditProvider",
    "WellfoundProvider",
    "CompanyPagesProvider",
    
    "InternshalaProvider",
    "ApnaProvider",
    "CutshortProvider",
    "InstahyreProvider",
    "FreshersworldProvider",
    "ShineProvider",
    "TimesJobsProvider",
    
    "GlassdoorProvider",
    "ZipRecruiterProvider",
    "GoogleJobsProvider",
    
    "RemoteOKProvider",
    "WeWorkRemotelyProvider",
    "ArcProvider",
    "TuringProvider",
    
    "PROVIDER_REGISTRY",
]
