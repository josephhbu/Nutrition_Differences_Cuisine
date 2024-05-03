import streamlit as st
import pandas as pd
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import seaborn as sns
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

# Tasty API Call
def tasty_api_call():
    url = "https://tasty.p.rapidapi.com/recipes/list"
    headers = {
        "X-RapidAPI-Key": "dd58e28f74mshf97412c4025af7dp11d682jsn25eeb7f04c48",
        "X-RapidAPI-Host": "tasty.p.rapidapi.com"
    }

    all_recipes = []

    # Set the maximum number of recipes to fetch to handle pagination
    max_recipes = 280
    recipes_per_request = 100

    # Make requests until the maximum number of recipes is reached
    offset = 0
    while len(all_recipes) < max_recipes:
        querystring = {"from": str(offset), "size": str(recipes_per_request)}
        response = requests.get(url, headers=headers, params=querystring)
        
        if response.status_code == 200:
            recipes_data = response.json()
            recipes = recipes_data.get('results', [])
            
            # If no more recipes are returned, break the loop
            if len(recipes) == 0:
                break
            
            # Add fetched recipes to the list
            all_recipes.extend(recipes)
            
            # Increment the offset for the next request
            offset += recipes_per_request
        else:
            print("Failed to retrieve recipes. Status code:", response.status_code)
            break

    # Storing recipes in a list of dictionaries
    recipes_list = []
    for recipe in all_recipes:
        ingredients_list = []
        for section in recipe.get('sections', []):
            for component in section.get('components', []):
                ingredient = component.get('ingredient', [])
                if ingredient.get('name'):
                    ingredients_list.append(ingredient.get('name'))
        
        # Extracting cuisine type from tags
        cuisine = 'Uncategorized Cuisine'
        for tag in recipe.get('tags', []):
            if tag.get('root_tag_type') == 'cuisine':
                cuisine = tag.get('display_name')
                break

        if recipe.get('nutrition'):
            nutrition = recipe.get('nutrition', {})
        
        recipe_dict = {
            'Name': recipe.get('name', 'Name not available'),
            'Ingredients': ingredients_list,
            'Calories': nutrition.get('calories', 0),
            'Protein (g)': nutrition.get('protein', 0),
            'Carbs (g)': nutrition.get('carbohydrates', 0),
            'Fat (g)': nutrition.get('fat', 0),
            'Sugar (g)': nutrition.get('sugar', 0),
            'Fiber (g)': nutrition.get('fiber', 0),
            'Cuisine': cuisine
        }
        recipes_list.append(recipe_dict)

    recipes_df = pd.DataFrame(recipes_list)

    return recipes_df


# RecipeDB Web Scraper
def recipeDB_web_scraper():
    base_url = "https://cosylab.iiitd.edu.in"

    # List of cuisines you want to search for
    cuisines = ['Chinese','Italian', 'US', 'French', 'Indian', 'Mexican', 'Japanese', 'Thai', 'Russian']

    driver = webdriver.Chrome()

    recipe_list = list()
    for cuisine in cuisines:
        # Construct the search URL for the cuisine
        search_url = base_url + f"/recipedb/search_region/{cuisine}"
        
        driver.get(search_url)
        time.sleep(3)

        # Only grab specific number of pages, since it takes too long to grab every single page
        page_limit = 2
        for i in range(page_limit):
            soup = BeautifulSoup(driver.page_source, "html.parser")

            # Find all recipe links
            recipe_links = soup.find_all('tr')
            for recipe in recipe_links:
                rec = recipe.find('td')
                if rec:
                    recipe_link = rec.a.get('href')
                    recipe_name = rec.a.string.strip()
                    nutrition = recipe.find_all('td', class_="roundOff")
                    calories = nutrition[0].text
                    protein = nutrition[1].text
                    fat = nutrition[2].text
                    recipe_dict = {
                        'Cuisine': cuisine,
                        'Name': recipe_name,
                        'Calories (KCal)': calories,
                        'Protein (g)': protein,
                        'Fat (g)': fat,
                        'Link': base_url + recipe_link
                    }
                    recipe_list.append(recipe_dict)

            # Click next button to load more recipes
            next_button = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "nextpage")))
            next_button.click()

    driver.quit()
    recipe_df = pd.DataFrame(recipe_list)
    return recipe_df


