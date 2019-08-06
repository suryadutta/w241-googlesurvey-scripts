import numpy as np
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
from random import randint
from tqdm import tqdm_notebook as tqdm

class SurveyGenerator():

    def __init__(self, email, password):

        self.email = email
        self.password = password

        options = webdriver.ChromeOptions()
        options.add_argument('--ignore-certificate-errors')
        options.add_argument("--test-type")
        self.driver = webdriver.Chrome("/Users/surya/Downloads/chromedriver", options=options)

        self.genders = ["women","men"]
            
        self.answers = [
            "$0",
            "$20",
            "$40",
            "$60",
            "$80",
            "$100"
        ]

        self.male_names = pd.read_csv("male-names.csv", header=None)[0].values[:8]
        self.female_names = pd.read_csv("female-names.csv", header=None)[0].values[:8]

        self.gendered_names = {name:"male" for name in male_names}
        self.gendered_names.update({name:"female" for name in female_names})

        self.names = list(gendered_names.keys())

        self.products = ["bottle of perfume","bottle of cologne", "necktie", "silk scarf"]

    def login_google(self):
        self.driver.get("https://accounts.google.com/signin/v2/identifier?flowName=GlifWebSignIn&flowEntry=ServiceLogin")
        self.driver.find_element_by_name('identifier').send_keys(self.email+Keys.ENTER)
        time.sleep(1)
        self.driver.find_element_by_name('password').send_keys(self.password+Keys.ENTER)
        time.sleep(1)

    def generate_survey_data(self):

        survey_data = pd.DataFrame()

        survey_groups = np.stack(np.meshgrid(self.names, self.products, self.genders), -1).reshape(-1, 3)

        for survey_group_info in survey_groups:
            
            survey_id = "S-" + str(randint(100000, 999999))
            survey_name = "Seller Gender " + survey_id
            
            seller_name = survey_group_info[0]
            
            product = survey_group_info[1]
            
            respondent_gender = survey_group_info[2]
            
            survey_data = survey_data.append({
                "survey_id": survey_id,
                "survey_name": survey_name,
                "seller_name": seller_name,
                "product": product,
                "respondent_gender": respondent_gender,
            }, ignore_index=True)
            
        survey_data.set_index("survey_id", inplace=True)

        return survey_data

    def generate_all_surveys(self):
        
        self.login_google()

        failure_counter = 0

        survey_data = self.generate_survey_data()
        survey_len = len(survey_data)

        pbar = tqdm(total=(survey_len))

        if index>0:
            pbar.update(index)

        while index < survey_len and failure_counter < 5:
            
            try:
                row = survey_data.iloc[index]
                
                create_survey(
                    row["survey_name"],
                    row["seller_name"],
                    row["product"],
                    row["respondent_gender"])
                
                index += 1
                pbar.update(1)
                failure_counter = 0
            
            except:
                print("Index",index,"failed. Retrying...")
                failure_counter += 1
                time.sleep(10)

        pbar.close()

    def create_survey(self, survey_name, seller_name, product, gender):

        self.driver.get("https://surveys.google.com/create")
        time.sleep(1)

        name = self.driver.find_element_by_name('survey_name')
        name.clear()
        name.send_keys(survey_name)
        
        question = self.generate_question(seller_name, product)
        self.driver.find_element_by_tag_name("textarea").send_keys(question)

        for i in range(len(answers)):
            self.driver.find_elements_by_tag_name("input")[i+1].send_keys(answers[i]+Keys.TAB)

        self.driver.find_element_by_xpath( "//*[contains(@class, 'menu-random-select')]").click()
        time.sleep(0.25)

        self.driver.find_elements_by_class_name("goog-menuitem-content")[-1].click()
        time.sleep(0.25)

        self.driver.find_element_by_xpath( "//*[contains(@class, 'raised-action-button')]").click()
        time.sleep(1)

        Gender = self.driver.find_elements_by_class_name("jfk-select")[5]
        Gender.click()
        time.sleep(0.25)

        for index, element in enumerate(self.driver.find_elements_by_class_name("jfk-checkbox-checked")[6:8]):
            if index != genders.index(gender):
                element.click()
                time.sleep(0.25)

        self.driver.find_element_by_xpath( "//*[contains(@class, 'raised-action-button')]").click()
        time.sleep(0.5)

        response_count = self.driver.find_element_by_name("target_response_count")
        response_count.clear()
        response_count.send_keys("24")
        time.sleep(0.5)
        
        self.driver.find_element_by_class_name("js-submit-button").click()
        time.sleep(4)
        
        popup = self.driver.find_element_by_class_name("modal-dialog")
        popup.click()
        popup.send_keys(Keys.TAB + Keys.TAB + Keys.TAB + Keys.ENTER)
        
        time.sleep(7)

    @staticmethod
    def generate_question(seller_name, product):
        return seller_name + " is selling a "+ product +". What is a fair price for this?"