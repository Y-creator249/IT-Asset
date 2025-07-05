-- Script SQL pour corriger le problème de journal de vente manquant
-- À exécuter dans la base de données Odoo: psql -U <utilisateur> -d l3_db -f fix_journal.sql

-- Vérifier si un journal de vente existe déjà
DO $$
DECLARE
    journal_count INTEGER;
    sequence_id INTEGER;
    company_id INTEGER;
    journal_id INTEGER;
BEGIN
    -- Récupérer l'ID de la société
    SELECT id INTO company_id FROM res_company ORDER BY id LIMIT 1;

    -- Vérifier si un journal de vente existe déjà
    SELECT COUNT(*) INTO journal_count FROM account_journal 
    WHERE type = 'sale' AND company_id = company_id;

    RAISE NOTICE 'Nombre de journaux de vente trouvés: %', journal_count;

    IF journal_count = 0 THEN
        RAISE NOTICE 'Création d''un nouveau journal de vente...';
        
        -- Créer une séquence pour le journal
        INSERT INTO ir_sequence (name, implementation, padding, number_next, number_increment, prefix, company_id, code, active)
        VALUES ('Factures IT', 'standard', 4, 1, 1, 'IT/%(year)s/', company_id, 'account.invoice', true)
        RETURNING id INTO sequence_id;
        
        -- Créer le journal de vente
        INSERT INTO account_journal (name, code, type, sequence_id, company_id, active)
        VALUES ('Ventes IT Asset', 'ITSAL', 'sale', sequence_id, company_id, true)
        RETURNING id INTO journal_id;
        
        RAISE NOTICE 'Journal de vente créé avec ID: %', journal_id;
    ELSE
        RAISE NOTICE 'Un journal de vente existe déjà dans la base de données.';
    END IF;
END $$; 