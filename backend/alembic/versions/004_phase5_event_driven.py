"""Phase V: Event-driven architecture tables

Task: T-501 - Create migration file skeleton for Phase V
Phase: Phase 1 - Database Migrations and Schema Extensions

This migration extends the database schema for Phase V features:
- Task reminders with due dates and notification preferences
- Recurring task patterns with flexible scheduling
- Event sourcing and audit logging
- Notification history tracking

Revision ID: 004
Revises: 003
Create Date: 2026-01-08

Note: Filename follows task specification. Subsequent tasks (T-502 onwards)
will populate upgrade() and downgrade() with actual migration logic.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    """
    Apply Phase V schema changes.

    This function will be populated by subsequent tasks:
    - T-502: Extend tasks table with reminder/recurrence columns ✅ COMPLETE
    - T-503: Add indexes for tasks table extensions ✅ COMPLETE
    - T-504: Create recurrence_patterns table ✅ COMPLETE
    - T-505: Add recurrence_patterns constraints ✅ COMPLETE
    - T-506: Add recurrence_patterns indexes ✅ COMPLETE
    - T-507: Create reminders table ✅ COMPLETE
    - T-508: Add reminders constraints
    - T-509: Add reminders indexes
    - T-510: Create events table (audit log)
    - T-511: Add events indexes
    - T-512: Create notifications table
    - T-513: Add notifications constraints
    - T-514: Add notifications indexes

    Current status: T-507 complete
    """

    # ========================================================================
    # T-502: Extend tasks table with Phase V columns
    # ========================================================================
    # Add support for task reminders with due dates and notification preferences
    op.add_column('tasks', sa.Column('due_date', sa.TIMESTAMP(), nullable=True))
    op.add_column('tasks', sa.Column('reminder_time', sa.TIMESTAMP(), nullable=True))
    op.add_column('tasks', sa.Column('reminder_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    # Add support for recurring task patterns
    # Note: Foreign key constraint will be added in subsequent task (not T-502)
    op.add_column('tasks', sa.Column('recurrence_pattern_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('tasks', sa.Column('recurrence_instance_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('tasks', sa.Column('is_recurring', sa.Boolean(), server_default='false', nullable=False))

    # ========================================================================
    # T-503: Add partial indexes for tasks table extensions
    # ========================================================================
    # Partial indexes improve query performance for tasks with due dates and recurring patterns
    # Only index rows where the column is NOT NULL (most tasks may not have these fields)
    op.create_index(
        'idx_tasks_due_date',
        'tasks',
        ['due_date'],
        postgresql_where=sa.text('due_date IS NOT NULL')
    )
    op.create_index(
        'idx_tasks_recurrence_pattern',
        'tasks',
        ['recurrence_pattern_id'],
        postgresql_where=sa.text('recurrence_pattern_id IS NOT NULL')
    )

    # ========================================================================
    # T-504: Create recurrence_patterns table
    # ========================================================================
    # Store recurring task patterns with flexible scheduling rules
    # Supports daily, weekly, monthly, yearly, and custom recurrence patterns
    op.create_table(
        'recurrence_patterns',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_template', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('frequency', sa.String(length=20), nullable=False),
        sa.Column('interval', sa.Integer(), nullable=False),
        sa.Column('days_of_week', postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column('day_of_month', sa.Integer(), nullable=True),
        sa.Column('end_date', sa.TIMESTAMP(), nullable=True),
        sa.Column('max_occurrences', sa.Integer(), nullable=True),
        sa.Column('timezone', sa.String(length=50), nullable=False, server_default='UTC'),
        sa.Column('last_generated_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id')
    )

    # ========================================================================
    # T-505: Add recurrence_patterns constraints
    # ========================================================================
    # Data integrity constraints to ensure valid recurrence pattern configurations

    # Constraint 1: Validate frequency is one of the supported pattern types
    op.create_check_constraint(
        'ck_recurrence_frequency',
        'recurrence_patterns',
        sa.text("frequency IN ('daily', 'weekly', 'monthly', 'yearly', 'custom')")
    )

    # Constraint 2: Ensure interval is positive (must repeat at least every 1 unit)
    op.create_check_constraint(
        'ck_recurrence_interval_positive',
        'recurrence_patterns',
        sa.text('interval > 0')
    )

    # Constraint 3: Mutual exclusion - only one end condition allowed
    # Pattern must end by date OR by occurrence count, not both
    op.create_check_constraint(
        'ck_recurrence_end_condition',
        'recurrence_patterns',
        sa.text('(end_date IS NULL) OR (max_occurrences IS NULL)')
    )

    # Constraint 4: Foreign key to users table with CASCADE delete
    # When user is deleted, all their recurrence patterns are deleted
    op.create_foreign_key(
        'fk_recurrence_patterns_user_id',
        'recurrence_patterns',
        'users',
        ['user_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # ========================================================================
    # T-506: Add recurrence_patterns indexes
    # ========================================================================
    # Performance optimization indexes for recurring pattern queries

    # Index 1: User lookup - optimize queries by user_id
    # Used by: GET /api/tasks/recurring (list user's patterns)
    op.create_index(
        'idx_recurrence_user',
        'recurrence_patterns',
        ['user_id']
    )

    # Index 2: Generation tracking - optimize recurring task generator queries
    # Used by: CronJob to find patterns needing new instances
    # Queries filter by last_generated_at to avoid duplicate generation
    op.create_index(
        'idx_recurrence_last_generated',
        'recurrence_patterns',
        ['last_generated_at']
    )

    # ========================================================================
    # T-507: Create reminders table
    # ========================================================================
    # Track scheduled reminders for tasks with due dates
    # Reminder Service uses this table to manage reminder scheduling and firing
    op.create_table(
        'reminders',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scheduled_time', sa.TIMESTAMP(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('notification_channels', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('fired_at', sa.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    # Note: Foreign keys, CHECK constraints, and indexes will be added by T-508 and T-509
    # ========================================================================
    # T-508: Add reminders constraints
    # ========================================================================
    # Data integrity constraints for the reminders table

    # Constraint 1: Validate reminder status
    op.create_check_constraint(
        'ck_reminders_status',
        'reminders',
        sa.text("status IN ('pending', 'fired', 'cancelled')")
    )

    # Constraint 2: Foreign key to tasks table with CASCADE delete
    op.create_foreign_key(
        'fk_reminders_task_id',
        'reminders',
        'tasks',
        ['task_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # Constraint 3: Foreign key to users table with CASCADE delete
    op.create_foreign_key(
        'fk_reminders_user_id',
        'reminders',
        'users',
        ['user_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # ========================================================================
    # T-509: Add reminders indexes
    # ========================================================================
    # Performance optimization indexes for reminder queries

    # Index 1: Task lookup - optimize queries by task_id
    op.create_index(
        'idx_reminders_task_id',
        'reminders',
        ['task_id']
    )

    # Index 2: User lookup - optimize queries by user_id
    op.create_index(
        'idx_reminders_user_id',
        'reminders',
        ['user_id']
    )

    # Index 3: Scheduling tracking - optimize reminder worker queries
    op.create_index(
        'idx_reminders_scheduled_time',
        'reminders',
        ['scheduled_time']
    )

    # ========================================================================
    # T-510: Create events table (audit log)
    # ========================================================================
    # Store system and user events for audit logging and event sourcing
    # Provides a complete history of changes across the system
    op.create_table(
        'events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('aggregate_type', sa.String(length=50), nullable=False),
        sa.Column('aggregate_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id')
    )

    # ========================================================================
    # T-511: Add basic CHECK constraints to events table
    # ========================================================================
    # Data integrity constraints for the events table

    # Constraint 1: Ensure event_type is not empty
    op.create_check_constraint(
        'ck_events_event_type_not_empty',
        'events',
        sa.text("length(event_type) > 0")
    )

    # Constraint 2: Ensure aggregate_type is not empty
    op.create_check_constraint(
        'ck_events_aggregate_type_not_empty',
        'events',
        sa.text("length(aggregate_type) > 0")
    )

    # ========================================================================
    # T-512: Add indexes to events table
    # ========================================================================
    # Performance optimization indexes for the events table

    # Index 1: Lookups by entity - optimize history/audit trails for objects
    op.create_index(
        'idx_events_aggregate',
        'events',
        ['aggregate_type', 'aggregate_id']
    )

    # Index 2: Time-based lookups - optimize chronological event queries
    op.create_index(
        'idx_events_created_at',
        'events',
        ['created_at']
    )

    # Note: Index for unprocessed events skipped as 'processed' column does not exist.
    # TODO: Add partial index for unprocessed events when 'processed' column is added in a future task.

    # ========================================================================
    # T-513: Create notifications table
    # ========================================================================
    # Track sent and pending notifications across multiple channels
    # Provides notification history and delivery tracking
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('reminder_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('channel', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('attempt', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('sent_at', sa.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # ========================================================================
    # T-514: Add constraints to notifications table
    # ========================================================================
    # Data integrity constraints for the notifications table

    # Constraint 1: Validate notification status
    op.create_check_constraint(
        'ck_notifications_status',
        'notifications',
        sa.text("status IN ('pending', 'sent', 'failed')")
    )

    # Constraint 2: Ensure attempt count is non-negative
    op.create_check_constraint(
        'ck_notifications_attempt_non_negative',
        'notifications',
        sa.text('attempt >= 0')
    )

    # Constraint 3: Foreign key to reminders table with CASCADE delete
    op.create_foreign_key(
        'fk_notifications_reminder_id',
        'notifications',
        'reminders',
        ['reminder_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # Constraint 4: Foreign key to users table with CASCADE delete
    op.create_foreign_key(
        'fk_notifications_user_id',
        'notifications',
        'users',
        ['user_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # ========================================================================
    # T-515: Add indexes to notifications table
    # ========================================================================
    # Performance optimization indexes for notification queries

    # Index 1: Reminder lookup - optimize queries by reminder_id
    # Used by: GET /api/notifications?reminder_id=X (list notifications for a reminder)
    op.create_index(
        'idx_notifications_reminder_id',
        'notifications',
        ['reminder_id']
    )

    # Index 2: User lookup - optimize queries by user_id
    # Used by: GET /api/notifications?user_id=X (list user's notifications)
    op.create_index(
        'idx_notifications_user_id',
        'notifications',
        ['user_id']
    )

    # Index 3: Status and time tracking - optimize notification worker queries
    # Used by: Worker to find pending notifications ordered by creation time
    # Composite index on (status, created_at) for efficient filtering and sorting
    op.create_index(
        'idx_notifications_status_created',
        'notifications',
        ['status', 'created_at']
    )


def downgrade():
    """
    Reverse Phase V schema changes.

    This function will be populated by task T-515 to reverse all changes
    made in upgrade(), ensuring clean rollback capability.

    Current status: Skeleton only (T-501 complete)
    """
    # Rollback logic will be added by task T-515
    pass
