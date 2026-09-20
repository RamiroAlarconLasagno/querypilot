# scripts/seed_demo.py
"""Genera la base sintetica de demostracion.

Deliberadamente incomoda: nombres cripticos, relaciones implicitas, estados
codificados, nulos y una ambiguedad semantica real. Un esquema de manual haria
que la interpretacion pareciera facil y no probaria nada.

No usa datos reales. Es reproducible: misma semilla, mismos datos.
"""

from __future__ import annotations

import random
from datetime import date, timedelta
from decimal import Decimal

import typer

app = typer.Typer(help="Genera la base de negocio de demostracion.")

SEMILLA = 20260816

# --- Esquema ---------------------------------------------------------------
# ent_com  mezcla clientes y proveedores (tp = 1 cliente, 2 proveedor)
# cmp_cab  cabecera de comprobante; est_cod = 9 es anulado
# cmp_det  detalle; imp_neto sin impuestos, cost_rep costo de reposicion
# art_mae  articulos; art_rub rubros; geo_ref zonas; usr_int usuarios internos
#
# Ambiguedad semantica deliberada: cmp_cab tiene imp_tot (con impuestos) e
# imp_neto en el detalle. "ventas" podria ser cualquiera de las dos; la capa
# semantica declara cual es la acepcion por defecto.

ESQUEMA = """
DROP TABLE IF EXISTS cmp_det, cmp_cab, art_mae, art_rub, ent_com, geo_ref, usr_int CASCADE;

CREATE TABLE geo_ref (
    geo_id   INTEGER PRIMARY KEY,
    desc_1   TEXT NOT NULL,
    desc_2   TEXT
);

CREATE TABLE usr_int (
    usr_id   INTEGER PRIMARY KEY,
    nom_ape  TEXT NOT NULL,
    act      SMALLINT DEFAULT 1
);

CREATE TABLE ent_com (
    ent_id   INTEGER PRIMARY KEY,
    raz_soc  TEXT NOT NULL,
    tp       SMALLINT NOT NULL,      -- 1 cliente, 2 proveedor
    geo_id   INTEGER REFERENCES geo_ref(geo_id),
    f_alta   DATE
);

CREATE TABLE art_rub (
    rub_cod  INTEGER PRIMARY KEY,
    rub_desc TEXT NOT NULL
);

CREATE TABLE art_mae (
    art_cod    TEXT PRIMARY KEY,
    desc_larga TEXT NOT NULL,
    rub_cod    INTEGER REFERENCES art_rub(rub_cod)
);

CREATE TABLE cmp_cab (
    nro_int  BIGINT PRIMARY KEY,
    f_emis   DATE NOT NULL,
    ent_id   INTEGER REFERENCES ent_com(ent_id),
    usr_id   INTEGER REFERENCES usr_int(usr_id),
    est_cod  SMALLINT NOT NULL,      -- 1 emitido, 5 pendiente, 9 anulado
    imp_tot  NUMERIC(14,2)           -- CON impuestos: no es la metrica de negocio
);

CREATE TABLE cmp_det (
    nro_int  BIGINT REFERENCES cmp_cab(nro_int),
    reng     SMALLINT,
    art_cod  TEXT REFERENCES art_mae(art_cod),
    cant     NUMERIC(12,3) NOT NULL,
    imp_neto NUMERIC(14,2) NOT NULL,
    cost_rep NUMERIC(14,2),          -- admite nulos: no siempre se registro
    PRIMARY KEY (nro_int, reng)
);

CREATE INDEX ix_cmp_cab_f_emis ON cmp_cab (f_emis);
CREATE INDEX ix_cmp_cab_ent    ON cmp_cab (ent_id);
CREATE INDEX ix_cmp_det_art    ON cmp_det (art_cod);
"""


@app.command()
def generate(
    url: str = typer.Option(None, envvar="QP_BUSINESS_DB_URL"),
    meses: int = typer.Option(18, help="Meses de historia a generar."),
    clientes: int = typer.Option(1240),
    articulos: int = typer.Option(3800),
) -> None:
    """Crea el esquema y lo puebla con datos sinteticos reproducibles.

    Genera una caida real de facturacion en el ultimo mes cerrado, concentrada
    en unos pocos clientes: es el escenario de la traza nominal.
    """
    random.seed(SEMILLA)
    typer.echo(f"Semilla {SEMILLA} | {meses} meses | {clientes} clientes | {articulos} articulos")
    typer.echo("Pendiente de implementar en el sub-peldano 5.2 (ver MAPA_AVANCE.md).")
    typer.echo("El primer MVP solo necesita el ESQUEMA, no los datos.")


@app.command()
def schema_only(url: str = typer.Option(None, envvar="QP_BUSINESS_DB_URL")) -> None:
    """Crea solo el esquema. Es lo unico que el primer MVP necesita."""
    typer.echo(ESQUEMA)


if __name__ == "__main__":
    app()
