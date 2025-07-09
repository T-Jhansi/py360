#!/usr/bin/env python
"""
Setup script for Intelipro Insurance Policy Renewal System Backend
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description=""):
    """Run a shell command and handle errors"""
    print(f"🔄 {description or command}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(f"✅ {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr}")
        return False

def check_requirements():
    """Check if required software is installed"""
    print("🔍 Checking system requirements...")
    
    requirements = {
        'python': 'python --version',
        'pip': 'pip --version',
        'postgresql': 'psql --version',
        'redis': 'redis-cli --version'
    }
    
    missing = []
    for name, command in requirements.items():
        if not run_command(command, f"Checking {name}"):
            missing.append(name)
    
    if missing:
        print(f"❌ Missing requirements: {', '.join(missing)}")
        print("Please install the missing software before continuing.")
        return False
    
    print("✅ All requirements satisfied!")
    return True

def setup_virtual_environment():
    """Set up Python virtual environment"""
    print("🐍 Setting up virtual environment...")
    
    if os.path.exists('venv'):
        print("Virtual environment already exists")
        return True
    
    if not run_command('python -m venv venv', "Creating virtual environment"):
        return False
    
    print("✅ Virtual environment created!")
    return True

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    
    # Determine the correct pip command based on OS
    pip_cmd = 'venv\\Scripts\\pip' if os.name == 'nt' else 'venv/bin/pip'
    
    if not run_command(f'{pip_cmd} install --upgrade pip', "Upgrading pip"):
        return False
    
    if not run_command(f'{pip_cmd} install -r requirements.txt', "Installing dependencies"):
        return False
    
    print("✅ Dependencies installed!")
    return True

def setup_environment():
    """Set up environment configuration"""
    print("⚙️ Setting up environment configuration...")
    
    if not os.path.exists('.env'):
        if os.path.exists('env.example'):
            shutil.copy('env.example', '.env')
            print("✅ Environment file created from template")
            print("📝 Please edit .env file with your configuration")
        else:
            print("❌ env.example file not found")
            return False
    else:
        print("Environment file already exists")
    
    return True

def setup_database():
    """Set up database"""
    print("🗄️ Setting up database...")
    
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    # Run Django migrations
    python_cmd = 'venv\\Scripts\\python' if os.name == 'nt' else 'venv/bin/python'
    
    if not run_command(f'{python_cmd} manage.py makemigrations', "Creating migrations"):
        return False
    
    if not run_command(f'{python_cmd} manage.py migrate', "Running migrations"):
        return False
    
    print("✅ Database setup completed!")
    return True

def create_superuser():
    """Create Django superuser"""
    print("👤 Creating superuser...")
    
    python_cmd = 'venv\\Scripts\\python' if os.name == 'nt' else 'venv/bin/python'
    
    print("Please create a superuser account:")
    if not run_command(f'{python_cmd} manage.py createsuperuser', "Creating superuser"):
        print("❌ Failed to create superuser")
        return False
    
    print("✅ Superuser created!")
    return True

def collect_static():
    """Collect static files"""
    print("📁 Collecting static files...")
    
    python_cmd = 'venv\\Scripts\\python' if os.name == 'nt' else 'venv/bin/python'
    
    if not run_command(f'{python_cmd} manage.py collectstatic --noinput', "Collecting static files"):
        return False
    
    print("✅ Static files collected!")
    return True

def load_initial_data():
    """Load initial data fixtures"""
    print("📊 Loading initial data...")
    
    python_cmd = 'venv\\Scripts\\python' if os.name == 'nt' else 'venv/bin/python'
    
    # Check if fixtures exist
    fixtures_path = Path('fixtures')
    if fixtures_path.exists():
        for fixture_file in fixtures_path.glob('*.json'):
            run_command(f'{python_cmd} manage.py loaddata {fixture_file}', f"Loading {fixture_file.name}")
    
    print("✅ Initial data loaded!")
    return True

def print_next_steps():
    """Print next steps for the user"""
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your configuration")
    print("2. Set up your database credentials")
    print("3. Configure third-party API keys")
    print("4. Start the development server:")
    
    if os.name == 'nt':
        print("   venv\\Scripts\\python manage.py runserver")
        print("\n5. Start Celery worker (in another terminal):")
        print("   venv\\Scripts\\celery -A renewal_backend worker -l info")
        print("\n6. Start Celery beat (in another terminal):")
        print("   venv\\Scripts\\celery -A renewal_backend beat -l info")
    else:
        print("   source venv/bin/activate")
        print("   python manage.py runserver")
        print("\n5. Start Celery worker (in another terminal):")
        print("   source venv/bin/activate")
        print("   celery -A renewal_backend worker -l info")
        print("\n6. Start Celery beat (in another terminal):")
        print("   source venv/bin/activate")
        print("   celery -A renewal_backend beat -l info")
    
    print("\n🌐 Access points:")
    print("   - API: http://localhost:8000/api/")
    print("   - Admin: http://localhost:8000/admin/")
    print("   - Docs: http://localhost:8000/api/docs/")
    print("   - Health: http://localhost:8000/health/")

def main():
    """Main setup function"""
    print("🚀 Intelipro Insurance Policy Renewal System - Backend Setup")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists('manage.py'):
        print("❌ manage.py not found. Please run this script from the project root directory.")
        sys.exit(1)
    
    # Run setup steps
    steps = [
        ("Checking requirements", check_requirements),
        ("Setting up virtual environment", setup_virtual_environment),
        ("Installing dependencies", install_dependencies),
        ("Setting up environment", setup_environment),
        ("Setting up database", setup_database),
        ("Collecting static files", collect_static),
        ("Loading initial data", load_initial_data),
    ]
    
    for description, func in steps:
        print(f"\n{description}...")
        if not func():
            print(f"❌ Failed at step: {description}")
            sys.exit(1)
    
    # Optional superuser creation
    print("\n" + "=" * 60)
    create_superuser_choice = input("Do you want to create a superuser? (y/n): ").lower()
    if create_superuser_choice == 'y':
        create_superuser()
    
    print_next_steps()

if __name__ == '__main__':
    main() 