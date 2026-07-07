import os
import urllib.request
import pandas as pd
import numpy as np

def download_dataset():
    # Attempt to download a clean public HDI dataset
    url = "https://raw.githubusercontent.com/yhpong/Scientific-Toolkit/master/HDI_Data.csv"
    try:
        print(f"Attempting to download dataset from: {url}")
        urllib.request.urlretrieve(url, "dataset_raw.csv")
        df_raw = pd.read_csv("dataset_raw.csv")
        print("Download successful. Inspecting columns...")
        print("Raw columns:", df_raw.columns.tolist())
        
        # Mapping raw columns to standard names
        # Raw dataset from this repo typically contains: Country, HDI, Life_Expectancy, Expected_Schooling, Mean_Schooling, GNI_Per_Capita
        rename_map = {}
        for col in df_raw.columns:
            col_lower = col.lower()
            if 'life' in col_lower:
                rename_map[col] = 'Life_Expectancy'
            elif 'expect' in col_lower and 'school' in col_lower:
                rename_map[col] = 'Expected_Schooling'
            elif 'mean' in col_lower and 'school' in col_lower:
                rename_map[col] = 'Mean_Schooling'
            elif 'gni' in col_lower or 'income' in col_lower:
                rename_map[col] = 'GNI_Per_Capita'
            elif 'hdi' in col_lower and 'cat' in col_lower:
                rename_map[col] = 'HDI_Category'
                
        df_renamed = df_raw.rename(columns=rename_map)
        required_cols = ['Life_Expectancy', 'Expected_Schooling', 'Mean_Schooling', 'GNI_Per_Capita']
        
        if all(c in df_renamed.columns for c in required_cols):
            print("Found all required columns in downloaded dataset.")
            # Standardize and save
            df_final = df_renamed[required_cols].copy()
            
            # Calculate HDI Score using standard formula
            le = df_final['Life_Expectancy']
            eys = df_final['Expected_Schooling']
            mys = df_final['Mean_Schooling']
            gni = df_final['GNI_Per_Capita']
            
            h_idx = (le - 20) / (85 - 20)
            e_idx = ((mys / 15) + (eys / 18)) / 2
            i_idx = (np.log(gni) - np.log(100)) / (np.log(75000) - np.log(100))
            
            hdi_score = (h_idx.clip(0,1) * e_idx.clip(0,1) * i_idx.clip(0,1)) ** (1/3)
            df_final['HDI_Score'] = hdi_score
            
            # Assign Category
            def get_category(score):
                if score >= 0.8: return 'Very High'
                elif score >= 0.7: return 'High'
                elif score >= 0.55: return 'Medium'
                else: return 'Low'
                
            df_final['HDI_Category'] = df_final['HDI_Score'].apply(get_category)
            
            # Inject some missing values for data cleaning demonstration (3% missing)
            np.random.seed(42)
            for col in ['Life_Expectancy', 'Mean_Schooling']:
                mask = np.random.rand(len(df_final)) < 0.03
                df_final.loc[mask, col] = np.nan
                
            df_final.to_csv("dataset.csv", index=False)
            print("Saved downloaded dataset as dataset.csv.")
            # Clean up temp file
            if os.path.exists("dataset_raw.csv"):
                os.remove("dataset_raw.csv")
            return True
            
    except Exception as e:
        print(f"Failed to process downloaded dataset: {e}")
        if os.path.exists("dataset_raw.csv"):
            os.remove("dataset_raw.csv")
            
    return False

