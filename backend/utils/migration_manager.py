#!/usr/bin/env python3
"""
Migration management utility for Flask-Migrate with backup and rollback capabilities.
"""

import os
import sys
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config

class MigrationManager:
    """Migration management utility with backup and rollback capabilities."""
    
    def __init__(self, config_name='development'):
        self.config_name = config_name
        self.config = config[config_name]
        self.project_root = Path(__file__).parent.parent
        self.migrations_dir = self.project_root / 'migrations'
        self.backups_dir = self.project_root / 'backups'
        
        # Ensure backups directory exists
        self.backups_dir.mkdir(exist_ok=True)
        
    def _run_flask_command(self, command, capture_output=True):
        """Run a Flask command with proper environment setup."""
        env = os.environ.copy()
        env['FLASK_ENV'] = self.config_name
        env['FLASK_APP'] = 'app.py'
        
        cmd = f"flask {command}"
        print(f"Running: {cmd}")
        
        try:
            result = subprocess.run(
                cmd.split(),
                cwd=self.project_root,
                env=env,
                capture_output=capture_output,
                text=True,
                check=True
            )
            
            if capture_output:
                return result.stdout, result.stderr
            return None, None
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Command failed with exit code {e.returncode}"
            if capture_output:
                error_msg += f"\nSTDOUT: {e.stdout}\nSTDERR: {e.stderr}"
            raise Exception(error_msg)
    
    def _backup_database(self):
        """Create a database backup before migrations."""
        if self.config_name == 'production':
            print("🔄 Creating database backup...")
            
            db_config = self._parse_db_config()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backups_dir / f"backup_{timestamp}.sql"
            
            # Create PostgreSQL backup
            backup_cmd = [
                'pg_dump',
                '-h', db_config['host'],
                '-p', str(db_config['port']),
                '-U', db_config['user'],
                '-d', db_config['database'],
                '-f', str(backup_file),
                '--no-password'
            ]
            
            env = os.environ.copy()
            env['PGPASSWORD'] = db_config['password']
            
            try:
                subprocess.run(backup_cmd, env=env, check=True)
                print(f"✅ Database backup created: {backup_file}")
                return backup_file
            except subprocess.CalledProcessError as e:
                print(f"⚠️  Backup failed: {e}")
                return None
        else:
            print("ℹ️  Skipping backup for non-production environment")
            return None
    
    def _parse_db_config(self):
        """Parse database configuration from URL."""
        url = self.config.SQLALCHEMY_DATABASE_URI
        # Extract components from postgresql://user:pass@host:port/db
        parts = url.replace('postgresql://', '').split('@')
        user_pass = parts[0].split(':')
        host_port_db = parts[1].split('/')
        host_port = host_port_db[0].split(':')
        
        return {
            'user': user_pass[0],
            'password': user_pass[1],
            'host': host_port[0],
            'port': int(host_port[1]) if len(host_port) > 1 else 5432,
            'database': host_port_db[1]
        }
    
    def init_migrations(self):
        """Initialize migration repository."""
        print("🔧 Initializing migration repository...")
        
        if self.migrations_dir.exists():
            print("⚠️  Migrations directory already exists")
            return False
        
        try:
            stdout, stderr = self._run_flask_command('db init')
            print("✅ Migration repository initialized")
            print(f"Output: {stdout}")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize migrations: {e}")
            return False
    
    def create_migration(self, message=None):
        """Create a new migration."""
        if not message:
            message = f"Migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print(f"📝 Creating migration: {message}")
        
        try:
            stdout, stderr = self._run_flask_command(f'db migrate -m "{message}"')
            print("✅ Migration created successfully")
            print(f"Output: {stdout}")
            
            # Show created migration file
            if self.migrations_dir.exists():
                versions_dir = self.migrations_dir / 'versions'
                if versions_dir.exists():
                    migration_files = sorted(versions_dir.glob('*.py'))
                    if migration_files:
                        latest_migration = migration_files[-1]
                        print(f"📄 Created migration file: {latest_migration.name}")
            
            return True
        except Exception as e:
            print(f"❌ Failed to create migration: {e}")
            return False
    
    def upgrade_database(self, revision='head'):
        """Upgrade database to a specific revision."""
        print(f"⬆️  Upgrading database to revision: {revision}")
        
        # Create backup for production
        backup_file = self._backup_database()
        
        try:
            stdout, stderr = self._run_flask_command(f'db upgrade {revision}')
            print("✅ Database upgrade completed successfully")
            print(f"Output: {stdout}")
            return True
        except Exception as e:
            print(f"❌ Database upgrade failed: {e}")
            
            # Offer to restore backup for production
            if backup_file and self.config_name == 'production':
                print(f"💾 Backup available at: {backup_file}")
                print("Consider restoring from backup if needed")
            
            return False
    
    def downgrade_database(self, revision):
        """Downgrade database to a specific revision."""
        print(f"⬇️  Downgrading database to revision: {revision}")
        
        # Create backup for production
        backup_file = self._backup_database()
        
        try:
            stdout, stderr = self._run_flask_command(f'db downgrade {revision}')
            print("✅ Database downgrade completed successfully")
            print(f"Output: {stdout}")
            return True
        except Exception as e:
            print(f"❌ Database downgrade failed: {e}")
            
            # Offer to restore backup for production
            if backup_file and self.config_name == 'production':
                print(f"💾 Backup available at: {backup_file}")
                print("Consider restoring from backup if needed")
            
            return False
    
    def show_migration_history(self):
        """Show migration history."""
        print("📋 Migration history:")
        
        try:
            stdout, stderr = self._run_flask_command('db history')
            print(stdout)
            return True
        except Exception as e:
            print(f"❌ Failed to show migration history: {e}")
            return False
    
    def show_current_revision(self):
        """Show current database revision."""
        print("🔍 Current database revision:")
        
        try:
            stdout, stderr = self._run_flask_command('db current')
            print(stdout)
            return True
        except Exception as e:
            print(f"❌ Failed to show current revision: {e}")
            return False
    
    def show_migration_heads(self):
        """Show migration heads."""
        print("👑 Migration heads:")
        
        try:
            stdout, stderr = self._run_flask_command('db heads')
            print(stdout)
            return True
        except Exception as e:
            print(f"❌ Failed to show migration heads: {e}")
            return False
    
    def validate_migrations(self):
        """Validate migration files."""
        print("🔍 Validating migrations...")
        
        if not self.migrations_dir.exists():
            print("❌ No migrations directory found")
            return False
        
        versions_dir = self.migrations_dir / 'versions'
        if not versions_dir.exists():
            print("❌ No versions directory found")
            return False
        
        migration_files = list(versions_dir.glob('*.py'))
        if not migration_files:
            print("ℹ️  No migration files found")
            return True
        
        print(f"📁 Found {len(migration_files)} migration files:")
        for migration_file in sorted(migration_files):
            print(f"   - {migration_file.name}")
            
            # Basic validation - check if file is valid Python
            try:
                with open(migration_file, 'r') as f:
                    content = f.read()
                    # Check for required functions
                    if 'def upgrade():' not in content:
                        print(f"   ⚠️  Missing upgrade() function in {migration_file.name}")
                    if 'def downgrade():' not in content:
                        print(f"   ⚠️  Missing downgrade() function in {migration_file.name}")
                    
            except Exception as e:
                print(f"   ❌ Error reading {migration_file.name}: {e}")
                return False
        
        print("✅ Migration validation completed")
        return True
    
    def run_migrations(self):
        """Run full migration setup (init + create + upgrade)."""
        print("🚀 Running full migration setup...")
        
        success = True
        
        # Initialize if needed
        if not self.migrations_dir.exists():
            success &= self.init_migrations()
        
        # Check if we need to create initial migration
        versions_dir = self.migrations_dir / 'versions'
        if not versions_dir.exists() or not list(versions_dir.glob('*.py')):
            print("📝 Creating initial migration...")
            success &= self.create_migration("Initial database schema")
        
        # Upgrade to latest
        if success:
            success &= self.upgrade_database()
        
        if success:
            print("🎉 Migration setup completed successfully!")
            self.show_current_revision()
        else:
            print("❌ Migration setup failed")
        
        return success
    
    def cleanup_old_backups(self, keep_days=30):
        """Clean up old backup files."""
        print(f"🧹 Cleaning up backups older than {keep_days} days...")
        
        cutoff_date = datetime.now().timestamp() - (keep_days * 24 * 3600)
        deleted_count = 0
        
        for backup_file in self.backups_dir.glob('backup_*.sql'):
            if backup_file.stat().st_mtime < cutoff_date:
                try:
                    backup_file.unlink()
                    print(f"   🗑️  Deleted old backup: {backup_file.name}")
                    deleted_count += 1
                except Exception as e:
                    print(f"   ⚠️  Failed to delete {backup_file.name}: {e}")
        
        print(f"✅ Cleaned up {deleted_count} old backup files")
        return deleted_count

