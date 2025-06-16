import os
import subprocess
from ftplib import FTP
from pathlib import Path

from werkzeug.utils import secure_filename


class FileObs:
    def __init__(self):
        pass

    def descargar_archivos_por_hora(self, hora):
        HOST = "10.0.100.224"
        USER = "estaciones"
        PASS = "CasaB2024*"
        PORT = "990"
        REMOTE_DIR = "/Reportes Procesados"
        LOCAL_DIR = "./media/obs"

        # Validar hora
        horas_validas = ["00", "03", "06", "09", "12", "15", "18", "21"]
        if hora not in horas_validas:
            raise ValueError(f"Hora inválida. Usa una de: {horas_validas}")

        # Crear directorio local si no existe
        os.makedirs(LOCAL_DIR, exist_ok=True)

        # Comando LFTP corregido (usando `-O` para directorio de salida)
        comando = f"""
        set ftp:ssl-allow yes;
        set ssl:verify-certificate no;
        cd '{REMOTE_DIR}';
        mget SM35[0-5].{hora} -O {LOCAL_DIR}/;
        mget SI35[0-5].{hora} -O {LOCAL_DIR}/;
        bye
        """

        # Ejecutar LFTP
        try:
            subprocess.run(
                ["lftp", "-u", f"{USER},{PASS}", "-p", PORT, f"ftps://{HOST}", "-e", comando],
                check=True,
                text=True
            )
            print(f"✅ Descarga completada para hora {hora}. Archivos en {LOCAL_DIR}")
            print("Archivos descargados:", os.listdir(LOCAL_DIR))
        except subprocess.CalledProcessError as e:
            print(f"❌ Error al descargar archivos para hora {hora}: {e}")
