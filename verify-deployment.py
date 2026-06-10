#!/usr/bin/env python3
"""
Verify deployment readiness for exam-helper app
"""
import os
import sys
import json

def check_file(filepath, description):
    """Check if a file exists and is readable"""
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print(f"✓ {description}: {filepath} ({size:,} bytes)")
        return True
    else:
        print(f"✗ {description}: {filepath} - MISSING")
        return False

def check_directory(dirpath, description):
    """Check if directory exists"""
    if os.path.isdir(dirpath):
        count = len(os.listdir(dirpath))
        print(f"✓ {description}: {dirpath} ({count} files)")
        return True
    else:
        print(f"✗ {description}: {dirpath} - MISSING")
        return False

def check_json_files(resources_dir):
    """Check JSON exam files"""
    json_files = [f for f in os.listdir(resources_dir) if f.endswith('.json')]
    total_questions = 0
    
    for json_file in sorted(json_files):
        filepath = os.path.join(resources_dir, json_file)
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                questions = data.get('total_questions', 0)
                exam_name = data.get('exam', 'Unknown')
                code = data.get('code', 'N/A')
                print(f"  ✓ {json_file}: {exam_name} ({code}) - {questions} questions")
                total_questions += questions
        except Exception as e:
            print(f"  ✗ {json_file}: Error - {e}")
    
    print(f"\n  Total: {len(json_files)} exams, {total_questions:,} questions")
    return len(json_files) > 0

def main():
    print("=" * 60)
    print("Exam Helper - Deployment Readiness Check")
    print("=" * 60)
    print()
    
    all_good = True
    
    # Check deployment files
    print("📋 Deployment Files:")
    all_good &= check_file("Dockerfile", "Docker configuration")
    all_good &= check_file(".dockerignore", "Docker ignore file")
    all_good &= check_file(".gcloudignore", "GCloud ignore file")
    all_good &= check_file("requirements.txt", "Python requirements")
    all_good &= check_file("deploy.sh", "Deployment script")
    all_good &= check_file("test-local.sh", "Local test script")
    all_good &= check_file("DEPLOYMENT.md", "Deployment guide")
    print()
    
    # Check application files
    print("📱 Application Files:")
    all_good &= check_file("app.py", "Flask application")
    all_good &= check_directory("templates", "HTML templates")
    all_good &= check_directory("static", "Static files (CSS/JS)")
    print()
    
    # Check resources
    print("📚 Exam Resources:")
    if check_directory("resources", "Exam JSON files"):
        check_json_files("resources")
    else:
        all_good = False
    print()
    
    # Check scripts are executable
    print("🔧 Script Permissions:")
    deploy_exec = os.access("deploy.sh", os.X_OK)
    test_exec = os.access("test-local.sh", os.X_OK)
    print(f"{'✓' if deploy_exec else '✗'} deploy.sh is executable")
    print(f"{'✓' if test_exec else '✗'} test-local.sh is executable")
    all_good &= deploy_exec and test_exec
    print()
    
    # Summary
    print("=" * 60)
    if all_good:
        print("✅ All checks passed! Ready for deployment.")
        print()
        print("Next steps:")
        print("  1. Local test: ./test-local.sh")
        print("  2. Deploy: ./deploy.sh YOUR-PROJECT-ID")
        print("  3. See DEPLOYMENT.md for detailed instructions")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        sys.exit(1)
    print("=" * 60)

if __name__ == "__main__":
    main()
