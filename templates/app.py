from flask import Flask, request, jsonify, render_template, send_from_directory
import re
from textblob import TextBlob
import google.generativeai as genai
from dotenv import load_dotenv
import os
from fpdf import FPDF

app = Flask(__name__)
load_dotenv()

# Define the rubric with corrected weights
rubric = {
    "Excellent": {
        "min_score": 90,
        "criteria": {
            "Accuracy": {"weight": 0.14},
            "Completeness": {"weight": 0.175},
            "Relevance": {"weight": 0.08},
            "Clarity": {"weight": 0.175},
            "Depth": {"weight": 0.09},
            "Organization": {"weight": 0.1},
            "Use of Evidence": {"weight": 0.09},
            "Grammar and Spelling": {"weight": 0.1},
            "Sentiment": {"weight": 0.075}
        }
    },
    "Good": {
        "min_score": 75,
        "criteria": {
            "Accuracy": {"weight": 0.14},
            "Completeness": {"weight": 0.175},
            "Relevance": {"weight": 0.08},
            "Clarity": {"weight": 0.175},
            "Depth": {"weight": 0.09},
            "Organization": {"weight": 0.1},
            "Use of Evidence": {"weight": 0.09},
            "Grammar and Spelling": {"weight": 0.1},
            "Sentiment": {"weight": 0.075}
        }
    },
    "Satisfactory": {
        "min_score": 55,
        "criteria": {
            "Accuracy": {"weight": 0.14},
            "Completeness": {"weight": 0.175},
            "Relevance": {"weight": 0.08},
            "Clarity": {"weight": 0.175},
            "Depth": {"weight": 0.09},
            "Organization": {"weight": 0.1},
            "Use of Evidence": {"weight": 0.09},
            "Grammar and Spelling": {"weight": 0.1},
            "Sentiment": {"weight": 0.075}
        }
    },
    "Fair": {
        "min_score": 40,
        "criteria": {
            "Accuracy": {"weight": 0.14},
            "Completeness": {"weight": 0.175},
            "Relevance": {"weight": 0.08},
            "Clarity": {"weight": 0.175},
            "Depth": {"weight": 0.09},
            "Organization": {"weight": 0.1},
            "Use of Evidence": {"weight": 0.09},
            "Grammar and Spelling": {"weight": 0.1},
            "Sentiment": {"weight": 0.075}
        }
    },
    "Poor": {
        "min_score": 0,
        "criteria": {
            "Accuracy": {"weight": 0.14},
            "Completeness": {"weight": 0.175},
            "Relevance": {"weight": 0.08},
            "Clarity": {"weight": 0.175},
            "Depth": {"weight": 0.09},
            "Organization": {"weight": 0.1},
            "Use of Evidence": {"weight": 0.09},
            "Grammar and Spelling": {"weight": 0.1},
            "Sentiment": {"weight": 0.075}
        }
    }
}


@app.route('/evaluate', methods=['POST'])
def evaluate():
    data = request.get_json()
    question = data.get('question')
    answer = data.get('answer')

    prompt = f"""
        You are conducting a professional interview and are tasked with evaluating the candidate's response to the following question. 

        Question: '{question}'

        Evaluation Criteria:

        The candidate's response will be assessed based on the following criteria. Each criterion has a specific weight, which contributes to the final score.

    1. Accuracy (14%): We need to ensure that the response is factually correct and aligns with industry best practices. It should demonstrate a solid understanding of the subject matter without any major errors.

    2. Completeness (17.5%): The response should cover all essential aspects of the question, providing relevant details and considering various nuances. It's important to strike a balance between being concise and comprehensive.

    3. Relevance (8%): Is the response directly focused on the question asked, without getting sidetracked by irrelevant information? It should also show an understanding of the requirements of the role.

    4. Clarity (17.5%): We're looking for a response that is clear, concise, and easy to understand. The candidate should use language that's appropriate for a professional setting and avoid any ambiguity.

    5. Depth (9%): Does the response demonstrate a deep understanding of the topic, going beyond surface-level explanations? This is particularly important for complex questions that require insightful analysis.

    6. Organization (10%): The response should be well-organized, with a logical flow of ideas and clear transitions between points. This demonstrates effective communication skills.

    7. Use of Evidence (9%): Where appropriate, the response should provide evidence to support its claims, whether it's statistics, research findings, case studies, or personal experiences.

    8. Grammar and Spelling (10%): We'll also assess the response for grammatical accuracy and spelling errors. A polished response enhances readability and professionalism.

    9. Sentiment (7.5%): Finally, we'll consider the overall tone and emotion conveyed in the response. We're looking for professionalism, confidence, and positivity.

    After evaluating each criterion and assigning a score (ranging from 0 to 100), we'll calculate the final score by multiplying each score by its corresponding weight and summing up the results.
        Scoring & Justification:

        Assign a score (0-100) for each criterion. Justify your scores with specific examples from the Candidate's Response, highlighting both strengths and areas for improvement.
        Candidate's Response: '{answer}'
        """
    # Configure the generative model
    genai.configure(api_key=os.getenv("gemini_api_key"))
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)

    # Extract scores from the generated evaluation text
    evaluation = response.text.strip()
    scores = [float(value) for value in re.findall(r'-?\d+', evaluation)]

    # Calculate the breakdown of scores based on the rubric weights
    breakdown = {criterion: min(score * rubric["Excellent"]["criteria"][criterion]["weight"], 100) for criterion, score
                 in zip(rubric["Excellent"]["criteria"].keys(), scores)}

    # Calculate the final score
    final_score = min(sum(breakdown.values()), 100)

    # Analyze sentiment of the candidate's response
    sentiment = TextBlob(answer).sentiment.polarity

    # Determine the grade based on the final score
    grade = None
    for level, level_criteria in rubric.items():
        if final_score >= level_criteria["min_score"]:
            grade = level
            break

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Candidate's Answer", ln=True, align='C')
    pdf.multi_cell(0, 10, txt=answer)  # Adding candidate's answer as multiline text

    # Save the PDF to a file
    pdf_file = "candidate_answer.pdf"
    pdf.output(pdf_file)

    return jsonify({
        "final_score": final_score,
        "grade": grade,
        "breakdown": breakdown,
        "sentiment": sentiment,
        "pdf_file": pdf_file
    })


@app.route('/<path:filename>')
def download_file(filename):
    return send_from_directory(directory='.', path=filename)


@app.route('/')
def index():
    return render_template('indexP.html')


if __name__ == '__main__':
    app.run(debug=True)
