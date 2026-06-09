import sqlite3
import json

db_path = 'backend/esperanto_repair.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT filename, debug_info FROM documents WHERE debug_info IS NOT NULL;")

all_ambiguities = []

for row in cursor.fetchall():
    filename, debug_info_str = row
    try:
        debug_info = json.loads(debug_info_str)
        metrics = debug_info.get('glyph_corruption_metrics', {})
        ambiguities = metrics.get('ambiguity_catalogue', [])
        for amb in ambiguities:
            amb['filename'] = filename
            all_ambiguities.append(amb)
    except:
        pass

print(json.dumps(all_ambiguities, indent=2))
