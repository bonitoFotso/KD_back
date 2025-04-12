from api.user.models import User
from document.models import Entity, Category, Product

def seed_data():
    # Création des entités
    kes_inspections = Entity.objects.create(code="KIP", name="KES INSPECTIONS & PROJECTS")
    kes_energy = Entity.objects.create(code="KEC", name="KES ENERGY & CARBON")
    kes_sarl = Entity.objects.create(code="KES", name="KAMER ENGINEERING SOLUTIONS")  # Correction du nom

    # Création des catégories pour KES INSPECTIONS & PROJECTS
    categories_kes = {
        "INS": "INSPECTION",
        "DEV": "DEVELOPPEMENT",  # Ajouté
        "FOR": "FORMATION",
        "QHS": "QUALITE HYGIENE SECURITE ENVIRONNEMENT (QHSE)",  # Correction du nom complet
        "CAR": "CARTOGRAPHIE",  # Correction orthographique
        "IND": "INDUSTRIE",
        "PRJ": "PROJETS",  # Ajouté
        "CTC": "CONTRÔLE TECHNIQUE DES CONSTRUCTIONS",
    }
    kes_categories = {}
    for code, name in categories_kes.items():
        kes_categories[code] = Category.objects.create(code=code, name=name, entity=kes_inspections)

    # Création des catégories pour KES ENERGY & CARBON
    categories_kec = {
        "INS": "INSPECTION",
        "DEV": "DEVELOPPEMENT",  # Ajouté
        "FOR": "FORMATION",
        "QHS": "QUALITE HYGIENE SECURITE ENVIRONNEMENT (QHSE)",  # Correction du nom complet
        "CAR": "CARTOGRAPHIE",  # Correction orthographique
        "ETD": "ETUDE",  # Ajouté - spécifique à KES EC
    }
    kec_categories = {}
    for code, name in categories_kec.items():
        kec_categories[code] = Category.objects.create(code=code, name=name, entity=kes_energy)

    # Création des produits pour KES INSPECTIONS & PROJECTS
    products_kes = [
        # INSPECTION
        ("INS", "VINS1", "Verification electrique"),
        ("INS", "VINS2", "Mesure de terre"),
        ("INS", "VINS3", "Vérification électrique par thermographie infrarouge"),
        ("INS", "VINS4", "Etude Arc Flash"),
        ("INS", "VINS5", "Etude Selectivité"),
        ("INS", "VINS6", "Foudre"),
        ("INS", "VINS7", "Verification des ascenseurs"),
        ("INS", "VINS8", "Evaluation risque ATEX"),
        ("INS", "VINS9", "Vérification des appareils de levage"),
        ("INS", "VINS10", "Audit sécurité incendie"),
        ("INS", "VINS11", "Diagnostic CTC"),
        ("INS", "VINS12", "Audit climatisation"),
        ("INS", "VINS13", "Audit énergetique"),
        ("INS", "VINS14", "Verification des extincteurs"),
        ("INS", "VINS15", "Audit plomberie"),
        ("INS", "VINS16", "Expertise technique"),
        ("INS", "VINS17", "Facility management"),
        ("INS", "VINS18", "Eclairage public"),
        ("INS", "VINS19", "Accompagnement technique"),
        ("INS", "VINS20", "Verification equipement de chantier"),
        ("INS", "VINS21", "Analyse laboratoire"),
        ("INS", "VINS22", "Vente EPI"),
        ("INS", "VINS23", "Verification des echafaudages, echelles et point d'ancrage"),
        # FORMATION
        ("FOR", "VF1", "Habilitation électrique"),
        ("FOR", "VF2", "Travaux en hauteur"),
        ("FOR", "VF3", "Premiers secours"),
        ("FOR", "VF4", "Sécurité incendie"),
        ("FOR", "VF5", "Conduite des appareils de levage"),
        ("FOR", "VF6", "Elingage"),
        ("FOR", "VF7", "Equipements sous pression"),
        ("FOR", "VF8", "Thermographie infrarouge"),
        ("FOR", "VF9", "Fresque du climat"),
        ("FOR", "VF10", "Habilitation mecanique"),
        ("FOR", "VF11", "Sensibilisation du personnel aux risques ATEX"),
        ("FOR", "VF12", "Maîtriser le risque ATEX lors des opérations de maintenance"),
        ("FOR", "VF13", "Formation Habilitation GAZ"),
        ("FOR", "VF14", "Bornes de recharge électrique - IRVE"),
        ("FOR", "VF15", "Habilitation electrique - Bornes de recharge électrique - IRVE"),
        # Ajout d'autres formations selon le fichier Excel
        # QHSE
        ("QHS", "VQ1", "Mesure sonore"),
        ("QHS", "VQ2", "Mesure d'éclairement"),
        ("QHS", "VQ3", "Mesure de la qualité d'air"),
        ("QHS", "VQ4", "Bilan carbone"),
        # INDUSTRIE
        ("IND", "VI1", "Verification des equipements sous pression"),
        ("IND", "VI2", "Contrôle non destructif"),
        ("IND", "VI3", "Baremage"),
        ("IND", "VI4", "Tarage des soupapes"),
        # CARTOGRAPHIE
        ("CAR", "VC1", "Cartographie"),
        ("CAR", "VC2", "Inspection drone"),
        ("CAR", "VC3", "Projets spéciaux"),
        # CONTRÔLE TECHNIQUE DES CONSTRUCTIONS
        ("CTC", "VC4", "Diagnostique"),
        ("CTC", "VC5", "Contrôle technique"),
        # PROJETS
        ("PRJ", "VP1", "Bureau d'etude"),
        ("PRJ", "VP2", "Maitrise d'œuvre"),
    ]
    for category_code, code, name in products_kes:
        category = kes_categories[category_code]
        Product.objects.create(code=code, name=name, category=category)

    # Création des produits pour KES ENERGY & CARBON
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
        ("FOR", "EC22", "Fresque du climat"),  # Remplacé par un produit spécifique
        ("FOR", "EC23", "Energie - Carbone"),  # Ajouté
        # CARTOGRAPHIE
        ("CAR", "EC24", "Cartographie"),
        ("CAR", "EC25", "Inspection drone"),
        ("CAR", "EC26", "Projets spéciaux"),
        # ETUDE - Catégorie spécifique à KES EC
        ("ETD", "EC27", "Études énergétiques"),
        ("ETD", "EC28", "Études de décarbonation"),
    ]
    for category_code, code, name in products_kec:
        category = kec_categories[category_code]
        Product.objects.create(code=code, name=name, category=category)

    print("Seed data successfully added!")
    
    from django.contrib.auth.models import User

