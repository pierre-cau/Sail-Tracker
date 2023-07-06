from tracker_tools import DataBase, TrackerServer

if __name__ == '__main__':
    db = DataBase()
    db.run(complete_init=False)
    server = TrackerServer()
