import shutil
import datetime
import os

today = datetime.date.today().isoformat()
source = 'school.db'

# Local backup
os.makedirs('backups', exist_ok=True)
local_dest = f'backups/school_backup_{today}.db'
shutil.copy2(source, local_dest)
print(f"نسخة احتياطية محلية: {local_dest}")

# Google Drive backup
drive_folder = r'C:\Users\DELL\Documents\Google Drive\school_backups'
os.makedirs(drive_folder, exist_ok=True)

drive_dest = os.path.join(
    drive_folder,
    f'school_backup_{today}.db'
)

shutil.copy2(source, drive_dest)
print(f"نسخة احتياطية على Drive: {drive_dest}")

input("اضغط أي مفتاح للإغلاق...")