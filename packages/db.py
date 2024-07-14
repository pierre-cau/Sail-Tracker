# IMPORT
import pandas as pd
import numpy as np
from aisexplorer.AIS import AIS
import urllib
from tqdm import tqdm
import requests
# on récupère beautifulsoup4 pour parser le html
from bs4 import BeautifulSoup
from datetime import datetime
import time
import random
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
    path_saving_data = "Tracker_fleet_YCC/DATA_SAVES/"
    format_path_saving_data = path_saving_data + '/SAVE__{0}.csv'
    format_print = "%d/%m/%Y %H:%M:%S" # format d'affichage de la date
    FORMAT_DATE_CSV_FILE = "%d_%m_%Y_%H_%M_%S" # format de la date pour le nom du fichier csv
    MAX_NUMBER_OF_FILES = 5 # on ne garde que les n derniers fichiers de données AIS dans le dossier data_ship
    
    # Liste des colonnes à récupérer dans la base de données de contrôle des navires
    TO_INT_COLUMNS = ['MMSI', 'Numero du skipper/armateur']

    # Borne de temps de sleep entre chaque requête pour- ne pas surcharger les serveurs
    minTIME_SLEEP = 0.2
    maxTIME_SLEEP = 0.4
    newTIME_SLEEP_MAX = 0.2 # le serveur pour le musée maritime de La Rochelle est plus tolérant

    num_retries = 8 # nombre de tentatives de requêtes avant de passer à la suivante pour l'API
    seconds_wait = 5 # nombre de secondes à attendre avant de relancer une requête pour l'API

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
        if not complete_init and self.load_last_save: # si le chargement de la dernière sauvegarde a réussi
            self.updatetDB(complete_update=False) # on lance une mise à jour partielle qui ne met à jour que infos qui nous intéressent
        else: # si le chargement de la dernière sauvegarde a échoué
            self.updatetDB(complete_update=True)

    def updatetDB(self,complete_update=True,print_ggsheet_extraction=False):
        
        if complete_update :
            print("\n  --- COMPLETE UPDATE DATABASE ---   ")
            print("====================================")
            self.request_update_ggsheet()
            # on fait une copie de la base de données pour pouvoir comparer les deux
            self._last_update_db = self._tracked_fleet_df.copy()
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
            self.load_last_save()
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
        self._last_update_db = pd.read_csv(DataBase.format_path_saving_data.format(date.strftime(DataBase.FORMAT_DATE_CSV_FILE)))
        if print_result:
            print("                                 ----- DATAFRAME -----")
            print(self._last_update_db.tail(10)) # on affiche les 10 dernières lignes du dataframe
            # on affiche les 10 dernières lignes du dataframe
            print("Affichage des 10 dernières lignes du dataframe")
            print(self._last_update_db.info())
        # on print le nombre de bateaux 
        print("\nNombre de bateaux présents sur la sauvegarde : ", len(self._last_update_db))
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
        print(" --> Save database...")
        date = datetime.now()
        # on récupère la liste des fichiers de données AIS dans le dossier data_ship
        list_files = self.get_list_of_saves()
        # si la longueur de la liste est supérieure ou égale à MAX_NUMBER_OF_FILES, on devra supprimer le plus vieux fichier
        if len(list_files) >= DataBase.MAX_NUMBER_OF_FILES:
            # on récupère le plus vieux fichier
            oldest_file = min(list_files)
            print("     → Le serveur ne peut pas stocker plus de {0} fichiers de données AIS.\      → Le fichier le plus ancien sera supprimé : {1}".format(
                DataBase.MAX_NUMBER_OF_FILES, 'SAVE__'+oldest_file.strftime(DataBase.FORMAT_DATE_CSV_FILE)+'.csv'))
            # on supprime le fichier le plus ancien
            os.remove(DataBase.format_path_saving_data.format(oldest_file.strftime(DataBase.FORMAT_DATE_CSV_FILE)))

        self._last_update = date.strftime(DataBase.FORMAT_DATE_CSV_FILE)
        # on test si on a accès au dossier data_ship
        if os.path.isdir(DataBase.path_saving_data):
            # on sauvegarde le dataframe dans un fichier csv 
            self._tracked_fleet_df.to_csv(DataBase.format_path_saving_data.format(date.strftime(DataBase.FORMAT_DATE_CSV_FILE)), index=False)


        else :
            print("Le dossier data_ship n'existe pas ou n'est pas accessible")
                   
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

    def request_update_API(self, complete_update=True,trace_on_log=True):
        """
        On recherche les données AIS pour chaque bateau de la flotte du YCC
        """
        self._tracked_fleet_df =pd.DataFrame(self._tracked_fleet_df)

        LONG = []
        LAT = []
        SPEED = []
        LAST_POSITION = []
        SHIP_ID = []
        CAP = []
        COUNTRY_CODE = []

        print(" --> Request API for AIS data")
        # on recherche les données AIS pour chaque bateau de la flotte
 
        always_updated_columns = ["time_of_latest_position",
                                "lat_of_latest_position",
                                "lon_of_latest_position",
                                "speed",
                                "course",
                                ]
        fixable_columns = ["flag",
                            "imo",
                            ]
        
        Conversion = {"flag":"COUNTRY_CODE",
                    "imo":"SHIP_ID",
                    "time_of_latest_position":"LAST_POSITION",
                    "lat_of_latest_position":"LAT",
                    "lon_of_latest_position":"LONG",
                    "speed":"SPEED",
                    "course":"CAP",
                    }
        
        response_conversion = {"flag":"CODE2",
                            "imo":"SHIP_ID",
                            "time_of_latest_position":"LAST_POS",
                            "lat_of_latest_position":"LAT",
                            "lon_of_latest_position":"LON",
                            "speed":"SPEED",
                            "course":"COURSE",
                            }
        
        skipped = {}
        for column in fixable_columns:
            skipped[column] = 0
        
        for column in fixable_columns+always_updated_columns:
            self._tracked_fleet_df[Conversion[f"{column}"]] = [np.nan for i in range(self._tracked_fleet_df.shape[0])]
        if complete_update:
            wanted_columns = always_updated_columns+fixable_columns
        
        for index, row in tqdm(self._tracked_fleet_df.iterrows(), total=self._tracked_fleet_df.shape[0], desc='Recherche des données AIS pour les bateaux de la flotte...',leave=False):
            # on attend un temps aléatoire entre minTIME_SLEEP et maxTIME_SLEEP (float)
            time.sleep(random.uniform(DataBase.minTIME_SLEEP, DataBase.maxTIME_SLEEP))
            try:
                # on récupère les données AIS du bateau
                if not(complete_update):
                    #print("not complete update")
                    wanted_columns = always_updated_columns
                    for index,column in enumerate(fixable_columns):
                            if not(pd.isna(self._last_update_db.loc[self._last_update_db['MMSI'] == row['MMSI']][Conversion[f"{column}"]].values[0])):
                                wanted_columns.append(column)
                            else : 
                                skipped[column] += 1

                #print(wanted_columns)
                ais = AIS(verbose=False,
                        return_df=False,
                        return_total_count=False,
                        seconds_wait=DataBase.seconds_wait,
                        num_retries = DataBase.num_retries,
                    )
                response = ais.get_location(row['MMSI'])
                print(response[0])
                

                for index, column in enumerate(wanted_columns):
                    #print(response[0][response_conversion[column]])
                    self._tracked_fleet_df.loc[self._last_update_db['MMSI'] == row['MMSI'],Conversion[f"{column}"]] = response[0][response_conversion[column]]
                    #print(f"→ {row['Nom du bateau']} ({row['MMSI']}) : {column} → {response[0][response_conversion[f'{column}']]}")
                for index,column in enumerate([column for column in fixable_columns if column not in wanted_columns]):
                    self._tracked_fleet_df.iloc[self._last_update_db['MMSI'] == row['MMSI'], Conversion[f"{column}"]] = self._last_update_db.loc[self._last_update_db['MMSI'] == row['MMSI'], Conversion[f"{column}"]]
                    #print(f"→ {row['Nom du bateau']} ({row['MMSI']}) : {column} → {self._last_update_db.loc[self._last_update_db['MMSI'] == row['MMSI'], Conversion[f'{column}']]}")
                
            except Exception as e:
                # on print l'erreur et son explication0
                print("→ {0} ({1}) : 'UNFOUND → {2}'".format(
                    row['Nom du bateau'], row['MMSI'], e))
                # on récupère l'index à supprimer
                index_to_drop = self._tracked_fleet_df[self._tracked_fleet_df['MMSI'] == row['MMSI']].index
                # on supprime la ligne
                self._tracked_fleet_df.drop(index_to_drop, inplace=True)

        
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

        if not(complete_update):
            for column in fixable_columns:
                print(f"    → {skipped[column]} bateaux n'ont pas été mis à jour pour la colonne {Conversion[f'{column}']}")

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
                page = self._last_update_db.loc[self._last_update_db['MMSI'] == row['MMSI']]['PAGE_LINK']
                if page.empty:
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
                    PAGE_LINK.append(page.values[0])
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


if __name__ == "__main__":
    db = DataBase()
    db.run(complete_init=True)
    