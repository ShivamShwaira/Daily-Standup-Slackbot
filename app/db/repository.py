"""Repository pattern for database operations (async)."""

import logging
from typing import Optional, List
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.db.models import User, StandupReport, StandupState, Workspace

logger = logging.getLogger(__name__)


class BaseCRUDRepository:
    """Base async CRUD repository."""

    def __init__(self, session: AsyncSession):
        """Initialize with async session."""
        self.session = session

    async def commit(self) -> None:
        """Commit transaction."""
        await self.session.commit()

    async def rollback(self) -> None:
        """Rollback transaction."""
        await self.session.rollback()


class UserRepository(BaseCRUDRepository):
    """Async repository for User operations."""

    async def create(
        self,
        workspace_id: int,
        slack_user_id: str,
        display_name: str,
        email: Optional[str] = None,
        timezone: Optional[str] = None,
    ) -> User:
        """Create a new user."""
        user = User(
            workspace_id=workspace_id,
            slack_user_id=slack_user_id,
            display_name=display_name,
            email=email,
            timezone=timezone,
        )
        self.session.add(user)
        await self.session.flush()
        logger.info(f"Created user: {slack_user_id}")
        return user

    async def get_by_slack_id(self, slack_user_id: str) -> Optional[User]:
        """Get user by Slack ID."""
        stmt = select(User).where(User.slack_user_id == slack_user_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_slack_id_and_workspace(
        self, slack_user_id: str, workspace_id: int
    ) -> Optional[User]:
        """Get user by Slack ID and workspace."""
        stmt = select(User).where(
            and_(
                User.slack_user_id == slack_user_id,
                User.workspace_id == workspace_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return await self.session.get(User, user_id)

    async def list_active(self) -> List[User]:
        """List all active users."""
        stmt = select(User).where(User.active == True).order_by(User.id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_active_by_workspace(self, workspace_id: int) -> List[User]:
        """List all active users in a workspace."""
        stmt = select(User).where(
            and_(User.active == True, User.workspace_id == workspace_id)
        ).order_by(User.id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_all(self) -> List[User]:
        """List all users."""
        stmt = select(User).order_by(User.id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update(self, user_id: int, **kwargs) -> Optional[User]:
        """Update user fields."""
        user = await self.get_by_id(user_id)
        if not user:
            return None

        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)

        user.updated_at = datetime.utcnow()
        await self.session.flush()
        logger.info(f"Updated user: {user_id}")
        return user

    async def delete(self, user_id: int) -> bool:
        """Delete user by ID (cascade deletes reports and state)."""
        user = await self.get_by_id(user_id)
        if not user:
            return False

        await self.session.delete(user)
        await self.session.flush()
        logger.info(f"Deleted user: {user_id}")
        return True

    async def count_active(self) -> int:
        """Count active users."""
        stmt = select(func.count(User.id)).where(User.active == True)
        result = await self.session.execute(stmt)
        return result.scalar() or 0


class StandupReportRepository(BaseCRUDRepository):
    """Async repository for StandupReport operations."""

    async def create(
        self,
        user_id: int,
        report_date: date,
        feeling: Optional[str] = None,
        yesterday: Optional[str] = None,
        today: Optional[str] = None,
        blockers: Optional[str] = None,
        skipped: bool = False,
    ) -> StandupReport:
        """Create a new standup report."""
        report = StandupReport(
            user_id=user_id,
            report_date=report_date,
            feeling=feeling,
            yesterday=yesterday,
            today=today,
            blockers=blockers,
            skipped=skipped,
        )
        self.session.add(report)
        await self.session.flush()
        logger.info(f"Created report for user {user_id} on {report_date}")
        return report

    async def get_by_user_date(self, user_id: int, report_date: date) -> Optional[StandupReport]:
        """Get report by user and date."""
        stmt = select(StandupReport).where(
            and_(
                StandupReport.user_id == user_id,
                StandupReport.report_date == report_date,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_id(self, report_id: int) -> Optional[StandupReport]:
        """Get report by ID."""
        return await self.session.get(StandupReport, report_id)

    async def get_latest_by_user(self, user_id: int) -> Optional[StandupReport]:
        """Get most recent report for user."""
        stmt = (
            select(StandupReport)
            .where(StandupReport.user_id == user_id)
            .order_by(StandupReport.report_date.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def update(self, report_id: int, **kwargs) -> Optional[StandupReport]:
        """Update report fields."""
        report = await self.session.get(StandupReport, report_id)
        if not report:
            return None

        for key, value in kwargs.items():
            if hasattr(report, key):
                setattr(report, key, value)

        report.updated_at = datetime.utcnow()
        await self.session.flush()
        logger.info(f"Updated report: {report_id}")
        return report

    async def mark_completed(self, report_id: int) -> Optional[StandupReport]:
        """Mark report as completed."""
        return await self.update(report_id, completed_at=datetime.utcnow())

    async def list_for_date(self, report_date: date) -> List[StandupReport]:
        """List all reports for a specific date."""
        stmt = (
            select(StandupReport)
            .where(StandupReport.report_date == report_date)
            .order_by(StandupReport.created_at)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_completed_for_date(self, report_date: date) -> List[StandupReport]:
        """List completed reports for a date."""
        stmt = (
            select(StandupReport)
            .where(
                and_(
                    StandupReport.report_date == report_date,
                    StandupReport.completed_at.isnot(None),
                    StandupReport.skipped == False,
                )
            )
            .order_by(StandupReport.completed_at)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class StandupStateRepository(BaseCRUDRepository):
    """Async repository for StandupState operations."""

    async def create_or_update(
        self,
        user_id: int,
        pending_report_date: date,
        current_question_index: int = 0,
    ) -> StandupState:
        """Create or update standup state for user."""
        state = await self.get_by_user(user_id)

        if state:
            state.pending_report_date = pending_report_date
            state.current_question_index = current_question_index
            state.updated_at = datetime.utcnow()
        else:
            state = StandupState(
                user_id=user_id,
                pending_report_date=pending_report_date,
                current_question_index=current_question_index,
            )
            self.session.add(state)

        await self.session.flush()
        logger.info(f"Updated state for user {user_id}: q_index={current_question_index}")
        return state

    async def get_by_user(self, user_id: int) -> Optional[StandupState]:
        """Get state for user."""
        stmt = select(StandupState).where(StandupState.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def increment_question(self, user_id: int) -> Optional[StandupState]:
        """Increment current question index."""
        state = await self.get_by_user(user_id)
        if not state:
            return None

        state.current_question_index += 1
        state.updated_at = datetime.utcnow()
        await self.session.flush()
        return state

    async def delete(self, user_id: int) -> bool:
        """Delete state for user."""
        state = await self.get_by_user(user_id)
        if not state:
            return False

        await self.session.delete(state)
        await self.session.flush()
        logger.info(f"Deleted state for user {user_id}")
        return True


class WorkspaceRepository(BaseCRUDRepository):
    """Async repository for Workspace operations."""

    async def get_or_create_default(self, slack_team_id: str, report_channel_id: str) -> Workspace:
        """Get or create default workspace."""
        stmt = select(Workspace).where(Workspace.slack_team_id == slack_team_id)
        result = await self.session.execute(stmt)
        workspace = result.scalars().first()

        if not workspace:
            workspace = Workspace(
                slack_team_id=slack_team_id,
                report_channel_id=report_channel_id,
            )
            self.session.add(workspace)
            await self.session.flush()
            logger.info(f"Created workspace: {slack_team_id}")

        return workspace

    async def get_by_team_id(self, slack_team_id: str) -> Optional[Workspace]:
        """Get workspace by Slack team ID."""
        stmt = select(Workspace).where(Workspace.slack_team_id == slack_team_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def update(self, workspace_id: int, **kwargs) -> Optional[Workspace]:
        """Update workspace."""
        workspace = await self.session.get(Workspace, workspace_id)
        if not workspace:
            return None

        for key, value in kwargs.items():
            if hasattr(workspace, key):
                setattr(workspace, key, value)

        workspace.updated_at = datetime.utcnow()
        await self.session.flush()
        logger.info(f"Updated workspace: {workspace_id}")
        return workspace
