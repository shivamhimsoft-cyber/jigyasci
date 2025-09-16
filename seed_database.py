from seed_users import create_seed_users
from seed_opportunities import create_seed_opportunities
import sys

def main():
    """Main function to run all seeders"""
    print("Starting database seeding process...")
    
    # Create seed users first
    create_seed_users()
    
    # Create seed opportunities
    create_seed_opportunities()
    
    print("Database seeding completed successfully!")

if __name__ == "__main__":
    main()