-- Ejecutar únicamente tras confirmar la conexión a la base correcta.
-- No modifica pedidos existentes. Para un esquema compatible con v1.
DO $$ BEGIN
    IF current_database() <> 'sig_banqueteria_mica' THEN
        RAISE EXCEPTION 'Base incorrecta: use únicamente sig_banqueteria_mica';
    END IF;
END $$;
CREATE SEQUENCE IF NOT EXISTS public.pedido_numero_seq START WITH 10000;
