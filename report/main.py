import os
import json
import requests
from datetime import datetime
from collections import defaultdict
import statistics
import dotenv

dotenv.load_dotenv()

def fetch_supabase_data():
    """Fetch all submissions from Supabase"""
    
    # Get Supabase credentials from environment
    supabase_url = os.getenv('SUPABASE_URL', 'https://snkbgibsrfcioeedwvph.supabase.co')
    supabase_key = os.getenv('SUPABASE_KEY')
    table_name = os.getenv('SUPABASE_TABLE', 'phonikud-user-study')
    
    if not supabase_key:
        raise ValueError("SUPABASE_KEY environment variable is required")
    
    # Fetch all data from Supabase
    url = f"{supabase_url}/rest/v1/{table_name}?select=*"
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {supabase_key}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    return response.json()

def analyze_submissions(submissions):
    """Analyze submissions and create summary statistics"""
    
    # Extract data from submissions
    all_responses = []
    for submission in submissions:
        data = submission.get('data', {})
        if data:
            all_responses.append(data)
    
    if not all_responses:
        return {
            "error": "No valid submissions found",
            "total_submissions": 0
        }
    
    # Initialize analysis structures
    model_stats = defaultdict(lambda: {
        'naturalness_scores': [],
        'pronunciation_scores': [],
        'total_ratings': 0
    })
    
    user_languages = defaultdict(int)
    questions_analyzed = set()
    
    # Process each submission
    for submission in all_responses:
        user_info = submission.get('user', {})
        responses = submission.get('responses', {})
        
        # Count user languages
        native_lang = user_info.get('native_language', 'unknown')
        user_languages[native_lang] += 1
        
        # Process responses for each question
        for question_id, question_data in responses.items():
            questions_analyzed.add(question_id)
            ratings = question_data.get('ratings', {})
            
            # Process each model's ratings
            for model_id, rating_data in ratings.items():
                naturalness = rating_data.get('naturalness')
                pronunciation = rating_data.get('pronunciation')
                
                if naturalness is not None and pronunciation is not None:
                    model_stats[model_id]['naturalness_scores'].append(naturalness)
                    model_stats[model_id]['pronunciation_scores'].append(pronunciation)
                    model_stats[model_id]['total_ratings'] += 1
    
    # Calculate summary statistics for each model
    model_summary = {}
    for model_id, stats in model_stats.items():
        nat_scores = stats['naturalness_scores']
        pron_scores = stats['pronunciation_scores']
        
        if nat_scores and pron_scores:
            total_ratings = stats['total_ratings']
            nat_mean = statistics.mean(nat_scores)
            pron_mean = statistics.mean(pron_scores)
            combined_mean = (nat_mean + pron_mean) / 2
            
            # Calculate satisfaction levels (scores 4-5 = satisfied, 1-2 = unsatisfied, 3 = neutral)
            nat_satisfied = sum(1 for score in nat_scores if score >= 4)
            nat_unsatisfied = sum(1 for score in nat_scores if score <= 2)
            pron_satisfied = sum(1 for score in pron_scores if score >= 4)
            pron_unsatisfied = sum(1 for score in pron_scores if score <= 2)
            
            model_summary[model_id] = {
                'total_ratings': total_ratings,
                'naturalness': {
                    'mean': round(nat_mean, 2),
                    'median': statistics.median(nat_scores),
                    'std_dev': round(statistics.stdev(nat_scores) if len(nat_scores) > 1 else 0, 2),
                    'percentage_score': round((nat_mean / 5) * 100, 1),  # Convert to percentage
                    'satisfaction_rate': round((nat_satisfied / total_ratings) * 100, 1),
                    'dissatisfaction_rate': round((nat_unsatisfied / total_ratings) * 100, 1),
                    'scores_distribution': {str(i): nat_scores.count(i) for i in range(1, 6)},
                    'scores_distribution_percent': {str(i): round((nat_scores.count(i) / total_ratings) * 100, 1) for i in range(1, 6)}
                },
                'pronunciation': {
                    'mean': round(pron_mean, 2),
                    'median': statistics.median(pron_scores),
                    'std_dev': round(statistics.stdev(pron_scores) if len(pron_scores) > 1 else 0, 2),
                    'percentage_score': round((pron_mean / 5) * 100, 1),  # Convert to percentage
                    'satisfaction_rate': round((pron_satisfied / total_ratings) * 100, 1),
                    'dissatisfaction_rate': round((pron_unsatisfied / total_ratings) * 100, 1),
                    'scores_distribution': {str(i): pron_scores.count(i) for i in range(1, 6)},
                    'scores_distribution_percent': {str(i): round((pron_scores.count(i) / total_ratings) * 100, 1) for i in range(1, 6)}
                },
                'combined_score': round(combined_mean, 2),
                'combined_percentage': round((combined_mean / 5) * 100, 1),
                'overall_satisfaction': round(((nat_satisfied + pron_satisfied) / (total_ratings * 2)) * 100, 1),
                'improvement_potential': round((5 - combined_mean) * 20, 1)  # How much room for improvement (0-100%)
            }
    
    # Create model rankings
    models_by_naturalness = sorted(model_summary.items(), 
                                 key=lambda x: x[1]['naturalness']['mean'], reverse=True)
    models_by_pronunciation = sorted(model_summary.items(), 
                                   key=lambda x: x[1]['pronunciation']['mean'], reverse=True)
    models_by_combined = sorted(model_summary.items(), 
                              key=lambda x: x[1]['combined_score'], reverse=True)
    
    # Calculate comparative insights
    if model_summary:
        best_overall = models_by_combined[0]
        worst_overall = models_by_combined[-1]
        
        best_naturalness = models_by_naturalness[0]
        best_pronunciation = models_by_pronunciation[0]
        
        # Calculate performance gaps
        overall_gap = best_overall[1]['combined_score'] - worst_overall[1]['combined_score']
        naturalness_gap = best_naturalness[1]['naturalness']['mean'] - models_by_naturalness[-1][1]['naturalness']['mean']
        pronunciation_gap = best_pronunciation[1]['pronunciation']['mean'] - models_by_pronunciation[-1][1]['pronunciation']['mean']
        
        # Calculate average satisfaction across all models
        avg_satisfaction = statistics.mean([data['overall_satisfaction'] for data in model_summary.values()])
        
        insights = {
            'best_overall_model': best_overall[0],
            'best_naturalness_model': best_naturalness[0],
            'best_pronunciation_model': best_pronunciation[0],
            'performance_gaps': {
                'overall': round(overall_gap, 2),
                'naturalness': round(naturalness_gap, 2),
                'pronunciation': round(pronunciation_gap, 2)
            },
            'average_satisfaction_rate': round(avg_satisfaction, 1),
            'models_above_average': [model for model, data in model_summary.items() 
                                   if data['overall_satisfaction'] > avg_satisfaction],
            'consistency_analysis': {
                model: {
                    'difference_nat_pron': round(abs(data['naturalness']['mean'] - data['pronunciation']['mean']), 2),
                    'more_consistent': data['naturalness']['std_dev'] < 1.0 and data['pronunciation']['std_dev'] < 1.0
                }
                for model, data in model_summary.items()
            }
        }
    else:
        insights = {}
    
    return {
        'total_submissions': len(all_responses),
        'total_questions': len(questions_analyzed),
        'total_models': len(model_summary),
        'user_language_distribution': dict(user_languages),
        'models_summary': model_summary,
        'rankings': {
            'by_naturalness': [(model, data['naturalness']['mean']) for model, data in models_by_naturalness],
            'by_pronunciation': [(model, data['pronunciation']['mean']) for model, data in models_by_pronunciation],
            'by_combined_score': [(model, data['combined_score']) for model, data in models_by_combined],
            'by_satisfaction': sorted([(model, data['overall_satisfaction']) for model, data in model_summary.items()], 
                                    key=lambda x: x[1], reverse=True)
        },
        'research_insights': insights
    }

