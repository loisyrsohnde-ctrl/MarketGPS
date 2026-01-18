-- MarketGPS - Long-Term Scoring Migration
-- Adds lt_* columns to scores_latest table
-- Non-destructive: adds columns if they don't exist

-- Add lt_score column
ALTER TABLE scores_latest ADD COLUMN lt_score REAL;

-- Add lt_confidence column  
ALTER TABLE scores_latest ADD COLUMN lt_confidence REAL;

-- Add lt_breakdown column (JSON)
ALTER TABLE scores_latest ADD COLUMN lt_breakdown TEXT;

-- Add lt_updated_at timestamp
ALTER TABLE scores_latest ADD COLUMN lt_updated_at TEXT;

-- Create index for lt_score ranking
CREATE INDEX IF NOT EXISTS idx_scores_lt_score ON scores_latest(lt_score DESC) WHERE lt_score IS NOT NULL;

-- Also add to scores_staging table for production pipeline
ALTER TABLE scores_staging ADD COLUMN lt_score REAL;
ALTER TABLE scores_staging ADD COLUMN lt_confidence REAL;
ALTER TABLE scores_staging ADD COLUMN lt_breakdown TEXT;
ALTER TABLE scores_staging ADD COLUMN lt_updated_at TEXT;
