import os
import shutil
from ftplib import FTP
from pathlib import Path


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

        filename = f'Salida/TRAFICO/{self.file_name(station_number, hour)}'
        try:
            ftp = FTP(host='10.0.100.204')
            ftp.encoding = 'utf-8'
            ftp.login(user='todos', passwd='todos')

            with open(filename, "wb") as file:
                ftp.retrbinary(f"RETR {filename}", file.write)
            ftp.quit()

            path = Path('media/salida/telex')
            path.mkdir(parents=True, exist_ok=True)

            shutil.copy(f'{filename}', f'media/{filename}')
            
            shutil.rmtree('Salida')

        except Exception:
            shutil.rmtree('Salida')
            return f'media/{filename}'
        
        return f'media/{filename}'