# Loading in Food Nutrition Dataset
def load_food_nutrition_data():
    df = pd.read_csv('food.csv')
    # Clean up column names and dropping unnecessary columns
    for col in df.columns:
        new_col = col.replace('Data.', '')
        df.rename(columns={col: new_col}, inplace=True)
    df.drop([
        'Alpha Carotene',
        'Beta Carotene',
        'Beta Cryptoxanthin',
        'Ash',
        'Choline',
        'Lutein and Zeaxanthin',
        'Lycopene',
        'Manganese',
        'Niacin', 
        'Pantothenic Acid',
        'Refuse Percentage',
        'Retinol', 
        'Riboflavin',
        'Selenium',
        'Thiamin',
        'Vitamins.Vitamin A - IU',
        'Household Weights.1st Household Weight Description',
        'Household Weights.2nd Household Weight',
        'Household Weights.2nd Household Weight Description',
        'Major Minerals.Copper',
        'Major Minerals.Phosphorus',
        'Vitamins.Vitamin K'
        ], axis=1, inplace=True)
    return df

# Save pandas to csv
def save_df_to_csv(df):
    df.to_csv('data.csv', index=False)

# Load csv back into a pandas dataframe
def load_to_csv():
    loaded_df = pd.read_csv('data.csv')
    return loaded_df

# Filtering a dataframe by the cuisine type
def filter_dataframe_by_cuisine(dataframe, selected_cuisines):
        if selected_cuisines:
            filtered_df = dataframe[dataframe['Cuisine'].isin(selected_cuisines)]
        else:
            filtered_df = dataframe
        return filtered_df



### Streamlit Code ###

#Intro page
def intro():
    st.title('Comparing Nutritional Differences between Recipes across Cuisines')
    st.subheader('Joseph Bu')
    st.markdown(
        """
            Welcome to my project exploring nutritional differences in recipes across different cuisines! 

            This is a Web Application that showcases the differences in nutritional values, such as Calories, Carbs, Protein, Fats,
            in different recipes and compares the average of each Cuisine.
            
            # Interactivity: #
            To navigate between pages, please use the left dropdown.
            
            There are two main pages, the Tasty Dataset and the RecipeDB Dataset. 
            In each page, you can view the aggregated data containing recipes and nutrition info. You can also filter
            by an individual cuisine to get only recipes from those cuisines.

            There are also four plots for each dataset, **Bar Plot**, **Box Plot**, **Violin Plot**, and **Pair Plot**. 
            
            Each of these plots look at the average of all the recipes in the cuisine and compare each nutritional value between the different cuisines.
            You are able to filter which plots to look at as well as filter again by cuisine to compare and contrast the plots of specific cuisines.

            # Conclusions and Shortcomings #
            It was hard to discern a consistent tangible difference across cuisines. The Tasty API was very unorganized and doesn't contain enough recipes of each cuisine and matching recipe
            to cuisine was difficult. 
            The RecipeDB dataset is more robust and consistent, but is also very large and hard to gather data from. If we try and access too much data it is extremely slow, since we are using
            Selenium to dynamically webscrape the page. 
            
            However since there are an even number of recipes between each cuisine, the statistics are consistent and are more meaningful in discerning nutritional differences across cuisines.
        """ 
    )

