import argparse
import glob
import os
import pandas as pd
import mlflow
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score

def main(args):
    print(f"Received training_data path: {args.training_data}")
    print(f"Received reg_rate: {args.reg_rate}")

    # Enable autologging
    mlflow.sklearn.autolog()
    
    # Set the experiment name to ensure the runs are logged under the same experiment
    mlflow.set_experiment('train-diabetes-classification')

    # Start a new MLflow run
    with mlflow.start_run() as run:
        run_id = run.info.run_id
        print(f"Running MLflow run with ID: {run_id}")

        # Read data
        df = get_csvs_df(args.training_data)

        # Split data
        X_train, X_test, y_train, y_test = split_data(df)

        # Train model
        model = train_model(args.reg_rate, X_train, X_test, y_train, y_test)

        # Evaluate model
        y_hat = model.predict(X_test)
        acc = accuracy_score(y_test, y_hat)
        y_scores = model.predict_proba(X_test)
        auc = roc_auc_score(y_test, y_scores[:, 1])

        # Log metrics including accuracy and auc and reg_rate
        mlflow.log_param("reg_rate", args.reg_rate)
        mlflow.log_metric("accuracy", acc)
        mlflow.log_metric("auc", auc)

        # Log model in a unique sub-directory within the artifact path
        artifact_subdir = f"model_{run_id}"
        mlflow.sklearn.log_model(model, artifact_subdir)

def get_csvs_df(path):
    if not os.path.exists(path):
        raise RuntimeError(f"Cannot use non-existent path provided: {path}")
    csv_files = glob.glob(f"{path}/*.csv")
    if not csv_files:
        raise RuntimeError(f"No CSV files found in provided data path: {path}")
    return pd.concat((pd.read_csv(f) for f in csv_files), sort=False)

def split_data(df):
    X, y = df[['Pregnancies', 'PlasmaGlucose', 'DiastolicBloodPressure', 'TricepsThickness', 'SerumInsulin', 'BMI',
               'DiabetesPedigree', 'Age']].values, df['Diabetic'].values
    return train_test_split(X, y, test_size=0.30, random_state=0)

def train_model(reg_rate, X_train, X_test, y_train, y_test):
    model = LogisticRegression(C=1/reg_rate, solver="liblinear").fit(X_train, y_train)
    return model

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--training_data", dest='training_data', type=str)
    parser.add_argument("--reg_rate", dest='reg_rate', type=float, default=0.01)
    return parser.parse_args()

if __name__ == "__main__":
    print("\n\n")
    print("*" * 60)
    args = parse_args()
    main(args)
    print("*" * 60)
    print("\n\n")
