# Project Development Phase

## Step 1: Dataset Collection

Download the Human Development Index dataset from Kaggle.

## Step 2: Data Preprocessing

- Handle missing values
- Remove duplicates
- Perform Label Encoding (if required)
- Split independent and dependent variables

## Step 3: Exploratory Data Analysis

Generate

- Correlation Matrix
- Heatmap
- Distribution Plot
- Scatter Plot

## Step 4: Model Building

Train a Linear Regression model using Scikit-learn.

## Step 5: Model Evaluation

Evaluate using

- R² Score
- Mean Absolute Error
- Mean Squared Error

## Step 6: Save Model

Save the trained model using Pickle.

Example:

```python
import pickle

pickle.dump(model, open("model.pkl","wb"))
```

## Step 7: Flask Application

Develop a Flask web application where users enter

- Life Expectancy
- Mean Years of Schooling
- Expected Years of Schooling
- GNI Per Capita

The application predicts the HDI score.

## Expected Output

A web interface displaying the predicted Human Development Index.