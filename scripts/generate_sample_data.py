#!/usr/bin/env python3
"""
Generate sample clinical data for testing the Skin Wellness Navigator.
Creates a CSV file with synthetic patient data and skin lesion characteristics.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

def generate_patient_id():
    """Generate a unique patient ID."""
    return f"TCGA-{random.randint(1000, 9999)}"

def generate_age():
    """Generate a random age between 18 and 90."""
    return random.randint(18, 90)

def generate_gender():
    """Generate random gender."""
    return random.choice(['male', 'female'])

def generate_race():
    """Generate random race."""
    races = ['white', 'black', 'asian', 'native_american', 'pacific_islander']
    weights = [0.6, 0.2, 0.15, 0.03, 0.02]
    return random.choices(races, weights=weights)[0]

def generate_vital_status():
    """Generate vital status with weighted probability."""
    return random.choices(['Alive', 'Deceased'], weights=[0.8, 0.2])[0]

def generate_stage():
    """Generate disease stage with weighted probability."""
    stages = ['Stage I', 'Stage II', 'Stage III', 'Stage IV']
    weights = [0.4, 0.3, 0.2, 0.1]
    return random.choices(stages, weights=weights)[0]

def generate_morphology():
    """Generate morphology code."""
    morphology_codes = [
        '8720/3',  # Malignant melanoma, NOS
        '8721/3',  # Nodular melanoma
        '8742/3',  # Lentigo maligna melanoma
        '8743/3',  # Superficial spreading melanoma
        '8744/3',  # Acral lentiginous melanoma
    ]
    weights = [0.3, 0.25, 0.2, 0.15, 0.1]
    return random.choices(morphology_codes, weights=weights)[0]

def generate_treatment_type():
    """Generate treatment type."""
    treatments = ['Surgery', 'Radiation', 'Chemotherapy', 'Immunotherapy', 'Targeted Therapy']
    weights = [0.4, 0.2, 0.15, 0.15, 0.1]
    return random.choices(treatments, weights=weights)[0]

def generate_treatment_outcome():
    """Generate treatment outcome."""
    outcomes = [
        'Complete Response',
        'Partial Response',
        'Stable Disease',
        'Progressive Disease'
    ]
    weights = [0.4, 0.3, 0.2, 0.1]
    return random.choices(outcomes, weights=weights)[0]

def generate_treatment_intent():
    """Generate treatment intent."""
    return random.choices(['Curative', 'Palliative'], weights=[0.8, 0.2])[0]

def generate_sample_data(num_records=1000):
    """
    Generate sample clinical data.
    
    Args:
        num_records: Number of records to generate
        
    Returns:
        pandas.DataFrame: Generated clinical data
    """
    data = {
        'cases_submitter_id': [generate_patient_id() for _ in range(num_records)],
        'demographic_gender': [generate_gender() for _ in range(num_records)],
        'demographic_age_at_index': [generate_age() for _ in range(num_records)],
        'demographic_vital_status': [generate_vital_status() for _ in range(num_records)],
        'demographic_race': [generate_race() for _ in range(num_records)],
        'cases_primary_site': ['Skin' for _ in range(num_records)],
        'cases_disease_type': ['Melanoma' for _ in range(num_records)],
        'diagnoses_ajcc_pathologic_stage': [generate_stage() for _ in range(num_records)],
        'diagnoses_morphology': [generate_morphology() for _ in range(num_records)],
        'treatments_treatment_type': [generate_treatment_type() for _ in range(num_records)],
        'treatments_treatment_outcome': [generate_treatment_outcome() for _ in range(num_records)],
        'treatments_treatment_intent_type': [generate_treatment_intent() for _ in range(num_records)]
    }
    
    return pd.DataFrame(data)

def add_derived_fields(df):
    """
    Add derived fields based on existing data.
    
    Args:
        df: pandas.DataFrame with clinical data
        
    Returns:
        pandas.DataFrame: Data with added derived fields
    """
    # Add diagnosis dates
    start_date = datetime(2015, 1, 1)
    end_date = datetime(2023, 12, 31)
    days_range = (end_date - start_date).days
    
    df['diagnosis_date'] = [
        start_date + timedelta(days=random.randint(0, days_range))
        for _ in range(len(df))
    ]
    
    # Add follow-up dates
    df['last_follow_up'] = df['diagnosis_date'].apply(
        lambda x: x + timedelta(days=random.randint(30, 1825))  # 1 month to 5 years
    )
    
    # Add survival time for deceased patients
    df.loc[df['demographic_vital_status'] == 'Deceased', 'survival_days'] = \
        df.loc[df['demographic_vital_status'] == 'Deceased'].apply(
            lambda x: (x['last_follow_up'] - x['diagnosis_date']).days,
            axis=1
        )
    
    return df

def main():
    """Generate sample data and save to CSV."""
    # Create output directory if it doesn't exist
    output_dir = 'data'
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate base data
    print("Generating sample clinical data...")
    df = generate_sample_data()
    
    # Add derived fields
    print("Adding derived fields...")
    df = add_derived_fields(df)
    
    # Save to CSV
    output_file = os.path.join(output_dir, 'clinical.csv')
    df.to_csv(output_file, index=False)
    print(f"Data saved to {output_file}")
    
    # Print summary statistics
    print("\nSummary Statistics:")
    print("-" * 50)
    print(f"Total records: {len(df)}")
    print(f"Gender distribution:\n{df['demographic_gender'].value_counts()}")
    print(f"\nStage distribution:\n{df['diagnoses_ajcc_pathologic_stage'].value_counts()}")
    print(f"\nTreatment outcomes:\n{df['treatments_treatment_outcome'].value_counts()}")
    print(f"\nAge statistics:\n{df['demographic_age_at_index'].describe()}")
    
    # Create a backup
    backup_file = os.path.join(
        output_dir,
        f'clinical_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )
    df.to_csv(backup_file, index=False)
    print(f"\nBackup saved to {backup_file}")

if __name__ == '__main__':
    main()
