import pandas as pd
import numpy as np
from aisexplorer.AIS import AIS
import folium
from tqdm import tqdm
# on récupère beautifulsoup4 pour parser le html
from datetime import datetime
import os
from db import DataBase

class TrackerServer():
    """
    Classe qui  permet de tracker les bateaux d'une flotte,
    de générer un fichier les fichiers HTML correspondants
    et de les héberger sur un serveur.
    """
    LIEN_SITE = 'https://pierre-cau.github.io/FleetyTracker/'
    LOCAL_PATH_TO_BACKUP = os.path.dirname(os.path.abspath(__file__)) + "\Tracker_fleet_YCC"
    LOCAL_PATH_TO_SITE = os.path.dirname(os.path.abspath(__file__)) + "\..\FLeetyTracker"
    LIEN_GITHUB = 'https://github.com/pierre-cau/YCC_fleet_tracker'
    
    URL_YCC = 'https://www.yachtclubclassique.com/'
    DEFAULT_HTML_FILE_NAME = "index.html" # nom du fichier HTML par défaut
    LOGO_URL = "images/fleetytrack_logo_withbg.png" # URL du logo
    
    EMAIL = "pcaupro@gmail.com" # email de contact
    USERNAME = "pierre-cau" # username du compte github
    REMOTE_NAME = "FleetyTracker" # nom du repo github
    BRANCH_NAME = "main" # nom de la branche github
    GIT_URL = "https://github.com/pierre-cau/FleetyTracker.git" # URL du repo github

    # PARAMETRES DE LA CARTE
    NAME = 'FleetyTrack' # nom en haut dans l'onglet du navigateur
    ZOOM = 6 # zoom de la carte par défaut
    MAX_ZOOM = 25 # zoom max
    MIN_ZOOM = 3 # zoom min
    ZOOM_LEVEL = 15 # zoom level pour focus sur un bateau
    LOCATION=[46.227638, 2.213749] # position de la carte par défaut (France)
    ATTRIBUTION = """©  <a href="https://www.yachtclubclassique.com/">Yacht Club Classique</a> | 
                        <a href="https://www.marinetraffic.com/">Marine Traffic</a> | 
                        <a href="https://www.museemaritimelarochelle.fr/">Musée Maritime de La Rochelle</a> | 
                        <a href="https://www.shom.fr//">SHOM</a> |
                        <a href="https://github.com/pierre-cau/YCC_fleet_tracker">Git de Pierre CAU</a>""" # attribution de la carte
    
    TILE_URL = 'https://geoapi.fr/shomgt/tile.php/gtpyr/{z}/{x}/{y}.png' # URL des tuiles de la carte

    # Pop up des bateaux
    TIME_TO_TURN = 2 # temps pour tourner le bateau afin de générer l'animation (en secondes)
    WIDTH = 320 # largeur de la popup
    HEIGHT = 400 # hauteur de la popup
    POSITION_BOAT_SCHEME = 90 # position du bateau sur le schéma
    MAX_WIDTH = 400 # largeur max de la popup
    MAX_HEIGHT = 400 # hauteur max de la popup

    # focus sur un bateau
    icon_size = (25, 25) # taille des icones
    icon_targeted_size = (35, 35) # taille des icones quand on clique dessus
    offset = (0, 0.001) # offset des icones (longitude, latitude)


    # dictionnaire des pays avec le lien de leur drapeau
    dictionnary_country = { 'FR':'https://upload.wikimedia.org/wikipedia/commons/thumb/9/93/Flag_of_France_%281794%E2%80%931815%2C_1830%E2%80%931974%29.svg/1280px-Flag_of_France_%281794%E2%80%931815%2C_1830%E2%80%931974%29.svg.png',
                            'GB':'https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Flag_of_the_United_Kingdom_%283-5%29.svg/1920px-Flag_of_the_United_Kingdom_%283-5%29.svg.png',
                            'IT':'https://upload.wikimedia.org/wikipedia/commons/thumb/0/03/Flag_of_Italy.svg/1280px-Flag_of_Italy.svg.png',
                            'MT':'https://upload.wikimedia.org/wikipedia/commons/thumb/7/73/Flag_of_Malta.svg/120px-Flag_of_Malta.svg.png',
                            'NL':'https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Flag_of_the_Netherlands.svg/120px-Flag_of_the_Netherlands.svg.png',
                            'PT':'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Flag_of_Portugal.svg/120px-Flag_of_Portugal.svg.png',
                            'ES':'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/Flag_of_Spain.svg/120px-Flag_of_Spain.svg.png',
                            'US':'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e2/Flag_of_the_United_States_%28Pantone%29.svg/152px-Flag_of_the_United_States_%28Pantone%29.svg.png',
                            'CH':'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/Flag_of_Switzerland.svg/80px-Flag_of_Switzerland.svg.png',
                            'BE':'https://upload.wikimedia.org/wikipedia/commons/thumb/6/65/Flag_of_Belgium.svg/92px-Flag_of_Belgium.svg.png',
                            'DE':'https://upload.wikimedia.org/wikipedia/commons/thumb/b/ba/Flag_of_Germany.svg/134px-Flag_of_Germany.svg.png',
                            'DK':'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9c/Flag_of_Denmark.svg/106px-Flag_of_Denmark.svg.png',
                            'IE':'https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/Flag_of_Ireland.svg/160px-Flag_of_Ireland.svg.png',
                            'NO':'https://upload.wikimedia.org/wikipedia/commons/thumb/d/d9/Flag_of_Norway.svg/110px-Flag_of_Norway.svg.png',
                            'SE':'Sweden',
                            }

    def __init__(self, DataBase=None,html_file_name=DEFAULT_HTML_FILE_NAME):
        """
        Constructeur de la classe TrackerServer.
        """
        self._html_file_name = html_file_name # nom du fichier HTML

    def load_data(self, date:datetime,print_result=False)-> None:
        """
        Charge les données AIS à partir d'un fichier csv
        :param date: date de la sauvegarde des données AIS
        """
        self._last_update = date
        print("_________________________________________________________")
        print("► Date de sauvegarde choisie :", date.strftime(DataBase.format_print))
        print("► Chargement des données AIS...")
        self._tracked_fleet_df = pd.read_csv(DataBase.format_path_saving_data.format(date.strftime(DataBase.FORMAT_DATE_CSV_FILE)))
        if print_result:
            print("                                 ----- DATAFRAME -----")
            print(self._tracked_fleet_df.tail(10)) # on affiche les 10 dernières lignes du dataframe
            # on affiche les 10 dernières lignes du dataframe
            print("Affichage des 10 dernières lignes du dataframe")
            print(self._tracked_fleet_df.info())
        # on print le nombre de bateaux 
        print("\nNombre de bateaux présents sur la sauvegarde : ", len(self._tracked_fleet_df))
        print("_________________________________________________________")

    def load_last_save(self)-> None:
        """
        Charge les données AIS à partir du dernier fichier csv sauvegardé

        :return: True si le chargement a réussi, False sinon
        """
        print("              --- LOAD LAST SAVE ---   ")
        list_files = self.get_list_of_saves()
        if len(list_files) > 0:
            # on charge le dernier fichier
            last_save = max(list_files)
            self.load_data(last_save)
            return True
        else:
            print("Aucune sauvegarde disponible → Lancement de la mise à jour complète de la base de données")
            print("Veuillez patienter générer un objet DataBase pour lancer la mise à jour complète")
            return False

    def load_a_save(self,print_result)-> None:
        """
        Charge les données AIS à partir d'un fichier csv en demandant à l'utilisateur de choisir une date
        """

        list_files = self.get_list_of_saves()
        print("Liste des sauvegardes disponibles :\n")
        for i, file in enumerate(list_files):
            print("{0} : {1}".format(i, file.strftime(DataBase.format_print)))
        # on demande à l'utilisateur de choisir une date
        choice = int(input("\nChoisissez le numéro d'une sauvegarde : "))
        if choice < len(list_files):
            self.load_data(list_files[choice],print_result)
        else:
            print("Choix invalide. L'intervalle de choix est [0, {0}]".format(len(list_files)-1))
        
    def get_list_of_saves(self)-> list[datetime]:
        """
        Retourne la liste des dates des sauvegardes des données AIS
        """
        list_files = os.listdir(DataBase.path_saving_data)
        # on récupère les dates associées à chaque fichier selon le format de date défini dans la classe
        list_files = [datetime.strptime(file.split('SAVE__')[1].split('.csv')[0], DataBase.FORMAT_DATE_CSV_FILE) for file in list_files]
        return list_files  

    def generate_html(self) -> None:
        """
        Fonction qui génère le fichier HTML.
        """
        print("\n\n      --> GENERATION HTML <--")
        print("--------------------------------------")
        tracked_fleet_df = self._tracked_fleet_df

        # on commence par ranger les bateaux par ordre alphabétique
        tracked_fleet_df = tracked_fleet_df.sort_values(by=['Nom du bateau'])
        tracked_fleet_df = tracked_fleet_df.reset_index(drop=True) # on reset l'index
        

        ZOOM = TrackerServer.ZOOM # zoom de la carte par défaut
        MAX_ZOOM = TrackerServer.MAX_ZOOM # zoom max
        MIN_ZOOM = TrackerServer.MIN_ZOOM # zoom min
        ZOOM_LEVEL = TrackerServer.ZOOM_LEVEL # zoom level pour focus sur un bateau
        NAME = TrackerServer.NAME # nom de la page

        # Pop up des bateaux
        POP_UPS = {} # dictionnaire qui va contenir les popups des bateaux en fonction de leur MMSI
        WIDTH = TrackerServer.WIDTH # largeur de la popup
        HEIGHT = TrackerServer.HEIGHT # hauteur de la popup
        POSITION_BOAT_SCHEME = TrackerServer.POSITION_BOAT_SCHEME # position du bateau sur le schéma
        
        TIME_TO_TURN = TrackerServer.TIME_TO_TURN # temps pour tourner le bateau afin de générer l'animation (en secondes)
        MAX_WIDTH = TrackerServer.MAX_WIDTH # largeur max de la popup
        MAX_HEIGHT = TrackerServer.MAX_HEIGHT # hauteur max de la popup

        # focus sur un bateau
        icon_size = TrackerServer.icon_size # taille des icones
        icon_targeted_size = TrackerServer.icon_targeted_size # taille des icones quand on clique dessus
        offset = TrackerServer.offset # offset des icones (longitude, latitude)

        TIME_TO_TURN = TrackerServer.TIME_TO_TURN # temps pour tourner le bateau afin de générer l'animation (en secondes)
        TILE_URL = TrackerServer.TILE_URL # url de layer pour le leaflet
        ATTRIBUTION = TrackerServer.ATTRIBUTION # attribution pour le leaflet

        print("\n >> Création de la carte")
        m = folium.Map(location=TrackerServer.LOCATION, zoom_start=ZOOM,max_zoom=MAX_ZOOM, min_zoom=MIN_ZOOM,control_scale=True)
            
        # on change le label du fond de carte
        folium.TileLayer('cartodbpositron',name="Positron").add_to(m, name='Positron')
        folium.TileLayer('cartodbdark_matter',name="Dark Matter").add_to(m, name='Dark Matter')
        folium.TileLayer(TILE_URL,attr=ATTRIBUTION,name="Carte Shom").add_to(m, name='Carte Shom')

        
        print(" >> Création des marqueurs et popups")
        # MARQUEURS + POPUPS
        for index, row in tqdm(tracked_fleet_df.iterrows(), total=tracked_fleet_df.shape[0], desc="Création des marqueurs et popups...", leave=False):
            ANGLE_TO_TURN = row['CAP'] - POSITION_BOAT_SCHEME # angle à tourner pour avoir le bateau dans le bon sens
            last_position = datetime.fromtimestamp(row['LAST_POSITION'])
            if pd.isna(row['CAP']) :
                row['CAP'] = 0 # on met 0 si on a pas de cap par défaut pour l'affichage

            if row['PAGE_LINK'] is np.nan :
                # on ajoute un marker sur la carte
                HTML = f"""
                <div style="width: {WIDTH}px;
                    height: {HEIGHT}px;
                    overflow-y: auto;
                    overflow-x: hidden;
                    padding: 5px;
                    ">
                <h3><b>{row['Nom du bateau']}</b> ({row['COUNTRY_CODE']})</h3>
                <br>
                <!-- on ajoute une image du bateau si on peut -->
                <img src="{row['IMAGE_URL']}" alt="{row['Nom du bateau']}" 
                    style="width:100%;
                    max-width: 300px; 
                    height: auto;
                    border-radius: 5px;
                    border: 1px solid #ddd;
                    padding: 5px;
                    margin-bottom: 10px;
                    /* GREY */
                    display: block;
                    margin-left: auto;
                    margin-right: auto;
                        "/>

                <p style="font-size: 14px;">
                    <!-- on crée une box qui aura à gauche le cap et à droite le schéma du bateau -->
                    <div style="width: 100%;
                        border: 1px solid #ddd;
                        border-radius: 5px;
                        padding: 5px;
                        margin-bottom: 10px;
                        /* GREY */
                        background-color: #f2f2f2;
                        ">
                    <div style="float: left;
                        position: relative;
                        max-width: {int(WIDTH/1.5)}px;
                        height: 15px;
                        display: block;
                        margin-left: auto;
                        margin-right: auto;
                        padding: 5px;
                        ">
                    <b>Vitesse : </b> {row['SPEED']} noeuds<br>
                    <b>Cap : </b> {row['CAP']}°<br>
                    <b>Latitude : </b> {row['LAT']}°<br>
                    <b>Longitude : </b> {row['LONG']}°<br>
                    <b>Dernière position : </b> {last_position}<br>
                    </div>
                    <!-- on affiche le schéma du bateau au centre de la div, tournée de ANGLE_TO_TURN pour faire le cap -->
                    <img class='tourne' src="images/boat.png" alt="boat" 
                        style="width: 100%; 
                        position: relative;
                        max-width: {int(WIDTH/3.5)}px; 
                        height: auto; 
                        transform: rotate({ANGLE_TO_TURN}deg); 
                        display: block; 
                        margin-left: auto; 
                        margin-right: 5%;
                        "/>
                    </div>
                </p>

                <button 
                    onclick="window.open('https://www.marinetraffic.com/en/ais/details/ships/mmsi:{row['MMSI']}')"
                    style="background-color: #4CAF50; /* Green */
                    border: none;
                    color: white;
                    padding: 15px 32px;
                    text-align: center;
                    text-decoration: none;
                    /* on centre le bouton */
                    display: block;
                    margin-left: auto;
                    margin-right: auto;
                    font-size: 16px;
                    cursor: pointer;
                    border-radius: 12px;
                    box-shadow: 0 0 2px 1px rgba(0, 0, 0, 0.2);
                ">
                    Voir sur Marine Traffic</button>
                </div> 
                """
                HTML +="""
                    <style>
                    @-moz-keyframes spin {
                    100% { -moz-transform: rotate(-360deg); }
                    }
                    @-webkit-keyframes spin {
                    100% { -webkit-transform: rotate(-360deg); }
                    }
                    @keyframes spin {
                    100% { -webkit-transform: rotate(-360deg); transform: rotate(-360deg); }
                    }
                """
                HTML += f"""
                .tourne {{
                -webkit-animation-name: spin;
                -webkit-animation-duration: {TIME_TO_TURN}s;
                -webkit-animation-iteration-count: 1;
                -webkit-animation-timing-function: ease-out;
                -moz-animation-name: spin;
                -moz-animation-duration: {TIME_TO_TURN}s;
                -moz-animation-iteration-count: 1;
                -moz-animation-timing-function: ease-out;
                animation-name: spin;
                animation-duration: {TIME_TO_TURN}s;
                animation-iteration-count: 1;
                animation-timing-function: ease-out;
                }}
                </style>
                """
            
            else : # on ajoute un petit bouton en bas sous forme de livre qui permet d'afficher les informations du bateau en redirigeant vers la page du musée maritime de La Rochelle
                HTML = f"""
                <div style="width: {WIDTH}px;
                    height: {HEIGHT}px;
                    overflow-y: auto;
                    overflow-x: hidden;
                    padding: 5px;
                    ">
                <h3><b>{row['Nom du bateau']}</b> ({row['COUNTRY_CODE']})</h3>
                <br>
                <img src="{row['IMAGE_URL']}" alt="{row['Nom du bateau']}" 
                    style="width:100%;
                    max-width: 300px; 
                    height: auto;
                    border-radius: 5px;
                    border: 1px solid #ddd;
                    padding: 5px;
                    margin-bottom: 10px;
                    display: block;
                    margin-left: auto;
                    margin-right: auto;
                    "/>

                <p style="font-size: 14px;">
                    <!-- on crée une box qui aura à gauche le cap et à droite le schéma du bateau -->
                    <div style="width: 100%;
                        border: 1px solid #ddd;
                        border-radius: 5px;
                        padding: 5px;
                        margin-bottom: 10px;
                        /* GREY */
                        background-color: #f2f2f2;
                        ">
                    <div style="float: left;
                        position: relative;
                        max-width: {int(WIDTH/1.5)}px;
                        height: 15px;
                        display: block;
                        margin-left: auto;
                        margin-right: auto;
                        padding: 5px;
                        ">
                    <b>Vitesse : </b> {row['SPEED']} noeuds<br>
                    <b>Cap : </b> {row['CAP']}°<br>
                    <b>Latitude : </b> {row['LAT']}°<br>
                    <b>Longitude : </b> {row['LONG']}°<br>
                    <b>Dernière position : </b> {last_position}<br>
                    </div>
                    <!-- on affiche le schéma du bateau au centre de la div, tournée de ANGLE_TO_TURN pour faire le cap -->
                    <img class='tourne' src="images/boat.png" alt="boat" 
                        style="width: 100%; 
                        position: relative;
                        max-width: {int(WIDTH/3.5)}px; 
                        height: auto; 
                        transform: rotate({ANGLE_TO_TURN}deg); 
                        display: block; 
                        margin-left: auto; 
                        margin-right: 5%;
                        "/>
                    </div>
                </p>

                <a href="{row['PAGE_LINK']}" target="_blank" title='En apprendre plus sur le site du musée maritime de La Rochelle'>
                    <img src="images/idea.png" alt="Livre"
                    style="
                    width: 50px;
                    height: auto;
                    border-radius: 50%;
                    border: 1px solid #ddd;
                    padding: 5px;
                    margin-bottom: 10px;
                    box-shadow: 0 0 2px 1px rgba(0, 0, 0, 0.2);
                    display: block;
                    margin-left: auto;
                    margin-right: auto;">
                </a>

        
                <button 
                    onclick="window.open('https://www.marinetraffic.com/en/ais/details/ships/mmsi:{row['MMSI']}')"
                    style="background-color: #4CAF50; /* Green */
                    border: none;
                    color: white;
                    padding: 15px 32px;
                    text-align: center;
                    text-decoration: none;
                    /* on centre le bouton */
                    display: block;
                    margin-left: auto;
                    margin-right: auto;
                    font-size: 16px;
                    cursor: pointer;
                    border-radius: 12px;
                    box-shadow: 0 0 2px 1px rgba(0, 0, 0, 0.2);
                ">
                    Voir sur Marine Traffic</button>
                </div>
                """    
                HTML +="""
                    <style>
                    @-moz-keyframes spin {
                    100% { -moz-transform: rotate(-360deg); }
                    }
                    @-webkit-keyframes spin {
                    100% { -webkit-transform: rotate(-360deg); }
                    }
                    @keyframes spin {
                    100% { -webkit-transform: rotate(-360deg); transform: rotate(-360deg); }
                    }
                """
                HTML += f"""
                .tourne {{
                -webkit-animation-name: spin;
                -webkit-animation-duration: {TIME_TO_TURN}s;
                -webkit-animation-iteration-count: 1;
                -webkit-animation-timing-function: ease-out;
                -moz-animation-name: spin;
                -moz-animation-duration: {TIME_TO_TURN}s;
                -moz-animation-iteration-count: 1;
                -moz-animation-timing-function: ease-out;
                animation-name: spin;
                animation-duration: {TIME_TO_TURN}s;
                animation-iteration-count: 1;
                animation-timing-function: ease-out;
                }}
                </style>
                """

            popup = folium.Popup(lazy=True, html=HTML, width=WIDTH, max_height=MAX_HEIGHT)
            POP_UPS[row['MMSI']] = popup.get_name()

            marker = folium.Marker(
                location=[row['LAT'], row['LONG']],
                popup=popup,
                icon=folium.features.CustomIcon('Tracker_fleet_YCC/images/ship.png', 
                                                icon_size=icon_size, 
                                                popup_anchor=(0, -5), 
                                                icon_anchor=(0, 0),
                                                shadow_image=None,
                                                ),
                id='marker-{}'.format(row['MMSI']),
                )
            marker.add_to(m)
                
        # on affiche la carte
        folium.LayerControl().add_to(m, name='Layer Control')

        # on ajoute une petite box par dessus la carte pour afficher les informations de la carte
        # on crée une box qui contiendra la liste des bateaux, la date de la dernière mise à jour et la possibilité focus sur un bateau
        today = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        dictionnary_country = TrackerServer.dictionnary_country
        for i in tracked_fleet_df['COUNTRY_CODE'].unique(): # on parcourt tous les pays pour vérifier qu'ils sont bien dans la liste des pays supportés
            if i not in dictionnary_country:
                print(f"-- Le code pays {i} n'est pas dans la liste des pays, merci de l'ajouter --")

        
        print(" >> Création de la box d'informations")
        # BOX D'INFORMATIONS
        HTML = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="utf-8">
        <title>{TrackerServer.NAME}</title>
        <link rel="icon" type="image/png" href="images\Logo_FleetyTrack\BG_blanc65\Logo_fleetytrack_BGW65_round.svg" width="100%">
        </head>
        <div id="box" style="width: min-content;
            position: absolute;
            /* on le met au dessus de la carte */
            z-index: 999;
            /* on le met en haut à droite */
            top: 20%;
            left: 20px;
            /* on lui donne une bordure gris foncé */
            border: 1px solid #ddd;
            border-radius: 10px;
            /* on lui donne une ombre grise comme une popup */
            box-shadow: 0 0 2px 1px #ddd;
            background-color: white;
            padding: 5px;
            ">
            <img onclick="window.open('{TrackerServer.URL_YCC}')"
                class=zoomable1 src="images\logo.png" alt="logo"
                style="width: 50%; 
                    height: auto; 
                    display: block; 
                    margin-left: auto; 
                    margin-right: auto; 
                    margin-top:5px;
                    border-radius: 50%;"/>
            <div id="track_container" style="overflow-y: scroll; height: 200px; width: max-content; margin-left: auto; margin-right: auto; margin-top:5px; margin-bottom:10px">
        """

        for index, row in tracked_fleet_df.iterrows(): # on parcourt tous les bateaux
            assert ZOOM_LEVEL > MIN_ZOOM and ZOOM_LEVEL < MAX_ZOOM, f"Le niveau de zoom doit être compris entre 0 et {MAX_ZOOM-1}"
            HTML += f"""
            <!-- on ajoute le nom du bateau à la liste. Quand on click dessus on déclenche la fonction setView() définie plus bas -->
                <a class="zoomable2 trackerbox-container-item" onclick="printTrack('{row['Nom du bateau']}','{index}'); setView({row['LAT']}, {row['LONG']}, {ZOOM_LEVEL},{index});">
                    <!-- on met le nom du bateau à gauche et le drapeau à droite -->
                    <p style="float: left;
                        margin-top: 8px;
                        margin-left: 5px;
                        margin-right: auto;
                        font-size: 15px;
                        font-family: Georgia, serif;">{row['Nom du bateau']}</p>
                    <img src="{dictionnary_country[row['COUNTRY_CODE']]}" alt="drapeau" 
                    style="  width: auto;
                            height: 25px;
                            display: block;
                            margin-left: auto;
                            margin-right: 15px;
                            float: right;
                            border-radius: 20%;
                            margin-top: 5px;
                            margin-bottom: auto;
                            ">
                """
            if not(pd.isna(row['PAGE_LINK'])): # si le bateau a une page web on ajoute un lien vers cette page : 
                    HTML += f"""
                    <img id="is_mmr_{index}" class="is_mrr" src="images/logo_mmr.png" alt="logo_mmr"/>
                        """
            HTML += f"""
                </a>
            
                <script>
                function printTrack(NAME, index) {{
                    console.log('... Tracking sur ' + NAME +' ('+ index+ ') ...');
                }}

                function setView(lat, long, zoom,index) {{
                    console.log('setView(' + lat + ', ' + long + ', ' + zoom + ')');
                    // on descend un peu les coordonnées cible pour que la popup soit bien centrée sur la carte 
                    lat = lat + {offset[1]} ;
                    long = long + {offset[0]} ;
                    {m.get_name()}.setView([lat, long], zoom);
                    // On cherche tous les éléments avec la classe leaflet-marker-icon leaflet-zoom-animated leaflet-interactive
                    // On les met dans une liste
                    var list_markers = document.getElementsByClassName('leaflet-marker-icon leaflet-zoom-animated leaflet-interactive');
                    // on récupère le marker qui a le même index que le bateau 
                    var marker = list_markers[index];

                    // si trageted_marker est défini, on le met à jour 
                    if (typeof targeted_marker !== 'undefined') {{
                    
                        // on change la source de l'image de targeted_marker pour qu'il reprenne l'image ship.png 
                        targeted_marker.src = 'images/ship.png';
                        // on change la taille de l'image 
                        targeted_marker.style.width = '{icon_size[0]}'+'px';
                        targeted_marker.style.height = '{icon_size[1]}'+'px';
                        // on redefini le targeted_marker 
                        targeted_marker = marker;
                        // on défini la source de l'image de targeted_marker pour qu'il prenne l'image logo.png
                        targeted_marker.src = 'images/logo.png';
                        // on change la taille de l'image
                        targeted_marker.style.width = '{icon_targeted_size[0]}'+'px';
                        targeted_marker.style.height = '{icon_targeted_size[1]}'+'px'; 

                    }} else {{
                    
                        // si targeted_marker n'est pas défini, on le défini
                        targeted_marker = marker;
                        // on défini la source de l'image de targeted_marker pour qu'il prenne l'image logo.png
                        targeted_marker.src = 'images/logo.png';
                        // on change la taille de l'image
                        targeted_marker.style.width = '{icon_targeted_size[0]}'+'px';
                        targeted_marker.style.height = '{icon_targeted_size[1]}'+'px';
                    }};
                }}

                </script>
                <style>
                .hoverable:hover {{
                    background-color: #ddd;
                }}
                .zoomable1:hover {{
                    /* on fait un effet de zoom */
                    transform: scale(1.1);
                    /* on rajoute une ombre grise */
                    box-shadow: 0 0 2px 1px #ddd;
                }}
                .zoomable2:hover {{
                    /* on fait un effet de zoom */
                    transform: scale(1.05);
                    /* on rajoute une ombre grise */
                    box-shadow: 0 0 2px 1px #ddd;
                }}
                </style>
            """

        HTML += f"""
            </div>
            <p class="trackbox-container-footer">
            <b>Nombre de bateaux : </b> {len(tracked_fleet_df)}<br>
            <b>Dernière mise à jour de la carte : </b> {today}<br>
            </p>
        </div>
        """
        WIDTH = 5
        HTML+= f"""

        <!-- on ajoute le logo en bas à droite de la carte -->
        <div class="zoomable1 signature" onclick="window.open('{TrackerServer.LIEN_GITHUB}')">
                <img src="images\Logo_FleetyTrack\sansBG\Logo_fleetytrack_sansBG.svg" alt="logo" style="
                    width: auto;
                    float: left;
                    margin-left: 5px;
                    padding: 5px;
                    height: inherit;">
                <img src="images/fleetytrack_logopowered.png" alt='poweredby' style="
                    float:right;
                    height:inherit;
                    width:auto;">
        </div>


        <style>
        /* on cible les screen de moins de plus de 600px de large */
        @media only screen and (min-width: 700px) {{
            .signature {{
                height: 120px;
                position: absolute;
                margin-right: 5px;
                margin-bottom: 20px;
                background-color: rgba(255, 255, 255, 0.5);
                box-shadow: 0 0 2px 1px #ddd;
                border-radius: 5%;
                display: block;
                z-index: 1000;
                width: fit-content;
                bottom: 0;
                right: 0;
                }}

            .is_mrr {{
                 width: auto;
                 height: 25px;
                 display: block;
                 margin-left: auto;
                 margin-right: 10px;
                 float: right;
                 border-radius: 20%;
                 margin-top: 5%;
                 margin-bottom: auto;
                }}

            .trackerbox-container-footer {{
                font-size: 13px;
                padding : 10px;
                height: 70px;
                font-family: Georgia, serif;
                }}   
            .trackerbox-container-item {{
                color: #000;
                text-decoration: none;
                display: block;
                height: 45px;
                padding: 5px;
                border-radius: 5px;
                border: 1px solid #ddd;
                margin-bottom: 5px;
                text-align: left;
                /* on rajoute une ombre grise */
                box-shadow: 0 0 2px 1px #ddd;
                }}        
            
        }}
        @media only screen and (max-width: 700px) {{
            .signature {{
                height: 40px;
                position: absolute;
                margin-right: 5px;
                margin-bottom: 20px;
                background-color: rgba(255, 255, 255, 0.5);
                box-shadow: 0 0 2px 1px #ddd;
                border-radius: 5%;
                display: block;
                z-index: 1000;
                width: fit-content;
                bottom: 0;
                right: 0;
                }}
            .is_mrr {{
                 width: auto;
                 height: 25px;
                 display: block;
                 margin-left: auto;
                 margin-right: 10px;
                 float: right;
                 border-radius: 20%;
                 margin-top: 5%;
                 margin-bottom: auto;
                }}

            .trackerbox-container-footer {{
                font-size: 13px;
                padding : 10px;
                height: 70px;
                font-family: Georgia, serif;
                }}  

            .trackerbox-container-item {{
                color: #000;
                text-decoration: none;
                display: block;
                height: 45px;
                padding: 5px;
                border-radius: 5px;
                border: 1px solid #ddd;
                margin-bottom: 5px;
                text-align: left;
                /* on rajoute une ombre grise */
                box-shadow: 0 0 2px 1px #ddd;
                }}
            
        }}
        </style>
            
        </html>

        
