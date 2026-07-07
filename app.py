import os
import re
import pickle
import sqlite3
import pandas as pd
import numpy as np
from flask import Flask, request, jsonify, render_template, send_file
import io

app = Flask(__name__)
DB_PATH = 'hdi_history.db'

# Ensure model and scaler are loaded, or load dynamically on requests
MODEL_PATH = 'model.pkl'
model_meta = None

def load_model():
    global model_meta
    if os.path.exists(MODEL_PATH):
        try:
            with open(MODEL_PATH, 'rb') as f:
                model_meta = pickle.load(f)
            print("Model loaded successfully.")
        except Exception as e:
            print(f"Error loading model: {e}")
            model_meta = None
    else:
        print("Model file not found. Please run train_model.py first.")
        model_meta = None

# Initialize Database
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            life_expectancy REAL,
            expected_schooling REAL,
            mean_schooling REAL,
            gni_capita REAL,
            predicted_category TEXT,
            confidence REAL,
            explanation TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# HTTP Page Routing
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict')
def predict_page():
    return render_template('predict.html')

@app.route('/dashboard')
def dashboard_page():
    # Load model stats if available to show metrics on dashboard
    if model_meta is None:
        load_model()
    
    metrics = {}
    model_name = "Not Trained"
    if model_meta is not None:
        metrics = model_meta.get('metrics', {})
        model_name = model_meta.get('model_name', "Unknown")
        
    return render_template('dashboard.html', metrics=metrics, model_name=model_name)

@app.route('/about')
def about_page():
    return render_template('about.html')

@app.route('/compare')
def compare_page():
    return render_template('compare.html')

# Country Comparison Helpers
HDI_CATEGORY_RANK = {'Low': 1, 'Medium': 2, 'High': 3, 'Very High': 4}

COUNTRY_NAME_POOL = [
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
    'United Arab Emirates', 'United Kingdom', 'United States', 'Uruguay', 'Venezuela',
    'Vietnam', 'Yemen', 'Zambia', 'Zimbabwe', 'Bolivia', 'Paraguay', 'Panama', 'Honduras',
    'Nicaragua', 'El Salvador', 'Dominican Republic', 'Cuba', 'Jamaica', 'Trinidad and Tobago',
    'Iceland', 'Luxembourg', 'Slovakia', 'Slovenia', 'Serbia', 'Bosnia and Herzegovina',
    'North Macedonia', 'Montenegro', 'Kosovo', 'Moldova', 'Belarus', 'Georgia', 'Armenia',
    'Azerbaijan', 'Kazakhstan', 'Uzbekistan', 'Turkmenistan', 'Kyrgyzstan', 'Tajikistan',
    'Mongolia', 'Laos', 'Maldives', 'Bhutan', 'Papua New Guinea', 'Fiji', 'Botswana',
    'Namibia', 'Mozambique', 'Angola', 'Madagascar', 'Malawi', 'Rwanda', 'Burundi',
    'Democratic Republic of the Congo', 'Republic of the Congo', 'Gabon', 'Chad', 'Niger',
    'Mali', 'Burkina Faso', 'Guinea', 'Sierra Leone', 'Liberia', 'Togo', 'Benin',
    'Central African Republic', 'Eritrea', 'Somalia', 'Djibouti', 'Libya', 'Mauritania',
    'Gambia', 'Lesotho', 'Eswatini', 'Mauritius', 'Seychelles', 'Comoros', 'Cape Verde',
    'Sao Tome and Principe', 'Equatorial Guinea', 'South Sudan', 'Palestine', 'Qatar',
    'Bahrain', 'Oman', 'Cyprus', 'Malta', 'Estonia', 'Latvia', 'Lithuania', 'Moldova',
    'Haiti', 'Belize', 'Guyana', 'Suriname', 'Timor-Leste', 'Brunei', 'North Korea',
    'Vatican City', 'Monaco', 'Andorra', 'San Marino', 'Liechtenstein'
]

