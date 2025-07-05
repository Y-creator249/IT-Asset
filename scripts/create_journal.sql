-- Vérifier si un journal de vente existe déjà
DO $$
DECLARE
    company_id INTEGER;
    account_id INTEGER;
    journal_id INTEGER;
    sequence_id INTEGER;
    journal_exists BOOLEAN;
BEGIN
    -- Récupérer l'ID de la société principale
    SELECT id INTO company_id FROM res_company WHERE id = 1;
    
    -- Vérifier si un journal de vente existe déjà
    SELECT EXISTS(SELECT 1 FROM account_journal WHERE type = 'sale' AND company_id = company_id) INTO journal_exists;
    
    IF NOT journal_exists THEN
        -- Créer une séquence pour le nouveau journal
        INSERT INTO ir_sequence (name, implementation, padding, number_next, number_increment, prefix, suffix, use_date_range, company_id, active)
        VALUES ('Customer Invoices', 'standard', 6, 1, 1, 'INV/', '', false, company_id, true)
        RETURNING id INTO sequence_id;
        
        -- Trouver un compte pour les factures clients (si disponible)
        SELECT id INTO account_id FROM account_account 
        WHERE code LIKE '4111%' OR code LIKE '411%' OR code LIKE '4%' 
        AND company_id = company_id 
        LIMIT 1;
        
        -- Si aucun compte trouvé, utiliser le premier compte disponible
        IF account_id IS NULL THEN
            SELECT id INTO account_id FROM account_account WHERE company_id = company_id LIMIT 1;
        END IF;
        
        -- Créer le journal de vente
        INSERT INTO account_journal (name, code, type, sequence_id, default_account_id, refund_sequence, company_id, active)
        VALUES ('Sales Journal', 'SALE', 'sale', sequence_id, account_id, true, company_id, true)
        RETURNING id INTO journal_id;
        
        RAISE NOTICE 'Journal de vente créé avec ID %', journal_id;
    ELSE
        RAISE NOTICE 'Un journal de vente existe déjà';
    END IF;
END $$;

-- Insérer un compte de revenus si nécessaire
DO $$
DECLARE
    company_id INTEGER;
    account_type_id INTEGER;
    account_id INTEGER;
    account_exists BOOLEAN;
BEGIN
    -- Récupérer l'ID de la société principale
    SELECT id INTO company_id FROM res_company WHERE id = 1;
    
    -- Vérifier si un compte de revenus existe déjà
    SELECT EXISTS(
        SELECT 1 FROM account_account 
        WHERE (code LIKE '70%' OR code LIKE '7%') 
        AND company_id = company_id
    ) INTO account_exists;
    
    IF NOT account_exists THEN
        -- Trouver l'ID du type de compte pour les revenus
        SELECT id INTO account_type_id FROM account_account_type 
        WHERE type IN ('other', 'income', 'other_income')
        LIMIT 1;
        
        -- Si aucun type de compte trouvé, utiliser le premier disponible
        IF account_type_id IS NULL THEN
            SELECT id INTO account_type_id FROM account_account_type LIMIT 1;
        END IF;
        
        -- Créer le compte de revenus
        INSERT INTO account_account (code, name, user_type_id, company_id, reconcile)
        VALUES ('706000', 'Prestations de services', account_type_id, company_id, false)
        RETURNING id INTO account_id;
        
        RAISE NOTICE 'Compte de revenus créé avec ID %', account_id;
    ELSE
        RAISE NOTICE 'Un compte de revenus existe déjà';
    END IF;
END $$; 