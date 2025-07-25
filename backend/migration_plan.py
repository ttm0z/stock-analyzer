#!/usr/bin/env python3
"""
Database Migration Plan: Float to Numeric Conversion
This script provides the migration strategy to convert Float fields to Numeric
"""

import os
from decimal import Decimal
from sqlalchemy import text, inspect
from flask import Flask
from app import create_app, db

class DatabaseMigrator:
    """Handles migration from Float to Numeric data types"""
    
    def __init__(self, app=None):
        self.app = app or create_app('development')
        
    def check_migration_status(self):
        """Check current database schema status"""
        with self.app.app_context():
            inspector = inspect(db.engine)
            
            # Check portfolios table structure
            try:
                portfolios_columns = inspector.get_columns('portfolios')
                float_columns = []
                numeric_columns = []
                
                for col in portfolios_columns:
                    if 'FLOAT' in str(col['type']).upper():
                        float_columns.append(col['name'])
                    elif 'NUMERIC' in str(col['type']).upper():
                        numeric_columns.append(col['name'])
                
                return {
                    'float_columns': float_columns,
                    'numeric_columns': numeric_columns,
                    'migration_needed': len(float_columns) > 0
                }
            except Exception as e:
                return {'error': str(e)}
    
    def backup_float_data(self):
        """Backup current float data before migration"""
        backup_queries = [
            "CREATE TABLE IF NOT EXISTS portfolios_backup AS SELECT * FROM portfolios;",
            "CREATE TABLE IF NOT EXISTS positions_backup AS SELECT * FROM positions;", 
            "CREATE TABLE IF NOT EXISTS transactions_backup AS SELECT * FROM transactions;"
        ]
        
        with self.app.app_context():
            try:
                for query in backup_queries:
                    db.session.execute(text(query))
                db.session.commit()
                return True
            except Exception as e:
                print(f"Backup failed: {e}")
                return False
    
    def migrate_to_numeric(self):
        """Execute migration from Float to Numeric"""
        migration_sql = """
        -- Step 1: Add new Numeric columns
        ALTER TABLE portfolios ADD COLUMN initial_capital_new NUMERIC(15,2);
        ALTER TABLE portfolios ADD COLUMN current_capital_new NUMERIC(15,2);
        ALTER TABLE portfolios ADD COLUMN cash_balance_new NUMERIC(15,2);
        ALTER TABLE portfolios ADD COLUMN total_value_new NUMERIC(15,2);
        ALTER TABLE portfolios ADD COLUMN total_return_new NUMERIC(15,4);
        ALTER TABLE portfolios ADD COLUMN unrealized_pnl_new NUMERIC(15,2);
        ALTER TABLE portfolios ADD COLUMN realized_pnl_new NUMERIC(15,2);
        
        -- Step 2: Copy data with conversion
        UPDATE portfolios SET 
            initial_capital_new = CAST(initial_capital AS NUMERIC(15,2)),
            current_capital_new = CAST(current_capital AS NUMERIC(15,2)),
            cash_balance_new = CAST(cash_balance AS NUMERIC(15,2)),
            total_value_new = CAST(total_value AS NUMERIC(15,2)),
            total_return_new = CAST(total_return AS NUMERIC(15,4)),
            unrealized_pnl_new = CAST(unrealized_pnl AS NUMERIC(15,2)),
            realized_pnl_new = CAST(realized_pnl AS NUMERIC(15,2));
        
        -- Step 3: Drop old columns
        ALTER TABLE portfolios DROP COLUMN initial_capital;
        ALTER TABLE portfolios DROP COLUMN current_capital;
        ALTER TABLE portfolios DROP COLUMN cash_balance;
        ALTER TABLE portfolios DROP COLUMN total_value;
        ALTER TABLE portfolios DROP COLUMN total_return;
        ALTER TABLE portfolios DROP COLUMN unrealized_pnl;
        ALTER TABLE portfolios DROP COLUMN realized_pnl;
        
        -- Step 4: Rename new columns
        ALTER TABLE portfolios RENAME COLUMN initial_capital_new TO initial_capital;
        ALTER TABLE portfolios RENAME COLUMN current_capital_new TO current_capital;
        ALTER TABLE portfolios RENAME COLUMN cash_balance_new TO cash_balance;
        ALTER TABLE portfolios RENAME COLUMN total_value_new TO total_value;
        ALTER TABLE portfolios RENAME COLUMN total_return_new TO total_return;
        ALTER TABLE portfolios RENAME COLUMN unrealized_pnl_new TO unrealized_pnl;
        ALTER TABLE portfolios RENAME COLUMN realized_pnl_new TO realized_pnl;
        """
        
        with self.app.app_context():
            try:
                db.session.execute(text(migration_sql))
                db.session.commit()
                return True
            except Exception as e:
                print(f"Migration failed: {e}")
                db.session.rollback()
                return False

if __name__ == '__main__':
    migrator = DatabaseMigrator()
    
    print("🔍 Checking migration status...")
    status = migrator.check_migration_status()
    print(f"Status: {status}")
    
    if status.get('migration_needed'):
        print("📦 Creating backup...")
        if migrator.backup_float_data():
            print("✅ Backup completed")
            
            print("🔄 Starting migration...")
            if migrator.migrate_to_numeric():
                print("✅ Migration completed successfully")
            else:
                print("❌ Migration failed")
        else:
            print("❌ Backup failed - aborting migration")
    else:
        print("✅ No migration needed - already using Numeric types")