def load_dataset_with_countries():
    """Load dataset.csv and ensure each row has a Country label."""
    if not os.path.exists("dataset.csv"):
        return None
    df = pd.read_csv("dataset.csv")
    if 'Country' not in df.columns:
        df['Country'] = [COUNTRY_NAME_POOL[i % len(COUNTRY_NAME_POOL)] for i in range(len(df))]
    return df

def normalize_country_name(name):
    """Strip duplicate suffixes like ' (2)' from country names."""
    if pd.isna(name):
        return name
    return re.sub(r'\s+\(\d+\)$', '', str(name).strip())

def get_unique_countries(df):
    """
    Return one representative row per unique country (alphabetically sorted).
    Multiple dataset rows for the same country are averaged on numeric indicators.
    """
    required = ['Life_Expectancy', 'Expected_Schooling', 'Mean_Schooling', 'GNI_Per_Capita']
    working = df.copy()
    working['Country'] = working['Country'].apply(normalize_country_name)

    grouped = (
        working.groupby('Country', as_index=False)[required]
        .mean(numeric_only=True)
        .dropna(subset=required, how='any')
        .sort_values('Country', key=lambda s: s.str.lower())
        .reset_index(drop=True)
    )
    return grouped

def get_country_row(df, country_name):
    """Look up a single country's representative row by name."""
    unique_df = get_unique_countries(df)
    normalized = normalize_country_name(country_name)
    matches = unique_df[unique_df['Country'] == normalized]
    if matches.empty:
        return None
    return matches.iloc[0]

def compute_hdi_indices(life_expectancy, expected_schooling, mean_schooling, gni_capita):
    """Compute UNDP dimension indices and overall HDI score."""
    health_idx = max(0.0, min(1.0, (life_expectancy - 20.0) / (85.0 - 20.0)))
    edu_idx = max(0.0, min(1.0, ((mean_schooling / 15.0) + (expected_schooling / 18.0)) / 2.0))
    if gni_capita > 100:
        inc_idx = max(0.0, min(1.0, (np.log(gni_capita) - np.log(100.0)) / (np.log(75000.0) - np.log(100.0))))
    else:
        inc_idx = 0.0
    calculated_hdi = (health_idx * edu_idx * inc_idx) ** (1.0 / 3.0)
    return {
        'health_index': round(health_idx, 3),
        'education_index': round(edu_idx, 3),
        'income_index': round(inc_idx, 3),
        'calculated_hdi': round(calculated_hdi, 3)
    }

def predict_category_from_features(life_expectancy, expected_schooling, mean_schooling, gni_capita):
    """Run ML model prediction for a country's indicators."""
    if model_meta is None:
        load_model()
    if model_meta is None:
        return None, None

    features = ['Life_Expectancy', 'Expected_Schooling', 'Mean_Schooling', 'GNI_Per_Capita']
    input_df = pd.DataFrame(
        [[life_expectancy, expected_schooling, mean_schooling, gni_capita]],
        columns=features
    )
    imputer = model_meta['imputer']
    scaler = model_meta['scaler']
    model = model_meta['model']

    input_imputed = imputer.transform(input_df)
    input_scaled = scaler.transform(input_imputed)
    predicted_category = model.predict(input_scaled)[0]

    confidence = 1.0
    if hasattr(model, 'predict_proba'):
        probs = model.predict_proba(input_scaled)[0]
        confidence = float(np.max(probs))

    return predicted_category, confidence

def build_country_profile(row):
    """Build a full country profile from a dataset row."""
    required = ['Life_Expectancy', 'Expected_Schooling', 'Mean_Schooling', 'GNI_Per_Capita']
    if row[required].isna().any():
        return None, 'Incomplete indicator data (missing values).'

    le = float(row['Life_Expectancy'])
    eys = float(row['Expected_Schooling'])
    mys = float(row['Mean_Schooling'])
    gni = float(row['GNI_Per_Capita'])

    indices = compute_hdi_indices(le, eys, mys, gni)
    predicted_category, confidence = predict_category_from_features(le, eys, mys, gni)

    if predicted_category is None:
        return None, 'Machine learning model not available for prediction.'

    return {
        'country': row['Country'],
        'life_expectancy': round(le, 1),
        'expected_schooling': round(eys, 1),
        'mean_schooling': round(mys, 1),
        'gni_per_capita': round(gni, 0),
        'predicted_category': predicted_category,
        'confidence': round(confidence * 100, 1),
        'indices': indices,
        'radar_values': {
            'Life Expectancy': round(indices['health_index'] * 100, 1),
            'Expected Schooling': round((eys / 18.0) * 100, 1),
            'Mean Schooling': round((mys / 15.0) * 100, 1),
            'GNI Per Capita': round(indices['income_index'] * 100, 1)
        }
    }, None

