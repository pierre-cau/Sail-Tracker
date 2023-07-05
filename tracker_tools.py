# IMPORT
import pandas as pd
import numpy as np
from aisexplorer.AIS import AIS
from folium.plugins import HeatMap
import folium
import urllib
from tqdm import tqdm
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import requests
# on récupère beautifulsoup4 pour parser le html
from bs4 import BeautifulSoup
from datetime import datetime
import time
import random
import re
import os


class DataBase():
    """
    Classe qui permet de récupérer les données AIS et de les stocker dans un dataframe et de gérer toute la partie
    base de données du site Web
    """

    # Lien vers la base de données de contrôle des navire (ggsheet)
    googleSheetId = "1Jqa28X5tSbMgV_F3SgXxd4Qv3fD4xtBE52VflBqPPBQ"
    worksheetName = "summary"
    url_fleet = 'https://docs.google.com/spreadsheets/d/{0}/gviz/tq?tqx=out:csv&sheet={1}'.format(
        googleSheetId, urllib.parse.quote(worksheetName))

    # Paramètrage des saves locales des données AIS
    path_saving_data = "Tracker_fleet_YCC/data_ship/"
    format_path_saving_data = path_saving_data + '/SAVE__{0}.csv'
    format_print = "%d/%m/%Y %H:%M:%S" # format d'affichage de la date
    FORMAT_DATE_CSV_FILE = "%d_%m_%Y_%H_%M_%S" # format de la date pour le nom du fichier csv
    MAX_NUMBER_OF_FILES = 10 # on ne garde que les 10 derniers fichiers de données AIS dans le dossier data_ship
    
    # Liste des colonnes à récupérer dans la base de données de contrôle des navires
    TO_INT_COLUMNS = ['MMSI', 'Numero du skipper/armateur']

    # Borne de temps de sleep entre chaque requête pour- ne pas surcharger les serveur
    minTIME_SLEEP = 0.2
    maxTIME_SLEEP = 0.3
    newTIME_SLEEP_MAX = 0.2 # le serveur pour le musée maritime de La Rochelle est plus tolérant

    # Template de la réquête API de marinetraffic pour récupérer les données AIS
    API_TEMPLATE = "https://www.marinetraffic.com/en/data/?asset_type=vessels&columns={1}&mmsi|eq|mmsi={0}"
    # Template de la page sur le musée maritime de La Rochelle pour check si le bateau est un bateau du YCC enregistré au musée
    PAGE_URL_TEMPLATE = "https://museemaritime.larochelle.fr/au-dela-de-la-visite/a-decouvrir-a-proximite/yatchs-classiques/{0}"
    # Template pour récupérer une image sur marine traffic
    TEMPLATE_IMG_URL_MT = "https://photos.marinetraffic.com/ais/showphoto.aspx?shipid={0}&size=thumb600"

    # URL par défaut pour l'image du bateau
    DEFAULT_BOAT_IMG_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e1/Sail_plan_schooner.svg/1200px-Sail_plan_schooner.svg.png"

    def __init__(self) -> None:
        self._db_updated = False # booléen qui indique si la base de données a été mise à jour. Par défaut elle n'est pas à jour
        
    def run(self,complete_init=False):
        """
        Fonction qui lance la mise à jour de la base de données de manière automatique
        """
        if self.load_last_save() and not complete_init: # si le chargement de la dernière sauvegarde a réussi
            self.updatetDB(complete_update=False) # on lance une mise à jour partielle qui ne met à jour que infos qui nous intéressent
        else: # si le chargement de la dernière sauvegarde a échoué
            self.updatetDB(complete_update=True)



    def updatetDB(self,complete_update=True,print_ggsheet_extraction=False):
        
        if complete_update :
            print("\n  --- COMPLETE UPDATE DATABASE ---   ")
            print("====================================")
            self.request_update_ggsheet()
            if print_ggsheet_extraction :
                print(" ----- GGSHEET EXTRACTION -----")
                print(self.__df)
            self.check_page_MMR(complete_check=True)
            self.request_update_API(complete_update=True)
            self.request_image_links()
            self._db_updated = True
            self.saveDB()
            print(" ► Base de données mise à jour ! ◄")
            print("====================================\n")

        else : # on lance une mise à jour partielle
            print("\n  --- PARTIAL UPDATE DATABASE ---   ")
            print("====================================")
            self._last_update_db = self._tracked_fleet_df
            self.request_update_ggsheet()
            if print_ggsheet_extraction :
                print("                                 ----- GGSHEET EXTRACTION -----")
                # on affiche les 10 dernières lignes du dataframe
                print(self.__df.tail(10))
                print("Affichage des 10 dernières lignes du dataframe")
                print(self.__df.info())
            self.check_page_MMR(complete_check=False)
            self.request_update_API(complete_update=False)
            self.request_image_links()
            self._db_updated = True
            self.saveDB()
            
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
            self.updatetDB(complete_update=True)
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
    
    def saveDB(self):
        date = datetime.now()
        # on récupère la liste des fichiers de données AIS dans le dossier data_ship
        list_files = self.get_list_of_saves()
        # si la longueur de la liste est supérieure ou égale à MAX_NUMBER_OF_FILES, on devra supprimer le plus vieux fichier
        if len(list_files) >= DataBase.MAX_NUMBER_OF_FILES:
            # on récupère le plus vieux fichier
            oldest_file = min(list_files)
            print("--> Le serveur ne peut pas stocker plus de {0} fichiers de données AIS,\nle fichier le plus ancien sera supprimé : {1}".format(
                DataBase.MAX_NUMBER_OF_FILES, 'SAVE_'+oldest_file.strftime(DataBase.FORMAT_DATE_CSV_FILE)+'.csv'))

        self._last_update = date.strftime(DataBase.FORMAT_DATE_CSV_FILE)
        self._tracked_fleet_df.to_csv (DataBase.path_saving_data.format(date.strftime(DataBase.FORMAT_DATE_CSV_FILE)))
            
    def filter_mmsi(self):
        """
        Ne récupère que les données des bateaux du YCC possédant un MMSI
        """
        self._tracked_fleet_df = self.__df[self.__df['MMSI'].notnull()].drop_duplicates(
            subset=['MMSI'], ignore_index=True)
        self._nb_mmsi = len(self.__df.MMSI.dropna().unique())
        self._nb_bateaux = len(self.__df['Nom du bateau'].unique())
        self._nb_bateaux_sans_mmsi = self._nb_bateaux - self._nb_mmsi

    def request_update_ggsheet(self):
        """
        Met à jour les données de la flotte du YCC à partir de la base de données de contrôle des navires
        """
        print(" --> Request update from Google Sheet")
        self.__df = pd.read_csv(DataBase.url_fleet)
        self.__df[DataBase.TO_INT_COLUMNS] = self.__df[DataBase.TO_INT_COLUMNS].astype('Int64')
        self.filter_mmsi()

    def request_update_API(self, complete_update=True,trace_on_log=False):
        """
        On recherche les données AIS pour chaque bateau de la flotte du YCC
        """

        LONG = []
        LAT = []
        SPEED = []
        LAST_POSITION = []
        COUNT_PHOTOS = []
        SHIP_ID = []
        CAP = []
        COUNTRY_CODE = []

        # on crée un objet AIS
        ais = AIS(print_query=False)
        print(" --> Request API for AIS data")
        # on recherche les données AIS pour chaque bateau de la flotte
        Conversion = {"time_of_latest_position": "LAST_POS",
                                "flag": "COUNTRY_CODE",
                                "imo": "SHIP_ID",
                                "lat_of_latest_position": "LAT",
                                "lon_of_latest_position": "LONG",
                                "speed": "SPEED",
                                "course": "CAP",
                                }
        
        Var_Conversion = {"time_of_latest_position": LAST_POSITION,
                                "flag": COUNTRY_CODE,
                                "imo": SHIP_ID,
                                "lat_of_latest_position": LAT,
                                "lon_of_latest_position": LONG,
                                "speed": SPEED,
                                "course": CAP,
                                }
        response_conversion = {"time_of_latest_position": "LAST_POS",
                                "flag": "CODE2",
                                "imo": "SHIP_ID",
                                "lat_of_latest_position": "LAT",
                                "lon_of_latest_position": "LON",
                                "speed": "SPEED",
                                "course": "COURSE",
                                }

        skipped = {}
        for key in Conversion.values(): 
            skipped[key] = 0

        always_updated_columns = ["time_of_latest_position",
                                "lat_of_latest_position",
                                "lon_of_latest_position",
                                "speed",
                                "course",
                                ]
        fixable_columns = ["flag",
                            "imo",
                            ]
        
        for index, row in tqdm(self._tracked_fleet_df.iterrows(), total=self._tracked_fleet_df.shape[0], desc='Recherche des données AIS pour les bateaux de la flotte...',leave=False):
            # on attend un temps aléatoire entre minTIME_SLEEP et maxTIME_SLEEP (float)
            time.sleep(random.uniform(
                DataBase.minTIME_SLEEP, DataBase.maxTIME_SLEEP))
            try: 
                wanted_colums = always_updated_columns.copy() + fixable_columns.copy()             
                # on fait un petit trie
                if not complete_update :
                    for column in fixable_columns:
                        data = self._last_update_db.loc[self._last_update_db['MMSI'] == row['MMSI']][Conversion[f"{column}"]].values[0]
                        if not pd.isna(data):
                            skipped[Conversion[f"{column}"]] +=1
                            wanted_colums.remove(column)
                            

                    
                substring = ""
                substring = substring.join(
                    [wanted_colums[i] + "," for i in range(len(wanted_colums))])
                str = DataBase.API_TEMPLATE.format(row['MMSI'], substring)
                reply = ais.get_data_by_url(str)
                

                if type(reply) == list:
                    response = reply[0]
                    for key in always_updated_columns + fixable_columns:
                        try:
                            if key not in wanted_colums:
                                Var_Conversion[key].append(self._last_update_db.loc[self._last_update_db['MMSI'] == row['MMSI']][Conversion[key]].values[0])
                            else : 
                                Var_Conversion[key].append(response[response_conversion[key]])
                        except Exception as e:
                            print(e)
                            Var_Conversion[key].append(None)


                else:
                    self._tracked_fleet_df = self._tracked_fleet_df.drop(
                        index=index)
                    print("→ {0} ({1}) : 'UNFOUND'\nVeuillez vérifier le numéro MMSI ou augmenter le temps de recherche !".format(
                        row['Nom du bateau'], row['MMSI']))
            except Exception as e:
                # on print l'erreur et son explication
                print("→ {0} ({1}) : 'UNFOUND → {2}'".format(
                    row['Nom du bateau'], row['MMSI'], e))
                self._tracked_fleet_df = self._tracked_fleet_df.drop(
                    index=index)

        for key in always_updated_columns + fixable_columns:
            self._tracked_fleet_df[Conversion[key]] = Var_Conversion[key]


        self._tracked_fleet_df['LONG'] = self._tracked_fleet_df['LONG'].astype(
            'float64')
        self._tracked_fleet_df['LAT'] = self._tracked_fleet_df['LAT'].astype(
            'float64')
        self._tracked_fleet_df['SPEED'] = self._tracked_fleet_df['SPEED'].astype(
            'float64')
        self._tracked_fleet_df['SHIP_ID'] = self._tracked_fleet_df['SHIP_ID'].astype(
            'int64')
        self._tracked_fleet_df['CAP'] = self._tracked_fleet_df['CAP'].astype(
            'float64')
        self._tracked_fleet_df['COUNTRY_CODE'] = self._tracked_fleet_df['COUNTRY_CODE'].astype(
            'str')
        
        if trace_on_log:
            print(self._tracked_fleet_df)

        if not complete_update:
            for key in skipped.keys():
                print(f"→ {skipped[key]} bateaux n'ont pas été mis à jour pour la colonne {key}")

    def check_page_MMR(self,complete_check=False):
        """
        Fonction qui pour chaque bateau de la flotte vérifie si une page sur le site du
        Musée Maritime de La Rochelle existe. Si oui, on ajoute l'URL de la page dans la
        colonne 'PAGE_LINK' du DataFrame.
        """
        # Pour chaque bateau, on check si il y a une page sur le site du musée maritime de La Rochelle
        PAGE_LINK = []
        NEW_TIME_SLEEP_MAX = DataBase.newTIME_SLEEP_MAX  # ce serveur est plus tolérant
        assert NEW_TIME_SLEEP_MAX < DataBase.maxTIME_SLEEP, f"NEW_TIME_SLEEP_MAX ({NEW_TIME_SLEEP_MAX}) doit être inférieur à DataBase.maxTIME_SLEEP ({DataBase.maxTIME_SLEEP})"

        print(" --> Checking 'https://museemaritime.larochelle.fr/' for pages")

        if complete_check : # on check pour tous les bateaux de la flotte
            for index, row in tqdm(self._tracked_fleet_df.iterrows(), total=self._tracked_fleet_df.shape[0], desc='Search for "MMR" pages...', leave=False):
                # on attend un temps aléatoire entre minTIME_SLEEP et maxTIME_SLEEP (float)
                time.sleep(random.uniform(
                    DataBase.minTIME_SLEEP, NEW_TIME_SLEEP_MAX))
                try:
                    # on met en minuscule et on remplace les espaces par des tirets
                    nom = row['Nom du bateau'].lower().replace(" ", "-")
                    str = DataBase.PAGE_URL_TEMPLATE.format(nom)
                    response = requests.get(str)
                    if response.status_code == 200:
                        PAGE_LINK.append(response.url)
                    else:
                        PAGE_LINK.append(np.nan)

                except Exception as e:
                    print("→ {0} ({1}) : 'ERREUR → {2}'".format(
                        row['Nom du bateau'], row['MMSI'], e))
                    PAGE_LINK.append(np.nan)
        
        else : # seulement pour les bateaux qui n'ont pas encore de page MMR
            skip_count = 0
            for index, row in tqdm(self._tracked_fleet_df.iterrows(), total=self._tracked_fleet_df.shape[0], desc='Search for "MMR" pages...', leave=False):
                # on check si le bateau n'a pas déjà une page MMR en passant par son MMSI 
                page = self._last_update_db.loc[self._last_update_db['MMSI'] == row['MMSI']]['PAGE_LINK'].values[0]
                if pd.isna(page):
                        # on attend un temps aléatoire entre minTIME_SLEEP et maxTIME_SLEEP (float)
                    time.sleep(random.uniform(
                        DataBase.minTIME_SLEEP, NEW_TIME_SLEEP_MAX))
                    try:
                        # on met en minuscule et on remplace les espaces par des tirets
                        nom = row['Nom du bateau'].lower().replace(" ", "-")
                        str = DataBase.PAGE_URL_TEMPLATE.format(nom)
                        response = requests.get(str)
                        if response.status_code == 200:
                            PAGE_LINK.append(response.url)
                        else:
                            PAGE_LINK.append(np.nan)

                    except Exception as e:
                        print("→ {0} ({1}) : 'ERREUR → {2}'".format(
                            row['Nom du bateau'], row['MMSI'], e))
                        PAGE_LINK.append(np.nan)
                else :
                    skip_count += 1
                    PAGE_LINK.append(page)
            print(f"        AVERTISSEMENT : {skip_count} bateaux ont une page sur le site du Musée Maritime de La Rochelle. Ces dernières ne seront pas mises à jour.")


        self._tracked_fleet_df['PAGE_LINK'] = PAGE_LINK

    def get_tracked_fleet_df(self):
        """
        Getter de l'attribut _tracked_fleet_df.
        """
        return self._tracked_fleet_df

    def request_image_links(self):
        """
        Fonction qui met à jour les liens des images des bateaux.
        """
        IMAGES_URL = []

        print(" --> Downlad images")
        for index, row in tqdm(self._tracked_fleet_df.iterrows(), total=self._tracked_fleet_df.shape[0], desc="Récupération des images des bateaux...", leave=False):
            try:
                IMAGES_URL.append(self.get_image_from_page_link(
                    row['PAGE_LINK'], row['SHIP_ID']))
            except Exception as e:
                print(
                    "→ Erreur lors de la récupération de l'image du bateau → {0}".format(e))
                IMAGES_URL.append(DataBase.DEFAULT_BOAT_IMG_URL)

        self._tracked_fleet_df['IMAGE_URL'] = IMAGES_URL

    def get_image_from_page_link(self, url, ship_id):
        """
        Fonction qui récupère l'image d'un bateau à partir de son lien sur le site du musée maritime de La Rochelle par scrapping
        """
        if pd.isna(url):
            try:
                response = requests.get(self.TEMPLATE_IMG_URL_MT.format(ship_id))
                if response.status_code == 200:
                    return response.url
                else :
                    raise Exception(f'Marine Traffic : {response.status_code}')

            except Exception as e:  # si on n'a pas d'image sur Marine Traffic ni sur le site du musée maritime de La Rochelle
                return DataBase.DEFAULT_BOAT_IMG_URL
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            image_url = soup.find(
                "figure", {"class": "image"}).find("img")['src']
            return image_url
        except Exception as e:
            print(
                "  → Erreur lors de la récupération de l'image du bateau → {0}".format(e))
            return DataBase.DEFAULT_BOAT_IMG_URL
 

