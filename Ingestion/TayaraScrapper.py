from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from bs4 import BeautifulSoup
import time
from math import ceil
import Config
from Cleaning.ColumnStandardiser import ColumnsStandardiser
from Cleaning.BrandModelExtraction import ExtractionMarqueModele
import pandas as pd 
import os
from Cleaning.Cleaner import *
from Config import *
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker
from urllib.parse import urljoin
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


class TayaraPostScrapping(Base):
    __tablename__ = 'TayaraPostScrapping'
    id = Column(Integer, primary_key=True)
    Annee = Column(String)
    BoiteVitesse = Column(String)
    Kilometrage = Column(String)
    Energie = Column(String)
    PuissanceFiscale = Column(String)
    datedelannonce = Column(String)
    desc = Column(String)
    Prix = Column(String)
    description = Column(String)
    Couleur = Column(String)
    Carrosserie = Column(String)
    etatdevehicule = Column(String)
    Cylindree = Column(String)
    Marque = Column(String)
    Modele = Column(String)


class ScrappOccasionTayaraTn:

    def __init__(self):
        self.driver = Config.driverConfig
        self.baseUrl = Config.baseUrlTayara
        self.nativeUrl = Config.nativeUrlTayara
        self.pageInitiale = 1
        self.pageFinale = 2
        
    def parsing_page_source(self, url):
        try:
            self.driver.get(url)
            time.sleep(3)
        except WebDriverException:
            self.driver.refresh()
            time.sleep(4)
        return BeautifulSoup(self.driver.page_source,'html.parser') if BeautifulSoup(self.driver.page_source,'html.parser') else None
    
    def nbre_de_page(self, soup):
        div = soup.find('data', {'class': 'block mt-1 text-sm lg:text-base font-bold text-info'}).text.strip()
        nbreDAnnonce = int(div[1:-19])
        nbreDePage = ceil(nbreDAnnonce/70)
        return nbreDePage
    
    def extract_Immo_urls(self, pageUrl):
        soup = self.parsing_page_source(pageUrl)
        links = soup.find_all('a', {'target': '_blank'})
        liste = list(set([a.get('href') for a in links]))
        return [element for element in liste if '/item/' in element]
    
    def click_show_phone(self,driver, timeout=10):
        try:
            btn = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//button[@aria-label='Afficher numéro' or .//span[contains(text(),'Afficher le numéro')]]"
                ))
            )
            driver.execute_script("arguments[0].click();", btn)
            return True
        except TimeoutException:
            return False
    def extract_phone_after_click(self,driver, timeout=5):
        try:
            phone_el = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "a[href^='tel:']")
                )
            )
            return phone_el.text.strip()
        except TimeoutException:
            return None
    def extract_data(self, soup):
        data = {}
        try: 
            dateDeLannonce = soup.find('div', {'class': 'flex items-center space-x-2 mb-1'}).text.strip() if soup.find('div',{'class':'flex items-center space-x-2 mb-1'}) else None
            categorie = soup.select_one("div.flex.items-center span").text.strip()
            titre = soup.find('h1', {'class': 'text-gray-700 font-bold text-2xl font-arabic'}).text.strip() if soup.find('h1', {'class': 'text-gray-700 font-bold text-2xl font-arabic'}) else None
            if self.click_show_phone(self.driver):
                numeroTelephone = self.extract_phone_after_click(self.driver)
            
            mt4 = soup.find_all('div', {'class': 'mt-4'})
            if len(mt4) > 1:
                prix = mt4[1].find('data')['value']
            else:
                prix = None
            ul = soup.find("ul", class_="grid gap-3 grid-cols-12")
            for li in ul.find_all("li", recursive=False):
                spans = li.select("span.flex.flex-col.py-1 > span")
                if len(spans) >= 2:
                    label = spans[0].get_text(strip=True)
                    value = spans[1].get_text(strip=True)
                    data[label] = value
            h2 = soup.find("h2", string="Description")
            if h2:
                p = h2.find_next("p")

                description = "".join(
                    t for t in p.find("span").contents
                    if isinstance(t, str)
                ).strip()
            else:
                description = None
            # listCarac = soup.find_all('li', {'class': 'col-span-6 lg:col-span-3'})
            # for div in listCarac:
            #     spec_name = div.find('span',{'class':'text-gray-600/80 text-2xs md:text-xs lg:text-xs font-medium'}).text.strip() if div.find('span',{'class':'text-gray-600/80 text-2xs md:text-xs lg:text-xs font-medium'}) else None
            #     spec_value = div.find('span',{'class':'text-gray-700/80 text-xs md:text-sm lg:text-sm font-semibold'}).text.strip() if div.find('span',{'class':'text-gray-700/80 text-xs md:text-sm lg:text-sm font-semibold'}) else None
            #     data[spec_name] = spec_value
            data['date de l"annonce'] = dateDeLannonce
            data['desc'] = titre
            data['prix'] = prix
            data['description'] = description
            data['categorie']= categorie
            data['imamges_url']= self.extract_images(soup)
            data['NumeroTelephone'] = numeroTelephone
        except AttributeError as e:
            print(f"An error occurred while extracting data: {e}")
        return data
    
    def extract_images(self,soup):

        container = soup.select_one("div.grow.overflow-y-hidden")
        if not container:
            return []

        img_tags = container.find_all("img", src=True)

        image_urls = set()

        for img in img_tags:
            src = img["src"]

            # Skip blurred background images
            if "blur" in img.get("class", []):
                continue

            # Normalize URL
            full_url = urljoin(Config.nativeUrlTayara, src)
            image_urls.add(full_url)

        return list(image_urls)

    def scrape(self, PageInitiale, PageFinale):
        all_Data = {}
        listeDesImmobiliers = []
        for i in range(PageInitiale, PageFinale+1):
        # for i in range(1, 2):
            listeDesImmobiliers.extend(self.extract_Immo_urls(self.baseUrl+str(i)))
        try:
            for index, voiture in enumerate(listeDesImmobiliers, start=1):
                soup = self.parsing_page_source(self.nativeUrl + voiture)
                data = self.extract_data(soup)
                all_Data[f'dict{index}'] = data
        finally: 
            self.driver.quit()
        return all_Data
    
    def tayara_scrapper_runner(self):
        data = self.scrape(self.pageInitiale, self.pageFinale)
        standardize = ColumnsStandardiser()
        dataStandardized = standardize.column_standardize(data)
        Base.metadata.create_all(engine)
        # Créer une session
        Session = sessionmaker(bind=engine)
        session = Session()
        for key, item in dataStandardized.items():
            tayarapostscrapping = TayaraPostScrapping(
                Energie=item['Carburant'], Annee=item['Année'], Kilometrage=item['Kilométrage'],
                PuissanceFiscale=item['Puissance fiscale'], Carrosserie=item['Type de carrosserie'],
                BoiteVitesse=item['Boite'], datedelannonce=item['date de l"annonce'],Cylindree=item['Cylindrée'],
                desc=item['desc'], description=item['description'], Prix=item['prix'], Marque=item['Marque'],
                Modele=item['Modèle'],Couleur=item['Couleur du véhicule'],etatdevehicule=item['Etat du véhicule'])
            session.add(tayarapostscrapping)
        # Commit les transactions
        session.commit()
        # Fermer la session
        session.close()

    def tayara_columns_standardise(self, dataframe):
        dataframe = dataframe.drop(columns={"Cylindree", 'datedelannonce', "description", "etatdevehicule"})
        dataframe = dataframe.dropna(how='all')
        cln = cleaner()
        dataframe = cln.eliminate_unnamed_columns(dataframe)
        dataframe = self.tayara_missing_marque_modele(dataframe)
        return dataframe
    
    def tayara_missing_marque_modele(self, dataframe):
        extraction = ExtractionMarqueModele()
        dataframe['desc'] = dataframe['desc'].str.upper()
        dataframe.dropna(subset=["desc"], inplace=True)
        # dataframe.dropna(subset=["Modele", "desc", "Marque"], inplace=True)
        ## Si la valeur du colonne marque est null: extraire le marque depuis la description (colonne desc)
        maskMarque = dataframe['Marque'].isnull()
        dataframe.loc[maskMarque, 'Marque'] = dataframe.loc[maskMarque, 'desc'].apply(lambda x: extraction.extraire_marque(x))
        ## Si la valeur du colonne modele est null: extraire le modele depuis la description (colonne desc)
        dataframe = dataframe.dropna(subset=['Marque'])
        maskModele = dataframe['Modele'].isnull()
        dataframe.loc[maskModele, 'Modele'] = dataframe.loc[maskModele, ['desc', 'Marque']].apply(lambda row: extraction.extraire_modele(row['desc'], row['Marque']), axis=1)
        ## Si la valeur du colonne marque est Autres: extraire le marque depuis la description (colonne desc)
        maskMarque = dataframe['Marque'] == 'Autres'
        dataframe.loc[maskMarque, 'Marque'] = dataframe.loc[maskMarque, 'desc'].apply(lambda x: extraction.extraire_marque(x))
        ## Si la valeur du colonne modele est Autres: extraire le modele depuis la description (colonne desc)
        dataframe = dataframe.dropna(subset=['Marque'])
        maskModele = dataframe['Modele'] == 'Autres'
        dataframe.loc[maskModele, 'Modele'] = dataframe.loc[maskModele, ['desc', 'Marque']].apply(lambda row: extraction.extraire_modele(row['desc'], row['Marque']), axis=1)
        modelesList = ["CLIO", "GOLF", "POLO"]
        for modele in modelesList:
            maskModele = dataframe['Modele'].str.upper() == modele
            dataframe.loc[maskModele, 'Modele'] = dataframe.loc[maskModele, ['desc', 'Marque']].apply(
                lambda row: extraction.extraire_modele(row['desc'], row['Marque']), axis=1)
        dataframe = dataframe.drop(columns={"desc"})
        return dataframe
    
    def run_whole_process(self):
        self.tayara_scrapper_runner()
        tayaraDf = pd.read_sql('TayaraPostScrapping', con=engine)
        tayaraDataStandardised = self.tayara_columns_standardise(tayaraDf)
        tayaraDataStandardised.to_sql('DataStandardised', con=engine, if_exists='append', index=False)


##MAIN##
if __name__ == "__main__":
    test = ScrappOccasionTayaraTn()
    soup = test.parsing_page_source('https://www.tayara.tn/item/appartements/ariana/riadh-andalous/a-louer-s2-meubl-a-riadh-el-andalous/692dd57c265523b710ee1887/#item-caroussel-1')
    data = test.extract_data(soup)
    
    print('data: ',data)