def generate_synthetic_dataset():
    print("Generating a high-fidelity synthetic HDI dataset...")
    np.random.seed(42)
    n_samples = 1000
    
    # Generate realistic distributions
    # 1. Life Expectancy (40 to 85)
    life_expectancy = np.random.normal(70, 8, n_samples)
    life_expectancy = np.clip(life_expectancy, 40, 85)
    
    # 2. Expected Years of Schooling (4 to 18)
    expected_schooling = np.random.normal(12.5, 3, n_samples)
    expected_schooling = np.clip(expected_schooling, 4, 18)
    
    # 3. Mean Years of Schooling (0 to 15, must be <= expected_schooling)
    mean_schooling = life_expectancy * 0.12 + np.random.normal(0, 1.5, n_samples)
    mean_schooling = np.clip(mean_schooling, 1, 15)
    mean_schooling = np.minimum(mean_schooling, expected_schooling)
    
    # 4. GNI Per Capita (100 to 75000) - Log Normal
    # A country's GNI per capita correlates with schooling and life expectancy
    log_gni = 5.0 + 0.04 * life_expectancy + 0.15 * mean_schooling + np.random.normal(0, 0.4, n_samples)
    gni_per_capita = np.exp(log_gni)
    gni_per_capita = np.clip(gni_per_capita, 100, 75000)
    
    # Create DataFrame
    df = pd.DataFrame({
        'Life_Expectancy': life_expectancy,
        'Expected_Schooling': expected_schooling,
        'Mean_Schooling': mean_schooling,
        'GNI_Per_Capita': gni_per_capita
    })
    
    # Calculate indices according to standard UNDP formulas
    health_index = (df['Life_Expectancy'] - 20) / (85 - 20)
    education_index = ((df['Mean_Schooling'] / 15) + (df['Expected_Schooling'] / 18)) / 2
    income_index = (np.log(df['GNI_Per_Capita']) - np.log(100)) / (np.log(75000) - np.log(100))
    
    # Geometric mean
    hdi_score = (health_index.clip(0, 1) * education_index.clip(0, 1) * income_index.clip(0, 1)) ** (1/3)
    
    # Add small random noise to final score to represent model complexity
    hdi_score_noisy = hdi_score + np.random.normal(0, 0.015, n_samples)
    hdi_score_noisy = np.clip(hdi_score_noisy, 0, 1)
    
    df['HDI_Score'] = hdi_score_noisy
    
    # Classify HDI Category
    def get_category(score):
        if score >= 0.8: return 'Very High'
        elif score >= 0.7: return 'High'
        elif score >= 0.55: return 'Medium'
        else: return 'Low'
        
    df['HDI_Category'] = df['HDI_Score'].apply(get_category)
    
    # Assign country names for comparison feature
    country_names = []
    country_pool = [
        'Afghanistan', 'Albania', 'Algeria', 'Argentina', 'Australia', 'Austria', 'Bangladesh',
        'Belgium', 'Brazil', 'Bulgaria', 'Cambodia', 'Cameroon', 'Canada', 'Chile', 'China',
        'Colombia', 'Costa Rica', 'Croatia', 'Czech Republic', 'Denmark', 'Ecuador', 'Egypt',
        'Ethiopia', 'Finland', 'France', 'Germany', 'Ghana', 'Greece', 'Guatemala', 'Hungary',
        'India', 'Indonesia', 'Iran', 'Iraq', 'Ireland', 'Israel', 'Italy', 'Japan', 'Jordan',
        'Kenya', 'South Korea', 'Kuwait', 'Lebanon', 'Malaysia', 'Mexico', 'Morocco', 'Myanmar',
        'Nepal', 'Netherlands', 'New Zealand', 'Nigeria', 'Norway', 'Pakistan', 'Peru',
        'Philippines', 'Poland', 'Portugal', 'Romania', 'Russia', 'Saudi Arabia', 'Senegal',
        'Singapore', 'South Africa', 'Spain', 'Sri Lanka', 'Sudan', 'Sweden', 'Switzerland',
        'Syria', 'Taiwan', 'Tanzania', 'Thailand', 'Tunisia', 'Turkey', 'Uganda', 'Ukraine',
        'United Arab Emirates', 'United Kingdom', 'United States', 'Uruguay', 'Venezuela', 'Vietnam'
    ]
    for i in range(n_samples):
        country_names.append(country_pool[i % len(country_pool)])
    df['Country'] = country_names
    
    # Inject ~3% missing values for data cleaning demonstration
    for col in ['Life_Expectancy', 'Mean_Schooling']:
        mask = np.random.rand(n_samples) < 0.03
        df.loc[mask, col] = np.nan
        
    df.to_csv("dataset.csv", index=False)
    print(f"Generated synthetic dataset with {n_samples} samples and saved as dataset.csv.")

if __name__ == "__main__":
    # Try downloading first, otherwise generate synthetic
    success = download_dataset()
    if not success:
        generate_synthetic_dataset()