def generate_report():
    """Generate complete JSON report"""
    
    print("Fetching data from Supabase...")
    raw_submissions = fetch_supabase_data()
    
    print(f"Found {len(raw_submissions)} submissions")
    print("Analyzing data...")
    
    # Analyze submissions
    analysis = analyze_submissions(raw_submissions)
    
    # Create complete report
    report = {
        'report_metadata': {
            'generated_at': datetime.now().isoformat(),
            'generator': 'phonikud-tts-study-analyzer',
            'version': '1.0.0'
        },
        'summary': analysis,
        'individual_submissions': []
    }
    
    # Add individual submissions (clean format)
    for i, submission in enumerate(raw_submissions):
        data = submission.get('data', {})
        if data:
            clean_submission = {
                'submission_id': i + 1,
                'timestamp': data.get('timestamp'),
                'user': data.get('user', {}),
                'responses': data.get('responses', {}),
                'model_mappings': data.get('model_mappings', {})
            }
            report['individual_submissions'].append(clean_submission)
    
    return report

def main():
    try:
        # Generate report
        report = generate_report()
        
        # Save to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'tts_study_report_{timestamp}.json'
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"Report saved to: {filename}")
        
        # Print summary
        summary = report['summary']
        print(f"\n=== STUDY SUMMARY ===")
        print(f"Total Submissions: {summary['total_submissions']}")
        print(f"Total Questions: {summary['total_questions']}")
        print(f"Total Models: {summary['total_models']}")
        print(f"User Languages: {summary['user_language_distribution']}")
        
        print(f"\n=== MODEL RANKINGS ===")
        if 'rankings' in summary:
            print("By Combined Score:")
            for i, (model, score) in enumerate(summary['rankings']['by_combined_score'], 1):
                print(f"  {i}. {model}: {score}")
            
            print("\nBy Naturalness:")
            for i, (model, score) in enumerate(summary['rankings']['by_naturalness'], 1):
                print(f"  {i}. {model}: {score}")
            
            print("\nBy Pronunciation:")
            for i, (model, score) in enumerate(summary['rankings']['by_pronunciation'], 1):
                print(f"  {i}. {model}: {score}")
            
            print("\nBy User Satisfaction:")
            for i, (model, satisfaction) in enumerate(summary['rankings']['by_satisfaction'], 1):
                print(f"  {i}. {model}: {satisfaction}%")
        
        print(f"\n=== RESEARCH INSIGHTS ===")
        if 'research_insights' in summary and summary['research_insights']:
            insights = summary['research_insights']
            print(f"🏆 Best Overall Model: {insights['best_overall_model']}")
            print(f"🎯 Best for Naturalness: {insights['best_naturalness_model']}")
            print(f"🗣️  Best for Pronunciation: {insights['best_pronunciation_model']}")
            print(f"📊 Average Satisfaction: {insights['average_satisfaction_rate']}%")
            print(f"🔝 Above Average Models: {', '.join(insights['models_above_average'])}")
            
            print(f"\n=== PERFORMANCE GAPS ===")
            gaps = insights['performance_gaps']
            print(f"Overall Performance Gap: {gaps['overall']} points")
            print(f"Naturalness Gap: {gaps['naturalness']} points")
            print(f"Pronunciation Gap: {gaps['pronunciation']} points")
            
            print(f"\n=== MODEL DETAILS ===")
            for model, data in summary['models_summary'].items():
                print(f"\n{model.upper()}:")
                print(f"  • Combined Score: {data['combined_score']}/5 ({data['combined_percentage']}%)")
                print(f"  • Naturalness: {data['naturalness']['percentage_score']}% (satisfaction: {data['naturalness']['satisfaction_rate']}%)")
                print(f"  • Pronunciation: {data['pronunciation']['percentage_score']}% (satisfaction: {data['pronunciation']['satisfaction_rate']}%)")
                print(f"  • Overall Satisfaction: {data['overall_satisfaction']}%")  
                print(f"  • Improvement Potential: {data['improvement_potential']}%")
        
    except Exception as e:
        print(f"Error generating report: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