#RecipeDB page
def recipeDB_analysis():
    df = pd.read_csv('Nutritional_Diff_Cuisines/recipeDB.csv')

    def plot_nutritional_comparison_recipeDB(dataframe, selected_plots, selected_cuisines):
        filtered_df = filter_dataframe_by_cuisine(dataframe, selected_cuisines)
        # Selecting relevant columns for the comparison
        nutritional_columns = ['Calories (KCal)', 'Protein (g)', 'Fat (g)']

        # Plotting selected nutritional comparisons
        for plot_type in selected_plots:
            if plot_type == 'Box Plot':
                for col in nutritional_columns:
                    plt.figure(figsize=(10, 6))
                    sns.boxplot(x='Cuisine', y=col, data=filtered_df)
                    plt.title(f'Box Plot: {col} by Cuisine')
                    plt.xlabel('Cuisine')
                    plt.ylabel(col)
                    plt.xticks(rotation=45)
                    st.pyplot(plt)
            elif plot_type == 'Violin Plot':
                for col in nutritional_columns:
                    plt.figure(figsize=(10, 6))
                    sns.violinplot(x='Cuisine', y=col, data=filtered_df)
                    plt.title(f'Violin Plot: {col} by Cuisine')
                    plt.xlabel('Cuisine')
                    plt.ylabel(col)
                    plt.xticks(rotation=45)
                    st.pyplot(plt)
            elif plot_type == 'Pair Plot':
                plt.figure(figsize=(10, 6))
                sns.pairplot(filtered_df, hue='Cuisine', vars=nutritional_columns)
                plt.title('Pair Plot: Nutritional Values')
                st.pyplot(plt)
            elif plot_type == 'Bar Plot':
                filtered_df_numeric = filtered_df.dropna(subset=nutritional_columns)
                filtered_df_numeric[nutritional_columns] = filtered_df_numeric[nutritional_columns].apply(pd.to_numeric, errors='coerce')

                # Grouping the data by cuisine and calculating the mean nutritional values
                grouped_data = filtered_df_numeric.groupby('Cuisine')[nutritional_columns].mean()
                for col in nutritional_columns:
                    plt.figure(figsize=(10, 6))
                    sns.barplot(x=grouped_data.index, y=col, data=grouped_data)
                    plt.title(f'Bar Plot: Mean {col} by Cuisine')
                    plt.xlabel('Cuisine')
                    plt.ylabel(f'Mean {col}')
                    plt.xticks(rotation=45)
                    st.pyplot(plt)

    all_cuisines = df['Cuisine'].unique()
    selected_cuisines = st.sidebar.multiselect('Select Cuisines', all_cuisines)

    # Filtered DataFrame based on selected cuisines
    filtered_df = filter_dataframe_by_cuisine(df, selected_cuisines)
    st.write(filtered_df)  

    selected_plots = st.sidebar.multiselect('Select Plot Types', ['Box Plot', 'Violin Plot', 'Pair Plot', 'Bar Plot'], ['Bar Plot'])

    # Plotting nutritional comparison based on selected plot types and cuisines
    if selected_plots:
        plot_nutritional_comparison_recipeDB(df, selected_plots, selected_cuisines)

# Tasty page
def tasty_analysis():
    df = pd.read_csv('Nutritional_Diff_Cuisines/tasty.csv')

    def plot_nutritional_comparison(dataframe, selected_plots, selected_cuisines):
        filtered_df = filter_dataframe_by_cuisine(dataframe, selected_cuisines)
        
        nutritional_columns = ['Calories', 'Protein (g)', 'Carbs (g)', 'Fat (g)', 'Sugar (g)', 'Fiber (g)']

        # Plotting selected nutritional comparisons
        for plot_type in selected_plots:
            if plot_type == 'Box Plot':
                for col in nutritional_columns:
                    plt.figure(figsize=(10, 6))
                    sns.boxplot(x='Cuisine', y=col, data=filtered_df)
                    plt.title(f'Box Plot: {col} by Cuisine')
                    plt.xlabel('Cuisine')
                    plt.ylabel(col)
                    plt.xticks(rotation=45)
                    st.pyplot(plt)
            elif plot_type == 'Violin Plot':
                for col in nutritional_columns:
                    plt.figure(figsize=(10, 6))
                    sns.violinplot(x='Cuisine', y=col, data=filtered_df)
                    plt.title(f'Violin Plot: {col} by Cuisine')
                    plt.xlabel('Cuisine')
                    plt.ylabel(col)
                    plt.xticks(rotation=45)
                    st.pyplot(plt)
            elif plot_type == 'Pair Plot':
                plt.figure(figsize=(10, 6))
                sns.pairplot(filtered_df, hue='Cuisine', vars=nutritional_columns)
                plt.title('Pair Plot: Nutritional Values')
                st.pyplot(plt)
            elif plot_type == 'Bar Plot':
                # Grouping the data by cuisine and calculating the mean nutritional values
                grouped_data = filtered_df.groupby('Cuisine')[nutritional_columns].mean()
                for col in nutritional_columns:
                    plt.figure(figsize=(10, 6))
                    sns.barplot(x=grouped_data.index, y=col, data=grouped_data)
                    plt.title(f'Bar Plot: Mean {col} by Cuisine')
                    plt.xlabel('Cuisine')
                    plt.ylabel(f'Mean {col}')
                    plt.xticks(rotation=45)
                    st.pyplot(plt)


    all_cuisines = df['Cuisine'].unique()
    selected_cuisines = st.sidebar.multiselect('Select Cuisines', all_cuisines)

    filtered_df = filter_dataframe_by_cuisine(df, selected_cuisines)
    st.write(filtered_df)  # Display the filtered DataFrame

    selected_plots = st.sidebar.multiselect('Select Plot Types', ['Box Plot', 'Violin Plot', 'Pair Plot', 'Bar Plot'], ['Bar Plot'])

    # Plotting nutritional comparison based on selected plot types and cuisines
    if selected_plots:
        plot_nutritional_comparison(df, selected_plots, selected_cuisines)


