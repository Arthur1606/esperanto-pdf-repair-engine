import sqlite3
import os
import re
from collections import Counter
import logging

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "corpus.db")

class Biblioteko:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self._init_db()

    def _init_db(self):
        cursor = self.conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS corpus_sources (
                id INTEGER PRIMARY KEY,
                source_name TEXT UNIQUE,
                source_type TEXT,
                version_date TEXT,
                description TEXT
            );

            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY,
                word TEXT UNIQUE,
                frequency INTEGER DEFAULT 1
            );
            
            CREATE TABLE IF NOT EXISTS co_occurrences (
                id INTEGER PRIMARY KEY,
                word1_id INTEGER,
                word2_id INTEGER,
                distance INTEGER,
                frequency INTEGER DEFAULT 1,
                UNIQUE(word1_id, word2_id, distance)
            );
            
            CREATE TABLE IF NOT EXISTS corrections_memory (
                id INTEGER PRIMARY KEY,
                corrupt_word TEXT,
                corrected_word TEXT,
                occurrences INTEGER DEFAULT 1,
                confidence_sum REAL DEFAULT 0,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(corrupt_word, corrected_word)
            );
            
            CREATE TABLE IF NOT EXISTS roots (
                id INTEGER PRIMARY KEY,
                root_text TEXT UNIQUE,
                type TEXT -- radiko, prefikso, sufikso
            );

            CREATE TABLE IF NOT EXISTS lexical_families (
                word_id INTEGER,
                root_id INTEGER,
                UNIQUE(word_id, root_id)
            );

            CREATE TABLE IF NOT EXISTS semantic_relations (
                word1_id INTEGER,
                word2_id INTEGER,
                relation_type TEXT,
                UNIQUE(word1_id, word2_id, relation_type)
            );

            CREATE TABLE IF NOT EXISTS sentences_corpus (
                id INTEGER PRIMARY KEY,
                text TEXT,
                source_id INTEGER,
                UNIQUE(text)
            );

            CREATE TABLE IF NOT EXISTS grammar_patterns (
                id INTEGER PRIMARY KEY,
                pattern_regex TEXT UNIQUE,
                description TEXT
            );
            
            CREATE INDEX IF NOT EXISTS idx_word ON words(word);
            CREATE INDEX IF NOT EXISTS idx_co_occ ON co_occurrences(word1_id, word2_id);
            CREATE INDEX IF NOT EXISTS idx_memory ON corrections_memory(corrupt_word);
        """)
        self.conn.commit()

    def register_source(self, name, type, date, desc):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO corpus_sources (source_name, source_type, version_date, description)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(source_name) DO UPDATE SET version_date = ?, description = ?
        """, (name, type, date, desc, date, desc))
        self.conn.commit()
        return cursor.lastrowid

    def get_word_id(self, word):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM words WHERE word = ?", (word.lower(),))
        row = cursor.fetchone()
        if row:
            return row[0]
        
        cursor.execute("INSERT INTO words (word, frequency) VALUES (?, 0)", (word.lower(),))
        self.conn.commit()
        return cursor.lastrowid

    def ingest_text(self, text):
        words = [w.lower() for w in re.findall(r'\b[a-zĉĝĥĵŝŭ]+\b', text.lower()) if len(w) > 1]
        
        cursor = self.conn.cursor()
        
        # Ingest frequencies
        word_counts = Counter(words)
        for w, count in word_counts.items():
            cursor.execute("""
                INSERT INTO words (word, frequency) 
                VALUES (?, ?)
                ON CONFLICT(word) DO UPDATE SET frequency = frequency + ?
            """, (w, count, count))
            
        # Ingest co-occurrences (window = 3)
        for i, w1 in enumerate(words):
            w1_id = self.get_word_id(w1)
            for j in range(1, 4):
                if i + j < len(words):
                    w2 = words[i+j]
                    w2_id = self.get_word_id(w2)
                    cursor.execute("""
                        INSERT INTO co_occurrences (word1_id, word2_id, distance, frequency)
                        VALUES (?, ?, ?, 1)
                        ON CONFLICT(word1_id, word2_id, distance) DO UPDATE SET frequency = frequency + 1
                    """, (w1_id, w2_id, j))
        self.conn.commit()
        
    def get_word_frequency(self, word):
        cursor = self.conn.cursor()
        cursor.execute("SELECT frequency FROM words WHERE word = ?", (word.lower(),))
        row = cursor.fetchone()
        return row[0] if row else 0
        
    def get_co_occurrence(self, word1, word2, max_distance=3):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT SUM(c.frequency) FROM co_occurrences c
            JOIN words w1 ON c.word1_id = w1.id
            JOIN words w2 ON c.word2_id = w2.id
            WHERE w1.word = ? AND w2.word = ? AND c.distance <= ?
        """, (word1.lower(), word2.lower(), max_distance))
        row = cursor.fetchone()
        return row[0] if row and row[0] else 0

    def record_correction(self, corrupt, corrected, confidence):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO corrections_memory (corrupt_word, corrected_word, occurrences, confidence_sum, last_seen)
            VALUES (?, ?, 1, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(corrupt_word, corrected_word) 
            DO UPDATE SET 
                occurrences = occurrences + 1,
                confidence_sum = confidence_sum + ?,
                last_seen = CURRENT_TIMESTAMP
        """, (corrupt.lower(), corrected.lower(), confidence, confidence))
        self.conn.commit()

    def get_historical_confidence(self, corrupt, corrected):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT occurrences, confidence_sum FROM corrections_memory 
            WHERE corrupt_word = ? AND corrected_word = ?
        """, (corrupt.lower(), corrected.lower()))
        row = cursor.fetchone()
        if row:
            occurrences, conf_sum = row
            return conf_sum / occurrences if occurrences > 0 else 0.0
        return 0.0

biblioteko = Biblioteko()
