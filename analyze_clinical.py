import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Read the clinical data
df = pd.read_csv('clinical.csv')

# Basic patient demographics analysis
def analyze_demographics(df):
    demo_stats = {
        'Total Unique Patients': len(df['cases_submitter_id'].unique()),
        'Gender Distribution': df.groupby('demographic_gender')['cases_submitter_id'].nunique().to_dict(),
        'Age Statistics': {
            'Mean': df['demographic_age_at_index'].mean(),
            'Median': df['demographic_age_at_index'].median(),
            'Range': f"{df['demographic_age_at_index'].min()}-{df['demographic_age_at_index'].max()}"
        },
        'Vital Status': df.groupby('demographic_vital_status')['cases_submitter_id'].nunique().to_dict(),
        'Race Distribution': df.groupby('demographic_race')['cases_submitter_id'].nunique().to_dict()
    }
    return demo_stats

# Disease characteristics analysis
def analyze_disease(df):
    disease_stats = {
        'Primary Sites': df['cases_primary_site'].value_counts().to_dict(),
        'Disease Types': df['cases_disease_type'].value_counts().to_dict(),
        'Stage Distribution': df['diagnoses_ajcc_pathologic_stage'].value_counts().to_dict(),
        'Morphology Types': df['diagnoses_morphology'].value_counts().to_dict()
    }
    return disease_stats

# Treatment analysis
def analyze_treatments(df):
    treatment_stats = {
        'Treatment Types': df['treatments_treatment_type'].value_counts().to_dict(),
        'Treatment Outcomes': df['treatments_treatment_outcome'].value_counts().to_dict(),
        'Treatment Intent': df['treatments_treatment_intent_type'].value_counts().to_dict()
    }
    return treatment_stats

# Generate summary report
def generate_report():
    print("\n=== Clinical Data Analysis Report ===\n")
    
    print("\nDemographic Summary:")
    demo_stats = analyze_demographics(df)
    for key, value in demo_stats.items():
        print(f"{key}: {value}")
        
    print("\nDisease Characteristics:")
    disease_stats = analyze_disease(df)
    for key, value in disease_stats.items():
        print(f"{key}: {value}")
        
    print("\nTreatment Summary:")
    treatment_stats = analyze_treatments(df)
    for key, value in treatment_stats.items():
        print(f"{key}: {value}")

# Create visualizations
def create_visualizations():
    # Age distribution
    plt.figure(figsize=(10, 6))
    sns.histplot(data=df, x='demographic_age_at_index', bins=30)
    plt.title('Age Distribution')
    plt.savefig('age_distribution.png')
    plt.close()
    
    # Gender distribution
    plt.figure(figsize=(8, 6))
    df['demographic_gender'].value_counts().plot(kind='bar')
    plt.title('Gender Distribution')
    plt.savefig('gender_distribution.png')
    plt.close()
    
    # Disease stage distribution
    plt.figure(figsize=(12, 6))
    df['diagnoses_ajcc_pathologic_stage'].value_counts().plot(kind='bar')
    plt.title('Disease Stage Distribution')
    plt.xticks(rotation=45)
    plt.savefig('stage_distribution.png')
    plt.close()

if __name__ == "__main__":
    generate_report()
    create_visualizations()
