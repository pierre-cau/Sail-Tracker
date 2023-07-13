from tracker_tools import DataBase, TrackerServer
import time 
if __name__ == '__main__':
    DELAY_HOURS = 0 # unité: heures
    DELAY_MINUTES = 2 # unité: minutes
    DELAY_SECONDS = 0 # unité: secondes

    DELAY = DELAY_HOURS*3600 + DELAY_MINUTES*60 + DELAY_SECONDS
    
    print("__________________________STARTING TRACKER SERVER__________________________\n\n")
    db = DataBase()
    site = TrackerServer()
    site.config_git()

    # on initialise la base de données avec un initialisation complète
    db.run(complete_init=True)
    site.load_last_save()
    site.generate_html()
    site.publish_site()
    print("\n\n__________________________TRACKER SERVER INITIALIZED__________________________\n\n")
    




### VERSION AVEC BOUCLE INFINIE
"""
    # on lance le serveur
    while True:
        # on attend DELAY secondes avant de recommencer en affichant le temps restant
        for i in range(DELAY):
            # on affiche le temps restant en format hh:mm:ss
            print("Time remaining before next update: {:02d}:{:02d}:{:02d}".format((DELAY-i)//3600, ((DELAY-i)%3600)//60, (DELAY-i)%60), end="\r")
            time.sleep(1)
        print("Time remaining before next update: 00:00:00", end="\r")

        # on relance le serveur
        print("\n\n__________________________UPDATING TRACKER SERVER__________________________\n\n")
        db.run(complete_init=False)
        site.load_last_save()
        site.generate_html()
        site.publish_site()
        print("\n\n__________________________TRACKER SERVER UPDATED__________________________\n\n")

"""      
        




    


