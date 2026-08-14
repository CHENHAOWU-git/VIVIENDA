"""Actualización periódica, pensada para ejecutarse desde una tarea programada
(ver README.md, sección "Automatización").

Solo el IPV del INE se actualiza solo con el tiempo (nueva publicación cada
trimestre) -- los datasets abiertos (Fotocasa, properties_Spain) son
publicaciones estáticas y no cambian entre ejecuciones, así que no tiene
sentido "programarlos" para construir una serie temporal por sí mismos; se
re-descargan aquí solo por si la fuente original publica una revisión.

Si hay cambios en los archivos versionados (data/processed/ine_ipv.csv,
outputs/figures/ine_ipv_evolucion.png), hace commit y push automáticamente
-- así el historial de git queda como registro de cuándo apareció cada
trimestre nuevo del INE. Si no hay cambios, no hace nada (sin commits vacíos).
"""
from __future__ import annotations

import datetime
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG_PATH = ROOT / "outputs" / "reports" / "actualizar_todo.log"

ARCHIVOS_VERSIONADOS = [
    "data/processed/ine_ipv.csv",
    "outputs/figures/ine_ipv_evolucion.png",
]


def _log(mensaje: str) -> None:
    marca = datetime.datetime.now().isoformat(timespec="seconds")
    linea = f"[{marca}] {mensaje}"
    print(linea)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(linea + "\n")


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=ROOT, check=True)


def _hay_cambios() -> bool:
    resultado = subprocess.run(
        ["git", "status", "--porcelain", *ARCHIVOS_VERSIONADOS],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    return bool(resultado.stdout.strip())


def main() -> None:
    _log("Iniciando actualización periódica")
    try:
        _run([sys.executable, "scripts/fetch_ine_data.py"])
        _run([sys.executable, "scripts/fetch_open_datasets.py"])
        _run([sys.executable, "scripts/analisis_avanzado.py"])
    except subprocess.CalledProcessError as exc:
        _log(f"ERROR: un paso falló ({exc}), no se hace commit")
        return

    if not _hay_cambios():
        _log("Sin cambios en el IPV del INE, nada que subir")
        return

    fecha = datetime.date.today().isoformat()
    _run(["git", "add", *ARCHIVOS_VERSIONADOS])
    _run(["git", "commit", "-m", f"Actualizacion automatica del IPV del INE ({fecha})"])
    _run(["git", "push", "origin", "HEAD:main"])
    _log("Cambios detectados en el IPV del INE, commit y push realizados")


if __name__ == "__main__":
    main()
