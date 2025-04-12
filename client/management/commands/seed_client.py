# seeders.py
from django.db import transaction
from django.utils import timezone

from api.user.models import User
from client.models import Contact, Pays, Region, Ville, Client, Site


class CameroonSeeder:
    def __init__(self):
        self.pays = None
        
    @transaction.atomic
    def seed(self):
        #self.seed_susers()
        self.seed_cameroon()
        self.seed_regions()
        self.seed_cities()
        self.seed_sabc()
        self.seed_companies()
        self.seed_contacts()  # Ajout de la nouvelle méthode
        
    #def seed_susers(self):
    #    User.objects.create_superuser(email="r@r.com", password="2016", username="root")
    #    print("✓ Superutilisateur créé")
        
    def seed_cameroon(self):
        self.pays = Pays.objects.create(
            nom="Cameroun",
            code_iso="CMR"
        )
        print("✓ Pays créé : Cameroun")
        
    
        
    def seed_regions(self):
        regions_data = [
            "Adamaoua",
            "Centre",
            "Est",
            "Extrême-Nord",
            "Littoral",
            "Nord",
            "Nord-Ouest",
            "Ouest",
            "Sud",
            "Sud-Ouest"
        ]
        
        self.regions = {}
        for region_name in regions_data:
            region = Region.objects.create(
                nom=region_name,
                pays=self.pays
            )
            self.regions[region_name] = region
        print("✓ 10 régions créées")
        
    def seed_cities(self):
        cities_data = {
            "Adamaoua": ["Ngaoundéré", "Meiganga", "Tibati", "Banyo"],
            "Centre": ["Yaoundé", "Obala", "Mbalmayo", "Nanga-Eboko"],
            "Est": ["Bertoua", "Abong-Mbang", "Batouri", "Yokadouma"],
            "Extrême-Nord": ["Maroua", "Kousseri", "Mokolo", "Kaélé"],
            "Littoral": ["Douala", "Nkongsamba", "Edéa", "Loum"],
            "Nord": ["Garoua", "Guider", "Pitoa", "Poli"],
            "Nord-Ouest": ["Bamenda", "Kumbo", "Nkambé", "Wum"],
            "Ouest": ["Bafoussam", "Dschang", "Mbouda", "Bafang"],
            "Sud": ["Ebolowa", "Kribi", "Sangmélima", "Ambam"],
            "Sud-Ouest": ["Buéa", "Limbé", "Kumba", "Tiko"]
        }
        
        self.villes = {}
        for region_name, cities in cities_data.items():
            region = self.regions[region_name]
            for city_name in cities:
                ville = Ville.objects.create(
                    nom=city_name,
                    region=region
                )
                self.villes[city_name] = ville
        print("✓ 40 villes créées")
        
    def seed_sabc(self):
        # Création du client SABC
        sabc = Client.objects.create(
            nom="Société Anonyme des Brasseries du Cameroun",
            email="contact@sabc.cm",
            telephone="+237 233 42 35 25",
            adresse="76 Rue Prince Bell, Bonanjo",
            ville=self.villes["Douala"],
            secteur_activite="Industrie Brassicole",
            bp="BP 4036",
            quartier="Bonanjo",
            matricule="M0392847365",
            agreer=False,
            agreement_fournisseur=False,
            entite=""
        )
        print("✓ Client SABC créé")
        
        # Création des sites SABC dans différentes villes
        sites_data = [
            {
                "ville": "Douala",
                "nom": "Siège Social SABC",
                "localisation": "76 Rue Prince Bell, Bonanjo",
                "description": "Siège social et site de production principal"
            },
            {
                "ville": "Yaoundé",
                "nom": "SABC Yaoundé",
                "localisation": "Zone Industrielle Mvan",
                "description": "Site de production et distribution"
            },
            {
                "ville": "Garoua",
                "nom": "SABC Garoua",
                "localisation": "Zone Industrielle",
                "description": "Centre de distribution régional Nord"
            },
            {
                "ville": "Bafoussam",
                "nom": "SABC Bafoussam",
                "localisation": "Quartier Industriel",
                "description": "Centre de distribution régional Ouest"
            }
        ]
        
        for site_data in sites_data:
            Site.objects.create(
                nom=site_data["nom"],
                client=sabc,
                localisation=site_data["localisation"],
                description=site_data["description"],
                ville=self.villes[site_data["ville"]]
            )
        print("✓ 4 sites SABC créés")
        
    # seeders.py
    def seed_companies(self):
        # SCDP (Société Camerounaise des Dépôts Pétroliers)
        scdp = Client.objects.create(
            nom="Société Camerounaise des Dépôts Pétroliers",
            email="contact@scdp.cm",
            telephone="+237 233 42 30 30",
            adresse="Boulevard de la République",
            ville=self.villes["Douala"],
            secteur_activite="Stockage et Distribution de Produits Pétroliers",
            bp="BP 2271",
            quartier="Bonanjo",
            matricule="M123456789",
            agreer=False,
            agreement_fournisseur=False,
            entite=""
        )
        
        scdp_sites = [
            {
                "ville": "Douala",
                "nom": "SCDP Douala",
                "localisation": "Zone Portuaire",
                "description": "Dépôt principal et siège social"
            },
            {
                "ville": "Yaoundé",
                "nom": "SCDP Yaoundé",
                "localisation": "Nsam",
                "description": "Dépôt régional Centre"
            },
            {
                "ville": "Garoua",
                "nom": "SCDP Garoua",
                "localisation": "Zone Industrielle",
                "description": "Dépôt régional Nord"
            }
        ]
        
        for site_data in scdp_sites:
            Site.objects.create(
                nom=site_data["nom"],
                client=scdp,
                localisation=site_data["localisation"],
                description=site_data["description"],
                ville=self.villes[site_data["ville"]]
            )
        
        # CIMENCAM (Cimenteries du Cameroun)
        cimencam = Client.objects.create(
            nom="CIMENCAM",
            email="contact@cimencam.cm",
            telephone="+237 233 42 01 15",
            adresse="Rue Joffre",
            ville=self.villes["Douala"],
            secteur_activite="Production de Ciment",
            bp="BP 1323",
            quartier="Akwa",
            matricule="M987654321",
            agreer=False,
            agreement_fournisseur=False,
            entite=""
        )
        
        cimencam_sites = [
            {
                "ville": "Douala",
                "nom": "CIMENCAM Bonabéri",
                "localisation": "Zone Industrielle Bonabéri",
                "description": "Usine de production principale"
            },
            {
                "ville": "Yaoundé",
                "nom": "CIMENCAM Nomayos",
                "localisation": "Nomayos",
                "description": "Centre de broyage"
            },
            {
                "ville": "Garoua",
                "nom": "CIMENCAM Figuil",
                "localisation": "Figuil",
                "description": "Usine de production Nord"
            }
        ]
        
        for site_data in cimencam_sites:
            Site.objects.create(
                nom=site_data["nom"],
                client=cimencam,
                localisation=site_data["localisation"],
                description=site_data["description"],
                ville=self.villes[site_data["ville"]]
            )
        
        # BROLI
        broli = Client.objects.create(
            nom="BROLI",
            email="contact@broli.cm",
            telephone="+237 233 40 00 00",
            adresse="Rue Laquintinie",
            ville=self.villes["Douala"],
            secteur_activite="Agro Allimentaire",
            bp="BP 4036",
            quartier="Akwa",
            matricule="M456789123",
            agreer=False,
            agreement_fournisseur=False,
            entite=""
        )
        
        broli_sites = [
            {
                "ville": "Douala",
                "nom": "BROLI Production",
                "localisation": "Zone Industrielle",
                "description": "Site de production principal"
            },
            {
                "ville": "Yaoundé",
                "nom": "BROLI Distribution Centre",
                "localisation": "Quartier Industriel",
                "description": "Centre de distribution"
            }
        ]
        
        for site_data in broli_sites:
            Site.objects.create(
                nom=site_data["nom"],
                client=broli,
                localisation=site_data["localisation"],
                description=site_data["description"],
                ville=self.villes[site_data["ville"]]
            )
        
        # BOCOM
        bocom = Client.objects.create(
            nom="BOCOM",
            email="contact@bocom.cm",
            telephone="+237 233 43 00 00",
            adresse="Rue des Palmiers",
            ville=self.villes["Douala"],
            secteur_activite="Distribution et Commerce",
            bp="BP 5556",
            quartier="Bali",
            matricule="M789123456",
            agreer=False,
            agreement_fournisseur=False,
            entite=""
        )
        
        bocom_sites = [
            {
                "ville": "Douala",
                "nom": "BOCOM Siège",
                "localisation": "Quartier Bali",
                "description": "Siège social et entrepôt principal"
            },
            {
                "ville": "Yaoundé",
                "nom": "BOCOM Yaoundé",
                "localisation": "Centre ville",
                "description": "Bureau régional et entrepôt"
            }
        ]
        
        for site_data in bocom_sites:
            Site.objects.create(
                nom=site_data["nom"],
                client=bocom,
                localisation=site_data["localisation"],
                description=site_data["description"],
                ville=self.villes[site_data["ville"]]
            )
        
        # AGL
        agl = Client.objects.create(
            nom="AGL",
            email="contact@agl.cm",
            telephone="+237 233 44 00 00",
            adresse="Zone Industrielle Bonabéri",
            ville=self.villes["Douala"],
            secteur_activite="Logistique et Transport",
            bp="BP 12345",
            quartier="Bonabéri",
            matricule="M321654987",
            agreer=False,
            agreement_fournisseur=False,
            entite=""
        )
        
        agl_sites = [
            {
                "ville": "Douala",
                "nom": "AGL Centre Emplissage",
                "localisation": "Bonabéri",
                "description": "Centre d'emplissage principal"
            },
            {
                "ville": "Yaoundé",
                "nom": "AGL Distribution",
                "localisation": "Quartier Industriel",
                "description": "Centre de distribution"
            },
            {
                "ville": "Bafoussam",
                "nom": "AGL Ouest",
                "localisation": "Zone Industrielle",
                "description": "Dépôt régional"
            }
        ]
        
        for site_data in agl_sites:
            Site.objects.create(
                nom=site_data["nom"],
                client=agl,
                localisation=site_data["localisation"],
                description=site_data["description"],
                ville=self.villes[site_data["ville"]]
            )
        
        # SIKA Cameroun
        sika = Client.objects.create(
            nom="SIKA Cameroun",
            email="contact@sika.cm",
            telephone="+237 233 45 00 00",
            adresse="Rue des Industries",
            ville=self.villes["Douala"],
            secteur_activite="Matériaux de Construction",
            bp="BP 4012",
            quartier="Zone Industrielle",
            matricule="M147258369",
            agreer=False,
            agreement_fournisseur=False,
            entite=""
        )
        
        sika_sites = [
            {
                "ville": "Douala",
                "nom": "SIKA Production",
                "localisation": "Zone Industrielle",
                "description": "Usine de production"
            },
            {
                "ville": "Yaoundé",
                "nom": "SIKA Centre",
                "localisation": "Quartier Industriel",
                "description": "Centre de distribution"
            }
        ]
        
        for site_data in sika_sites:
            Site.objects.create(
                nom=site_data["nom"],
                client=sika,
                localisation=site_data["localisation"],
                description=site_data["description"],
                ville=self.villes[site_data["ville"]]
            )
            
        print("✓ 7 entreprises majeures créées avec leurs sites")
        
    def seed_contacts(self):
        # SABC Contacts
        Contact.objects.create(
            nom="Kamdem",
            prenom="Jean-Paul",
            email="jp.kamdem@sabc.cm",
            telephone="+237 233 42 35 26",
            mobile="+237 690 11 22 33",
            poste="Directeur des Achats",
            service="Direction des Achats",
            role_achat="Directeur",
            client=Client.objects.get(nom__contains="Société Anonyme des Brasseries du Cameroun"),
            ville=self.villes["Douala"],
            quartier="Bonanjo",
            bp="BP 4036",
            notes="Contact principal pour les appels d'offres"
        )

        Contact.objects.create(
            nom="Mbarga",
            prenom="Sophie",
            email="s.mbarga@sabc.cm",
            telephone="+237 233 42 35 27",
            mobile="+237 690 22 33 44",
            poste="Responsable Approvisionnement",
            service="Approvisionnement",
            role_achat="Approbateur",
            client=Client.objects.get(nom__contains="Société Anonyme des Brasseries du Cameroun"),
            ville=self.villes["Douala"],
            quartier="Bonanjo",
            bp="BP 4036"
        )

        # SCDP Contacts
        Contact.objects.create(
            nom="Tchinda",
            prenom="Robert",
            email="r.tchinda@scdp.cm",
            telephone="+237 233 42 30 31",
            mobile="+237 690 33 44 55",
            poste="Chef Service Achats",
            service="Service Achats",
            role_achat="Validation technique",
            client=Client.objects.get(nom__contains="Société Camerounaise des Dépôts Pétroliers"),
            ville=self.villes["Douala"],
            quartier="Bonanjo"
        )

        Contact.objects.create(
            nom="Ngo Banga",
            prenom="Marie",
            email="m.ngobanga@scdp.cm",
            telephone="+237 233 42 30 32",
            mobile="+237 690 44 55 66",
            poste="Responsable Logistique",
            service="Logistique",
            role_achat="Émetteur des bons de commande",
            client=Client.objects.get(nom__contains="Société Camerounaise des Dépôts Pétroliers"),
            ville=self.villes["Douala"],
            quartier="Bonanjo"
        )

        # CIMENCAM Contacts
        Contact.objects.create(
            nom="Fotso",
            prenom="Paul",
            email="p.fotso@cimencam.cm",
            telephone="+237 233 42 01 16",
            mobile="+237 690 55 66 77",
            poste="Directeur Supply Chain",
            service="Supply Chain",
            role_achat="Directeur",
            client=Client.objects.get(nom__contains="CIMENCAM"),
            ville=self.villes["Douala"],
            quartier="Bonaberi"
        )

        Contact.objects.create(
            nom="Ekambi",
            prenom="Thomas",
            email="t.ekambi@cimencam.cm",
            telephone="+237 233 42 01 17",
            mobile="+237 690 66 77 88",
            poste="Acheteur Senior",
            service="Achats",
            role_achat="Acheteur",
            client=Client.objects.get(nom__contains="CIMENCAM"),
            ville=self.villes["Douala"],
            quartier="Bonaberi"
        )

        # BROLI Contacts
        Contact.objects.create(
            nom="Ndongo",
            prenom="Alice",
            email="a.ndongo@broli.cm",
            telephone="+237 233 40 00 01",
            mobile="+237 690 77 88 99",
            poste="Responsable Achats",
            service="Achats",
            role_achat="Responsable",
            client=Client.objects.get(nom__contains="BROLI"),
            ville=self.villes["Douala"]
        )

        Contact.objects.create(
            nom="Tamba",
            prenom="Joseph",
            email="j.tamba@broli.cm",
            telephone="+237 233 40 00 02",
            mobile="+237 691 11 22 33",
            poste="Acheteur",
            service="Achats",
            role_achat="Acheteur",
            client=Client.objects.get(nom__contains="BROLI"),
            ville=self.villes["Douala"]
        )

        # BOCOM Contacts
        Contact.objects.create(
            nom="Simo",
            prenom="Pierre",
            email="p.simo@bocom.cm",
            telephone="+237 233 43 00 01",
            mobile="+237 691 22 33 44",
            poste="Directeur Commercial",
            service="Commercial",
            role_achat="Approbateur final",
            client=Client.objects.get(nom__contains="BOCOM"),
            ville=self.villes["Douala"]
        )

        Contact.objects.create(
            nom="Nkeng",
            prenom="Judith",
            email="j.nkeng@bocom.cm",
            telephone="+237 233 43 00 02",
            mobile="+237 691 33 44 55",
            poste="Chef Service Approvisionnement",
            service="Approvisionnement",
            role_achat="Gestionnaire des commandes",
            client=Client.objects.get(nom__contains="BOCOM"),
            ville=self.villes["Douala"]
        )

        # AGL Contacts
        Contact.objects.create(
            nom="Kuete",
            prenom="Bernard",
            email="b.kuete@agl.cm",
            telephone="+237 233 44 00 01",
            mobile="+237 691 44 55 66",
            poste="Responsable Supply Chain",
            service="Supply Chain",
            role_achat="Superviseur",
            client=Client.objects.get(nom__contains="AGL"),
            ville=self.villes["Douala"]
        )

        Contact.objects.create(
            nom="Nana",
            prenom="Clarisse",
            email="c.nana@agl.cm",
            telephone="+237 233 44 00 02",
            mobile="+237 691 55 66 77",
            poste="Acheteuse Senior",
            service="Achats",
            role_achat="Acheteuse",
            client=Client.objects.get(nom__contains="AGL"),
            ville=self.villes["Douala"]
        )

        # SIKA Contacts
        Contact.objects.create(
            nom="Tchoupo",
            prenom="Michel",
            email="m.tchoupo@sika.cm",
            telephone="+237 233 45 00 01",
            mobile="+237 691 66 77 88",
            poste="Directeur des Opérations",
            service="Direction des Opérations",
            role_achat="Directeur",
            client=Client.objects.get(nom__contains="SIKA Cameroun"),
            ville=self.villes["Douala"]
        )

        Contact.objects.create(
            nom="Meka",
            prenom="Christine",
            email="c.meka@sika.cm",
            telephone="+237 233 45 00 02",
            mobile="+237 691 77 88 99",
            poste="Responsable Achats",
            service="Achats",
            role_achat="Responsable",
            client=Client.objects.get(nom__contains="SIKA Cameroun"),
            ville=self.villes["Douala"]
        )

        print("✓ Contacts créés pour toutes les entreprises")




# Management command
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Seed the database with Cameroon data'

    def handle(self, *args, **options):
        self.stdout.write('Début du seeding...')
        seeder = CameroonSeeder()
        seeder.seed()
        self.stdout.write(self.style.SUCCESS('Seeding terminé avec succès !'))

# Pour l'utiliser, créez un fichier management/commands/seed_cameroon.py
# puis exécutez : python manage.py seed_cameroon