"""

        # on ajoute la box à la carte
        m.get_root().html.add_child(folium.Element(HTML))
        print("\n--------------------------------------")
        print(f">>> {len(tracked_fleet_df)} bateaux ajoutés à la carte <<<")
        # on sauvegarde la carte
        m.save("Tracker_fleet_YCC/"+self._html_file_name)
        print("\n... Carte sauvegardée ...")
        print("--------------------------------------\n")
    
    def config_git(self):
        """Configure le git pour pouvoir push le site sur le serveur
        """
        print("\n------------ CONFIG GIT ------------------")
        prefix = ">>> "
        
        # on supprime le remote site si il existe
        COMMANDE = f"git remote rm {TrackerServer.REMOTE_NAME}"
        print(prefix+COMMANDE)
        os.system(COMMANDE)

        COMMANDE = f"git remote -v"
        print(prefix+COMMANDE)
        print("")
        os.system(COMMANDE)

        # on ajoute le remote site
        COMMANDE = f"git remote add {TrackerServer.REMOTE_NAME} {TrackerServer.GIT_URL}"
        print("\n"+prefix+COMMANDE)
        os.system(COMMANDE)

        COMMANDE = f"git remote -v"
        print(prefix+COMMANDE)
        print("")
        os.system(COMMANDE)

        print("--------------------------------------\n")
        return self

    def publish_site(self)-> str:
        """Publie le site sur le serveur
        Returns:
            str: [lien du site]
        """
        print("\n------------ PUBLISH SITE ------------------")
        prefix = "\n>>> "
        # on init un dépot git
        COMMANDE = f"cd {TrackerServer.LOCAL_PATH_TO_SITE} && git init"
        print(prefix+COMMANDE)
        os.system(COMMANDE)

        # on se met dans la branche
        COMMANDE = f"cd {TrackerServer.LOCAL_PATH_TO_SITE} && git checkout {TrackerServer.BRANCH_NAME}"
        print(prefix+COMMANDE)
        os.system(COMMANDE)

        # on print le status du dépot git
        COMMANDE = f"cd {TrackerServer.LOCAL_PATH_TO_SITE} && git status"
        print(prefix+COMMANDE)
        os.system(COMMANDE)
        
        # on supprime tous les fichiers et dossiers présents dans le dossier du dépot git
        COMMANDE = f'cd {TrackerServer.LOCAL_PATH_TO_SITE} && del /f /q "index.html" && del /f /q "README.md" && del /f /q "LICENSE" && rmdir /s /q "images" && rmdir /s /q "DATA_SAVES"'
        print(prefix+COMMANDE)
        os.system(COMMANDE)

        # on copie colle tous les fichers du dossier backup dans le dossier du dépot git
        COMMANDE = f'copy {TrackerServer.LOCAL_PATH_TO_BACKUP} {TrackerServer.LOCAL_PATH_TO_SITE} /y'
        # on copie colle tous les sous dossiers du dossier backup dans le dossier du dépot git
        COMMANDE += f' && xcopy {TrackerServer.LOCAL_PATH_TO_BACKUP} {TrackerServer.LOCAL_PATH_TO_SITE} /e /y'
        print(prefix+COMMANDE)
        os.system(COMMANDE)
        # on affiche le contenu du dossier
        COMMANDE = f"cd {TrackerServer.LOCAL_PATH_TO_SITE} && tree /f"
        print(prefix+COMMANDE)
        os.system(COMMANDE)

        # on ajoute tous les fichiers du dossier du dépot git
        COMMANDE = f"cd {TrackerServer.LOCAL_PATH_TO_SITE} && git add ."
        print(prefix+COMMANDE)
        os.system(COMMANDE)

        # on pull les fichiers du dossier du dépot git
        COMMANDE = f"cd {TrackerServer.LOCAL_PATH_TO_SITE} && git pull {TrackerServer.REMOTE_NAME} {TrackerServer.BRANCH_NAME}"
        print(prefix+COMMANDE)
        os.system(COMMANDE)

        # on commit les fichiers du dossier du dépot git
        COMMANDE = f'cd {TrackerServer.LOCAL_PATH_TO_SITE} && git commit -m "Update FleetyTracker {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}"'
        print(prefix+COMMANDE)
        os.system(COMMANDE)

        # on push les fichiers du dossier du dépot git
        COMMANDE = f"cd {TrackerServer.LOCAL_PATH_TO_SITE} && git push {TrackerServer.REMOTE_NAME} {TrackerServer.BRANCH_NAME}"
        print(prefix+COMMANDE)
        os.system(COMMANDE)


        print("\n--------------------------------------")
        print(f">>> Site publié à l'adresse : {TrackerServer.LIEN_SITE} <<<")
        print("--------------------------------------\n")

        return TrackerServer.LIEN_SITE


if __name__ == "__main__":

    site = TrackerServer()
    site.load_last_save()
    site.generate_html()