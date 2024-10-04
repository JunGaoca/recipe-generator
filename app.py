import pandas as pd
import chromadb
import streamlit as st
from tqdm import tqdm

# Load CSV data into a DataFrame with error handling
@st.cache_data
def load_recipes_from_csv(file_path):
    try: 
        df = pd.read_csv(file_path, usecols=['Title', 'Ingredients', 'Instructions'])
        print("CSV file loaded successfully")
        print(df.head)
        return df
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
    except pd.errors.EmptyDataError:
        print(f"Error: The file '{file_path}' is empty.")
    except pd.errors.ParserError:
        print(f"Error: There was an issue parsing the CSV file.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

# Initialize ChromaDB and store recipe embeddings
@st.cache_resource
def initialize_chromadb_and_store_recipes(data_frame):
    if data_frame is None or data_frame.empty:
        print("DataFrame is empty or invalid. Exiting.")
        return None

    try: 
        # Initialize ChromaDB
        client = chromadb.PersistentClient('vectorstore')

        # Create a collection for the recipes
        collection = client.get_or_create_collection('recipes')
    

        # Add rows from the dataset to the ChromaDB collection
        for idx, row in tqdm(data_frame.iterrows(), total=len(data_frame)):
            ingredients = row['Ingredients']
            title = row['Title']
            instructions = row['Instructions']
            
            # Check for valid data
            if pd.notna(ingredients) and pd.notna(title) and pd.notna(instructions):
                collection.add(
                    documents=[ingredients],
                    metadatas=[{'title': title, 'recipe': instructions}],
                    ids=[str(idx)]
                )
            else:
                print(f"Row{idx} contains invalid data")

        print("Dataset successfully converted to ChromaDB collection!")
        return collection
    except Exception as e:
        st.error(f"An error occurred while connecting to ChromaDB: {str(e)}")
        return None

# Generate recipe based on ingredients input
def generate_recipe(ingredients, collection):
    # Query ChromaDB for the closest matching recipe
    results = collection.query(query_texts=ingredients, n_results=2)
    
    # Extract the recipe from the metadata
    if results['metadatas'] and results['metadatas'][0]:
        best_recipe_metadata = results['metadatas'][0][0]  # Get the first match
        recipe_title = best_recipe_metadata.get('title', 'No title available')
        recipe_text = best_recipe_metadata.get('recipe', 'No recipe instructions available')
        
        return f"Title: {recipe_title}\n\nRecipe: {recipe_text}"
    else:
        return "No recipe found for the given ingredients."
    

# Run the Streamlit app
if __name__ == "__main__":
    st.title("Recipe Generator")
    st.write("Enter ingredients to generate a recipe:")
    user_ingredients = st.text_input("Ingredients (comma-separated):")
    submit_button = st.button("Generate Recipe")

    # Load recipes from csv file
    file_path = "data/20-recipes.csv" # replace with the path to your CSV file
    df = load_recipes_from_csv(file_path)

    # Initialize ChromaDB and store recipe embeddings
    collection = initialize_chromadb_and_store_recipes(df)

    # Search the recipe database using langchain and ChromaDB
    if submit_button:
        if user_ingredients:
            st.subheader("Generated Recipe:")
            result = generate_recipe(user_ingredients, collection)
            st.write(result)
        else:
            st.error("Please enter at least one ingredient.")

