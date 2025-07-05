@echo off
REM Script pour corriger le problème de journal de vente manquant
echo Exécution du correctif pour le journal de vente...
cd %~dp0\..\..\..\..

REM Vérifier si le dossier scripts existe
if not exist "temp" mkdir temp

REM Copier le fichier Python avec adaptations pour le shell 
echo import sys,os >> temp\fix_journal_temp.py
echo sys.path.append(os.getcwd()) >> temp\fix_journal_temp.py
echo from odoo import api, fields, models, SUPERUSER_ID >> temp\fix_journal_temp.py
echo from odoo.modules.registry import Registry >> temp\fix_journal_temp.py
echo r = Registry(sys.argv[1]) >> temp\fix_journal_temp.py
echo with api.Environment.manage(): >> temp\fix_journal_temp.py
echo     with r.cursor() as cr: >> temp\fix_journal_temp.py
echo         env = api.Environment(cr, SUPERUSER_ID, {}) >> temp\fix_journal_temp.py
echo         print("Recherche de journaux de vente existants...") >> temp\fix_journal_temp.py
echo         journals = env['account.journal'].sudo().search([('type', '=', 'sale')]) >> temp\fix_journal_temp.py
echo         if journals: >> temp\fix_journal_temp.py
echo             for journal in journals: >> temp\fix_journal_temp.py
echo                 print(f"Journal de vente trouvé: {journal.name} [{journal.code}]") >> temp\fix_journal_temp.py
echo         else: >> temp\fix_journal_temp.py
echo             print("Aucun journal de vente trouvé. Création d'un nouveau journal...") >> temp\fix_journal_temp.py
echo             sequence = env['ir.sequence'].sudo().create({ >> temp\fix_journal_temp.py
echo                 'name': 'Factures IT', >> temp\fix_journal_temp.py
echo                 'implementation': 'standard', >> temp\fix_journal_temp.py
echo                 'padding': 4, >> temp\fix_journal_temp.py
echo                 'number_next': 1, >> temp\fix_journal_temp.py 
echo                 'number_increment': 1, >> temp\fix_journal_temp.py
echo                 'prefix': 'IT/%(year)s/', >> temp\fix_journal_temp.py
echo                 'company_id': env.company.id, >> temp\fix_journal_temp.py
echo             }) >> temp\fix_journal_temp.py
echo             journal = env['account.journal'].sudo().create({ >> temp\fix_journal_temp.py
echo                 'name': 'Ventes IT Asset', >> temp\fix_journal_temp.py
echo                 'code': 'ITSAL', >> temp\fix_journal_temp.py
echo                 'type': 'sale', >> temp\fix_journal_temp.py
echo                 'sequence_id': sequence.id, >> temp\fix_journal_temp.py
echo                 'company_id': env.company.id, >> temp\fix_journal_temp.py
echo                 'active': True, >> temp\fix_journal_temp.py
echo             }) >> temp\fix_journal_temp.py
echo             print(f"Journal de vente créé: {journal.name} [{journal.code}]") >> temp\fix_journal_temp.py
echo             cr.commit() >> temp\fix_journal_temp.py
echo             print("Les modifications ont été sauvegardées dans la base de données.") >> temp\fix_journal_temp.py

REM Exécution du script via Python
echo Exécution du script Python...
python -c "exec(open('temp/fix_journal_temp.py').read())" l3_db

echo Nettoyage...
del temp\fix_journal_temp.py

echo Terminé. 