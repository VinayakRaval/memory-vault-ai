-- ================================
-- MEMORY VAULT AI DATABASE SETUP
-- ================================

-- 1. CREATE DATABASE
CREATE DATABASE IF NOT EXISTS memory_vault;
USE memory_vault;

-- ================================
-- 2. FILES TABLE
-- ================================
CREATE TABLE IF NOT EXISTS files (
    id INT AUTO_INCREMENT PRIMARY KEY,

    name VARCHAR(255),
    path TEXT,
    type VARCHAR(50),

    size BIGINT,
    modified DOUBLE,

    hash VARCHAR(64),

    preview TEXT,

    views INT DEFAULT 0,
    last_opened TIMESTAMP NULL,

    importance FLOAT DEFAULT 0,
    category VARCHAR(20),

    malware TINYINT DEFAULT 0,
    malware_type VARCHAR(100),
    malware_severity VARCHAR(20),
    malware_reason TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================
-- 3. INDEXES (PERFORMANCE)
-- ================================
CREATE INDEX idx_hash ON files(hash);
CREATE INDEX idx_type ON files(type);
CREATE INDEX idx_importance ON files(importance);
CREATE INDEX idx_malware ON files(malware);

-- ================================
-- 4. SAMPLE INSERT (TEST DATA)
-- ================================
INSERT INTO files (
    name, path, type, size, modified,
    hash, preview,
    views, importance, category,
    malware, malware_type, malware_severity, malware_reason
)
VALUES (
    'sample.txt',
    'C:/sample.txt',
    'txt',
    1024,
    1700000000,
    'abc123hash',
    'This is sample preview',
    0,
    0.5,
    'Medium',
    0,S
    NULL,
    NULL,
    NULL
);

-- ================================
-- 5. DUPLICATE DETECTION
-- ================================

-- 🔹 Get duplicate groups
SELECT hash, COUNT(*) AS copies
FROM files
WHERE hash IS NOT NULL
GROUP BY hash
HAVING COUNT(*) > 1;

-- 🔹 Get duplicate files
SELECT *
FROM files
WHERE hash IN (
    SELECT hash FROM files
    GROUP BY hash
    HAVING COUNT(*) > 1
);

-- 🔹 Delete duplicates (keep best importance)
DELETE f1
FROM files f1
JOIN files f2
ON f1.hash = f2.hash
AND f1.id > f2.id
AND f1.importance <= f2.importance;

-- ================================
-- 6. MALWARE QUERIES
-- ================================

-- 🔹 Get malware files
SELECT * FROM files WHERE malware = 1;

-- ================================
-- 7. IMPORTANT FILES
-- ================================

-- 🔹 Sort by importance
SELECT * FROM files ORDER BY importance DESC;

-- ================================
-- 8. RECENT ACTIVITY
-- ================================

SELECT *
FROM files
WHERE last_opened IS NOT NULL
ORDER BY last_opened DESC;

-- ================================
-- 9. UPDATE OPERATIONS
-- ================================

-- 🔹 Update views + last opened
UPDATE files
SET 
    views = views + 1,
    last_opened = NOW()
WHERE id = 1;

-- 🔹 Update importance
UPDATE files
SET 
    importance = 0.8,
    category = 'High'
WHERE id = 1;

-- ================================
-- 10. DELETE FILE
-- ================================

DELETE FROM files WHERE id = 1;