from django.core.management.base import BaseCommand
from api.user.models import User
from document.models import Entity, Category, Product

class Command(BaseCommand):
    help = 'Seed initial data for documents application'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting data seeding...')

        try:
            # Création des entités
            self.stdout.write('Creating entities...')
            kes_inspections = Entity.objects.create(code="KIP", name="KES INSPECTIONS & PROJECTS")
            kes_energy = Entity.objects.create(code="KEC", name="KES ENERGY & CARBON")
            kes_sarl = Entity.objects.create(code="KES", name="KES SARL")
            kes_ar = Entity.objects.create(code="KAR", name="KES AfriK Recycling")

            # Création des catégories pour KES INSPECTIONS & PROJECTS
            self.stdout.write('Creating KES INSPECTIONS & PROJECTS categories...')
            categories_kes = {
                "INS": "INSPECTION",
                "FOR": "FORMATION",
                "QHS": "QHSE",
                "IND": "INDUSTRIE",
                "CAR": "CARTHOGRAPHIE",
                "CTC": "CONTRÔLE TECHNIQUE DES CONSTRUCTIONS",
            }
            kes_categories = {}
            for code, name in categories_kes.items():
                kes_categories[code] = Category.objects.create(
                    code=code,
                    name=name,
                    entity=kes_inspections
                )

            # Création des catégories pour KES ENERGY & CARBON
            self.stdout.write('Creating KES ENERGY & CARBON categories...')
            categories_kec = {
                "INS": "INSPECTION",
                "FOR": "FORMATION",
                "CAR": "CARTHOGRAPHIE",
            }
            kec_categories = {}
            for code, name in categories_kec.items():
                kec_categories[code] = Category.objects.create(
                    code=code,
                    name=name,
                    entity=kes_energy
                )

            # Création des produits pour KES INSPECTIONS & PROJECTS
            self.stdout.write('Creating KES INSPECTIONS & PROJECTS products...')
            products_kes = [
                # INSPECTION
                ("INS", "VTE1", "Verification electrique"),
                ("INS", "VTE2", "Mesure de terre"),
                ("INS", "VTE3", "Vérification électrique par thermographie infrarouge"),
                ("INS", "VTE4", "Etude Arc Flash"),
                ("INS", "VTE5", "Etude Selectivité"),
                ("INS", "VTE6", "Foudre"),
                ("INS", "VTE7", "Verification des ascenseurs"),
                ("INS", "VTE8", "Evaluation risque ATEX"),
                ("INS", "VTE9", "Vérification des appareils de levage"),
                ("INS", "VTE14", "Audit sécurité incendie"),
                ("INS", "VTE17", "Diagnostic CTC"),
                ("INS", "VTE20", "Audit climatisation"),
                ("INS", "VTE21", "Audit énergetique"),
                ("INS", "VTE22", "Verification des extincteurs"),
                ("INS", "VTE24", "Audit plomberie"),
                ("INS", "VTE49", "Expertise technique"),
                ("INS", "VTE43", "Maitrise d'œuvre"),
                ("INS", "VTE44", "Facility management"),
                ("INS", "VTE45", "Bureau d'etude"),
                ("INS", "VTE46", "Contrôle technique"),
                ("INS", "VTE47", "Eclairage public"),
                ("INS", "VTE48", "Accompagnement technique"),
                ("INS", "VTE50", "Verification equipement de chantier"),
                # FORMATION
                ("FOR", "VTE27", "Habilitation électrique"),
                ("FOR", "VTE28", "Travaux en hauteur"),
                ("FOR", "VTE29", "Premiers secours"),
                ("FOR", "VTE30", "Sécurité incendie"),
                ("FOR", "VTE31", "Conduite des appareils de levage"),
                ("FOR", "VTE32", "Elingage"),
                ("FOR", "VTE33", "Equipements sous pression"),
                ("FOR", "VTE34", "Thermographie infrarouge"),
                ("FOR", "VTE35", "Fresque du climat"),
                ("FOR", "VTE36", "Habilitation mecanique"),
                ("FOR", "VTE37", "Maintenance des installations electriques"),
                ("FOR", "VTE38", "Inspection des installations electrique"),
                ("FOR", "VTE39", "Bureau d'etude"),
                ("FOR", "VTE40", "Maitrise d'œuvre"),
                ("FOR", "VTE41", "HSE"),
                ("FOR", "VTE42", "Plomberie"),
                ("FOR", "VTE51", "ATEX"),
                ("FOR", "VTE52", "Equipement formation realité virtuelle"),
                ("FOR", "VTE53", "Equipement sous pression"),
                # QHSE
                ("QHS", "VTE11", "Mesure sonore"),
                ("QHS", "VTE12", "Mesure d'éclairement"),
                ("QHS", "VTE13", "Mesure de la qualité d'air"),
                ("QHS", "VTE16", "Bilan carbone"),
                # INDUSTRIE
                ("IND", "VTE10", "Verification des equipements sous pression"),
                ("IND", "VTE18", "Contrôle non destructif"),
                ("IND", "VTE19", "Baremage"),
                ("IND", "VTE25", "Tarage des soupapes"),
                # CARTOGRAPHIE
                ("CAR", "VTE15", "Cartographie"),
                ("CAR", "VTE23", "Inspection drone"),
                ("CAR", "VTE26", "Projets spéciaux"),
                # CONTRÔLE TECHNIQUE DES CONSTRUCTIONS
                ("CTC", "VTE54", "Diagnostique"),
                ("CTC", "VTE55", "Contrôle technique"),
                ("CTC", "VTE56", "Etude"),
            ]
            
            for category_code, code, name in products_kes:
                category = kes_categories[category_code]
                Product.objects.create(code=code, name=name, category=category)

            # Création des produits pour KES ENERGY & CARBON
            self.stdout.write('Creating KES ENERGY & CARBON products...')
            products_kec = [
                # INSPECTION
                ("INS", "EC1", "Production"),
                ("INS", "EC2", "Transport"),
                ("INS", "EC3", "Distribution"),
                ("INS", "EC4", "Regulation"),
                ("INS", "EC5", "Eclairage public"),
                ("INS", "EC6", "Marche de l'energie"),
                ("INS", "EC7", "Inventaire"),
                ("INS", "EC8", "Etude d'integration"),
                ("INS", "EC9", "Etude economique"),
                ("INS", "EC10", "Maitrise d'œuvre"),
                ("INS", "EC11", "Certification des capacités"),
                ("INS", "EC12", "Decarbonation"),
                ("INS", "EC13", "Analyse technique et financiere"),
                ("INS", "EC14", "Assistance a maitrise d'ouvrage"),
                ("INS", "EC15", "Audit de performance technique"),
                ("INS", "EC16", "Expertise technique"),
                ("INS", "EC17", "Evaluation des investissements"),
                ("INS", "EC18", "Facility management"),
                ("INS", "EC19", "Bureau d'etude"),
                ("INS", "EC20", "Contrôle technique"),
                ("INS", "EC21", "Accompagnement technique"),
                # FORMATION
                ("FOR", "EC22", "FORMATION"),
                # CARTOGRAPHIE
                ("CAR", "EC23", "Cartographie"),
                ("CAR", "EC24", "Inspection drone"),
                ("CAR", "EC25", "Projets spéciaux"),
            ]
            
            for category_code, code, name in products_kec:
                category = kec_categories[category_code]
                Product.objects.create(code=code, name=name, category=category)
                
            

            self.stdout.write(self.style.SUCCESS('Data seeding completed successfully!'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during data seeding: {str(e)}'))
            raise e

