import os
import shutil
from ftplib import FTP
from pathlib import Path

from werkzeug.utils import secure_filename


class FileObs:
    def __init__(self):
        pass

    def file_name(self, station_number, hour):
        station_number = str(station_number)
        tri_h = ['03', '09', '15', '21']  # horarios de observations tri horarias
        sinop = ['00', '06', '12', '18']  # horarios de observations sinópticas
        for h in tri_h:
            if hour == h:
                return f'SI{station_number[2:]}.{hour}'

        for h in sinop:
            if hour == h:
                return f'SM{station_number[2:]}.{hour}'

    def filename(self, station_number, hour):
        path = Path('Salida/TRAFICO')
        path.mkdir(parents=True, exist_ok=True)

        base_path = Path('Salida/TRAFICO').resolve()
        filename = base_path / secure_filename(self.file_name(station_number, hour))
        filename = Path(os.path.normpath(filename))
        if not str(filename).startswith(str(base_path)):
            raise Exception("Invalid file path")
        try:
            ftp = FTP(host='10.0.100.204')
            ftp.encoding = 'utf-8'
            ftp.login(user='todos', passwd='todos')

            with open(filename, "wb") as file:
                ftp.retrbinary(f"RETR {filename}", file.write)
            ftp.quit()

            path = Path('media/salida/telex')
            path.mkdir(parents=True, exist_ok=True)

            shutil.copy(filename, path / filename.name)
            
            shutil.rmtree('Salida')

        except Exception:
            shutil.rmtree('Salida')
            return str(path / filename.name)
        
        return str(path / filename.name)
