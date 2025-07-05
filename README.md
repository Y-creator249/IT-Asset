# Module de Gestion de Parc Informatique - Odoo

## 📋 Description du Projet

Ce module Odoo permet la gestion complète d'un parc informatique avec une approche multi-client et facturation récurrente intégrée, similaire à GLPI mais totalement intégré à l'environnement ERP Odoo (RH, Ventes, Stock, Comptabilité).

Conçu pour les prestataires IT en infogérance, ce module offre une solution complète pour la gestion du parc client, le suivi des interventions, et la facturation automatisée.

## 🎯 Objectifs du Projet

### 1. Analyse Métier
- ✅ Étudier le fonctionnement d'un prestataire IT en infogérance
- ✅ Identifier les besoins métiers : suivi de parc, interventions, alertes, contrats, facturation
- ✅ Définir les typologies de clients et les modèles de tarification

### 2. Conception Fonctionnelle
- ✅ Fiches clients et contrats de service
- ✅ Parc affecté par client (matériel, logiciels, licences)
- ✅ Affectation d'équipements aux utilisateurs finaux (employés du client)
- ✅ Historique des interventions, incidents et maintenance
- ✅ Alertes automatiques (fin de licence, garantie, maintenance préventive)
- ✅ Planification de la facturation récurrente personnalisée

### 3. Développement Technique
- ✅ Création d'un module spécifique Odoo
- ✅ Intégration avec les modules existants (RH, Achats, Stock, Comptabilité)
- ✅ Portail client intégré

## 🚀 Fonctionnalités Principales

### Gestion du Parc Informatique
- **Inventaire multi-client** : Suivi du matériel, logiciels et licences par client
- **Affectation utilisateurs** : Attribution d'équipements aux employés des clients
- **Historique complet** : Traçabilité de tous les mouvements et interventions
- **Alertes automatiques** : Notifications pour les échéances importantes

### Gestion des Interventions
- **Tickets d'incident** : Création et suivi via module Helpdesk intégré
- **Planification maintenance** : Interventions préventives programmées
- **Assignation techniciens** : Gestion des ressources humaines
- **Historique interventions** : Suivi complet des actions réalisées

### Facturation Récurrente
- **Contrats de service** : Définition des prestations et tarifs
- **Facturation automatique** : Génération selon fréquence définie
- **Suivi paiements** : Intégration comptabilité complète
- **Personnalisation tarifs** : Modèles flexibles par client

### Portail Client
- **Consultation parc** : Vue d'ensemble des équipements affectés
- **Signalement incidents** : Création de tickets directement
- **Suivi factures** : Accès aux documents comptables
- **Historique interventions** : Transparence sur les actions réalisées

### Intégrations Odoo
- **Module RH** : Gestion des techniciens et assignation des interventions
- **Module Achats/Stock** : Suivi du matériel fourni et approvisionnement
- **Module Comptabilité** : Génération automatique des écritures comptables
- **Module Abonnements** : Gestion des contrats récurrents
- **Module Helpdesk** : Suivi des incidents et demandes d'intervention
- **Module Portail** : Interface client pour consultation et signalement

## 📊 Modèles de Données Principaux

### IT Asset (Actif Informatique)
- Identification unique
- Type (matériel, logiciel, licence)
- Client propriétaire
- Utilisateur affecté
- Statut et localisation
- Dates importantes (achat, garantie, fin de licence)

### IT Client
- Informations client étendues
- Contrats de service associés
- Parc informatique affecté
- Historique interventions

### IT Contract (Contrat de Service)
- Prestations incluses
- Modèle de tarification
- Fréquence de facturation
- Dates de validité

### IT Intervention
- Ticket d'incident ou maintenance
- Technicien assigné
- Temps passé
- Matériel/équipement concerné
- Statut et résolution

## 🔧 Installation et Configuration

### Prérequis
- Odoo 18.0+
- Modules dépendants : `base`, `account`, `hr`, `purchase`, `stock`, `helpdesk`, `portal`

### Installation
1. Cloner le repository dans le dossier addons d'Odoo
2. Redémarrer le serveur Odoo
3. Activer le mode développeur
4. Installer le module via Apps

### Configuration Initiale
1. Configurer les types d'actifs informatiques
2. Définir les modèles de contrats de service
3. Paramétrer les alertes automatiques
4. Configurer les accès portail client

## 👥 Gestion des Droits

### Groupes d'Utilisateurs
- **IT Manager** : Accès complet à tous les modules
- **IT Technician** : Gestion des interventions et mise à jour du parc
- **IT Billing** : Gestion de la facturation et des contrats
- **Client Portal** : Accès limité via portail client

## 🔔 Alertes et Notifications

### Alertes Automatiques
- Fin de garantie matériel (30, 90 jours avant)
- Expiration licences logicielles
- Maintenance préventive programmée
- Renouvellement contrats de service

### Notifications
- Création nouveau ticket d'incident
- Assignation intervention technicien
- Facturation générée
- Paiement reçu

## 📈 Tableau de Bord

### Indicateurs Clés
- Nombre d'actifs par client
- Interventions en cours
- Prochaines échéances
- Chiffre d'affaires mensuel/annuel
- Temps de résolution moyen

### Rapports Disponibles
- Inventaire parc informatique
- Historique interventions
- Facturation récurrente
- Rentabilité par client

## 🚧 Roadmap

### Version 1.0 (Actuelle)
- [x] Gestion basique du parc informatique
- [x] Création et suivi des interventions
- [x] Facturation récurrente simple
- [x] Portail client de base

### Version 1.1 (Prochaine)
- [ ] Intégration avancée avec Stock
- [ ] Alertes personnalisables
- [ ] Rapports étendus
- [ ] API REST pour intégrations tierces

### Version 1.2 (Future)
- [ ] Module mobile pour techniciens
- [ ] Signature électronique interventions
- [ ] Intégration monitoring réseau
- [ ] Intelligence artificielle prédictive

## 📝 Documentation

### Guides Utilisateur
- Guide d'installation et configuration
- Manuel utilisateur IT Manager
- Guide technicien terrain
- Documentation portail client

### Documentation Technique
- Architecture du module
- Guide de développement
- API Reference
- Personnalisations possibles

## 🤝 Contribution

Les contributions sont les bienvenues ! Merci de :
1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Commiter vos changements (`git commit -m 'Ajout nouvelle fonctionnalité'`)
4. Pousser vers la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Ouvrir une Pull Request

## 📄 Licence

Ce projet est sous licence [MIT](LICENSE).

## 📞 Support

Pour toute question ou support technique :
- Email : yanncedricemmanuelo@gmail.com


## 🙏 Remerciements

- Équipe Odoo pour la plateforme ERP
- Communauté open source
- Contributeurs du projet

---

**Développé avec ❤️ pour la communauté Odoo**
