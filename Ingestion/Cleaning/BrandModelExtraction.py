import pandas as pd
import re
import os

class ExtractionMarqueModele:

    def __init__(self) :
        script_directory = os.path.dirname(os.path.abspath(__file__))
        data_directory = os.path.abspath(os.path.join(script_directory, "..", "Data", "CarsDatabase", "modeles"))
        self.CarDB = pd.read_csv(data_directory + ".csv", delimiter=';')
        self.ListeDesMarques = self.CarDB['rappel_marque'].drop_duplicates().to_list()
      
    def extraire_marque(self, description):
          description = description.upper()
          description = description.replace("Š", "S")
          description = description.replace("É", "E")
          description = description.replace("Ë", "E")
          marquefinale = ['']
          for marque in self.ListeDesMarques:
              x= r'\b{}\b'.format(re.escape(marque))
              if re.search(x, description, re.IGNORECASE):
                  marquefinale.append(marque)
          if 'GOLF' in marquefinale:
              return 'VOLKSWAGEN'
          if 'POLO' in marquefinale:
              return 'VOLKSWAGEN'
          if 'CLIO' in marquefinale:
              return 'RENAULT'
          return marquefinale[-1]
      # for marque in marquefinale:
      #     if 'GOLF' in marquefinale and 'VOLKSWAGEN' in marquefinale:
      #         return 'VOLKSWAGEN'
      #     if 'POLO' in marquefinale and 'VOLKSWAGEN' in marquefinale:
      #         return 'VOLKSWAGEN'

      
    def extraire_modele(self, description, marque):
        marque = marque.upper()
        modeles = self.CarDB[self.CarDB['rappel_marque'] == marque]['modele'].dropna().tolist()
        modeleFinale = ['']
        description = description.replace("é", "e")
        description = description.replace("É", "E")
        description = description.replace("Ë", "E")
        for modele in modeles:
            x = r'\b{}\b'.format(re.escape(modele))
            if re.search(x, description, re.IGNORECASE):
                modeleFinale.append(modele)
        return modeleFinale[-1]
    
    def extraire_marque_modele(self, dataframe):
        dataframe['description'] = dataframe['description'].astype(str)
        dataframe['Marque'] = dataframe['description'].apply(lambda x: self.extraire_marque(x))
        dataframe['Modele'] = (dataframe.apply(
            lambda row: self.extraire_modele(row['description'], row['Marque']), axis=1))
        modelesList = ["CLIO", "GOLF", "POLO"]
        for modele in modelesList:
            maskModele = dataframe['Modele'].str.upper() == modele
            dataframe.loc[maskModele, 'Modele'] = dataframe.loc[maskModele, ['description', 'Marque']].apply(
                lambda row: self.extraire_modele(row['description'], row['Marque']), axis=1)
        return dataframe
    def extraire_marque_modele_neuf(self, dataframe):
        dataframe['description'] = dataframe['description'].astype(str)
        dataframe['description'] = dataframe['description'].str.upper()
        dataframe['Marque'] = dataframe['description'].apply(lambda x: self.extraire_marque(x))
        dataframe['Modele'] = dataframe.apply(lambda row: row['description'].replace(row['Marque'], ''), axis=1)
        return dataframe

if __name__ == "__main__":
    pass