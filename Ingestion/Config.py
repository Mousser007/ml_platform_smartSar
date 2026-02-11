import os
from selenium import webdriver
import psycopg2
from configparser import ConfigParser
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base


def config(filename="database.ini", section="postgresql"):
    from configparser import ConfigParser
    import os

    # Make filename absolute relative to this file
    filename = os.path.join(os.path.dirname(__file__), filename)

    parser = ConfigParser()
    parser.read(filename)

    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception(
            f'Section {section} is not found in the {filename} file.'
        )
    return db


# Lire les paramètres de configuration
params = config()
# Construire l'URL de connexion PostgreSQL
DATABASE_URL = f"postgresql+psycopg2://{params['user']}:{params['password']}@{params['host']}/{params['database']}"
# Créer un moteur de base de données
engine = create_engine(DATABASE_URL)
Base = declarative_base()


def connect():
    connection = None
    try:
        params = config()
        print('Connecting to the postgreSQL database ...')
        connection = psycopg2.connect(**params)

        # create a cursor
        crsr = connection.cursor()
        print('PostgreSQL database version: ')
        crsr.execute('SELECT version()')
        db_version = crsr.fetchone()
        print(db_version)
        crsr.close()
    except(Exception, psycopg2.DatabaseError) as error:
        print(error)
    # finally:
    #     if connection is not None:
    #         connection.close()
    #         print('Database connection terminated.')
##Affare Config
##Tayara Config
baseUrlTayara = "https://www.tayara.tn/listing/c/immobilier/?page="
nativeUrlTayara = "https://www.tayara.tn"
##Path Config
path_to_DataPostColumnsStandardisedNeuf = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Data', 'DataPostColumnsStandardised', 'Neuf')
path_to_DataPostColumnsStandardisedOccasion = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Data', 'DataPostColumnsStandardised', 'Occasion')
path_to_NewCarsReady = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Data', 'DataNewCarsReady')
path_to_CarsDatabase = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Data', 'CarsDatabase')
path_to_DataPostCleaning = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Data', 'DataPostCleaning')
path_to_DataPostMl = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Data', 'DataPostMl')
path_to_DataPostScraping = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Data', 'DataPostScraping')
path_to_DataPourSimulateur = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Data', 'DataPourSimulateur')
path_to_RequirementsFiles = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ML', 'RequirementsFiles')
##Web driver Config
options = webdriver.ChromeOptions()
# options.add_argument('--headless')  # Run in headless mode
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument("--disable-javascript")
options.add_argument('--window-size=1920x1080')
options.add_argument(
"user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
driverConfig = webdriver.Chrome(options=options)

if __name__ == "__main__":
    pass