class TrackerServer():
    """
    Classe qui  permet de tracker les bateaux d'une flotte,
    de générer un fichier les fichiers HTML correspondants
    et de les héberger sur un serveur.
    """
    LIEN_GITHUB = 'https://github.com/pierre-cau/YCC_fleet_tracker'
    URL_YCC = 'https://www.ycc-voile.fr/'
    DEFAULT_HTML_FILE_NAME = "index.html" # nom du fichier HTML par défaut
    LOGO_URL = "images/fleetytrack_logo_withoutbg.png" # URL du logo

    # PARAMETRES DE LA CARTE
    NAME = 'Flotte_YCC' # nom en haut dans l'onglet du navigateur
    ZOOM = 6 # zoom de la carte par défaut
    MAX_ZOOM = 25 # zoom max
    MIN_ZOOM = 3 # zoom min
    ZOOM_LEVEL = 15 # zoom level pour focus sur un bateau
    LOCATION=[46.227638, 2.213749] # position de la carte par défaut (France)

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
    dictionnary_country = { 'FR':'https://upload.wikimedia.org/wikipedia/commons/thumb/b/bc/Flag_of_France_%281794%E2%80%931815%2C_1830%E2%80%931974%2C_2020%E2%80%93present%29.svg/1280px-Flag_of_France_%281794%E2%80%931815%2C_1830%E2%80%931974%2C_2020%E2%80%93present%29.svg.png',
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

        print("\n >> Création de la carte")
        m = folium.Map(location=TrackerServer.LOCATION, zoom_start=ZOOM,max_zoom=MAX_ZOOM, min_zoom=MIN_ZOOM,control_scale=True,name=NAME)
        # on change le label du fond de carte
        folium.TileLayer('cartodbpositron',name="Positron").add_to(m, name='Positron')
        folium.TileLayer('cartodbdark_matter',name="Dark Matter").add_to(m, name='Dark Matter')

        
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
        <title> Flotte YCC</title>
        <link rel="icon" type="image/png" href="Tracker_fleet_YCC/images/fleetytrack_logo_withoutbg.png" />
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
                class=zoomable1 src="images/logo.png" alt="logo"
                style="width: 50%; 
                    height: auto; 
                    display: block; 
                    margin-left: auto; 
                    margin-right: auto; 
                    margin-top:5px;
                    border-radius: 50%;"/>
            <img src="images/yacht-club-classique.png" alt="YCC" style="width: 95%; height: auto; display: block; margin-left: auto; margin-right: auto; margin-top:5px; margin-bottom:10px">
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
                <img src="images/fleetytrack_logo_withoutbg.png" alt="logo" style="
                    width: auto;
                    float: left;
                    margin-left: 5px;
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
        

if __name__ == "__main__":

    db = DataBase()
    db.run(complete_init=True)
    tracker = TrackerServer()
    tracker.load_last_save()
    tracker.generate_html()
