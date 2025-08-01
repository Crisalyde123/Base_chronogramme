import sys
from pathlib import Path
import pandas as pd
import pytest

# import project root to access main.py
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from main import run_pipeline


def create_config(dir: Path) -> Path:
    config = dir / "cfg"
    config.mkdir()
    (config / "mapping_headers.csv").write_text(
        (
            "En-tete original,En-tete standard\n"
            "Horodatage,horodatage\n"
            "Descriptif,description\n"
            "Type d'inject,type_inject\n"
            "id_chronogramme,id_chronogramme\n"
            "numero,numero\n"
            "id_inject,id_inject\n"
            "phase,phase\n"
            "statut,statut\n"
            "type,type\n"
            "emetteur,emetteur\n"
            "recepteur,recepteur\n"
            "nature,nature\n"
            "resume,description\n"
            "contenu,contenu\n"
            "actions_attendues,actions_attendues\n"
            "commentaires,commentaires\n"
        )
    )
    (config / "mapping_values.csv").write_text(
        "Colonne,Valeur brute,Valeur standard\ntype_inject,Majeur,Critique\n"
    )
    (config / "schema_definition.yaml").write_text(
        "fields:\n  - name: type_inject\n    values: ['Critique', 'Important']\n"
    )
    return config


def create_excel(path: Path) -> None:
    df = pd.DataFrame({
        "Horodatage": ["T0"],
        "Descriptif": ["Test"],
        "Type d'inject": ["Majeur"],
    })
    df.to_excel(path, index=False)


def test_main_runs_to_clean_data(tmp_path):
    config = create_config(tmp_path)
    excel = tmp_path / "sample.xlsx"
    create_excel(excel)
    res = run_pipeline(excel, config_dir=config, log_dir=tmp_path, db_path=tmp_path / "db.sqlite")
    assert res["clean_df"].shape[0] == 1


def test_main_standardizes_headers(tmp_path):
    config = create_config(tmp_path)
    excel = tmp_path / "sample.xlsx"
    create_excel(excel)
    res = run_pipeline(excel, config_dir=config, log_dir=tmp_path, db_path=tmp_path / "db.sqlite")
    cols = res["df"].columns
    assert {"horodatage", "description", "type_inject"}.issubset(set(cols))


def test_main_standardizes_values(tmp_path):
    config = create_config(tmp_path)
    excel = tmp_path / "sample.xlsx"
    create_excel(excel)
    res = run_pipeline(excel, config_dir=config, log_dir=tmp_path, db_path=tmp_path / "db.sqlite")
    assert "type_inject" in res["df"].columns


def test_main_logs_are_created(tmp_path):
    config = create_config(tmp_path)
    excel = tmp_path / "sample.xlsx"
    create_excel(excel)
    res = run_pipeline(excel, config_dir=config, log_dir=tmp_path, db_path=tmp_path / "db.sqlite")
    assert res["mapping_log"].exists()
    assert res["log_file"] is not None and res["log_file"].exists()


def test_main_id_chronogramme_created(tmp_path):
    config = create_config(tmp_path)
    excel = tmp_path / "sample.xlsx"
    create_excel(excel)
    res = run_pipeline(excel, config_dir=config, log_dir=tmp_path, db_path=tmp_path / "db.sqlite")
    assert isinstance(res["chrono_id"], int)


def test_main_fails_on_invalid_file(tmp_path):
    config = create_config(tmp_path)
    with pytest.raises(Exception):
        run_pipeline(tmp_path / "not_excel.txt", config_dir=config, log_dir=tmp_path, db_path=tmp_path / "db.sqlite")