# API Endpoints
@app.route('/api/predict', methods=['POST'])
def predict_api():
    if model_meta is None:
        load_model()
        if model_meta is None:
            return jsonify({'error': 'Machine learning model not trained yet. Run train_model.py.'}), 500
            
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No input data provided'}), 400
            
        # Extract features
        try:
            life_expectancy = float(data.get('life_expectancy'))
            expected_schooling = float(data.get('expected_schooling'))
            mean_schooling = float(data.get('mean_schooling'))
            gni_capita = float(data.get('gni_capita'))
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid inputs. All indicators must be numbers.'}), 400

        # Validate values
        errors = []
        if not (20 <= life_expectancy <= 85):
            errors.append("Life Expectancy must be between 20 and 85 years.")
        if not (0 <= expected_schooling <= 18):
            errors.append("Expected Schooling must be between 0 and 18 years.")
        if not (0 <= mean_schooling <= 15):
            errors.append("Mean Schooling must be between 0 and 15 years.")
        if not (100 <= gni_capita <= 75000):
            errors.append("GNI Per Capita must be between $100 and $75,000.")
        if mean_schooling > expected_schooling:
            errors.append("Mean Schooling cannot exceed Expected Schooling.")
            
        if errors:
            return jsonify({'errors': errors}), 400

        # Construct input vector
        features = ['Life_Expectancy', 'Expected_Schooling', 'Mean_Schooling', 'GNI_Per_Capita']
        input_df = pd.DataFrame([[life_expectancy, expected_schooling, mean_schooling, gni_capita]], columns=features)
        
        # Preprocessing
        imputer = model_meta['imputer']
        scaler = model_meta['scaler']
        model = model_meta['model']
        
        input_imputed = imputer.transform(input_df)
        input_scaled = scaler.transform(input_imputed)
        
        # Predict Category
        predicted_category = model.predict(input_scaled)[0]
        
        # Confidence score (max class probability)
        if hasattr(model, 'predict_proba'):
            probs = model.predict_proba(input_scaled)[0]
            confidence = float(np.max(probs))
        else:
            confidence = 1.0 # Fallback if model has no probabilities
            
        # Compute Explainable AI metrics
        features_dict = {
            'Life_Expectancy': life_expectancy,
            'Expected_Schooling': expected_schooling,
            'Mean_Schooling': mean_schooling,
            'GNI_Per_Capita': gni_capita
        }
        
        class_stats = model_meta['class_stats']
        global_stats = model_meta['global_stats']
        
        # Dimension Index calculation according to UNDP
        health_idx = max(0.0, min(1.0, (life_expectancy - 20.0) / (85.0 - 20.0)))
        edu_idx = max(0.0, min(1.0, ((mean_schooling / 15.0) + (expected_schooling / 18.0)) / 2.0))
        inc_idx = max(0.0, min(1.0, (np.log(gni_capita) - np.log(100.0)) / (np.log(75000.0) - np.log(100.0)))) if gni_capita > 100 else 0.0
        calculated_hdi = (health_idx * edu_idx * inc_idx) ** (1.0/3.0)
        
        sub_indices = {
            'Health Index': round(health_idx, 3),
            'Education Index': round(edu_idx, 3),
            'Income Index': round(inc_idx, 3),
            'Calculated HDI': round(calculated_hdi, 3)
        }
        
        # Determine weakest index
        weakest = 'Health Index'
        min_idx = health_idx
        if edu_idx < min_idx:
            weakest = 'Education Index'
            min_idx = edu_idx
        if inc_idx < min_idx:
            weakest = 'Income Index'
            min_idx = inc_idx
            
        # Explanations of features vs typical values of predicted category
        feature_explanations = []
        cat_medians = class_stats[predicted_category]['median']
        cat_stds = class_stats[predicted_category]['std']
        importances = model_meta['feature_importances']
        
        for f in features:
            user_val = features_dict[f]
            median_val = cat_medians[f]
            std_val = cat_stds[f] if cat_stds[f] > 0 else 1.0
            diff = user_val - median_val
            z_diff = diff / std_val
            importance = importances.get(f, 0.25)
            
            f_display = f.replace('_', ' ')
            
            # Formulate text contribution
            if abs(diff) < 0.05 * median_val:
                desc = f"Typical for {predicted_category} HDI countries"
                direction = "neutral"
            elif diff > 0:
                desc = f"Stronger than the median ({diff:+.1f} units above typical)"
                direction = "positive"
            else:
                desc = f"Weaker than the median ({diff:.1f} units below typical)"
                direction = "negative"
                
            feature_explanations.append({
                'feature': f,
                'display': f_display,
                'user_val': round(user_val, 2),
                'class_median': round(median_val, 2),
                'difference': round(diff, 2),
                'description': desc,
                'direction': direction,
                'importance': round(importance, 3)
            })
            
        explanation_payload = {
            'sub_indices': sub_indices,
            'weakest_dimension': weakest,
            'feature_comparisons': feature_explanations
        }
        
        import json
        explanation_json = json.dumps(explanation_payload)
        
        # Save to SQLite Database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO predictions (life_expectancy, expected_schooling, mean_schooling, gni_capita, predicted_category, confidence, explanation)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (life_expectancy, expected_schooling, mean_schooling, gni_capita, predicted_category, confidence, explanation_json))
        conn.commit()
        conn.close()
        
        return jsonify({
            'prediction': predicted_category,
            'confidence': confidence,
            'explanation': explanation_payload
        })
        
    except Exception as e:
        return jsonify({'error': f"Internal Server Error: {str(e)}"}), 500