def main():
    """Command-line interface for migration manager."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migration management utility')
    parser.add_argument('--config', default='development',
                       choices=['development', 'testing', 'production'],
                       help='Configuration to use')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Init command
    subparsers.add_parser('init', help='Initialize migration repository')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create new migration')
    create_parser.add_argument('-m', '--message', help='Migration message')
    
    # Upgrade command
    upgrade_parser = subparsers.add_parser('upgrade', help='Upgrade database')
    upgrade_parser.add_argument('revision', nargs='?', default='head', help='Target revision')
    
    # Downgrade command
    downgrade_parser = subparsers.add_parser('downgrade', help='Downgrade database')
    downgrade_parser.add_argument('revision', help='Target revision')
    
    # Status commands
    subparsers.add_parser('history', help='Show migration history')
    subparsers.add_parser('current', help='Show current revision')
    subparsers.add_parser('heads', help='Show migration heads')
    subparsers.add_parser('validate', help='Validate migration files')
    
    # Utility commands
    subparsers.add_parser('setup', help='Run full migration setup')
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up old backups')
    cleanup_parser.add_argument('--days', type=int, default=30, help='Keep backups newer than N days')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    manager = MigrationManager(args.config)
    
    try:
        if args.command == 'init':
            success = manager.init_migrations()
        elif args.command == 'create':
            success = manager.create_migration(args.message)
        elif args.command == 'upgrade':
            success = manager.upgrade_database(args.revision)
        elif args.command == 'downgrade':
            success = manager.downgrade_database(args.revision)
        elif args.command == 'history':
            success = manager.show_migration_history()
        elif args.command == 'current':
            success = manager.show_current_revision()
        elif args.command == 'heads':
            success = manager.show_migration_heads()
        elif args.command == 'validate':
            success = manager.validate_migrations()
        elif args.command == 'setup':
            success = manager.run_migrations()
        elif args.command == 'cleanup':
            manager.cleanup_old_backups(args.days)
            success = True
        else:
            print(f"Unknown command: {args.command}")
            success = False
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Operation failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()