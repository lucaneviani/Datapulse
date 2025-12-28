import sys
sys.path.insert(0, 'Datapulse')
from backend.database_manager import SessionManager, get_session_tables

m = SessionManager()
sid = m.create_session()
print('sid', sid)
succ, msg = m.upload_csv(sid, [('data.csv', b'col1,col2\n1,foo\n2,bar\n')])
print('succ,msg', succ, msg)
ok, tables = get_session_tables(sid)
print('ok,tables', ok, tables)

# Try listing files in uploads
import os
from pathlib import Path
base = Path(__file__).resolve().parent.parent
print('uploads dir exists:', (base / 'uploads').exists())
print('uploads content:', list((base / 'uploads').iterdir()) if (base / 'uploads').exists() else [])
print('session dir exists:', (base / 'uploads' / sid).exists())
print('db file exists:', (base / 'uploads' / sid / 'user_database.db').exists())