# Dataset Description page
def dataset_descr():
    st.title('Dataset Descriptions')
    st.markdown(
        """
            ## Data Source 1: Tasty API
            https://rapidapi.com/apidojo/api/tasty/

            This data source is an API for Tasty, a recipe blog platform that contains hundreds of recipes. This API can query for data regarding all the recipes in Tasty
            as well as the ingredients for each recipe and every single element for each recipe on the Tasty.co website.

            ## Data Source 2: RecipeDB
            https://cosylab.iiitd.edu.in/recipedb/

            This data source is a website called RecipeDB, which is a structured compilation of recipes, ingredients, and nutrition profiles interlinked with flavor profiles 
            and health associations. The database comprises of integration of over 118,000 recipes from different recipe websites all over the internet.

            ## Data Source 3: Food Nutrition Dataset
            https://www.kaggle.com/datasets/shrutisaxena/food-nutrition-dataset/data

            This food nutrition dataset comes from Kaggle but is sourced from the US Department of Agriculture and provides datasets that provide information on food and nutrient 
            profiles on a wide array of food products. The original USDA dataset was a little complicated and this Kaggle dataset merged the separate csvs into one csv.



        """
    )

# Final Questions page
def project_questions():
    st.title('Final Reflections')
    st.markdown(
        """
            1. What did you set out to study?  (i.e. what was the point of your project?  This should be close to your Milestone 1 assignment, but if you switched gears or changed things, note it here.)
                - I set out to study the differences between the nutritional profiles of recipes across different cuisines. I wanted to see if there were any significant variations in nutrient composition, 
                such as calories, protein, fat, etc. based on the main factor of different cuisine types and regions. There were a couple changes from my Milestone 1. First being that I found a cleaned
                USDA nutrition dataset off Kaggle, as the actual USDA dataset was a bit vague and had to be mapped. The biggest change however was finding RecipeDB a dynamic website database to web scrape
                different recipes across different cuisines.

            2. What did you Discover/what were your conclusions (i.e. what were your findings?  Were your original assumptions confirmed, etc.?)
                - Given that there are so many different recipes in each cuisine, I was only able to work with a smaller sample size of recipe datasets from different databases.  It was hard to draw any 
                specific conclusions. However my original assumptions were that American food is unhealthier on average than other cuisines, especially Asian cuisines which tend to be more balanced. 
                Italian and French recipes that I found were also less healthy than the Asian cuisines however my small sample size of recipes could have affected my analysis. 

            3. What difficulties did you have in completing the project?
                - There were many difficulties that I encountered. I struggled to find reliable and clean datasets for recipes that also indicated cuisine type. I really struggled to find a web-scrapable
                dataset, however once I did find one, I had to learn Selenium in order to scrape the site as it was a dynamic website, which was something I had to teach myself. After that, I had difficulties
                when trying to relate my datasets with my Nutrition dataset, as my Nutrition dataset was extremely large and messy. Learning how to create meaningful data visualizations 
                was also difficult since we did not really cover it in the class.

            4. What skills did you wish you had while you were doing the project?
                - I wish I had the skills to better be able to handle and process messy and large data so I could better fit the data to my needs. I also wished I was more knowledgable, in
                knowing and creating data visualizations that were meaningul to my research question. I had to spend so much time learning how to clean the data to the best of my ability as 
                well as gathering the data using Selenium, I would have been able to accomplish more if I was better prepared in those skills.

            5. What would you do “next” to expand or augment the project?
                - I would like to create more insightful connections between a multiple recipes' nutritional value and be able to better map to a cuisine and get some more descriptive
                and meaningful statistics for each cuisine. It would also be interesting to create a machine learning model that could take the features of a recipe, such as and be able to 
                predict the cuisine of that specific recipe. I think narrowing down my question could help me find better analyses.

        """
    )


page_names_to_funcs = {
    "Intro": intro,
    "Tasty Dataset": tasty_analysis,
    "RecipeDB Dataset": recipeDB_analysis,
    "Dataset Descriptions": dataset_descr,
    "Final Reflections": project_questions
}

demo_name = st.sidebar.selectbox("Choose a page", page_names_to_funcs.keys())
page_names_to_funcs[demo_name]()

