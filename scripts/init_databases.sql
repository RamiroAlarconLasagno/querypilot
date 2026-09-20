-- scripts/init_databases.sql
-- Se ejecuta una sola vez, al inicializar el volumen de PostgreSQL.
-- Crea la base de negocio de demostracion y un usuario de SOLO LECTURA.
--
-- Dos usuarios distintos no es cosmetica: es lo que impide que Acceso a datos
-- escriba por accidente en la base del cliente, y lo que hace que la prueba
-- "el usuario de negocio no puede escribir" pruebe algo.

CREATE DATABASE demo_negocio;

\connect demo_negocio

CREATE ROLE qp_readonly LOGIN PASSWORD 'cambiar';

REVOKE ALL ON DATABASE demo_negocio FROM PUBLIC;
GRANT CONNECT ON DATABASE demo_negocio TO qp_readonly;
GRANT USAGE ON SCHEMA public TO qp_readonly;

-- Sobre lo que exista ahora y sobre lo que se cree despues
GRANT SELECT ON ALL TABLES IN SCHEMA public TO qp_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO qp_readonly;

-- Explicitamente NO se otorga INSERT, UPDATE, DELETE ni CREATE.
