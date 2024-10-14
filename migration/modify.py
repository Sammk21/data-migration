import json

def restructure_json(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as file:
        exams = json.load(file)
    
    modified_exams = []
    
    for exam in exams:
        # Create the sections array
        sections = []
        
        # Add each section if available in the JSON
        if 'about_exam' in exam and 'description' in exam['about_exam']:
            sections.append({
                "title": "About",
                "content": exam['about_exam']['description']
            })
        
        if 'eligibility_criteria' in exam and 'html_content' in exam['eligibility_criteria']:
            sections.append({
                "title": "Eligibility Criteria",
                "content": exam['eligibility_criteria']['html_content']
            })
        
        if 'application_process' in exam and 'html_content' in exam['application_process']:
            sections.append({
                "title": "Application Process",
                "content": exam['application_process']['html_content']
            })
        
        if 'preparation_tips' in exam and 'html_content' in exam['preparation_tips']:
            sections.append({
                "title": "Preparation Tips",
                "content": exam['preparation_tips']['html_content']
            })
        
        if 'admit_card' in exam and 'html_content' in exam['admit_card']:
            sections.append({
                "title": "Admit Card",
                "content": exam['admit_card']['html_content']
            })
        
        if 'cutoffs' in exam and 'html_content' in exam['cutoffs']:
            sections.append({
                "title": "Cut Off",
                "content": exam['cutoffs']['html_content']
            })
        
        if 'counselling_process' in exam and 'html_content' in exam['counselling_process']:
            sections.append({
                "title": "Counselling Process",
                "content": exam['counselling_process']['html_content']
            })
        
        if 'Exam_Pattern' in exam and 'html_content' in exam['Exam_Pattern']:
            sections.append({
                "title": "Exam Pattern",
                "content": exam['Exam_Pattern']['html_content']
            })
        
        # Add the sections array to the exam
        exam['sections'] = sections
        
        # Remove the old individual section fields
        for key in ['about_exam', 'eligibility_criteria', 'application_process', 'preparation_tips', 'admit_card', 'cutoffs', 'counselling_process', 'Exam_Pattern']:
            if key in exam:
                del exam[key]
        
        # Add the modified exam to the list
        modified_exams.append(exam)
    
    # Write the modified exams to a new JSON file
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(modified_exams, file, ensure_ascii=False, indent=4)

# Usage example
restructure_json('../Exams/exams_data/example.json', 'm_example.json')
