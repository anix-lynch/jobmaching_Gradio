from sklearn.feature_extraction.text import CountVectorizer
from sentence_transformers import SentenceTransformer, util
import pandas as pd
import gradio as gr

# Load model for sentence similarity
model = SentenceTransformer('all-MiniLM-L6-v2')

# Function to get similarity score and improvement suggestions
def match_job_with_suggestions(resume_text, job_descriptions_csv):
    job_descriptions_df = pd.read_csv(job_descriptions_csv)
    
    results = []
    for idx, row in job_descriptions_df.iterrows():
        # Concatenate relevant job fields
        job_text = f"{row['title']} {row['description']}"

        # Calculate similarity score
        job_embedding = model.encode(job_text, convert_to_tensor=True)
        resume_embedding = model.encode(resume_text, convert_to_tensor=True)
        similarity_score = util.pytorch_cos_sim(resume_embedding, job_embedding).item()

        # Extract keywords from job description and resume
        vectorizer = CountVectorizer(stop_words='english', max_features=10)
        job_keywords = set(vectorizer.fit([job_text]).get_feature_names_out())
        resume_keywords = set(vectorizer.fit([resume_text]).get_feature_names_out())

        # Identify missing keywords in the resume
        missing_keywords = job_keywords - resume_keywords
        suggestions = (
            f"Consider adding relevant keywords from this job description: {', '.join(missing_keywords)}."
            if missing_keywords else "Your resume covers most relevant keywords for this job."
        )

        results.append({
            'title': row['title'],
            'company': row.get('company', 'N/A'),
            'link': row.get('link', 'N/A'),
            'similarity_score': round(similarity_score, 2),
            'suggestions': suggestions
        })

    # Convert results to DataFrame for Gradio output
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values(by='similarity_score', ascending=False)
    
    return results_df

# Define Gradio interface
def gradio_interface():
    resume_input = gr.Textbox(lines=10, placeholder="Paste your resume text here...", label="Resume Text")
    job_csv_input = gr.File(label="Upload Job Descriptions CSV", type="filepath")
    output_table = gr.Dataframe(label="Top Matching Jobs and Suggestions")
    
    interface = gr.Interface(
        fn=match_job_with_suggestions,
        inputs=[resume_input, job_csv_input],
        outputs=output_table,
        title="Job Matching App",
        description="Upload your resume and a CSV of LinkedIn job descriptions to find the best matching job based on the similarity score and get specific suggestions for improvement."
    )
    
    interface.launch()

gradio_interface()
