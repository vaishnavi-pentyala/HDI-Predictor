import os
import pickle
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix, precision_recall_fscore_support

def train_and_evaluate():
    print("--- Starting Machine Learning Pipeline ---")
    
    # 1. Load Dataset
    if not os.path.exists("dataset.csv"):
        raise FileNotFoundError("dataset.csv not found! Run generate_dataset.py first.")
        
    df = pd.read_csv("dataset.csv")
    print(f"Dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")
    
    # Check for missing values
    missing = df.isnull().sum()
    print("Missing values per column before cleaning:")
    print(missing)
    
    # 2. Data Cleaning & Imputation
    # Features & Target
    features = ['Life_Expectancy', 'Expected_Schooling', 'Mean_Schooling', 'GNI_Per_Capita']
    target = 'HDI_Category'
    
    X = df[features]
    y = df[target]
    
    # Impute missing values with median
    imputer = SimpleImputer(strategy='median')
    X_imputed = pd.DataFrame(imputer.fit_transform(X), columns=features)
    
    # Verify imputation
    print("Missing values after cleaning:", X_imputed.isnull().sum().sum())
    
    # 3. Train-Test Split (80/20)
    X_train, X_test, y_train, y_test = train_test_split(X_imputed, y, test_size=0.2, random_state=42, stratify=y)
    print(f"Train set: {X_train.shape[0]} samples, Test set: {X_test.shape[0]} samples")
    
    # 4. Feature Scaling
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # 5. Define Models to Compare
    models = {
        'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
        'Gradient Boosting': GradientBoostingClassifier(random_state=42),
        'K-Nearest Neighbors': KNeighborsClassifier(n_neighbors=5),
        'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42)
    }
    
    # 6. Train and Evaluate Models
    results = {}
    best_acc = 0.0
    best_model_name = None
    best_model = None
    
    # Ensure folders exist
    os.makedirs("static/images", exist_ok=True)
    os.makedirs("charts", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    
    for name, model in models.items():
        print(f"\nTraining {name}...")
        model.fit(X_train_scaled, y_train)
        y_pred = model.predict(X_test_scaled)
        
        # Calculate metrics
        acc = accuracy_score(y_test, y_pred)
        precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='weighted')
        
        results[name] = {
            'accuracy': acc,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'model': model
        }
        
        print(f"{name} Metrics - Accuracy: {acc:.4f}, Precision: {precision:.4f}, Recall: {recall:.4f}, F1: {f1:.4f}")
        
        if acc > best_acc:
            best_acc = acc
            best_model_name = name
            best_model = model
            
    print(f"\nBest Model: {best_model_name} with Accuracy: {best_acc:.4f}")
    
    # 7. Detailed Evaluation for Best Model
    y_pred_best = best_model.predict(X_test_scaled)
    # Define classes in specific order for visualization
    class_order = ['Low', 'Medium', 'High', 'Very High']
    # Check what classes are present in y_test to avoid errors
    unique_test_classes = sorted(y_test.unique())
    # Filter class_order to only include present classes
    labels = [c for c in class_order if c in unique_test_classes]
    
    # Print classification report
    report_text = classification_report(y_test, y_pred_best, target_names=labels)
    print("\nClassification Report for Best Model:")
    print(report_text)
    
    with open("reports/model_report.txt", "w") as f:
        f.write(f"Best Model Selected: {best_model_name}\n")
        f.write(f"Overall Accuracy: {best_acc:.4f}\n\n")
        f.write("Classification Report:\n")
        f.write(report_text)
        
    # Generate Confusion Matrix Chart (Save to both static/images and charts for presentation)
    cm = confusion_matrix(y_test, y_pred_best, labels=labels)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=labels, yticklabels=labels)
    plt.title(f'Confusion Matrix - {best_model_name}', fontsize=14, pad=15)
    plt.ylabel('True Category', fontsize=12)
    plt.xlabel('Predicted Category', fontsize=12)
    plt.tight_layout()
    plt.savefig("charts/confusion_matrix.png", dpi=150)
    plt.savefig("static/images/confusion_matrix.png", dpi=150)
    plt.close()
    print("Saved Confusion Matrix: charts/confusion_matrix.png")
    
    # Feature Importance (if model has it, or coefficients)
    importances = None
    if hasattr(best_model, 'feature_importances_'):
        importances = best_model.feature_importances_
    elif hasattr(best_model, 'coef_'):
        # For multi-class, coef_ has shape (n_classes, n_features). Average absolute coefficients across classes.
        coefs = np.abs(best_model.coef_)
        if len(coefs.shape) > 1:
            importances = np.mean(coefs, axis=0)
        else:
            importances = coefs
        # Normalize
        if np.sum(importances) > 0:
            importances = importances / np.sum(importances)

    if importances is not None:
        indices = np.argsort(importances)[::-1]
        
        plt.figure(figsize=(8, 5))
        plt.bar(range(X.shape[1]), importances[indices], color='#4f46e5', align='center')
        plt.xticks(range(X.shape[1]), [features[i].replace('_', ' ') for i in indices], rotation=15)
        plt.title('Feature Importances (Best Model)', fontsize=14, pad=15)
        plt.tight_layout()
        plt.savefig("charts/feature_importance.png", dpi=150)
        plt.savefig("static/images/feature_importance.png", dpi=150)
        plt.close()
        print("Saved Feature Importances chart: charts/feature_importance.png")
        
        feature_importance_dict = {features[i]: float(importances[i]) for i in range(len(features))}
    else:
        feature_importance_dict = {f: 0.25 for f in features} # Default uniform weight if no importances_
        
    # Generate Category Distribution Chart
    plt.figure(figsize=(8, 5))
    df[target].value_counts().reindex(labels).plot(kind='bar', color=['#ef4444', '#f59e0b', '#10b981', '#4f46e5'])
    plt.title('HDI Category Distribution in Dataset', fontsize=14, pad=15)
    plt.xlabel('HDI Category', fontsize=12)
    plt.ylabel('Count', fontsize=12)
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig("charts/category_distribution.png", dpi=150)
    plt.savefig("static/images/category_distribution.png", dpi=150)
    plt.close()
    
    # Generate Correlation Matrix Heatmap
    plt.figure(figsize=(8, 6))
    corr = X_imputed.corr()
    sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f", vmin=-1, vmax=1)
    plt.title('Feature Correlation Heatmap', fontsize=14, pad=15)
    plt.tight_layout()
    plt.savefig("charts/correlation_matrix.png", dpi=150)
    plt.savefig("static/images/correlation_matrix.png", dpi=150)
    plt.close()

    # Calculate class statistics (median and std dev) for Explainable AI comparisons
    class_stats = {}
    for cat in labels:
        indices_cat = (y_train == cat)
        if indices_cat.sum() > 0:
            medians = X_train[indices_cat].median().to_dict()
            stds = X_train[indices_cat].std().to_dict()
            class_stats[cat] = {
                'median': medians,
                'std': stds
            }
        else:
            class_stats[cat] = {
                'median': X_train.median().to_dict(),
                'std': X_train.std().to_dict()
            }
            
    # Calculate global dataset statistics
    global_stats = {
        'median': X_imputed.median().to_dict(),
        'mean': X_imputed.mean().to_dict(),
        'min': X_imputed.min().to_dict(),
        'max': X_imputed.max().to_dict(),
        'std': X_imputed.std().to_dict(),
        'total_records': int(len(df))
    }

    # 8. Save Best Model, Scaler, Imputer & Metadata to model.pkl
    model_metadata = {
        'model': best_model,
        'model_name': best_model_name,
        'scaler': scaler,
        'imputer': imputer,
        'features': features,
        'feature_importances': feature_importance_dict,
        'classes': best_model.classes_.tolist(),
        'class_stats': class_stats,
        'global_stats': global_stats,
        'all_models_metrics': {name: {k: float(v) for k, v in metrics.items() if k != 'model'} for name, metrics in results.items()},
        'correlation_matrix': {
            'features': features,
            'values': corr.round(4).values.tolist()
        },
        'metrics': {
            'accuracy': float(best_acc),
            'precision': float(results[best_model_name]['precision']),
            'recall': float(results[best_model_name]['recall']),
            'f1_score': float(results[best_model_name]['f1_score'])
        }
    }
    
    with open("model.pkl", "wb") as f:
        pickle.dump(model_metadata, f)
    print("Successfully saved best model and preprocessing objects to model.pkl.")

if __name__ == "__main__":
    train_and_evaluate()
