import numpy as np
import pandas as pd
import os

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
from tqdm import tqdm_notebook as tqdm

class SurveyAnalyzer():

    def __init__(email, password, download_filepath):

        self.email = email
        self.password = password

        options = webdriver.ChromeOptions()
        prefs = {"download.default_directory" : os.path.join(os.getcwd(),"Data")}
        options.add_experimental_option("prefs",prefs)
        options.add_argument('--ignore-certificate-errors')
        options.add_argument("--test-type")
        self.driver = webdriver.Chrome("/Users/surya/Downloads/chromedriver", options=options)

        self.survey_ids = []

    def login_google(self):
        self.driver.get("https://accounts.google.com/signin/v2/identifier?flowName=GlifWebSignIn&flowEntry=ServiceLogin")
        self.driver.find_element_by_name('identifier').send_keys(self.email+Keys.ENTER)
        time.sleep(1)
        self.driver.find_element_by_name('password').send_keys(self.password+Keys.ENTER)
        time.sleep(1)

    def download_surveys(self):

        self.login_google()
        self.driver.get("https://surveys.google.com/your-surveys?category=in-progress")
        time.sleep(5)

        while(True):    
            
            for a in self.driver.find_elements_by_xpath('.//a'):
                if "Seller Gender S-" in a.text:
                    url = a.get_attribute('href')
                    if url and url[:51] == 'https://surveys.google.com/reporting/survey?survey=':
                        self.survey_ids.append(url[51:])

            next_button = self.driver.find_element_by_xpath( "//*[contains(@class, 'next-page-icon-button')]")

            if not 'disabled' in next_button.get_attribute('class'):
                next_button.click()
                time.sleep(3)
                
            else:
                break

        for survey_id in tqdm(self.survey_ids):
            filename = 'https://surveys.google.com/reporting/export?format=xls&locale=en&survey='+survey_id
            self.driver.get(filename)

    def analyze_surveys(self, output_filename="results.csv"):

        male_names = pd.read_csv("male-names.csv", header=None)[0].values
        female_names = pd.read_csv("female-names.csv", header=None)[0].values

        gendered_names = {name:"male" for name in male_names}
        gendered_names.update({name:"female" for name in female_names})

        survey_results = pd.DataFrame()

        for file in os.listdir("Data"):
            
            if file[-4:] == 'xlsx':
                
                try:
                
                    data = pd.read_excel(prefix+'/'+file, 'Complete responses')

                    data["filename"] = file

                    answers = list(pd.read_excel(prefix+'/'+file, 'Topline')["Answer"].values)
                    data["answer_index"] = data["Question #1 Answer"].apply(lambda x: answers.index(x))

                    question = pd.read_excel(prefix+'/'+file, 'Overview').iloc[0]["Question text"]

                    product_start = question.find("selling a ") + 10
                    product_end = question.find(". What")
                    data["product"] = question[product_start:product_end]

                    name_end = question.find(" is selling")
                    data["seller_name"] = question[:name_end]

                    data["seller_gender"] = gendered_names[question[:name_end]]

                    survey_results = survey_results.append(data)
                    
                except:
                    print(file)

        survey_results.to_csv(output_filename)