@app.route('/api/history', methods=['GET'])
def history_api():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT id, timestamp, life_expectancy, expected_schooling, mean_schooling, gni_capita, predicted_category, confidence FROM predictions ORDER BY id DESC')
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for r in rows:
            history.append({
                'id': r[0],
                'timestamp': r[1],
                'life_expectancy': r[2],
                'expected_schooling': r[3],
                'mean_schooling': r[4],
                'gni_capita': r[5],
                'predicted_category': r[6],
                'confidence': round(r[7] * 100, 1) if r[7] else None
            })
        return jsonify(history)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history/clear', methods=['POST'])
def clear_history_api():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM predictions')
        conn.commit()
        conn.close()
        return jsonify({'status': 'success', 'message': 'Prediction history cleared.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history/export', methods=['GET'])
def export_history_api():
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query('SELECT timestamp, life_expectancy, expected_schooling, mean_schooling, gni_capita, predicted_category, confidence FROM predictions ORDER BY id DESC', conn)
        conn.close()
        
        output = io.StringIO()
        df.to_csv(output, index=False)
        csv_data = output.getvalue()
        
        return send_file(
            io.BytesIO(csv_data.encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name='hdi_prediction_history.csv'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dataset-stats', methods=['GET'])
def dataset_stats_api():
    try:
        if not os.path.exists("dataset.csv"):
            return jsonify({'error': 'dataset.csv not found.'}), 404
        df = pd.read_csv("dataset.csv")
        df_clean = df.dropna()
        
        # Count category distribution
        categories = df_clean['HDI_Category'].value_counts().to_dict()
        
        data = {
            'categories': categories,
            'life_expectancy': df_clean['Life_Expectancy'].tolist(),
            'expected_schooling': df_clean['Expected_Schooling'].tolist(),
            'mean_schooling': df_clean['Mean_Schooling'].tolist(),
            'gni_capita': df_clean['GNI_Per_Capita'].tolist()
        }
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/model-stats', methods=['GET'])
def model_stats_api():
    try:
        if model_meta is None:
            load_model()
        if model_meta is None:
            return jsonify({'error': 'Machine learning model not trained yet.'}), 500
            
        return jsonify({
            'model_name': model_meta.get('model_name'),
            'feature_importances': model_meta.get('feature_importances'),
            'metrics': model_meta.get('metrics'),
            'all_models_metrics': model_meta.get('all_models_metrics'),
            'correlation_matrix': model_meta.get('correlation_matrix')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/countries', methods=['GET'])
def countries_api():
    """Return unique countries available in dataset.csv for comparison dropdowns."""
    try:
        df = load_dataset_with_countries()
        if df is None:
            return jsonify({'error': 'dataset.csv not found.'}), 404

        unique_df = get_unique_countries(df)
        countries = [
            {'id': row['Country'], 'name': row['Country']}
            for _, row in unique_df.iterrows()
        ]
        return jsonify(countries)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/compare', methods=['POST'])
def compare_api():
    """Compare two countries side by side with HDI indicators and radar data."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No input data provided.'}), 400

        country_a_name = data.get('country_a')
        country_b_name = data.get('country_b')

        if not country_a_name or not country_b_name:
            return jsonify({'error': 'Please select both Country A and Country B.'}), 400

        country_a_name = str(country_a_name).strip()
        country_b_name = str(country_b_name).strip()

        if country_a_name == country_b_name:
            return jsonify({'error': 'Please select two different countries to compare.'}), 400

        df = load_dataset_with_countries()
        if df is None:
            return jsonify({'error': 'dataset.csv not found.'}), 404

        row_a = get_country_row(df, country_a_name)
        if row_a is None:
            return jsonify({'error': f'Country A ({country_a_name}) was not found in the dataset.'}), 404

        row_b = get_country_row(df, country_b_name)
        if row_b is None:
            return jsonify({'error': f'Country B ({country_b_name}) was not found in the dataset.'}), 404

        profile_a, err_a = build_country_profile(row_a)
        if profile_a is None:
            return jsonify({'error': f"Country A ({country_a_name}): {err_a}"}), 400

        profile_b, err_b = build_country_profile(row_b)
        if profile_b is None:
            return jsonify({'error': f"Country B ({country_b_name}): {err_b}"}), 400

        comparisons = [
            {
                'key': 'life_expectancy',
                'label': 'Life Expectancy',
                'unit': 'yrs',
                'value_a': profile_a['life_expectancy'],
                'value_b': profile_b['life_expectancy'],
                'winner': 'a' if profile_a['life_expectancy'] > profile_b['life_expectancy']
                          else ('b' if profile_b['life_expectancy'] > profile_a['life_expectancy'] else 'tie')
            },
            {
                'key': 'mean_schooling',
                'label': 'Mean Years of Schooling',
                'unit': 'yrs',
                'value_a': profile_a['mean_schooling'],
                'value_b': profile_b['mean_schooling'],
                'winner': 'a' if profile_a['mean_schooling'] > profile_b['mean_schooling']
                          else ('b' if profile_b['mean_schooling'] > profile_a['mean_schooling'] else 'tie')
            },
            {
                'key': 'expected_schooling',
                'label': 'Expected Years of Schooling',
                'unit': 'yrs',
                'value_a': profile_a['expected_schooling'],
                'value_b': profile_b['expected_schooling'],
                'winner': 'a' if profile_a['expected_schooling'] > profile_b['expected_schooling']
                          else ('b' if profile_b['expected_schooling'] > profile_a['expected_schooling'] else 'tie')
            },
            {
                'key': 'gni_per_capita',
                'label': 'GNI Per Capita',
                'unit': 'USD',
                'value_a': profile_a['gni_per_capita'],
                'value_b': profile_b['gni_per_capita'],
                'winner': 'a' if profile_a['gni_per_capita'] > profile_b['gni_per_capita']
                          else ('b' if profile_b['gni_per_capita'] > profile_a['gni_per_capita'] else 'tie')
            },
            {
                'key': 'education_index',
                'label': 'Education Index',
                'unit': '',
                'value_a': profile_a['indices']['education_index'],
                'value_b': profile_b['indices']['education_index'],
                'winner': 'a' if profile_a['indices']['education_index'] > profile_b['indices']['education_index']
                          else ('b' if profile_b['indices']['education_index'] > profile_a['indices']['education_index'] else 'tie')
            },
            {
                'key': 'income_index',
                'label': 'Income Level (Index)',
                'unit': '',
                'value_a': profile_a['indices']['income_index'],
                'value_b': profile_b['indices']['income_index'],
                'winner': 'a' if profile_a['indices']['income_index'] > profile_b['indices']['income_index']
                          else ('b' if profile_b['indices']['income_index'] > profile_a['indices']['income_index'] else 'tie')
            },
            {
                'key': 'predicted_category',
                'label': 'Predicted HDI Category',
                'unit': '',
                'value_a': profile_a['predicted_category'],
                'value_b': profile_b['predicted_category'],
                'winner': 'a' if HDI_CATEGORY_RANK.get(profile_a['predicted_category'], 0) > HDI_CATEGORY_RANK.get(profile_b['predicted_category'], 0)
                          else ('b' if HDI_CATEGORY_RANK.get(profile_b['predicted_category'], 0) > HDI_CATEGORY_RANK.get(profile_a['predicted_category'], 0) else 'tie')
            }
        ]

        a_wins = [c['label'] for c in comparisons if c['winner'] == 'a']
        b_wins = [c['label'] for c in comparisons if c['winner'] == 'b']

        score_a = len(a_wins)
        score_b = len(b_wins)

        if score_a > score_b:
            overall_winner = profile_a['country']
            overall_side = 'a'
            overall_reason = f"Leads in {score_a} of {len(comparisons)} indicators"
            if a_wins:
                overall_reason += f", including {', '.join(a_wins[:3])}"
                if len(a_wins) > 3:
                    overall_reason += f" and {len(a_wins) - 3} more"
        elif score_b > score_a:
            overall_winner = profile_b['country']
            overall_side = 'b'
            overall_reason = f"Leads in {score_b} of {len(comparisons)} indicators"
            if b_wins:
                overall_reason += f", including {', '.join(b_wins[:3])}"
                if len(b_wins) > 3:
                    overall_reason += f" and {len(b_wins) - 3} more"
        else:
            hdi_a = profile_a['indices']['calculated_hdi']
            hdi_b = profile_b['indices']['calculated_hdi']
            if hdi_a > hdi_b:
                overall_winner = profile_a['country']
                overall_side = 'a'
                overall_reason = f"Tied on indicator wins; higher calculated HDI score ({hdi_a:.3f} vs {hdi_b:.3f})"
            elif hdi_b > hdi_a:
                overall_winner = profile_b['country']
                overall_side = 'b'
                overall_reason = f"Tied on indicator wins; higher calculated HDI score ({hdi_b:.3f} vs {hdi_a:.3f})"
            else:
                overall_winner = 'Tie'
                overall_side = 'tie'
                overall_reason = 'Both countries perform equally across all compared indicators.'

        return jsonify({
            'country_a': profile_a,
            'country_b': profile_b,
            'comparisons': comparisons,
            'summary': {
                'a_better_count': score_a,
                'b_better_count': score_b,
                'a_better_indicators': a_wins,
                'b_better_indicators': b_wins,
                'a_message': f"{profile_a['country']} performs better in {score_a} indicator{'s' if score_a != 1 else ''}." + (
                    f" ({', '.join(a_wins)})" if a_wins else ''
                ),
                'b_message': f"{profile_b['country']} performs better in {score_b} indicator{'s' if score_b != 1 else ''}." + (
                    f" ({', '.join(b_wins)})" if b_wins else ''
                )
            },
            'winner': {
                'title': 'Overall Better HDI Profile',
                'country': overall_winner,
                'side': overall_side,
                'reason': overall_reason
            },
            'radar': {
                'categories': list(profile_a['radar_values'].keys()),
                'country_a_values': list(profile_a['radar_values'].values()),
                'country_b_values': list(profile_b['radar_values'].values())
            }
        })

    except Exception as e:
        return jsonify({'error': f'Internal Server Error: {str(e)}'}), 500

if __name__ == '__main__':
    load_model()
    app.run(debug=True, port=5000)

