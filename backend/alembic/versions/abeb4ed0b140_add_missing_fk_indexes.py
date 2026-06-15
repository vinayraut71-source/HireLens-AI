"""add_missing_fk_indexes

Revision ID: abeb4ed0b140
Revises: 0009_update_recommendation_signals
Create Date: 2026-06-16 01:03:51.640443

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'abeb4ed0b140'
down_revision: Union[str, None] = '0009_update_recommendation_signals'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Drop old non-standard indexes
    op.drop_index('idx_resume_profiles_user', table_name='resume_profiles')
    op.drop_index('idx_resume_versions_profile', table_name='resume_versions')
    op.drop_index('idx_resume_versions_user', table_name='resume_versions')
    op.drop_index('idx_ats_history_version', table_name='ats_score_history')
    op.drop_index('idx_ats_history_profile', table_name='ats_score_history')
    op.drop_index('idx_match_history_user', table_name='match_score_history')
    op.drop_index('idx_match_history_version_job', table_name='match_score_history')
    op.drop_index('idx_match_results_user_version', table_name='match_results')
    op.drop_index('idx_skill_gaps_user', table_name='skill_gaps')
    op.drop_index('idx_applications_user_id', table_name='applications')
    op.drop_index('idx_applications_status', table_name='applications')
    op.drop_index('idx_applications_applied_date', table_name='applications')
    op.drop_index('idx_outcome_events_app', table_name='outcome_events')
    op.drop_index('idx_outcome_events_user', table_name='outcome_events')
    op.drop_index('idx_app_packages_user', table_name='application_packages')
    op.drop_index('idx_agent_audit_user', table_name='agent_audit_log')
    op.drop_index('idx_agent_audit_action', table_name='agent_audit_log')
    op.drop_index('idx_roadmap_modules_roadmap', table_name='roadmap_modules')
    op.drop_index('idx_recommendation_signals_user', table_name='recommendation_signals')
    op.drop_index('idx_job_postings_company', table_name='job_postings')
    op.drop_index('idx_candidate_matches_posting', table_name='candidate_matches')
    op.drop_index('idx_jobs_user_id', table_name='jobs')

    # 2. Create standardized/new indexes on foreign key columns
    # resume_profiles
    op.create_index('ix_resume_profiles_user_id', 'resume_profiles', ['user_id'], unique=False)
    op.create_index('ix_resume_profiles_active_version_id', 'resume_profiles', ['active_version_id'], unique=False)
    
    # resume_versions
    op.create_index('ix_resume_versions_user_id', 'resume_versions', ['user_id'], unique=False)
    
    # ats_score_history
    op.create_index('ix_ats_score_history_version_id', 'ats_score_history', ['version_id'], unique=False)
    op.create_index('ix_ats_score_history_profile_id', 'ats_score_history', ['profile_id'], unique=False)
    op.create_index('ix_ats_score_history_user_id', 'ats_score_history', ['user_id'], unique=False)
    op.create_index('ix_ats_score_history_job_id', 'ats_score_history', ['job_id'], unique=False)
    
    # match_score_history
    op.create_index('ix_match_score_history_profile_id', 'match_score_history', ['profile_id'], unique=False)
    op.create_index('ix_match_score_history_user_id', 'match_score_history', ['user_id'], unique=False)
    op.create_index('ix_match_score_history_match_result_id', 'match_score_history', ['match_result_id'], unique=False)
    op.create_index('ix_match_score_history_job_id', 'match_score_history', ['job_id'], unique=False)
    op.create_index('ix_match_score_history_version_id', 'match_score_history', ['version_id'], unique=False)
    
    # match_results
    op.create_index('ix_match_results_user_id', 'match_results', ['user_id'], unique=False)
    op.create_index('ix_match_results_version_id', 'match_results', ['version_id'], unique=False)
    op.create_index('ix_match_results_job_id', 'match_results', ['job_id'], unique=False)
    
    # skill_gaps
    op.create_index('ix_skill_gaps_match_result_id', 'skill_gaps', ['match_result_id'], unique=False)
    op.create_index('ix_skill_gaps_user_id', 'skill_gaps', ['user_id'], unique=False)
    
    # applications
    op.create_index('ix_applications_job_id', 'applications', ['job_id'], unique=False)
    op.create_index('ix_applications_version_id', 'applications', ['version_id'], unique=False)
    op.create_index('ix_applications_user_id', 'applications', ['user_id'], unique=False)
    
    # application_packages
    op.create_index('ix_application_packages_application_id', 'application_packages', ['application_id'], unique=False)
    op.create_index('ix_application_packages_user_id', 'application_packages', ['user_id'], unique=False)
    op.create_index('ix_application_packages_tailored_version_id', 'application_packages', ['tailored_version_id'], unique=False)
    op.create_index('ix_application_packages_job_id', 'application_packages', ['job_id'], unique=False)
    
    # outcome_events
    op.create_index('ix_outcome_events_application_id', 'outcome_events', ['application_id'], unique=False)
    op.create_index('ix_outcome_events_version_id', 'outcome_events', ['version_id'], unique=False)
    op.create_index('ix_outcome_events_user_id', 'outcome_events', ['user_id'], unique=False)
    
    # analytics_snapshots
    op.create_index('ix_analytics_snapshots_strongest_resume_version_id', 'analytics_snapshots', ['strongest_resume_version_id'], unique=False)
    
    # agent_audit_log
    op.create_index('ix_agent_audit_log_user_id', 'agent_audit_log', ['user_id'], unique=False)
    
    # learning_roadmaps
    op.create_index('ix_learning_roadmaps_user_id', 'learning_roadmaps', ['user_id'], unique=False)
    op.create_index('ix_learning_roadmaps_match_result_id', 'learning_roadmaps', ['match_result_id'], unique=False)
    
    # roadmap_modules
    op.create_index('ix_roadmap_modules_roadmap_id', 'roadmap_modules', ['roadmap_id'], unique=False)
    op.create_index('ix_roadmap_modules_skill_gap_id', 'roadmap_modules', ['skill_gap_id'], unique=False)
    
    # recommendations
    op.create_index('ix_recommendation_signals_resume_version_id', 'recommendation_signals', ['resume_version_id'], unique=False)
    op.create_index('ix_recommendation_signals_application_id', 'recommendation_signals', ['application_id'], unique=False)
    op.create_index('ix_recommendation_signals_job_match_id', 'recommendation_signals', ['job_match_id'], unique=False)
    op.create_index('ix_recommendation_signals_user_id', 'recommendation_signals', ['user_id'], unique=False)
    
    # recruiters
    op.create_index('ix_recruiters_company_id', 'recruiters', ['company_id'], unique=False)
    
    # company_users
    op.create_index('ix_company_users_company_id', 'company_users', ['company_id'], unique=False)
    op.create_index('ix_company_users_user_id', 'company_users', ['user_id'], unique=False)
    
    # job_postings
    op.create_index('ix_job_postings_posted_by', 'job_postings', ['posted_by'], unique=False)
    op.create_index('ix_job_postings_company_id', 'job_postings', ['company_id'], unique=False)
    
    # candidate_matches
    op.create_index('ix_candidate_matches_version_id', 'candidate_matches', ['version_id'], unique=False)
    op.create_index('ix_candidate_matches_job_posting_id', 'candidate_matches', ['job_posting_id'], unique=False)
    op.create_index('ix_candidate_matches_user_id', 'candidate_matches', ['user_id'], unique=False)
    
    # jobs
    op.create_index('ix_jobs_user_id', 'jobs', ['user_id'], unique=False)


def downgrade() -> None:
    # 1. Drop new standardized/added indexes
    op.drop_index('ix_candidate_matches_user_id', table_name='candidate_matches')
    op.drop_index('ix_candidate_matches_job_posting_id', table_name='candidate_matches')
    op.drop_index('ix_candidate_matches_version_id', table_name='candidate_matches')
    op.drop_index('ix_job_postings_company_id', table_name='job_postings')
    op.drop_index('ix_job_postings_posted_by', table_name='job_postings')
    op.drop_index('ix_company_users_user_id', table_name='company_users')
    op.drop_index('ix_company_users_company_id', table_name='company_users')
    op.drop_index('ix_recruiters_company_id', table_name='recruiters')
    op.drop_index('ix_recommendation_signals_user_id', table_name='recommendation_signals')
    op.drop_index('ix_recommendation_signals_job_match_id', table_name='recommendation_signals')
    op.drop_index('ix_recommendation_signals_application_id', table_name='recommendation_signals')
    op.drop_index('ix_recommendation_signals_resume_version_id', table_name='recommendation_signals')
    op.drop_index('ix_roadmap_modules_skill_gap_id', table_name='roadmap_modules')
    op.drop_index('ix_roadmap_modules_roadmap_id', table_name='roadmap_modules')
    op.drop_index('ix_learning_roadmaps_match_result_id', table_name='learning_roadmaps')
    op.drop_index('ix_learning_roadmaps_user_id', table_name='learning_roadmaps')
    op.drop_index('ix_agent_audit_log_user_id', table_name='agent_audit_log')
    op.drop_index('ix_analytics_snapshots_strongest_resume_version_id', table_name='analytics_snapshots')
    op.drop_index('ix_outcome_events_user_id', table_name='outcome_events')
    op.drop_index('ix_outcome_events_version_id', table_name='outcome_events')
    op.drop_index('ix_outcome_events_application_id', table_name='outcome_events')
    op.drop_index('ix_application_packages_job_id', table_name='application_packages')
    op.drop_index('ix_application_packages_tailored_version_id', table_name='application_packages')
    op.drop_index('ix_application_packages_user_id', table_name='application_packages')
    op.drop_index('ix_application_packages_application_id', table_name='application_packages')
    op.drop_index('ix_applications_user_id', table_name='applications')
    op.drop_index('ix_applications_version_id', table_name='applications')
    op.drop_index('ix_applications_job_id', table_name='applications')
    op.drop_index('ix_skill_gaps_user_id', table_name='skill_gaps')
    op.drop_index('ix_skill_gaps_match_result_id', table_name='skill_gaps')
    op.drop_index('ix_match_results_job_id', table_name='match_results')
    op.drop_index('ix_match_results_version_id', table_name='match_results')
    op.drop_index('ix_match_results_user_id', table_name='match_results')
    op.drop_index('ix_match_score_history_version_id', table_name='match_score_history')
    op.drop_index('ix_match_score_history_job_id', table_name='match_score_history')
    op.drop_index('ix_match_score_history_match_result_id', table_name='match_score_history')
    op.drop_index('ix_match_score_history_user_id', table_name='match_score_history')
    op.drop_index('ix_match_score_history_profile_id', table_name='match_score_history')
    op.drop_index('ix_ats_score_history_job_id', table_name='ats_score_history')
    op.drop_index('ix_ats_score_history_user_id', table_name='ats_score_history')
    op.drop_index('ix_ats_score_history_profile_id', table_name='ats_score_history')
    op.drop_index('ix_ats_score_history_version_id', table_name='ats_score_history')
    op.drop_index('ix_resume_versions_user_id', table_name='resume_versions')
    op.drop_index('ix_resume_profiles_active_version_id', table_name='resume_profiles')
    op.drop_index('ix_resume_profiles_user_id', table_name='resume_profiles')
    op.drop_index('ix_jobs_user_id', table_name='jobs')

    # 2. Re-create old non-standard indexes
    op.create_index('idx_candidate_matches_posting', 'candidate_matches', ['job_posting_id', sa.text('overall_score DESC')])
    op.create_index('idx_job_postings_company', 'job_postings', ['company_id', 'status'])
    op.create_index('idx_recommendation_signals_user', 'recommendation_signals', ['user_id', 'signal_type'])
    op.create_index('idx_roadmap_modules_roadmap', 'roadmap_modules', ['roadmap_id', 'order_index'])
    op.create_index('idx_agent_audit_action', 'agent_audit_log', ['action_type', sa.text('created_at DESC')])
    op.create_index('idx_agent_audit_user', 'agent_audit_log', ['user_id', sa.text('created_at DESC')])
    op.create_index('idx_app_packages_user', 'application_packages', ['user_id', 'approval_status'])
    op.create_index('idx_outcome_events_user', 'outcome_events', ['user_id', sa.text('created_at DESC')])
    op.create_index('idx_outcome_events_app', 'outcome_events', ['application_id', 'event_type'])
    op.create_index('idx_applications_applied_date', 'applications', ['user_id', 'applied_date'])
    op.create_index('idx_applications_status', 'applications', ['user_id', 'status'])
    op.create_index('idx_applications_user_id', 'applications', ['user_id'])
    op.create_index('idx_skill_gaps_user', 'skill_gaps', ['user_id', 'status'])
    op.create_index('idx_match_results_user_version', 'match_results', ['user_id', 'version_id'])
    op.create_index('idx_match_history_version_job', 'match_score_history', ['version_id', 'job_id', 'created_at'])
    op.create_index('idx_match_history_user', 'match_score_history', ['user_id', sa.text('created_at DESC')])
    op.create_index('idx_ats_history_profile', 'ats_score_history', ['profile_id', 'created_at'])
    op.create_index('idx_ats_history_version', 'ats_score_history', ['version_id', 'created_at'])
    op.create_index('idx_resume_versions_user', 'resume_versions', ['user_id', sa.text('created_at DESC')])
    op.create_index('idx_resume_versions_profile', 'resume_versions', ['profile_id', 'version_number'])
    op.create_index('idx_resume_profiles_user', 'resume_profiles', ['user_id'])
    op.create_index('idx_jobs_user_id', 'jobs', ['user_id'])
