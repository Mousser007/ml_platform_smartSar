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
from sqlalchemy import Column, Integer, String,ForeignKey
from sqlalchemy.orm import sessionmaker
from urllib.parse import urljoin
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from sqlalchemy.orm import relationship

class TayaraPostScrapping(Base):
    __tablename__ = 'TayaraPostScrapping'
    id = Column(Integer, primary_key=True)
    date_annonce = Column(String)
    categorie = Column(String)
    titre = Column(String)
    numero_telephone = Column(String)
    prix = Column(String)
    description = Column(String)
    link = Column(String)
    type_de_transaction = Column(String)
    superficie = Column(String)
    salle_de_bain = Column(String)
    chambre = Column(String)
    images = relationship("TayaraPostImage", back_populates="property", cascade="all, delete-orphan")

class TayaraPostImage(Base):
    __tablename__ = 'TayaraPostImage'
    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey('TayaraPostScrapping.id', ondelete='CASCADE'))
    image_url = Column(String, nullable=False)

    # Relationship back to property
    property = relationship("TayaraPostScrapping", back_populates="images")

class ScrappOccasionTayaraTn:

    def __init__(self):
        self.driver = Config.driverConfig
        self.baseUrl = Config.baseUrlTayara
        self.nativeUrl = Config.nativeUrlTayara
        self.pageInitiale = 1
        self.pageFinale = 1
        
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
    
    def click_show_phone(self, driver, timeout=10):
        try:
            btn = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//button[.//span[contains(text(),'Afficher le numéro')]]"
                ))
            )

            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
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
    def get_date(self, soup):
        tag = soup.find('div', {'class': 'flex items-center space-x-2 mb-1'})
        return tag.text.strip() if tag else None

    def extract_category(self, driver, timeout=10):
        try:
            # Wait for the container div
            container = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "//div[contains(@class,'items-center') and contains(@class,'space-x-2')]//span"
                ))
            )

            category = container.text.strip()
            return category

        except TimeoutException:
            return None
        
    def extract_all_images(self, driver, timeout=10):
    
        try:
            # Wait until at least one image with mediaGateway appears
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "//img[contains(@src,'mediaGateway/resize-image')]"
                ))
            )

            # Small wait to ensure all images are rendered
            time.sleep(2)

            images = driver.find_elements(
                By.XPATH,
                "//img[contains(@src,'mediaGateway/resize-image')]"
            )

            image_links = list({
                img.get_attribute("src")
                for img in images
                if img.get_attribute("src")
            })

            return image_links

        except TimeoutException:
            return []
    def get_categorie(self, soup):
        tag = soup.select_one("div.flex.items-center span")
        return tag.text.strip() if tag else None

    def get_title(self, soup):
        tag = soup.find('h1', {'class': 'text-gray-700 font-bold text-2xl font-arabic'})
        return tag.text.strip() if tag else None

    def get_phone(self, driver):
        if self.click_show_phone(driver):
            return self.extract_phone_after_click(driver)
        return None

    def get_price(self, soup):
        mt4 = soup.find_all('div', {'class': 'mt-4'})
        if len(mt4) > 1:
            data_tag = mt4[1].find('data')
            if data_tag:
                return data_tag.get('value')  # fallback to text can be added if needed
        return None
    def get_specifications(self, soup):
        specs = {}
        ul = soup.find("ul", class_="grid gap-3 grid-cols-12")
        if ul:
            for li in ul.find_all("li", recursive=False):
                spans = li.select("span.flex.flex-col.py-1 > span")
                if len(spans) >= 2:
                    label = spans[0].get_text(strip=True)
                    value = spans[1].get_text(strip=True)
                    specs[label] = value
        return specs

    def get_description(self, soup):
        h2 = soup.find("h2", string="Description")
        if h2:
            p = h2.find_next("p")
            if p:
                span = p.find("span")
                if span:
                    return "".join(t for t in span.contents if isinstance(t, str)).strip()
        return None
    def extract_criteres(self, driver, timeout=10):
        criteres = {}

        try:
            section = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "//h2[normalize-space()='Critères']/parent::*"
                ))
            )

            items = section.find_elements(By.XPATH, ".//*[contains(@class,'flex')]")

            for item in items:
                texts = item.text.split("\n")
                if len(texts) == 2:
                    key = texts[0].strip()
                    value = texts[1].strip()
                    criteres[key] = value

            return criteres

        except:
            return {}

    def extract_data(self, soup,ImmobLink):
        data = {}
        try: 
            data['dateDeLannonce'] = self.get_date(soup)
            # data['categorie'] = self.get_categorie(soup)
            data['categorie'] = self.extract_category(self.driver,timeout=10)
            data['titre'] = self.get_title(soup)
            data['numeroTelephone'] = self.get_phone(self.driver)
            data['prix'] = self.get_price(soup)
            data.update(self.get_specifications(soup))
            data['description'] = self.get_description(soup)
            data['Link'] = ImmobLink
            criteres = self.extract_criteres(self.driver,timeout=10)
            for key,value in criteres.items(): 
                data[key]= value
            list = self.extract_all_images(self.driver,timeout=10)
            
        except AttributeError as e:
            print(f"An error occurred while extracting data: {e}")
        return data,list    
    
    
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
            print(listeDesImmobiliers)
            listeDesImmobiliers = ['/item/appartements/tunis/el-manar-2/manar-2-appartement-s2-a-louer/698c684b1a74f8e704a1138b/', '/item/bureaux-et-plateaux/tunis/lac-2/bureau-en-4-espaces-100m-lac-2-ifcl2187/698c66321a74f8e704a11219/']
        try:
            for index, immobilier in enumerate(listeDesImmobiliers, start=1):
                ImmobLink = self.nativeUrl + immobilier
                soup = self.parsing_page_source(ImmobLink)
                data,ImageList = self.extract_data(soup,ImmobLink)
                all_Data[f'dict{index}'] = data
        finally: 
            self.driver.quit()
        return all_Data,ImageList
    
    def tayara_scrapper_runner(self):
        data,ImageList = self.scrape(self.pageInitiale, self.pageFinale)
        standardize = ColumnsStandardiser()
        dataStandardized = standardize.column_standardize(data)
        Base.metadata.create_all(engine)
        # Créer une session
        Session = sessionmaker(bind=engine)
        session = Session()
        for idx, (key, item) in enumerate(dataStandardized.items()):
            tayarapostscrapping = TayaraPostScrapping(
                    date_annonce=item['dateDeLannonce'],
                    categorie=item['categorie'],
                    titre=item['titre'],
                    numero_telephone=item['numeroTelephone'],
                    prix=item['prix'],
                    description=item['description'],
                    link = item['Link'],
                    type_de_transaction = item['Type de transaction'],
                    superficie = item['Superficie'],
                    salle_de_bain = item['Salles de bains'],
                    chambre = item['Chambres'])
            if idx < len(ImageList):  # make sure there is a corresponding image list
                for img_link in ImageList:
                    tayarapostscrapping.images.append(TayaraPostImage(image_url=img_link))
            session.add(tayarapostscrapping)
        # Commit les transactions
        session.commit()
        # Fermer la session
        session.close()

    def tayara_columns_standardise(self, dataframe):
        # dataframe = dataframe.drop(columns={"Cylindree", 'datedelannonce', "description", "etatdevehicule"})
        dataframe = dataframe.dropna(how='all')
        cln = cleaner()
        dataframe = cln.eliminate_unnamed_columns(dataframe)
        # dataframe = self.tayara_missing_marque_modele(dataframe)
        return dataframe
       
    def run_whole_process(self):
        self.tayara_scrapper_runner()
        tayaraDf = pd.read_sql('TayaraPostScrapping', con=engine)
        tayaraDataStandardised = self.tayara_columns_standardise(tayaraDf)
        tayaraDataStandardised.to_sql('DataStandardised', con=engine, if_exists='append', index=False)


##MAIN##
if __name__ == "__main__":
    test = ScrappOccasionTayaraTn()
    test.run_whole_process()