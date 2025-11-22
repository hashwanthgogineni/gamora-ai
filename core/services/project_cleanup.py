import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import shutil

logger = logging.getLogger(__name__)


class ProjectCleanupService:
    # Manages automatic cleanup of old projects
    def __init__(self, projects_dir: Path, db_manager=None):
        self.projects_dir = Path(projects_dir)
        self.db_manager = db_manager
        
        # Cleanup policies (in days)
        self.failed_project_retention_days = 1  # Delete failed projects after 1 day
        self.completed_project_retention_days = 7  # Delete completed projects after 7 days
        self.incomplete_project_retention_days = 1  # Delete incomplete projects after 1 day
    
    async def cleanup_old_projects(self, dry_run: bool = False) -> Dict[str, int]:
        """
        Clean up old projects based on retention policies
        
        Returns:
            Dict with cleanup statistics
        """
        stats = {
            'deleted': 0,
            'failed': 0,
            'skipped': 0,
            'errors': 0,
            'space_freed_mb': 0
        }
        
        if not self.projects_dir.exists():
            logger.info(f"📁 Creating projects directory: {self.projects_dir}")
            self.projects_dir.mkdir(parents=True, exist_ok=True)
            return stats
        
        logger.info(f"Starting project cleanup (dry_run={dry_run})...")
        
        # Get all project directories
        project_dirs = [d for d in self.projects_dir.iterdir() if d.is_dir()]
        
        for project_dir in project_dirs:
            project_id = project_dir.name
            
            try:
                # Get project status from database if available
                project_status = None
                project_created = None
                
                if self.db_manager:
                    try:
                        project = await self.db_manager.get_project(project_id)
                        if project:
                            project_status = project.get('status')
                            created_at = project.get('created_at')
                            if created_at:
                                if isinstance(created_at, str):
                                    project_created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                                else:
                                    project_created = created_at
                    except Exception as e:
                        logger.debug(f"Could not get project status for {project_id}: {e}")
                
                # Determine if project should be deleted
                should_delete, reason = self._should_delete_project(
                    project_dir,
                    project_status,
                    project_created
                )
                
                if should_delete:
                    if dry_run:
                        logger.info(f"  [DRY RUN] Would delete: {project_id} ({reason})")
                        stats['skipped'] += 1
                    else:
                        # Delete project directory
                        size_mb = self._get_directory_size_mb(project_dir)
                        shutil.rmtree(project_dir)
                        stats['deleted'] += 1
                        stats['space_freed_mb'] += size_mb
                        logger.info(f"  Deleted: {project_id} ({reason}) - {size_mb:.2f} MB freed")
                        
                        # Optionally delete from database
                        if self.db_manager:
                            try:
                                # Database will handle cascade deletes for builds/logs
                                # We could add a delete_project method if needed
                                pass
                            except Exception as e:
                                logger.warning(f"  ⚠️  Could not delete project from database: {e}")
                else:
                    stats['skipped'] += 1
                    
            except Exception as e:
                logger.error(f"  ❌ Error processing {project_id}: {e}", exc_info=True)
                stats['errors'] += 1
        
        logger.info(
            f"🧹 Cleanup complete: {stats['deleted']} deleted, "
            f"{stats['skipped']} kept, {stats['errors']} errors, "
            f"{stats['space_freed_mb']:.2f} MB freed"
        )
        
        return stats
    
    def _should_delete_project(
        self,
        project_dir: Path,
        status: Optional[str],
        created_at: Optional[datetime]
    ) -> Tuple[bool, str]:
        # Determines if a project should be deleted
        # Check directory age
        dir_mtime = datetime.fromtimestamp(project_dir.stat().st_mtime)
        age_days = (datetime.now() - dir_mtime).days
        
        # If we have database info, use it
        if status and created_at:
            age_days = (datetime.now() - created_at.replace(tzinfo=None)).days
            
            # Failed projects: delete after 1 day
            if status in ['failed', 'error', 'cancelled']:
                if age_days >= self.failed_project_retention_days:
                    return True, f"failed project ({age_days} days old)"
            
            # Incomplete/generating projects: delete after 1 day
            if status in ['generating', 'pending', 'incomplete']:
                if age_days >= self.incomplete_project_retention_days:
                    return True, f"incomplete project ({age_days} days old)"
            
            # Completed projects: delete after 7 days
            if status == 'completed':
                if age_days >= self.completed_project_retention_days:
                    return True, f"completed project ({age_days} days old)"
        
        # Fallback: if no database info, use directory age
        # Delete if older than 7 days and no clear status
        if age_days >= self.completed_project_retention_days:
            return True, f"old project directory ({age_days} days old, no status)"
        
        return False, "within retention period"
    
    def _get_directory_size_mb(self, directory: Path) -> float:
        # Calculates directory size in MB
        total_size = 0
        try:
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except Exception as e:
            logger.debug(f"Error calculating size for {directory}: {e}")
        
        return total_size / (1024 * 1024)  # Convert to MB
    
    async def cleanup_on_startup(self):
        # Runs cleanup on server startup
        logger.info("🧹 Running startup project cleanup...")
        stats = await self.cleanup_old_projects(dry_run=False)
        return stats
    
    async def get_cleanup_stats(self) -> Dict[str, any]:
        # Gets statistics about projects that could be cleaned up
        stats = {
            'total_projects': 0,
            'failed_projects': 0,
            'completed_projects': 0,
            'incomplete_projects': 0,
            'total_size_mb': 0,
            'cleanup_candidates': 0,
            'space_to_free_mb': 0
        }
        
        if not self.projects_dir.exists():
            return stats
        
        project_dirs = [d for d in self.projects_dir.iterdir() if d.is_dir()]
        stats['total_projects'] = len(project_dirs)
        
        for project_dir in project_dirs:
            project_id = project_dir.name
            size_mb = self._get_directory_size_mb(project_dir)
            stats['total_size_mb'] += size_mb
            
            # Get project status
            project_status = None
            project_created = None
            
            if self.db_manager:
                try:
                    project = await self.db_manager.get_project(project_id)
                    if project:
                        project_status = project.get('status')
                        created_at = project.get('created_at')
                        if created_at:
                            if isinstance(created_at, str):
                                project_created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            else:
                                project_created = created_at
                except:
                    pass
            
            # Categorize project
            if project_status == 'failed':
                stats['failed_projects'] += 1
            elif project_status == 'completed':
                stats['completed_projects'] += 1
            elif project_status in ['generating', 'pending', 'incomplete']:
                stats['incomplete_projects'] += 1
            
            # Check if it's a cleanup candidate
            should_delete, _ = self._should_delete_project(
                project_dir,
                project_status,
                project_created
            )
            
            if should_delete:
                stats['cleanup_candidates'] += 1
                stats['space_to_free_mb'] += size_mb
        
        return stats