def seed_users():
    """Crée les utilisateurs avec leurs emails, noms d'utilisateur et mots de passe prédéfinis."""
    
    # Définition des données utilisateurs avec mot de passe prédéfini "Kes@2023!"
    users_data = [
        {"email": "alvin.jamfa@kes-africa.com", "username": "alvin.jamfa", "first_name": "Alvin", "last_name": "Jamfa", "password": "Kes@2023!"},
        {"email": "adriane.njike@kes-africa.com", "username": "adriane.njike", "first_name": "Adriane", "last_name": "Njike", "password": "Kes@2023!"},
        {"email": "jb.onomo@kes-africa.com", "username": "jb.onomo", "first_name": "Jean-Baptiste", "last_name": "Onomo", "password": "Kes@2023!"},
        {"email": "patrick.essame@kes-africa.com", "username": "patrick.essame", "first_name": "Patrick", "last_name": "Essame", "password": "Kes@2023!"},
        {"email": "helene.ndenga@kes-africa.com", "username": "helene.ndenga", "first_name": "Hélène", "last_name": "Ndenga", "password": "Kes@2023!"},
        {"email": "emiliene.matip@kes-africa.com", "username": "emiliene.matip", "first_name": "Émilienne", "last_name": "Matip", "password": "Kes@2023!"},
        {"email": "bonito.fotso@kes-africa.com", "username": "bonito.fotso", "first_name": "Bonito", "last_name": "Fotso", "password": "Kes@2023!"},
    ]
    
    created_users = []
    
    for user_data in users_data:
        # Vérification si l'utilisateur existe déjà
        if not User.objects.filter(username=user_data["username"]).exists():
            # Création de l'utilisateur
            user = User.objects.create_user(
                username=user_data["username"],
                email=user_data["email"],
                password=user_data["password"],

            )
            
            created_users.append({
                "username": user.username,
                "email": user.email,
                "password": user_data["password"],
                
            })
        else:
            print(f"L'utilisateur {user_data['username']} existe déjà.")
    
    # Affichage des informations des utilisateurs créés
    if created_users:
        print("Utilisateurs créés avec succès:")
        print("=" * 80)
        print(f"{'Nom d utilisateur':<20} {'Email':<35} {'Mot de passe':<15} ")
        print("-" * 80)
        
        for user in created_users:
            print(f"{user['username']:<20} {user['email']:<35} {user['password']:<15} ")
    else:
        print("Aucun nouvel utilisateur n'a été créé.")
    
    return created_users

# Pour utiliser cette fonction, appelez simplement:
# seed_users()