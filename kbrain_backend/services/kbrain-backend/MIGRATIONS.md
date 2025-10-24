# Database Migrations with Alembic

This project uses Alembic for database schema migrations.

## Setup

Alembic is already configured and initialized. The configuration files are:
- `alembic.ini` - Alembic configuration
- `alembic/env.py` - Migration environment setup
- `alembic/versions/` - Migration scripts

## Common Commands

### Create a new migration (after model changes)

```bash
cd services/kbrain-backend
alembic revision --autogenerate -m "Description of changes"
```

This will:
1. Compare your SQLAlchemy models with the database schema
2. Generate a migration script with the detected changes
3. Save it in `alembic/versions/`

**Always review the generated migration before applying it!**

### Apply migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply migrations up to a specific revision
alembic upgrade <revision_id>

# Upgrade by one revision
alembic upgrade +1
```

### Rollback migrations

```bash
# Rollback to previous revision
alembic downgrade -1

# Rollback to a specific revision
alembic downgrade <revision_id>

# Rollback all migrations
alembic downgrade base
```

### Check migration status

```bash
# Show current revision
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic history --verbose
```

## Database Connection

The database connection is configured in `.env` file:

```bash
DATABASE_URL=postgresql+asyncpg://kbrain:kbrain@localhost:5438/kbrain
```

Note: Alembic uses a synchronous PostgreSQL driver (psycopg2), so the URL is automatically converted from `postgresql+asyncpg://` to `postgresql://` in `alembic/env.py`.

## Workflow for Model Changes

1. **Modify your models** in `src/kbrain_backend/core/models/`
2. **Generate migration**: `alembic revision --autogenerate -m "Add new field"`
3. **Review the migration** in `alembic/versions/`
4. **Apply migration**: `alembic upgrade head`
5. **Commit both** the model changes and migration file to git

## Docker Setup

When using Docker:

```bash
# Start database
docker-compose up -d postgres

# Run migrations (from host or inside container)
alembic upgrade head
```

## Troubleshooting

### "Target database is not up to date"
This means you have migration files that haven't been applied. Run:
```bash
alembic upgrade head
```

### Clean slate (development only)
To start fresh:
```bash
# Stop and remove database
docker-compose down -v postgres

# Start fresh database
docker-compose up -d postgres

# Wait a few seconds for DB to start
sleep 5

# Apply all migrations
alembic upgrade head
```

## Migration File Structure

Each migration has:
- `revision`: Unique identifier
- `down_revision`: Previous migration ID
- `upgrade()`: Changes to apply
- `downgrade()`: How to revert changes

Example:
```python
def upgrade() -> None:
    op.create_table('new_table',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('new_table')
```